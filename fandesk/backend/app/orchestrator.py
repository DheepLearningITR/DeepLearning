"""Runs one request end to end: supervisor routes, one specialist answers.

The specialist's answer goes straight back to the user; there is no extra
supervisor call to summarise it.
"""

import logging
import time

from opentelemetry import trace

from .agents import cinema_buff, stats_guru, supervisor
from .config import Settings
from .events import Emitter
from .llm import BudgetBlocked, LLMClient, RunContext
from .store import Store
from .telemetry import request_id_var, span
from .tools.sql_tools import SqlTools
from .tools.wiki_tools import WikiTools

log = logging.getLogger("fandesk.orchestrator")

DECLINE = (
    "I can only help with IPL cricket stats and movies. "
    "Try asking about a season, a player, a team or a film."
)
ROUTE_NODE = {"sports": "stats_guru", "movies": "cinema_buff", "out_of_scope": "out_of_scope"}


class Orchestrator:
    def __init__(self, settings: Settings, store: Store, llm: LLMClient, sql: SqlTools, wiki: WikiTools):
        self.settings = settings
        self.store = store
        self.llm = llm
        self.sql = sql
        self.wiki = wiki

    async def run(self, request_id: str, question: str, mock: bool, emitter: Emitter) -> None:
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        ctx = RunContext(request_id=request_id, question=question, mock=mock, emitter=emitter)
        status, route = "failed", None
        try:
            with span("request", "CHAIN", root=True, **{"input.value": question, "fandesk.mock": mock}) as root:
                emitter.emit("request.received", "user", {"question": question, "mock": mock})
                try:
                    with span("supervisor.route", "CHAIN"):
                        decision = await supervisor.decide(ctx, self.llm, self.settings.supervisor_model)
                    route = decision.route
                    root.set_attribute("route", route)
                    root.set_attribute("reason", decision.reason)
                    self.store.update_request(request_id, route=route, reason=decision.reason)
                    emitter.emit(
                        "supervisor.decision",
                        "supervisor",
                        {"route": route, "reason": decision.reason, "task": decision.task},
                    )

                    node = ROUTE_NODE[route]
                    if route == "out_of_scope":
                        answer = DECLINE
                    else:
                        emitter.emit("agent.start", node, {"task": decision.task})
                        with span(f"agent.{node}", "AGENT", **{"input.value": decision.task}) as agent_span:
                            if route == "sports":
                                answer = await stats_guru.run(ctx, self.llm, self.sql, self.settings.agent_model, decision.task)
                            else:
                                answer = await cinema_buff.run(ctx, self.llm, self.wiki, self.settings.agent_model, decision.task)
                            agent_span.set_attribute("output.value", answer)
                    emitter.emit("agent.answer", node, {"text": answer, "sources": ctx.sources})

                    latency = round((time.perf_counter() - started) * 1000)
                    root.set_attribute("cost_usd", ctx.cost)
                    root.set_attribute("output.value", answer)
                    emitter.emit(
                        "request.completed",
                        "response",
                        {"total_cost": ctx.cost, "tokens": ctx.tokens, "llm_calls": ctx.calls, "latency_ms": latency},
                    )
                    status = "completed"
                except BudgetBlocked as e:
                    status = "blocked"
                    emitter.emit("budget.blocked", "response", {"message": str(e)})
                except Exception as e:  # any failure ends the request with a visible event
                    log.exception("request failed")
                    root.record_exception(e)
                    root.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    emitter.emit("request.failed", "response", {"message": _friendly(e)})
        finally:
            self.store.update_request(
                request_id,
                status=status,
                latency_ms=round((time.perf_counter() - started) * 1000),
                cost_usd=ctx.cost,
                tokens=ctx.tokens,
                llm_calls=ctx.calls,
            )
            request_id_var.reset(token)


def _friendly(e: Exception) -> str:
    name = type(e).__name__
    text = str(e) or name
    if "AuthenticationError" in name:
        return "OpenRouter rejected the API key. Check OPENROUTER_API_KEY in .env."
    if "RateLimitError" in name:
        return "OpenRouter is rate-limiting requests. Wait a moment and try again."
    if "NotFoundError" in name and "model" in text.lower():
        return "OpenRouter doesn't recognise one of the model IDs. Check SUPERVISOR_MODEL and AGENT_MODEL in .env."
    return text[:300]
