"""Multi-User Session, Profile, and Mastery State Management.

Ensures strict multi-user namespace isolation, persistent on-disk storage,
cross-session memory retention, domain-by-domain mastery tracking, and active
drill state pause/resume capabilities.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pca_study_agent.config import settings
from pca_study_agent.memory.async_worker import async_memory_worker
from pca_study_agent.memory.compaction import ConversationMessage, context_compactor
from pca_study_agent.memory.spaced_repetition import (
    SpacedItemRecord,
    SpacedRepetitionScheduler,
)
from pca_study_agent.observability.logger import logger


class ActiveDrillState(BaseModel):
    """Tracks state of an in-flight assessment or drill."""

    session_id: str
    mode: str = Field(description="'diagnostic' or 'adaptive_drill'")
    current_item_id: Optional[str] = None
    is_paused_for_deep_dive: bool = False
    question_queue: List[str] = Field(default_factory=list)
    completed_items: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: float = Field(default_factory=time.time)
    last_interaction_at: float = Field(default_factory=time.time)


class UserProfile(BaseModel):
    """Complete persistent candidate profile and mastery record."""

    user_id: str
    name: str
    target_exam_date: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    last_active_at: float = Field(default_factory=time.time)

    # Certification readiness metrics
    diagnostic_completed: bool = False
    domain_mastery: Dict[str, float] = Field(
        default_factory=lambda: {
            "domain_1": 0.5,
            "domain_2": 0.5,
            "domain_3": 0.5,
            "domain_4": 0.5,
            "domain_5": 0.5,
            "domain_6": 0.5,
        }
    )

    # Spaced repetition tracking
    spaced_items: Dict[str, SpacedItemRecord] = Field(default_factory=dict)

    # Active session & conversation history
    active_drill: Optional[ActiveDrillState] = None
    history_summary: str = ""
    messages: List[ConversationMessage] = Field(default_factory=list)

    # Cumulative statistics and zero-cost seen item tracking
    seen_item_ids: List[str] = Field(default_factory=list)
    total_questions_answered: int = 0
    total_correct_answers: int = 0


class UserManager:
    """Multi-user profile repository with file persistence and memory operations."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or settings.user_profiles_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_cache: Dict[str, UserProfile] = {}

    def _get_user_file_path(self, user_id: str) -> Path:
        """Sanitize user ID and return profile JSON path."""
        safe_id = "".join(c for c in user_id if c.isalnum() or c in ("-", "_")).lower()
        return self.storage_dir / f"user_{safe_id}.json"

    def get_or_create_user(
        self,
        user_id: str,
        name: str = "Cloud Candidate",
        target_exam_date: Optional[str] = None,
    ) -> UserProfile:
        """Load an existing user profile or register a new one.

        Args:
            user_id (str): Unique candidate identifier.
            name (str): Candidate display name.
            target_exam_date (Optional[str]): Target exam date string.

        Returns:
            UserProfile: The active user profile.
        """
        user_id_clean = user_id.strip().lower()
        if user_id_clean in self._profiles_cache:
            profile = self._profiles_cache[user_id_clean]
            profile.last_active_at = time.time()
            return profile

        user_file = self._get_user_file_path(user_id_clean)
        if user_file.exists():
            try:
                data = json.loads(user_file.read_text(encoding="utf-8"))
                profile = UserProfile(**data)
                profile.last_active_at = time.time()
                self._profiles_cache[user_id_clean] = profile
                logger.info("Loaded persistent user profile", user_id=user_id_clean, name=profile.name)
                return profile
            except Exception as exc:
                logger.error("Failed to load user profile JSON, creating fresh one", user_id=user_id_clean, error=str(exc))

        # Register new profile
        profile = UserProfile(
            user_id=user_id_clean,
            name=name,
            target_exam_date=target_exam_date,
        )
        self.save_user_sync(profile)
        self._profiles_cache[user_id_clean] = profile
        logger.info("Created new candidate profile", user_id=user_id_clean, name=name)
        return profile

    def save_user_sync(self, profile: UserProfile) -> None:
        """Synchronously write user profile to disk."""
        user_file = self._get_user_file_path(profile.user_id)
        user_file.write_text(json.dumps(profile.model_dump(), indent=2), encoding="utf-8")
        self._profiles_cache[profile.user_id] = profile

    def save_user_async(self, profile: UserProfile) -> None:
        """Save user profile in a non-blocking background task."""
        self._profiles_cache[profile.user_id] = profile

        async def _persist():
            user_file = self._get_user_file_path(profile.user_id)
            user_file.write_text(json.dumps(profile.model_dump(), indent=2), encoding="utf-8")

        async_memory_worker.schedule_task(_persist(), f"persist_user_{profile.user_id}")

    def update_item_score_and_mastery(
        self,
        user_id: str,
        item_id: str,
        item_type: str,
        domain_id: str,
        is_correct: bool,
    ) -> tuple[UserProfile, SpacedItemRecord, float]:
        """Update spaced repetition box and domain mastery score.

        Args:
            user_id (str): Candidate identifier.
            item_id (str): Question or Flashcard ID.
            item_type (str): 'question' or 'flashcard'.
            domain_id (str): Target domain e.g. 'domain_1'.
            is_correct (bool): True if answer was correct.

        Returns:
            tuple[UserProfile, SpacedItemRecord, float]: (updated_profile, updated_record, new_domain_mastery)
        """
        profile = self.get_or_create_user(user_id)

        # 1. Update Spaced Repetition Record
        if item_id not in profile.spaced_items:
            record = SpacedItemRecord(
                item_id=item_id,
                item_type=item_type,
                domain_id=domain_id,
            )
        else:
            record = profile.spaced_items[item_id]

        updated_record = SpacedRepetitionScheduler.update_item_result(record, is_correct)
        profile.spaced_items[item_id] = updated_record

        # 2. Update Domain Mastery (Exponential moving adjustment)
        current_mastery = profile.domain_mastery.get(domain_id, 0.5)
        if is_correct:
            # Increase mastery asymptotically towards 1.0
            new_mastery = min(1.0, current_mastery + 0.08 * (1.0 - current_mastery))
        else:
            # Decrease mastery by a weighted penalty
            new_mastery = max(0.1, current_mastery - 0.12 * current_mastery)

        profile.domain_mastery[domain_id] = round(new_mastery, 3)
        profile.total_questions_answered += 1
        if is_correct:
            profile.total_correct_answers += 1

        self.save_user_async(profile)
        return profile, updated_record, profile.domain_mastery[domain_id]

    def add_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        agent_response: str,
    ) -> UserProfile:
        """Append messages and trigger context compaction if needed.

        Args:
            user_id (str): Candidate identifier.
            user_message (str): Candidate prompt.
            agent_response (str): Agent reply.

        Returns:
            UserProfile: Updated profile.
        """
        profile = self.get_or_create_user(user_id)
        now = time.time()
        profile.messages.append(ConversationMessage(role="user", content=user_message, timestamp=now))
        profile.messages.append(ConversationMessage(role="assistant", content=agent_response, timestamp=now))

        # Compact history if exceeds threshold
        compacted_msgs, updated_summary = context_compactor.compact_history(
            profile.messages, profile.history_summary
        )
        profile.messages = compacted_msgs
        profile.history_summary = updated_summary

        self.save_user_async(profile)
        return profile

    def reset_user_progress(self, user_id: str) -> bool:
        """Reset mastery and drill history for a user (called after HITL confirmation)."""
        profile = self.get_or_create_user(user_id)
        profile.domain_mastery = {
            "domain_1": 0.5,
            "domain_2": 0.5,
            "domain_3": 0.5,
            "domain_4": 0.5,
            "domain_5": 0.5,
            "domain_6": 0.5,
        }
        profile.spaced_items.clear()
        profile.active_drill = None
        profile.messages.clear()
        profile.history_summary = ""
        profile.total_questions_answered = 0
        profile.total_correct_answers = 0
        profile.diagnostic_completed = False
        self.save_user_sync(profile)
        logger.info("User progress completely reset via HITL", user_id=user_id)
        return True


# Global User Manager instance
user_manager = UserManager()
