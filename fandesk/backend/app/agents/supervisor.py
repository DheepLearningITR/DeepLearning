"""The supervisor only routes: one forced `route` tool call, retried once if invalid."""

import logging
from dataclasses import dataclass

from ..llm import LLMClient, RunContext
from ..tools import function_spec

log = logging.getLogger("fandesk.supervisor")

ROUTES = ("sports", "movies", "out_of_scope")

SYSTEM_PROMPT = """You are the supervisor of FanDesk, a help desk with two specialists:
- sports: Stats Guru answers questions about IPL cricket using a database of every IPL match \
(players, teams, seasons, runs, wickets, results).
- movies: Cinema Buff answers questions about films using Wikipedia (directors, cast, plots, \
recommendations).
Anything else is out_of_scope.

Route by the task, not by keywords. "Suggest films about cricket" is a movies task even though it \
mentions cricket. A bare name like "Tell me about Dhoni" is ambiguous: pick the most likely reading \
and say in the reason what you assumed.

Always call the `route` tool.
- `reason`: one sentence an intern can follow that explains WHY this route, naming the kind of \
question and where the answer lives, e.g. "Asks for an IPL season bowling record, which is in the \
stats database." Do not just restate the question.
- `task`: the question rewritten as a clear instruction for the specialist."""

ROUTE_TOOL = function_spec(
    "route",
    "Send the question to one specialist, or mark it out of scope.",
    {
        "route": {"type": "string", "enum": list(ROUTES)},
        "reason": {"type": "string", "description": "One sentence: why this route."},
        "task": {"type": "string", "description": "The question rewritten as a clear task."},
    },
    ["route", "reason", "task"],
)


@dataclass
class Decision:
    route: str
    reason: str
    task: str


async def decide(ctx: RunContext, llm: LLMClient, model: str) -> Decision:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ctx.question}]
    for attempt in (1, 2):
        result = await llm.call(
            ctx,
            agent="supervisor",
            model=model,
            messages=messages,
            tools=[ROUTE_TOOL],
            tool_choice={"type": "function", "function": {"name": "route"}},
        )
        call = next((c for c in result.tool_calls if c.name == "route"), None)
        if call and call.arguments.get("route") in ROUTES:
            args = call.arguments
            return Decision(
                route=args["route"],
                reason=str(args.get("reason") or "No reason given."),
                task=str(args.get("task") or ctx.question),
            )
        log.warning("supervisor returned no valid route", extra={"attempt": attempt})
    return Decision(
        route="out_of_scope",
        reason="The supervisor couldn't produce a valid route, so the question was declined.",
        task=ctx.question,
    )
