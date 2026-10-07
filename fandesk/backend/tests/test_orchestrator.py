import pytest

from app.config import Settings
from app.events import Emitter
from app.llm import LLMClient, LLMResult, ToolCall
from app.orchestrator import Orchestrator
from app.store import Store
from app.tools import ToolOutput
from app.tools.sql_tools import SqlTools


class FakeWiki:
    async def search_wikipedia(self, args):
        return ToolOutput(text="<search_results>\n- Vikram (2022 film): film\n</search_results>", summary="1 results")

    async def get_page_summary(self, args):
        title = args["title"]
        return ToolOutput(
            text=f'<page title="{title}">\nVikram is a 2022 film directed by Lokesh Kanagaraj. It stars Kamal Haasan.\n</page>',
            summary="80 characters",
            extra={"title": title},
        )

    def handlers(self):
        return {"search_wikipedia": self.search_wikipedia, "get_page_summary": self.get_page_summary}


@pytest.fixture
def setup(tmp_path, ipl_db):
    settings = Settings(
        openrouter_api_key="", mock_latency_scale=0, ipl_db_path=ipl_db, app_db_path=tmp_path / "app.db",
        daily_budget_usd=1.0, max_cost_per_request_usd=0.1,
    )
    store = Store(settings.app_db_path)
    llm = LLMClient(settings, store)
    orch = Orchestrator(settings, store, llm, SqlTools(ipl_db), FakeWiki())
    return settings, store, llm, orch


async def run(orch, store, question, mock=True, request_id="a" * 32):
    store.create_request(request_id, question, mock)
    emitter = Emitter(request_id, store)
    await orch.run(request_id, question, mock, emitter)
    return store.get_request(request_id)


def types(found):
    return [e["type"] for e in found["events"]]


async def test_stats_question_runs_real_sql_in_mock_mode(setup):
    _, store, _, orch = setup
    found = await run(orch, store, "Who took the most wickets in IPL 2023?")
    assert types(found) == [
        "request.received", "llm.call", "supervisor.decision", "agent.start",
        "llm.call", "tool.call", "tool.result", "llm.call", "tool.call", "tool.result", "llm.call",
        "agent.answer", "request.completed",
    ]
    answer = next(e for e in found["events"] if e["type"] == "agent.answer")
    assert answer["node"] == "stats_guru"
    assert "Z Bowler" in answer["data"]["text"]  # came from the real query, not the script
    assert answer["data"]["sources"] == ["ipl.db"]
    s = found["summary"]
    assert s["status"] == "completed" and s["route"] == "sports" and s["llm_calls"] == 4 and s["mock"]


async def test_movie_question_cites_pages(setup):
    _, store, _, orch = setup
    found = await run(orch, store, "Who directed Vikram (2022) and what's it about?")
    answer = next(e for e in found["events"] if e["type"] == "agent.answer")
    assert answer["node"] == "cinema_buff"
    assert "Lokesh Kanagaraj" in answer["data"]["text"]
    assert answer["data"]["sources"] == ["Vikram (2022 film)"]


async def test_out_of_scope_makes_one_llm_call_and_no_specialist(setup):
    _, store, _, orch = setup
    found = await run(orch, store, "Write me a poem about rain")
    assert types(found) == ["request.received", "llm.call", "supervisor.decision", "agent.answer", "request.completed"]
    assert found["summary"]["llm_calls"] == 1
    assert found["events"][3]["node"] == "out_of_scope"


async def test_mock_runs_are_not_counted_as_spend(setup):
    _, store, _, orch = setup
    await run(orch, store, "Write me a poem about rain")
    assert store.spend_today() == 0.0


def _fake_live(results):
    it = iter(results)

    async def fake(model, messages, tools, tool_choice):
        return next(it)

    return fake


def _result(tool_calls=None, content=None, cost=0.001):
    return LLMResult(content=content, tool_calls=tool_calls or [], model="test/model",
                     prompt_tokens=100, completion_tokens=10, cost=cost)


async def test_supervisor_retries_once_then_declines(setup, monkeypatch):
    _, store, llm, orch = setup
    bad = ToolCall(id="1", name="route", arguments={"route": "weather"}, raw_arguments="{}")
    monkeypatch.setattr(llm, "_live", _fake_live([_result([bad]), _result()]))
    found = await run(orch, store, "Anything", mock=False)
    decision = next(e for e in found["events"] if e["type"] == "supervisor.decision")
    assert decision["data"]["route"] == "out_of_scope"
    assert found["summary"]["llm_calls"] == 2


async def test_budget_guard_blocks_before_the_call(setup, monkeypatch):
    settings, store, llm, orch = setup
    # A previous live request already used the whole daily budget.
    await run(orch, store, "Write me a poem about rain", mock=True, request_id="b" * 32)
    store.update_request("b" * 32, mock=0)
    store.add_event({"request_id": "b" * 32, "seq": 99, "ts": __import__("app.store", fromlist=["x"]).utc_now(),
                     "type": "llm.call", "node": "supervisor", "data": {"cost": settings.daily_budget_usd}})

    async def must_not_call(*a, **k):
        raise AssertionError("LLM was called despite the budget")

    monkeypatch.setattr(llm, "_live", must_not_call)
    found = await run(orch, store, "Who took the most wickets in IPL 2023?", mock=False)
    assert types(found) == ["request.received", "budget.blocked"]
    assert found["summary"]["status"] == "blocked"


async def test_live_failure_becomes_request_failed(setup, monkeypatch):
    _, store, llm, orch = setup

    async def boom(*a, **k):
        raise RuntimeError("upstream exploded")

    monkeypatch.setattr(llm, "_live", boom)
    found = await run(orch, store, "Anything", mock=False)
    assert types(found)[-1] == "request.failed"
    assert found["summary"]["status"] == "failed"
