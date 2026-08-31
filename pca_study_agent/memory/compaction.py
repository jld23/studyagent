"""Context Compaction and Conversation History Summarization.

Manages conversational token bloat using sliding windows, structured turn
pruning, and periodic dialogue summarization to stay within LLM context
limits while preserving key architectural insights and user weak points.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Atomic message in a conversation thread."""

    role: str = Field(description="'user', 'assistant', 'system'")
    content: str
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextCompactor:
    """Manages history truncation and rolling summarization."""

    def __init__(self, max_uncompacted_turns: int = 10) -> None:
        self.max_uncompacted_turns = max_uncompacted_turns

    def compact_history(
        self,
        messages: List[ConversationMessage],
        existing_summary: str = "",
    ) -> tuple[List[ConversationMessage], str]:
        """Compact conversation messages if they exceed threshold.

        Args:
            messages (List[ConversationMessage]): Complete list of messages.
            existing_summary (str): Previous rolling summary.

        Returns:
            tuple[List[ConversationMessage], str]: (recent_window_messages, updated_summary)
        """
        if len(messages) <= self.max_uncompacted_turns:
            return messages, existing_summary

        # Split into historical turns to summarize and recent active window
        turns_to_summarize = messages[:-self.max_uncompacted_turns]
        recent_window = messages[-self.max_uncompacted_turns:]

        # Build compact extractive summary of key questions & topics discussed
        summarized_topics: List[str] = []
        for msg in turns_to_summarize:
            if msg.role == "user" and len(msg.content) > 5:
                # Capture question/inquiry intent
                snippet = msg.content[:80].strip().replace("\n", " ")
                summarized_topics.append(f"Candidate asked: '{snippet}'")

        new_summary_part = "; ".join(summarized_topics[-5:])
        updated_summary = (
            f"{existing_summary} | Prior Context: {new_summary_part}"
            if existing_summary
            else f"Prior Context: {new_summary_part}"
        )

        return recent_window, updated_summary


# Global compactor instance
context_compactor = ContextCompactor()
