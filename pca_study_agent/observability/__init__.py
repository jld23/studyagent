"""Observability, Logging, Tracing, Guardrails, and HITL module."""

from pca_study_agent.observability.logger import (
    logger,
    setup_structured_logging,
    log_agent_intent,
    log_agent_outcome,
)
from pca_study_agent.observability.pii_scrubber import redact_pii_text, redact_pii_data
from pca_study_agent.observability.telemetry import tracer, trace_span, get_current_trace_id
from pca_study_agent.observability.guardrails import (
    self_eval_explanation,
    validate_input_safety,
    validate_output_safety,
    verify_architectural_soundness,
)
from pca_study_agent.observability.hitl import hitl_manager

__all__ = [
    "logger",
    "setup_structured_logging",
    "log_agent_intent",
    "log_agent_outcome",
    "redact_pii_text",
    "redact_pii_data",
    "tracer",
    "trace_span",
    "get_current_trace_id",
    "validate_input_safety",
    "validate_output_safety",
    "verify_architectural_soundness",
    "self_eval_explanation",
    "hitl_manager",
]
