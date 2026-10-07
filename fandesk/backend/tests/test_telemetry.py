from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import telemetry
from app.events import Emitter


async def test_trace_id_is_the_request_id_even_inside_another_span(setup, monkeypatch):
    _, store, _, orch = setup
    exporter = InMemorySpanExporter()
    provider = TracerProvider(id_generator=telemetry._RequestIdGenerator())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(telemetry, "tracer", provider.get_tracer("test"))

    rid = "c" * 32
    store.create_request(rid, "Who took the most wickets in IPL 2023?", True)
    # Simulate a web framework's HTTP span being active when the run starts.
    with provider.get_tracer("http").start_as_current_span("POST /api/ask"):
        await orch.run(rid, "Who took the most wickets in IPL 2023?", True, Emitter(rid, store))

    spans = {s.name: s for s in exporter.get_finished_spans()}
    root = spans["request"]
    assert root.parent is None
    assert format(root.context.trace_id, "032x") == rid
    for name in ("supervisor.route", "agent.stats_guru", "tool.get_schema", "tool.run_sql"):
        assert spans[name].context.trace_id == root.context.trace_id, name
    assert spans["request"].attributes["route"] == "sports"
    assert spans["agent.stats_guru"].attributes[telemetry.SPAN_KIND] == "AGENT"
    assert spans["tool.run_sql"].attributes[telemetry.SPAN_KIND] == "TOOL"
    assert isinstance(trace.get_tracer_provider(), trace.ProxyTracerProvider)  # global provider untouched
