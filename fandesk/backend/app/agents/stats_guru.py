"""Stats Guru: answers IPL questions by writing SQL over ipl.db (text-to-SQL)."""

from ..llm import LLMClient, RunContext
from ..tools import sql_tools
from ..tools.sql_tools import SqlTools
from .loop import run_agent

MAX_CALLS = 5

SYSTEM_PROMPT = """You are Stats Guru, an IPL cricket statistician. You answer only from the IPL \
database, using the tools:
1. Call get_schema first to see the views and columns.
2. Write one focused SQLite query with run_sql. Prefer the views (batting_stats, bowling_stats, \
team_results) over raw deliveries. Filter seasons with season_year. Use LIKE for player names you \
aren't sure of (e.g. batter LIKE '%Kohli%').
3. If a query errors or returns nothing, fix it and try once more.

Answer in two to five short sentences or a short numbered list, with the actual numbers from the \
rows. Never invent figures. If the data can't answer the question, say so plainly.
Write plain text only: no Markdown, no asterisks, no headings."""


async def run(ctx: RunContext, llm: LLMClient, tools: SqlTools, model: str, task: str) -> str:
    def note_source(name, _args, output):
        if name == "run_sql" and output.ok and "ipl.db" not in ctx.sources:
            ctx.sources.append("ipl.db")

    return await run_agent(
        ctx,
        llm,
        node="stats_guru",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Task: {task}\n\nOriginal question: {ctx.question}",
        tool_specs=sql_tools.SPECS,
        handlers=tools.handlers(),
        max_calls=MAX_CALLS,
        on_tool_result=note_source,
    )
