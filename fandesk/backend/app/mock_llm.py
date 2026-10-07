"""Scripted stand-in for the model, for the UI's Mock switch.

Only the model's turns are scripted: which route to take, which tool to call
with which arguments. The tools themselves still run for real (SQL against
ipl.db, live Wikipedia), and the final answer is assembled from whatever
they actually returned. Scripts exist for the six demo questions only.
"""

import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field

from .llm import LLMResult, ToolCall

# Notional per-million-token prices so the UI still shows a plausible cost.
# Mock runs are never counted against the budget.
NOTIONAL = {"supervisor": (0.05, 0.40), "agent": (1.00, 5.00)}


@dataclass
class Script:
    match: re.Pattern
    route: str
    reason: str
    task: str
    steps: list[tuple[str, dict]] = field(default_factory=list)
    intro: str = ""


SCRIPTS = [
    Script(
        re.compile(r"csk|run-?scorers", re.I),
        "sports",
        "Asks for IPL batting totals for one franchise, which is structured stats data.",
        "Top 5 run-scorers for Chennai Super Kings across all IPL seasons",
        [
            ("get_schema", {}),
            ("run_sql", {"sql": "SELECT batter, SUM(runs) AS runs\nFROM batting_stats\n"
                                "WHERE team = 'Chennai Super Kings'\nGROUP BY batter\n"
                                "ORDER BY runs DESC\nLIMIT 5"}),
        ],
        "Chennai Super Kings' top run-scorers across all IPL seasons:",
    ),
    Script(
        re.compile(r"wickets.*20\d\d|20\d\d.*wickets", re.I),
        "sports",
        "A season-level bowling record from the IPL, answerable from the stats database.",
        "Bowlers with the most wickets in IPL 2023",
        [
            ("get_schema", {}),
            ("run_sql", {"sql": "SELECT bowler, team, SUM(wickets) AS wickets\nFROM bowling_stats\n"
                                "WHERE season_year = 2023\nGROUP BY bowler, team\n"
                                "ORDER BY wickets DESC\nLIMIT 5"}),
        ],
        "Most wickets in IPL 2023:",
    ),
    Script(
        re.compile(r"vikram", re.I),
        "movies",
        "Asks who directed a film and what it is about: a movie question.",
        "Director and plot of the 2022 film Vikram",
        [
            ("search_wikipedia", {"query": "Vikram 2022 film"}),
            ("get_page_summary", {"title": "Vikram (2022 film)"}),
        ],
    ),
    Script(
        re.compile(r"lagaan", re.I),
        "movies",
        "Mentions cricket, but the task is recommending films, so it is a movie question.",
        "Recommend films about cricket similar to Lagaan",
        [
            ("search_wikipedia", {"query": "Indian cricket sports drama film"}),
            ("get_page_summary", {"title": "Iqbal (film)"}),
            ("get_page_summary", {"title": "83 (film)"}),
        ],
    ),
    Script(
        re.compile(r"dhoni", re.I),
        "sports",
        "Dhoni most likely means MS Dhoni the cricketer, whose IPL record is in the stats database; "
        "a question about the Dhoni film would go to Cinema Buff.",
        "IPL career summary for MS Dhoni",
        [
            ("get_schema", {}),
            ("run_sql", {"sql": "SELECT COUNT(DISTINCT match_id) AS matches,\n       SUM(runs) AS runs,\n"
                                "       ROUND(100.0 * SUM(runs) / SUM(balls), 1) AS strike_rate\n"
                                "FROM batting_stats\nWHERE batter = 'MS Dhoni'"}),
        ],
        "MS Dhoni's IPL career:",
    ),
    Script(
        re.compile(r"poem|rain", re.I),
        "out_of_scope",
        "Creative writing is neither IPL cricket nor movies.",
        "Write a poem about rain",
    ),
]

FALLBACK = Script(
    re.compile(""),
    "out_of_scope",
    "Mock mode only has scripts for the six sample questions; switch to Live for anything else.",
    "Unscripted question",
)


def _script_for(question: str) -> Script:
    return next((s for s in SCRIPTS if s.match.search(question)), FALLBACK)


def _tokens(messages: list[dict]) -> int:
    return max(1, sum(len(str(m.get("content") or "")) for m in messages) // 4)


def _call(name: str, args: dict) -> ToolCall:
    raw = json.dumps(args)
    return ToolCall(id=f"call_{uuid.uuid4().hex[:12]}", name=name, arguments=args, raw_arguments=raw)


def _rows_answer(intro: str, tool_text: str) -> str:
    if tool_text.startswith("ERROR"):
        return f"The stats query failed: {tool_text[7:].strip()}"
    data = json.loads(tool_text)
    cols, rows = data["columns"], data["rows"]
    if not rows:
        return "The stats database returned no rows for that."
    if len(rows) == 1:
        return intro + " " + ", ".join(f"{c.replace('_', ' ')} {v}" for c, v in zip(cols, rows[0])) + "."
    lines = [f"{i}. " + " — ".join(str(v) for v in r) for i, r in enumerate(rows, 1)]
    return intro + "\n" + "\n".join(lines)


def _pages_answer(tool_texts: list[str]) -> str:
    parts, titles = [], []
    for text in tool_texts:
        m = re.match(r'<page title="([^"]+)">\n(.*)\n</page>', text, re.S)
        if not m:
            continue
        title, extract = m.group(1), m.group(2)
        sentences = re.split(r"(?<=[.!?])\s+", extract.strip())
        parts.append(" ".join(sentences[:2]))
        titles.append(title)
    if not parts:
        return "I couldn't reach Wikipedia for that one."
    return "\n\n".join(parts) + "\n\nSources: " + ", ".join(titles)


async def mock_complete(*, question, agent, messages, tool_choice, latency_scale) -> LLMResult:
    script = _script_for(question)
    role = "supervisor" if agent == "supervisor" else "agent"
    await asyncio.sleep((0.75 if role == "supervisor" else 1.2) * latency_scale)

    content: str | None = None
    calls: list[ToolCall] = []
    if agent == "supervisor":
        calls = [_call("route", {"route": script.route, "reason": script.reason, "task": script.task})]
    else:
        step = sum(1 for m in messages if m["role"] == "assistant")
        if step < len(script.steps) and tool_choice != "none":
            calls = [_call(*script.steps[step])]
        else:
            tool_texts = [m["content"] for m in messages if m["role"] == "tool"]
            if agent == "stats_guru":
                content = _rows_answer(script.intro, tool_texts[-1] if tool_texts else "ERROR: no data")
            else:
                content = _pages_answer([t for t in tool_texts if t.startswith("<page")])

    prompt_tokens = _tokens(messages)
    completion_tokens = max(20, len(content or json.dumps([c.arguments for c in calls])) // 4)
    pin, pout = NOTIONAL[role]
    return LLMResult(
        content=content,
        tool_calls=calls,
        model=f"mock/{role}",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=(prompt_tokens * pin + completion_tokens * pout) / 1e6,
        generation_id=None,
    )
