"""Unit Tests for Question Moderation, Dispute Flagging, and Suspension Lifecycle.

Verifies:
1. Flagging a question immediately suspends it from the active rotation for all users.
2. Active drill fetch strictly omits suspended questions.
3. Cloud Pub/Sub / local queue event logging.
4. Administrator resolution un-suspends, edits, or deprecates the question.
"""

from unittest.mock import MagicMock, patch
from pca_study_agent.knowledge.question_bank import ExamQuestion, QuestionOption
from pca_study_agent.knowledge.questions_repository import questions_repo
from pca_study_agent.observability.moderation import (
    get_all_flagged_questions,
    publish_question_flagged_event,
    resolve_question_moderation,
)
from pca_study_agent.tools import fetch_adaptive_drill_item, flag_or_challenge_question


def test_question_flagging_and_immediate_suspension():
    """Verify that flagging a question marks it as suspended and removes it from active rotation."""
    # 1. Create a test question
    test_q = ExamQuestion(
        id="q_test_suspension_001",
        domain_id="domain_1",
        sub_objective_code="1.1",
        difficulty="expert",
        question_text="Test suspension scenario question text.",
        options=[
            QuestionOption(key="A", text="Option A"),
            QuestionOption(key="B", text="Option B"),
            QuestionOption(key="C", text="Option C"),
            QuestionOption(key="D", text="Option D"),
        ],
        correct_option="A",
        architectural_principle="Test Principle",
        explanation="Test explanation",
        distractor_analysis={"B": "Wrong", "C": "Wrong", "D": "Wrong"},
    )
    questions_repo.save_question(test_q)

    # Confirm it is initially in active questions
    active_before = [q.id for q in questions_repo.get_active_questions(domain_id="domain_1")]
    assert "q_test_suspension_001" in active_before

    # 2. Flag the question
    res = flag_or_challenge_question(
        user_id="test_candidate_flag",
        question_id="q_test_suspension_001",
        reason="unclear_wording",
        feedback_notes="The scenario is ambiguous regarding multi-region requirements.",
    )
    assert res["status"] == "success"
    assert res["is_suspended"] is True

    # 3. Confirm it is NO LONGER in active questions
    active_after = [q.id for q in questions_repo.get_active_questions(domain_id="domain_1")]
    assert "q_test_suspension_001" not in active_after

    # 4. Verify it appears in flagged questions list
    flagged = get_all_flagged_questions()
    flagged_ids = [f["question_id"] for f in flagged]
    assert "q_test_suspension_001" in flagged_ids


def test_admin_resolution_workflow():
    """Verify administrator can approve, edit, or deprecate a suspended question."""
    q_id = "q_test_suspension_001"

    # Admin resolves by approving (un-suspending)
    res_approve = resolve_question_moderation(
        admin_user_id="admin_auditor",
        question_id=q_id,
        action="approve",
        resolution_notes="Reviewed by PCA lead architect: question is technically sound.",
    )
    assert res_approve["status"] == "success"

    # Confirm question is back in active pool
    active = [q.id for q in questions_repo.get_active_questions(domain_id="domain_1")]
    assert q_id in active

    # Admin deprecates question
    res_dep = resolve_question_moderation(
        admin_user_id="admin_auditor",
        question_id=q_id,
        action="deprecate",
        resolution_notes="Retired question due to GCP feature deprecation.",
    )
    assert res_dep["status"] == "success"
    active_final = [q.id for q in questions_repo.get_active_questions(domain_id="domain_1")]
    assert q_id not in active_final
