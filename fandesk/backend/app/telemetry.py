"""JSON logs with request_id on every line, and OpenTelemetry traces to Phoenix.

The request_id doubles as the trace ID: a custom ID generator hands the current
request's ID to the root span, so History can link straight to the trace.
"""

import contextvars
import json
import logging
import sys
from contextlib import contextmanager

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

SPAN_KIND = "openinference.span.kind"
# A private provider, not the global one: recent FastAPI versions emit their own
# HTTP spans through the global provider, which would wrap (and re-ID) our traces.
tracer: trace.Tracer = trace.NoOpTracer()


class _RequestIdGenerator(RandomIdGenerator):
    def generate_trace_id(self) -> int:
        rid = request_id_var.get()
        return int(rid, 16) if rid else super().generate_trace_id()


class _JsonFormatter(logging.Formatter):
    RESERVED = set(vars(logging.makeLogRecord({})))

    def format(self, record: logging.LogRecord) -> str:
        out = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        out.update({k: v for k, v in vars(record).items() if k not in self.RESERVED and k not in out})
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    for noisy in ("httpx", "httpcore", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def setup_tracing(endpoint: str) -> None:
    """Send spans to Phoenix over OTLP/HTTP. No endpoint, no tracing."""
    if not endpoint:
        return
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource

    provider = TracerProvider(
        resource=Resource.create({"service.name": "fandesk-api", "openinference.project.name": "fandesk"}),
        id_generator=_RequestIdGenerator(),
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    global tracer
    tracer = provider.get_tracer("fandesk")
    # LLM spans (messages, tokens, model) come from the OpenInference instrumentation.
    OpenAIInstrumentor().instrument(tracer_provider=provider)


@contextmanager
def span(name: str, kind: str, root: bool = False, **attributes):
    """A manual span tagged with an OpenInference kind (CHAIN, AGENT, TOOL).

    root=True starts a fresh trace, so its trace ID comes from the request ID.
    """
    parent = otel_context.Context() if root else None
    with tracer.start_as_current_span(name, context=parent) as s:
        s.set_attribute(SPAN_KIND, kind)
        for k, v in attributes.items():
            if v is not None:
                s.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else json.dumps(v, default=str))
        yield s
