import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import get_settings
from .events import TERMINAL, Emitter
from .llm import LLMClient
from .orchestrator import Orchestrator
from .store import Store
from .telemetry import setup_logging, setup_tracing
from .tools.sql_tools import SqlTools
from .tools.wiki_tools import WikiTools

log = logging.getLogger("fandesk.api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    setup_tracing(settings.phoenix_collector_endpoint)
    store = Store(settings.app_db_path)
    store.mark_interrupted()
    wiki = WikiTools(settings.wiki_user_agent)
    app.state.store = store
    app.state.orchestrator = Orchestrator(settings, store, LLMClient(settings, store), SqlTools(settings.ipl_db_path), wiki)
    app.state.tasks = set()
    log.info(
        "started",
        extra={"live_available": settings.live_available, "ipl_db": str(settings.ipl_db_path),
               "ipl_db_present": settings.ipl_db_path.exists()},
    )
    yield
    await wiki.aclose()


app = FastAPI(title="FanDesk API", lifespan=lifespan)


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    # The UI's Live/Mock switch. Omitted means the server default (MOCK_LLM).
    mock: bool | None = None


@app.post("/api/ask")
async def ask(body: AskBody):
    question = body.question.strip()
    mock = settings.mock_llm if body.mock is None else body.mock
    if not settings.live_available:
        mock = True
    request_id = uuid.uuid4().hex
    store: Store = app.state.store
    store.create_request(request_id, question, mock)
    emitter = Emitter(request_id, store)

    # The run continues even if the browser disconnects, so History stays complete.
    task = asyncio.create_task(app.state.orchestrator.run(request_id, question, mock, emitter))
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)

    async def stream():
        while True:
            event = await emitter.queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] in TERMINAL:
                break

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/requests")
def list_requests(limit: int = 100):
    return app.state.store.list_requests(limit=min(limit, 500))


@app.get("/api/requests/{request_id}")
def get_request(request_id: str):
    found = app.state.store.get_request(request_id)
    if found is None:
        raise HTTPException(status_code=404, detail="No request with that ID.")
    return found


@app.get("/api/spend")
def spend():
    return {"spent_usd": app.state.store.spend_today(), "budget_usd": settings.daily_budget_usd}


@app.get("/api/config")
def config():
    return {
        "live_available": settings.live_available,
        "default_mock": settings.mock_llm or not settings.live_available,
        "phoenix_url": settings.phoenix_url,
        "supervisor_model": settings.supervisor_model,
        "agent_model": settings.agent_model,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ipl_db": settings.ipl_db_path.exists(),
        "live_available": settings.live_available,
    }
