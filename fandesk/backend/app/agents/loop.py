"""The plain agent loop, no framework:
call model -> run any tools it asked for -> hand results back -> repeat,
until it answers or reaches its LLM-call limit.
"""

import time
from collections.abc import Awaitable, Callable

from ..llm import LLMClient, RunContext
from ..telemetry import span
from ..tools import ToolOutput

ToolHandler = Callable[[dict], Awaitable[ToolOutput]]


async def run_agent(
    ctx: RunContext,
    llm: LLMClient,
    *,
    node: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    tool_specs: list[dict],
    handlers: dict[str, ToolHandler],
    max_calls: int,
    on_tool_result: Callable[[str, dict, ToolOutput], None] | None = None,
) -> str:
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    for call_no in range(1, max_calls + 1):
        last = call_no == max_calls
        # On the final allowed call, forbid tools so the agent must answer.
        result = await llm.call(
            ctx,
            agent=node,
            model=model,
            messages=messages,
            tools=tool_specs,
            tool_choice="none" if last else "auto",
        )
        if not result.tool_calls:
            return (result.content or "").strip() or "I couldn't find an answer to that."

        messages.append(result.assistant_message())
        for call in result.tool_calls:
            ctx.emitter.emit("tool.call", node, {"name": call.name, "args": call.arguments})
            started = time.perf_counter()
            with span(f"tool.{call.name}", "TOOL", **{"tool.name": call.name, "input.value": call.raw_arguments}) as s:
                handler = handlers.get(call.name)
                if handler is None:
                    output = ToolOutput(text=f"ERROR: unknown tool {call.name}.", summary="Unknown tool", ok=False)
                else:
                    output = await handler(call.arguments)
                s.set_attribute("output.value", output.text[:4000])
            ms = round((time.perf_counter() - started) * 1000)
            ctx.emitter.emit(
                "tool.result",
                node,
                {"name": call.name, "summary": output.summary, "ms": ms, "ok": output.ok, **output.extra},
            )
            if on_tool_result:
                on_tool_result(call.name, call.arguments, output)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output.text})

    return "I ran out of steps before finishing. Try asking a narrower question."
