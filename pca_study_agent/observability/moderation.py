"""Quality Control, Question Dispute Lifecycle, and Pub/Sub Moderation Queue.

Enables candidates to flag/dispute questions that are inaccurate or unclear.
Immediately suspends flagged questions from rotation for all users and publishes
a structured moderation event to a Google Cloud Pub/Sub queue for admin notification.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pca_study_agent.config import settings
from pca_study_agent.knowledge.question_bank import ExamQuestion
from pca_study_agent.knowledge.questions_repository import questions_repo
from pca_study_agent.observability.logger import logger

PUB_SUB_TOPIC_NAME = "pca-question-reviews"


class QuestionFlagEvent(BaseModel):
    """Structured event for a question flagged by a candidate."""

    event_type: str = "question_flagged_for_review"
    question_id: str
    flagged_by_user: str
    reason: str = Field(description="E.g. 'unclear_wording', 'incorrect_explanation', 'outdated_feature', 'other'")
    feedback_notes: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    quarantine_status: str = "suspended_under_review"


def publish_question_flagged_event(
    user_id: str,
    question_id: str,
    reason: str,
    feedback_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Flag a question, suspend it immediately from rotation, and notify admin via Pub/Sub.

    Args:
        user_id: ID of candidate reporting the issue.
        question_id: ID of the question being flagged.
        reason: Categorization of issue ('unclear_wording', 'inaccurate_answer', etc.).
        feedback_notes: Detailed explanation from the candidate.

    Returns:
        Dict[str, Any]: Confirmation payload with suspension status and tracking ID.
    """
    event = QuestionFlagEvent(
        question_id=question_id,
        flagged_by_user=user_id,
        reason=reason,
        feedback_notes=feedback_notes,
    )

    # 1. Immediately suspend from rotation in global repository
    suspended = questions_repo.suspend_question(
        question_id=question_id,
        flagged_by_user=user_id,
        reason=reason,
        user_notes=feedback_notes,
    )

    # 2. Publish to Google Cloud Pub/Sub topic if configured
    pubsub_published = False
    gcp_project = settings.gcp_project_id
    if gcp_project:
        try:
            from google.cloud import pubsub_v1  # type: ignore

            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(gcp_project, PUB_SUB_TOPIC_NAME)
            event_bytes = json.dumps(event.model_dump()).encode("utf-8")
            future = publisher.publish(
                topic_path,
                event_bytes,
                reason=reason,
                question_id=question_id,
                flagged_by=user_id,
            )
            future.result(timeout=3.0)
            pubsub_published = True
            logger.info("Published question flag event to Cloud Pub/Sub", topic=topic_path, question_id=question_id)
        except Exception as exc:
            logger.warning("Pub/Sub publish skipped or failed (buffering locally)", error=str(exc))

    # 3. Always buffer to local persistent audit queue
    _append_local_review_queue(event.model_dump())

    logger.info(
        "Candidate flagged question for review",
        user_id=user_id,
        question_id=question_id,
        reason=reason,
        suspended=suspended,
        pubsub_published=pubsub_published,
    )

    return {
        "status": "success",
        "question_id": question_id,
        "is_suspended": suspended,
        "message": (
            f"Question '{question_id}' has been flagged and suspended from rotation. "
            "Our Principal Architect team has been notified for review. Thank you for your feedback!"
        ),
        "event": event.model_dump(),
    }


def resolve_question_moderation(
    admin_user_id: str,
    question_id: str,
    action: str,  # 'approve', 'edit', 'deprecate'
    resolution_notes: Optional[str] = None,
    updated_question: Optional[ExamQuestion] = None,
) -> Dict[str, Any]:
    """Admin resolution to un-suspend, edit, or deprecate a flagged question."""
    success = questions_repo.resolve_question(
        question_id=question_id,
        admin_user_id=admin_user_id,
        action=action,
        updated_question=updated_question,
        resolution_notes=resolution_notes,
    )

    if not success:
        return {
            "status": "error",
            "message": f"Question '{question_id}' not found in repository.",
        }

    return {
        "status": "success",
        "question_id": question_id,
        "action": action,
        "message": f"Question '{question_id}' has been successfully resolved with action: '{action}'.",
    }


def get_all_flagged_questions() -> List[Dict[str, Any]]:
    """Fetch all questions currently suspended under review for the admin dashboard."""
    return questions_repo.list_flagged_questions()


def _append_local_review_queue(event_data: Dict[str, Any]) -> None:
    """Save event to local JSON queue for auditing and offline review."""
    queue_file = settings.study_materials_dir / "flagged_reviews.json"
    queue_data = []
    if queue_file.exists():
        try:
            queue_data = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue_data = []

    queue_data.append(event_data)
    try:
        queue_file.write_text(json.dumps(queue_data, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to write to local flagged reviews file", error=str(exc))
