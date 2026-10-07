import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, ipl_db, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("MOCK_LATENCY_SCALE", "0")
    monkeypatch.setenv("IPL_DB_PATH", str(ipl_db))
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "app.db"))
    from app import config

    config.get_settings.cache_clear()
    import importlib

    import app.main as main

    importlib.reload(main)
    with TestClient(main.app) as c:
        yield c
    config.get_settings.cache_clear()


def read_sse(response) -> list[dict]:
    return [json.loads(line[5:]) for line in response.text.splitlines() if line.startswith("data:")]


def test_ask_streams_events_and_saves_history(client):
    with client.stream("POST", "/api/ask", json={"question": "Top 5 run-scorers for CSK across all IPL seasons?"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        r.read()
        events = read_sse(r)
    assert events[0]["type"] == "request.received"
    assert events[0]["data"]["mock"] is True  # no API key: forced to mock
    assert events[-1]["type"] == "request.completed"
    assert [e["seq"] for e in events] == list(range(len(events)))

    history = client.get("/api/requests").json()
    assert history[0]["id"] == events[0]["request_id"]
    assert history[0]["route"] == "sports"

    detail = client.get(f"/api/requests/{events[0]['request_id']}").json()
    assert len(detail["events"]) == len(events)


def test_config_reports_live_unavailable_without_key(client):
    cfg = client.get("/api/config").json()
    assert cfg == {**cfg, "live_available": False, "default_mock": True}


def test_spend_and_health(client):
    assert client.get("/api/spend").json() == {"spent_usd": 0.0, "budget_usd": 1.0}
    assert client.get("/health").json()["ipl_db"] is True


def test_unknown_request_is_404(client):
    assert client.get("/api/requests/nope").status_code == 404


def test_empty_question_is_rejected(client):
    assert client.post("/api/ask", json={"question": ""}).status_code == 422
