"""One place every LLM call goes through: budget guard, cost capture, llm.call events.

Live calls use the OpenAI SDK against OpenRouter's OpenAI-compatible API.
OpenRouter reports the real cost of each call in `usage.cost`, so no price
tables are needed. Mock calls return scripted turns from mock_llm.py.
"""

import json
import logging
import time
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from .config import Settings
from .events import Emitter
from .store import Store

log = logging.getLogger("fandesk.llm")


class BudgetBlocked(Exception):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    raw_arguments: str


@dataclass
class LLMResult:
    content: str | None
    tool_calls: list[ToolCall]
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    generation_id: str | None = None

    def assistant_message(self) -> dict:
        msg: dict = {"role": "assistant", "content": self.content or ""}
        if self.tool_calls:
            msg["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.raw_arguments}}
                for c in self.tool_calls
            ]
        return msg


@dataclass
class RunContext:
    """Per-request state shared by the supervisor and the specialist."""

    request_id: str
    question: str
    mock: bool
    emitter: Emitter
    cost: float = 0.0
    tokens: int = 0
    calls: int = 0
    sources: list[str] = field(default_factory=list)


def _parse_args(raw: str | None) -> dict:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


class LLMClient:
    def __init__(self, settings: Settings, store: Store):
        self.settings = settings
        self.store = store
        self._client = (
            AsyncOpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)
            if settings.live_available
            else None
        )

    def check_budget(self, ctx: RunContext) -> None:
        """Called before every live LLM call. Mock calls never spend money."""
        if ctx.mock:
            return
        spent = self.store.spend_today()
        if spent >= self.settings.daily_budget_usd:
            raise BudgetBlocked(
                f"Today's spend ${spent:.4f} has reached the daily budget of ${self.settings.daily_budget_usd:.2f}."
            )
        if ctx.cost >= self.settings.max_cost_per_request_usd:
            raise BudgetBlocked(
                f"This request has spent ${ctx.cost:.4f}, the per-request limit of "
                f"${self.settings.max_cost_per_request_usd:.2f}."
            )

    async def call(
        self,
        ctx: RunContext,
        *,
        agent: str,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ) -> LLMResult:
        self.check_budget(ctx)
        started = time.perf_counter()
        if ctx.mock:
            from .mock_llm import mock_complete

            result = await mock_complete(
                question=ctx.question,
                agent=agent,
                messages=messages,
                tool_choice=tool_choice,
                latency_scale=self.settings.mock_latency_scale,
            )
        else:
            result = await self._live(model, messages, tools, tool_choice)
        ms = round((time.perf_counter() - started) * 1000)

        ctx.calls += 1
        ctx.cost += result.cost
        ctx.tokens += result.prompt_tokens + result.completion_tokens
        ctx.emitter.emit(
            "llm.call",
            agent,
            {
                "agent": agent,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "cost": result.cost,
                "ms": ms,
                "generation_id": result.generation_id,
                "mock": ctx.mock,
            },
        )
        return result

    async def _live(self, model, messages, tools, tool_choice) -> LLMResult:
        if self._client is None:
            raise RuntimeError("Live mode needs OPENROUTER_API_KEY in .env.")
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": 1200,
            # Ask OpenRouter to include the call's real cost in `usage`.
            "extra_body": {"usage": {"include": True}},
        }
        if tools:
            kwargs["tools"] = tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
        if model.startswith("openai/gpt-5"):
            # Routing is easy; keep reasoning models quick and cheap.
            kwargs["extra_body"]["reasoning"] = {"effort": "low"}

        resp = await self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message
        usage = resp.usage
        cost = getattr(usage, "cost", None) if usage else None
        if cost is None and usage is not None:
            cost = (usage.model_extra or {}).get("cost")
        if cost is None:
            log.warning("OpenRouter response had no usage.cost", extra={"model": model})

        return LLMResult(
            content=choice.content,
            tool_calls=[
                ToolCall(id=c.id, name=c.function.name, arguments=_parse_args(c.function.arguments),
                         raw_arguments=c.function.arguments or "{}")
                for c in (choice.tool_calls or [])
            ],
            model=resp.model or model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            cost=float(cost or 0.0),
            generation_id=resp.id,
        )
