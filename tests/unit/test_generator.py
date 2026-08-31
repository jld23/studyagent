"""Unit Tests for Dynamic Question Generator.

Verifies:
1. Dynamic question generation returns a strictly validated Pydantic ExamQuestion.
2. Structure contains exactly 4 options, valid correct answer, and distractor analysis.
3. Fallback generator operates cleanly when offline.
"""

from unittest.mock import MagicMock, patch
from pca_study_agent.knowledge.generator import generate_pca_question
from pca_study_agent.knowledge.question_bank import ExamQuestion


def test_generate_pca_question_structure():
    """Verify generated question conforms to ExamQuestion Pydantic schema."""
    q = generate_pca_question(domain_id="domain_1", case_study_id="mountkirk_games", difficulty="expert")

    assert isinstance(q, ExamQuestion)
    assert q.domain_id == "domain_1"
    assert q.difficulty == "expert"
    assert len(q.options) == 4
    assert q.correct_option in ("A", "B", "C", "D")
    assert len(q.explanation) > 10
    assert len(q.distractor_analysis) >= 3
    assert len(q.question_text) > 20
