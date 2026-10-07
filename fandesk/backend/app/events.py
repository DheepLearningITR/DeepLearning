"""The event stream: every step is saved to app.db and pushed to the SSE queue."""

import asyncio
import logging
from dataclasses import dataclass, field

from .store import Store, utc_now

log = logging.getLogger("fandesk.events")

TERMINAL = {"request.completed", "request.failed", "budget.blocked"}


@dataclass
class Emitter:
    request_id: str
    store: Store
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    seq: int = 0

    def emit(self, type_: str, node: str, data: dict | None = None) -> dict:
        event = {
            "request_id": self.request_id,
            "seq": self.seq,
            "ts": utc_now(),
            "type": type_,
            "node": node,
            "data": data or {},
        }
        self.seq += 1
        self.store.add_event(event)
        self.queue.put_nowait(event)
        log.info("event", extra={"event_type": type_, "node": node})
        return event
