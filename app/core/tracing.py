"""OpenTelemetry initialisation.

Calling :func:`setup_tracing` from app startup wires OTel SDK + the OTLP
exporter. If ``OTEL_EXPORTER_OTLP_ENDPOINT`` is unset we install only the
SDK with a no-op exporter — we still create spans so libraries that use
``trace.get_tracer(...)`` work, but nothing is shipped over the wire.

Typical local + prod setup:

  OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317   # gRPC, default
  OTEL_SERVICE_NAME=sentifargo-api
  OTEL_TRACES_SAMPLER=parentbased_traceidratio
  OTEL_TRACES_SAMPLER_ARG=0.1   # 10 % sampling

Instrumentations applied:
  * FastAPI (request spans, automatic via FastAPIInstrumentor.instrument_app)
  * SQLAlchemy (engine spans)
  * httpx (outbound HTTP, used by the Anthropic client)
  * Redis
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

_log = logging.getLogger("Sentifargo.tracing")
_initialised = False
_lock = threading.Lock()


def setup_tracing(app: Any) -> None:
    """Idempotent and thread-safe. Safe to call from app startup."""
    global _initialised
    # Fast path — avoids lock acquisition on every call after first init.
    if _initialised:
        return
    with _lock:
        if _initialised:  # re-check after acquiring lock
            return

        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
        except Exception as exc:  # pragma: no cover - optional dep
            _log.info("OpenTelemetry not installed; skipping tracing setup: %s", exc)
            return

        service_name = os.getenv("OTEL_SERVICE_NAME", "sentifargo-api")
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "sentifargo"),
                "deployment.environment": os.getenv("APP_ENV", "development"),
            }
        )

        provider = TracerProvider(resource=resource)
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
        if endpoint:
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=endpoint.startswith("http://"))
            provider.add_span_processor(BatchSpanProcessor(exporter))
            _log.info("OTel exporting to %s as %s", endpoint, service_name)
        else:
            _log.info("OTel SDK active without exporter (set OTEL_EXPORTER_OTLP_ENDPOINT to ship spans)")

        trace.set_tracer_provider(provider)

        # Auto-instrument FastAPI on the running app + libraries we use.
        try:
            FastAPIInstrumentor.instrument_app(app)
        except Exception as exc:  # pragma: no cover
            _log.warning("FastAPI instrumentation failed: %s", exc)

        for name, fn in (
            ("sqlalchemy", SQLAlchemyInstrumentor),
            ("httpx", HTTPXClientInstrumentor),
            ("redis", RedisInstrumentor),
        ):
            try:
                fn().instrument()
            except Exception as exc:  # pragma: no cover
                _log.warning("%s instrumentation skipped: %s", name, exc)

        _initialised = True


def get_tracer(name: str = "sentifargo"):
    """Return a tracer; callers in agent code use this for manual spans."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except Exception:  # pragma: no cover
        return _NoopTracer()


class _NoopSpan:
    def set_attribute(self, *_a: Any, **_kw: Any) -> None:
        return None

    def record_exception(self, *_a: Any, **_kw: Any) -> None:
        return None

    def __enter__(self) -> "_NoopSpan":
        return self

    def __exit__(self, *_a: Any) -> None:
        return None


class _NoopTracer:
    def start_as_current_span(self, *_a: Any, **_kw: Any) -> _NoopSpan:
        return _NoopSpan()


__all__ = ["setup_tracing", "get_tracer"]
