"""Stats Guru's tools over ipl.db.

Guardrails: read-only connection (mode=ro) plus PRAGMA query_only, a
SELECT/WITH-only check, LIMIT 50 applied by wrapping the query, and a 5-second
timeout enforced with a progress handler (sqlite3's `timeout=` is only a lock wait).
"""

import asyncio
import json
import re
import sqlite3
import time
from pathlib import Path

from . import ToolOutput, function_spec

ROW_LIMIT = 50
TIMEOUT_S = 5.0

VIEW_NOTES = {
    "batting_stats": "One row per batter per match. Sum runs/balls across rows for totals.",
    "bowling_stats": "One row per bowler per match. wickets counts only dismissals credited to the bowler.",
    "team_results": "One row per team per match, with the opponent and whether the team won.",
    "matches": "One row per match. season_year is the IPL year (e.g. 2008, 2020).",
    "deliveries": "Raw ball-by-ball rows. Prefer the views above.",
}

SPECS = [
    function_spec(
        "get_schema",
        "List the tables and views in the IPL database with their columns. Call this first.",
        {},
    ),
    function_spec(
        "run_sql",
        "Run one read-only SQLite SELECT (or WITH ... SELECT) query on the IPL database. "
        f"At most {ROW_LIMIT} rows come back.",
        {"sql": {"type": "string", "description": "A single SQLite SELECT statement."}},
        ["sql"],
    ),
]

_COMMENTS = re.compile(r"(--[^\n]*)|(/\*.*?\*/)", re.S)


class SqlGuardError(ValueError):
    pass


def clean_select(sql: str) -> str:
    """Return the query without comments or a trailing semicolon, or raise if it isn't one SELECT."""
    body = _COMMENTS.sub(" ", sql).strip().rstrip(";").strip()
    if not body:
        raise SqlGuardError("The query is empty.")
    if ";" in body:
        raise SqlGuardError("Only one statement is allowed.")
    first = body.split(None, 1)[0].upper()
    if first not in ("SELECT", "WITH"):
        raise SqlGuardError("Only SELECT or WITH queries are allowed.")
    return body


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"IPL database not found at {db_path}. Run scripts/load_ipl.py.")
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, check_same_thread=False)
    conn.execute("PRAGMA query_only = ON")
    return conn


def describe_schema(db_path: Path) -> str:
    conn = _connect(db_path)
    try:
        objects = conn.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        # Views first: they make the model's SQL far more reliable than raw ball-by-ball rows.
        objects.sort(key=lambda o: (o[1] != "view", o[0]))
        lines = []
        for name, kind in objects:
            cols = [f"{c[1]} {c[2] or ''}".strip() for c in conn.execute(f'PRAGMA table_info("{name}")')]
            note = VIEW_NOTES.get(name, "")
            lines.append(f"{kind.upper()} {name}({', '.join(cols)})" + (f"  -- {note}" if note else ""))
        seasons = conn.execute("SELECT MIN(season_year), MAX(season_year) FROM matches").fetchone()
        lines.append(f"-- Data covers IPL seasons {seasons[0]}–{seasons[1]}. Filter seasons with season_year.")
        lines.append("-- Team names are full names, e.g. 'Chennai Super Kings', 'Mumbai Indians'.")
        lines.append("-- Player names are as Cricsheet records them, e.g. 'MS Dhoni', 'V Kohli', 'RG Sharma'.")
        return "\n".join(lines)
    finally:
        conn.close()


def run_query(db_path: Path, sql: str) -> tuple[list[str], list[tuple]]:
    body = clean_select(sql)
    conn = _connect(db_path)
    deadline = time.monotonic() + TIMEOUT_S
    # Returning non-zero from the handler aborts the running statement.
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
    try:
        cur = conn.execute(f"SELECT * FROM ({body}) LIMIT {ROW_LIMIT}")
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            raise TimeoutError(f"The query took longer than {TIMEOUT_S:.0f} seconds.") from e
        raise
    finally:
        conn.close()


class SqlTools:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def get_schema(self, _: dict) -> ToolOutput:
        text = await asyncio.to_thread(describe_schema, self.db_path)
        n = sum(1 for line in text.splitlines() if line.startswith(("VIEW", "TABLE")))
        views = sum(1 for line in text.splitlines() if line.startswith("VIEW"))
        return ToolOutput(text=text, summary=f"{views} views, {n - views} tables")

    async def run_sql(self, args: dict) -> ToolOutput:
        sql = str(args.get("sql", ""))
        try:
            cols, rows = await asyncio.to_thread(run_query, self.db_path, sql)
        except (SqlGuardError, TimeoutError, sqlite3.Error) as e:
            return ToolOutput(text=f"ERROR: {e}", summary=f"Error: {e}", ok=False)
        payload = {"columns": cols, "rows": [list(r) for r in rows]}
        noun = "row" if len(rows) == 1 else "rows"
        return ToolOutput(
            text=json.dumps(payload, default=str),
            summary=f"{len(rows)} {noun}" + (" (limit reached)" if len(rows) == ROW_LIMIT else ""),
            extra={"columns": cols, "row_count": len(rows)},
        )

    def handlers(self):
        return {"get_schema": self.get_schema, "run_sql": self.run_sql}
