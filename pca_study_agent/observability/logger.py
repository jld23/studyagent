"""Structured JSON Logging with Intent vs. Outcome Capture.

Utilizes structlog to emit rich, machine-readable JSON log events with
automatic PII scrubbing, execution latency tracking, session correlation,
and explicit Intent vs. Outcome logging pairs.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any, Dict, Optional
import structlog
from structlog.types import EventDict, WrappedLogger

from pca_study_agent.observability.pii_scrubber import redact_pii_data


def pii_redactor_processor(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Structlog processor to scrub sensitive PII from all log fields."""
    return redact_pii_data(event_dict)


def setup_structured_logging(log_level: str = "INFO") -> structlog.stdlib.BoundLogger:
    """Configure structlog for standard JSON output with structured metadata.

    Args:
        log_level (str): The logging level threshold (e.g., 'DEBUG', 'INFO', 'WARNING').

    Returns:
        structlog.stdlib.BoundLogger: The configured root bound logger.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric_level)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            pii_redactor_processor,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger("pca_study_agent")


# Root module logger
logger = setup_structured_logging()


def log_agent_intent(
    action_name: str,
    user_id: str,
    session_id: str,
    target_component: str,
    intended_parameters: Dict[str, Any],
    rationale: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> float:
    """Log the agent's intended action prior to execution.

    Args:
        action_name (str): The specific tool or agent action about to execute.
        user_id (str): Candidate identifier.
        session_id (str): Active session identifier.
        target_component (str): Component or tool executing the action.
        intended_parameters (Dict[str, Any]): Parameters passed to the action.
        rationale (Optional[str]): Explanation or LLM reasoning for the action.
        trace_id (Optional[str]): Distributed trace identifier.

    Returns:
        float: Start timestamp in seconds for latency tracking.
    """
    start_time = time.perf_counter()
    logger.info(
        "agent_intent",
        phase="intent",
        action=action_name,
        user_id=user_id,
        session_id=session_id,
        target_component=target_component,
        parameters=intended_parameters,
        rationale=rationale or "User-requested action dispatch",
        trace_id=trace_id or "",
    )
    return start_time


def log_agent_outcome(
    action_name: str,
    user_id: str,
    session_id: str,
    status: str,
    start_time: float,
    result_summary: Dict[str, Any],
    error_message: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log the actual outcome and latency after action execution.

    Args:
        action_name (str): The specific tool or agent action that completed.
        user_id (str): Candidate identifier.
        session_id (str): Active session identifier.
        status (str): Outcome status ('success', 'failed', 'partial').
        start_time (float): Start timestamp from log_agent_intent.
        result_summary (Dict[str, Any]): Summary of the result data.
        error_message (Optional[str]): Error description if failed.
        trace_id (Optional[str]): Distributed trace identifier.
    """
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "agent_outcome",
        phase="outcome",
        action=action_name,
        user_id=user_id,
        session_id=session_id,
        status=status,
        latency_ms=latency_ms,
        result=result_summary,
        error=error_message,
        trace_id=trace_id or "",
    )
