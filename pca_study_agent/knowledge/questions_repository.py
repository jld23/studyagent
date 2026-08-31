"""Question Repository and Lifecycle State Management.

Maintains the global question registry, merges static seed questions with dynamically
generated scenario questions, and enforces lifecycle state filtering:
- `active`: Eligible for candidate assessments and adaptive drills.
- `suspended_under_review`: Flagged/disputed by candidates, quarantined from all users.
- `deprecated`: Permanently retired from rotation.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pca_study_agent.config import settings
from pca_study_agent.knowledge.question_bank import ExamQuestion, PCA_QUESTIONS
from pca_study_agent.observability.logger import logger

_REPO_LOCK = threading.Lock()


class QuestionMetadata(ExamQuestion):
    """Extended question model including lifecycle status and moderation audit trail."""

    status: str = "active"  # 'active', 'suspended_under_review', 'deprecated'
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    flag_count: int = 0
    moderation_history: List[Dict[str, Any]] = Field(default_factory=list)


class QuestionsRepository:
    """Thread-safe persistent question store with lifecycle and suspension controls."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or settings.study_materials_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.dynamic_file = self.storage_dir / "generated_questions.json"
        self.status_file = self.storage_dir / "question_status_overrides.json"
        self._questions_cache: Dict[str, QuestionMetadata] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load static questions, dynamic stored questions, and status overrides."""
        with _REPO_LOCK:
            # 1. Load baseline static questions
            for q in PCA_QUESTIONS:
                self._questions_cache[q.id] = QuestionMetadata(**q.model_dump())

            # 2. Load dynamically generated questions
            if self.dynamic_file.exists():
                try:
                    data = json.loads(self.dynamic_file.read_text(encoding="utf-8"))
                    for item in data:
                        q_meta = QuestionMetadata(**item)
                        self._questions_cache[q_meta.id] = q_meta
                except Exception as exc:
                    logger.warning("Failed to load dynamic questions file", error=str(exc))

            # 3. Load status overrides (e.g. suspended items)
            if self.status_file.exists():
                try:
                    overrides = json.loads(self.status_file.read_text(encoding="utf-8"))
                    for q_id, override in overrides.items():
                        if q_id in self._questions_cache:
                            self._questions_cache[q_id].status = override.get("status", "active")
                            self._questions_cache[q_id].flag_count = override.get("flag_count", 0)
                            self._questions_cache[q_id].moderation_history = override.get("moderation_history", [])
                except Exception as exc:
                    logger.warning("Failed to load question status overrides", error=str(exc))

    def _save_dynamic_questions(self) -> None:
        """Persist dynamically generated questions to disk."""
        dynamic_items = [
            q.model_dump()
            for q in self._questions_cache.values()
            if q.id not in {base.id for base in PCA_QUESTIONS}
        ]
        try:
            self.dynamic_file.write_text(json.dumps(dynamic_items, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to save dynamic questions", error=str(exc))

    def _save_status_overrides(self) -> None:
        """Persist status overrides (suspensions, resolutions) to disk."""
        overrides = {
            q.id: {
                "status": q.status,
                "flag_count": q.flag_count,
                "moderation_history": q.moderation_history,
                "updated_at": q.updated_at,
            }
            for q in self._questions_cache.values()
            if q.status != "active" or q.flag_count > 0 or q.moderation_history
        }
        try:
            self.status_file.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to save status overrides", error=str(exc))

    def get_active_questions(self, domain_id: Optional[str] = None) -> List[ExamQuestion]:
        """Return only active questions (strictly excluding suspended and deprecated items)."""
        with _REPO_LOCK:
            active = [
                q
                for q in self._questions_cache.values()
                if q.status == "active" and (not domain_id or q.domain_id == domain_id)
            ]
            return [ExamQuestion(**q.model_dump()) for q in active]

    def get_question(self, question_id: str) -> Optional[QuestionMetadata]:
        """Fetch question metadata by ID."""
        with _REPO_LOCK:
            return self._questions_cache.get(question_id)

    def save_question(self, question: ExamQuestion) -> QuestionMetadata:
        """Save a new question to the repository."""
        with _REPO_LOCK:
            meta = QuestionMetadata(**question.model_dump())
            self._questions_cache[meta.id] = meta
            self._save_dynamic_questions()
            logger.info("Saved question to repository", question_id=meta.id, domain_id=meta.domain_id)
            return meta

    def suspend_question(
        self,
        question_id: str,
        flagged_by_user: str,
        reason: str,
        user_notes: Optional[str] = None,
    ) -> bool:
        """Immediately suspend a question from rotation and record dispute."""
        with _REPO_LOCK:
            if question_id not in self._questions_cache:
                return False

            q = self._questions_cache[question_id]
            q.status = "suspended_under_review"
            q.flag_count += 1
            q.updated_at = time.time()
            q.moderation_history.append(
                {
                    "action": "flagged_and_suspended",
                    "user_id": flagged_by_user,
                    "reason": reason,
                    "notes": user_notes or "",
                    "timestamp": time.time(),
                }
            )
            self._save_status_overrides()
            logger.warning(
                "Question suspended from rotation under review",
                question_id=question_id,
                flagged_by=flagged_by_user,
                reason=reason,
            )
            return True

    def resolve_question(
        self,
        question_id: str,
        admin_user_id: str,
        action: str,  # 'approve', 'edit', 'deprecate'
        updated_question: Optional[ExamQuestion] = None,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Admin resolution to un-suspend, edit, or deprecate a question."""
        with _REPO_LOCK:
            if question_id not in self._questions_cache:
                return False

            q = self._questions_cache[question_id]
            if action == "approve":
                q.status = "active"
            elif action == "deprecate":
                q.status = "deprecated"
            elif action == "edit" and updated_question:
                for k, v in updated_question.model_dump().items():
                    setattr(q, k, v)
                q.status = "active"

            q.updated_at = time.time()
            q.moderation_history.append(
                {
                    "action": f"resolved_{action}",
                    "admin_id": admin_user_id,
                    "notes": resolution_notes or "",
                    "timestamp": time.time(),
                }
            )
            self._save_status_overrides()
            if action == "edit":
                self._save_dynamic_questions()

            logger.info("Resolved question moderation status", question_id=question_id, action=action)
            return True

    def list_flagged_questions(self) -> List[Dict[str, Any]]:
        """Return all questions currently suspended under review."""
        with _REPO_LOCK:
            flagged = [
                {
                    "question_id": q.id,
                    "domain_id": q.domain_id,
                    "status": q.status,
                    "flag_count": q.flag_count,
                    "question_text": q.question_text,
                    "options": [opt.model_dump() for opt in q.options],
                    "correct_option": q.correct_option,
                    "explanation": q.explanation,
                    "moderation_history": q.moderation_history,
                }
                for q in self._questions_cache.values()
                if q.status == "suspended_under_review"
            ]
            return flagged


# Global questions repository singleton
questions_repo = QuestionsRepository()
