"""app.db: requests and their events. Spend is summed from llm.call events."""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id          TEXT PRIMARY KEY,
    question    TEXT NOT NULL,
    mock        INTEGER NOT NULL DEFAULT 0,
    route       TEXT,
    reason      TEXT,
    status      TEXT NOT NULL DEFAULT 'running',
    created_at  TEXT NOT NULL,
    latency_ms  INTEGER NOT NULL DEFAULT 0,
    cost_usd    REAL NOT NULL DEFAULT 0,
    tokens      INTEGER NOT NULL DEFAULT 0,
    llm_calls   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS events (
    request_id  TEXT NOT NULL REFERENCES requests(id),
    seq         INTEGER NOT NULL,
    ts          TEXT NOT NULL,
    type        TEXT NOT NULL,
    node        TEXT NOT NULL,
    data        TEXT NOT NULL,
    PRIMARY KEY (request_id, seq)
);
CREATE INDEX IF NOT EXISTS events_type_ts ON events(type, ts);
"""

SUMMARY_COLUMNS = "id, question, mock, route, status, created_at, latency_ms, cost_usd, tokens, llm_calls"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    def _summary(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["mock"] = bool(d["mock"])
        return d

    def create_request(self, request_id: str, question: str, mock: bool) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO requests (id, question, mock, created_at) VALUES (?, ?, ?, ?)",
                (request_id, question, int(mock), utc_now()),
            )

    def add_event(self, event: dict) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO events (request_id, seq, ts, type, node, data) VALUES (?, ?, ?, ?, ?, ?)",
                (event["request_id"], event["seq"], event["ts"], event["type"], event["node"], json.dumps(event["data"])),
            )

    def update_request(self, request_id: str, **fields) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._lock, self._conn:
            self._conn.execute(f"UPDATE requests SET {cols} WHERE id = ?", (*fields.values(), request_id))

    def list_requests(self, limit: int = 100) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {SUMMARY_COLUMNS} FROM requests ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._summary(r) for r in rows]

    def get_request(self, request_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(f"SELECT {SUMMARY_COLUMNS} FROM requests WHERE id = ?", (request_id,)).fetchone()
            if row is None:
                return None
            events = self._conn.execute(
                "SELECT request_id, seq, ts, type, node, data FROM events WHERE request_id = ? ORDER BY seq",
                (request_id,),
            ).fetchall()
        return {
            "summary": self._summary(row),
            "events": [{**dict(e), "data": json.loads(e["data"])} for e in events],
        }

    def spend_today(self) -> float:
        """Real (non-mock) LLM spend for the current UTC day."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock:
            (total,) = self._conn.execute(
                """
                SELECT COALESCE(SUM(json_extract(e.data, '$.cost')), 0)
                FROM events e JOIN requests r ON r.id = e.request_id
                WHERE e.type = 'llm.call' AND r.mock = 0 AND substr(e.ts, 1, 10) = ?
                """,
                (today,),
            ).fetchone()
        return float(total)

    def mark_interrupted(self) -> None:
        """Requests left 'running' by a previous process can never finish."""
        with self._lock, self._conn:
            self._conn.execute("UPDATE requests SET status = 'failed' WHERE status = 'running'")
