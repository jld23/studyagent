"""Distributed Tracing with OpenTelemetry.

Provides distributed tracing instrumentation to link spans from incoming user
queries across agent routing, tool executions, memory operations, and model inferences.
"""

from __future__ import annotations

import contextlib
from typing import Any, Dict, Generator, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode, Tracer

from pca_study_agent.config import settings

# Initialize OpenTelemetry TracerProvider
_provider = TracerProvider()
if settings.environment == "development" and settings.enable_otel_tracing:
    # In development, attach a simple exporter if needed or keep default in-memory provider
    _provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(_provider)
tracer: Tracer = trace.get_tracer("pca_study_agent", settings.app_version)


def get_current_trace_id() -> str:
    """Retrieve the current active distributed trace ID as a hex string."""
    span = trace.get_current_span()
    context = span.get_span_context()
    if context.is_valid:
        return format(context.trace_id, "032x")
    return "00000000000000000000000000000000"


@contextlib.contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Generator[trace.Span, None, None]:
    """Context manager for distributed tracing spans.

    Args:
        name (str): Name of the span operation (e.g. 'agent.coordinator', 'tool.evaluate_answer').
        attributes (Optional[Dict[str, Any]]): Span attributes and metadata tags.

    Yields:
        trace.Span: The active OpenTelemetry span.
    """
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, val in attributes.items():
                if val is not None:
                    span.set_attribute(key, str(val))
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
