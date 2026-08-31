"""Adaptive Spaced Repetition Engine using Leitner 5-Box Algorithm.

Calculates review intervals and adaptive priority for scenario questions and flashcards.
Items answered incorrectly drop back to Box 1 for immediate repetition; correct answers
advance to higher boxes with exponential review intervals.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SpacedItemRecord(BaseModel):
    """Spaced repetition progress record for a question or flashcard."""

    item_id: str
    item_type: str = Field(description="'question' or 'flashcard'")
    domain_id: str
    box_number: int = Field(default=1, ge=1, le=5)  # Leitner Box 1 to 5
    consecutive_correct: int = 0
    total_attempts: int = 0
    total_incorrect: int = 0
    last_reviewed_at: float = Field(default_factory=time.time)
    next_review_due_at: float = Field(default_factory=time.time)


# Leitner interval multipliers in seconds (for study sessions: Box 1=immediate, Box 2=1hr, Box 3=1day, Box 4=3days, Box 5=7days)
BOX_INTERVALS_SECONDS = {
    1: 0,           # Box 1: Immediate drill
    2: 3600,        # Box 2: 1 hour
    3: 86400,       # Box 3: 1 day
    4: 259200,      # Box 4: 3 days
    5: 604800,      # Box 5: 7 days
}


class SpacedRepetitionScheduler:
    """Calculates review schedules and selects items with lowest mastery/due status."""

    @staticmethod
    def update_item_result(
        record: SpacedItemRecord,
        is_correct: bool,
    ) -> SpacedItemRecord:
        """Update an item's Leitner box and due date based on answer accuracy.

        Args:
            record (SpacedItemRecord): Existing item record.
            is_correct (bool): True if candidate answered correctly.

        Returns:
            SpacedItemRecord: Updated record.
        """
        now = time.time()
        record.total_attempts += 1
        record.last_reviewed_at = now

        if is_correct:
            record.consecutive_correct += 1
            # Advance box up to maximum Box 5
            record.box_number = min(5, record.box_number + 1)
        else:
            record.consecutive_correct = 0
            record.total_incorrect += 1
            # Drop back to Box 1 for intensive drill
            record.box_number = 1

        interval = BOX_INTERVALS_SECONDS.get(record.box_number, 0)
        record.next_review_due_at = now + interval
        return record

    @staticmethod
    def calculate_priority_score(record: SpacedItemRecord, domain_mastery: float) -> float:
        """Calculate drill priority score (higher score = more urgent to review).

        Args:
            record (SpacedItemRecord): Item record.
            domain_mastery (float): Overall domain mastery score (0.0 to 1.0).

        Returns:
            float: Priority ranking score.
        """
        now = time.time()
        overdue_factor = 1.0
        if now >= record.next_review_due_at:
            overdue_factor = 2.0 + min(5.0, (now - record.next_review_due_at) / 3600)

        # Lower box = higher urgency; lower domain mastery = higher urgency
        box_urgency = (6 - record.box_number) * 1.5
        mastery_urgency = (1.0 - domain_mastery) * 3.0

        return round((box_urgency + mastery_urgency) * overdue_factor, 2)
