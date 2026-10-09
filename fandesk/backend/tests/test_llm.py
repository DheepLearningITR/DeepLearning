from types import SimpleNamespace

import pytest

from app.config import Settings
from app.llm import LLMClient, UpstreamError
from app.store import Store


def _resp(choices, error=None):
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=2, cost=0.0001, model_extra={})
    return SimpleNamespace(choices=choices, usage=usage, model="test/model", id="gen-1",
                           model_extra={"error": error} if error else {})


def _client(tmp_path, responses):
    settings = Settings(openrouter_api_key="sk-test", app_db_path=tmp_path / "app.db")
    llm = LLMClient(settings, Store(settings.app_db_path))
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        return responses[len(calls) - 1]

    llm._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return llm, calls


def _ok():
    msg = SimpleNamespace(content="hi", tool_calls=None)
    return _resp([SimpleNamespace(message=msg)])


async def test_empty_choices_are_retried_once(tmp_path):
    llm, calls = _client(tmp_path, [_resp(None, {"message": "Provider returned error"}), _ok()])
    result = await llm._live("test/model", [{"role": "user", "content": "x"}], None, None)
    assert result.content == "hi" and result.cost == 0.0001
    assert len(calls) == 2


async def test_repeated_empty_choices_raise_a_readable_error(tmp_path):
    bad = _resp(None, {"message": "Provider returned error"})
    llm, calls = _client(tmp_path, [bad, bad])
    with pytest.raises(UpstreamError, match="Provider returned error"):
        await llm._live("test/model", [{"role": "user", "content": "x"}], None, None)
    assert len(calls) == 2
