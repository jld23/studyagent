"""Unit Tests for Context & Memory Management (Rubric Category 2).

Verifies:
1. Multi-user session isolation and persistent state namespaces.
2. Leitner 5-box spaced repetition state transitions.
3. Conversation context compaction and summarization.
4. Async memory background persistence operations.
"""

import pytest
from pca_study_agent.memory.compaction import ConversationMessage, context_compactor
from pca_study_agent.memory.spaced_repetition import SpacedItemRecord, SpacedRepetitionScheduler
from pca_study_agent.memory.user_manager import user_manager


def test_multi_user_isolation():
    """Verify that User Alice and User Bob have completely independent profiles and mastery data."""
    alice = user_manager.get_or_create_user(user_id="alice_test", name="Alice")
    bob = user_manager.get_or_create_user(user_id="bob_test", name="Bob")

    assert alice.user_id != bob.user_id
    assert alice.name == "Alice"
    assert bob.name == "Bob"

    # Modify Alice's mastery in domain_1
    user_manager.update_item_score_and_mastery(
        user_id="alice_test",
        item_id="q_pca_001",
        item_type="question",
        domain_id="domain_1",
        is_correct=True,
    )

    # Bob's mastery must remain untouched at initial default
    alice_reloaded = user_manager.get_or_create_user("alice_test")
    bob_reloaded = user_manager.get_or_create_user("bob_test")

    assert alice_reloaded.domain_mastery["domain_1"] > bob_reloaded.domain_mastery["domain_1"]
    assert bob_reloaded.domain_mastery["domain_1"] == 0.5


def test_leitner_box_transitions():
    """Verify Leitner box transitions: correct answers advance, incorrect answers drop to Box 1."""
    rec = SpacedItemRecord(item_id="item_101", item_type="question", domain_id="domain_3", box_number=1)

    # Correct 1 -> advances to Box 2
    rec = SpacedRepetitionScheduler.update_item_result(rec, is_correct=True)
    assert rec.box_number == 2
    assert rec.consecutive_correct == 1

    # Correct 2 -> advances to Box 3
    rec = SpacedRepetitionScheduler.update_item_result(rec, is_correct=True)
    assert rec.box_number == 3

    # Incorrect -> drops directly back to Box 1
    rec = SpacedRepetitionScheduler.update_item_result(rec, is_correct=False)
    assert rec.box_number == 1
    assert rec.consecutive_correct == 0
    assert rec.total_incorrect == 1


def test_context_compaction():
    """Verify context compactor truncates long history and creates rolling summary."""
    messages = [
        ConversationMessage(role="user" if i % 2 == 0 else "assistant", content=f"Message turn number {i}", timestamp=1000 + i)
        for i in range(25)
    ]

    compacted, summary = context_compactor.compact_history(messages)

    # Must keep at most 10 recent turns
    assert len(compacted) == 10
    assert len(summary) > 0
    assert "Prior Context:" in summary


def test_async_memory_persistence():
    """Verify user profiles persist cleanly and can be loaded back from storage."""
    user_id = "async_persist_user"
    prof = user_manager.get_or_create_user(user_id=user_id, name="Async Persister")
    prof.domain_mastery["domain_4"] = 0.88
    user_manager.save_user_sync(prof)

    # Clear cache and reload
    user_manager._profiles_cache.pop(user_id, None)
    loaded = user_manager.get_or_create_user(user_id=user_id)
    assert loaded.domain_mastery["domain_4"] == 0.88
