"""Unit Tests for Tool & Interface Design (Rubric Category 1).

Verifies:
1. Comprehensive Google docstrings on all tools.
2. Descriptive naming conventions.
3. Explicit Pydantic JSON schema constraints.
4. Guided error handling with actionable recovery suggestions.
"""

import inspect
import pytest
from pydantic import ValidationError

from pca_study_agent.tools import (
    AuthCandidateInput,
    AnswerSubmissionInput,
    authenticate_or_register_candidate,
    evaluate_scenario_answer_and_update_mastery,
    fetch_adaptive_drill_item,
    fetch_diagnostic_assessment_batch,
    generate_certification_domain_progress_report,
    ingest_user_study_material,
    pause_assessment_session_for_deep_dive,
    request_destructive_action_confirmation,
    resume_assessment_session,
    sync_official_study_materials,
)

ALL_TOOL_FUNCTIONS = [
    authenticate_or_register_candidate,
    fetch_diagnostic_assessment_batch,
    fetch_adaptive_drill_item,
    evaluate_scenario_answer_and_update_mastery,
    pause_assessment_session_for_deep_dive,
    resume_assessment_session,
    generate_certification_domain_progress_report,
    ingest_user_study_material,
    sync_official_study_materials,
    request_destructive_action_confirmation,
]


def test_tool_docstrings_completeness():
    """Verify all tool functions have complete Google-format docstrings with Args and Returns."""
    for tool_fn in ALL_TOOL_FUNCTIONS:
        doc = inspect.getdoc(tool_fn)
        assert doc is not None, f"Tool {tool_fn.__name__} is missing a docstring."
        assert "Args:" in doc, f"Tool {tool_fn.__name__} docstring is missing 'Args:' section."
        assert "Returns:" in doc, f"Tool {tool_fn.__name__} docstring is missing 'Returns:' section."
        assert len(doc.splitlines()) >= 5, f"Tool {tool_fn.__name__} docstring is insufficiently descriptive."


def test_tool_descriptive_naming():
    """Verify tool names follow descriptive verb_noun naming patterns."""
    for tool_fn in ALL_TOOL_FUNCTIONS:
        name = tool_fn.__name__
        assert len(name) >= 12, f"Tool name '{name}' is too brief."
        assert any(
            name.startswith(prefix)
            for prefix in ("auth", "fetch", "evaluate", "pause", "resume", "generate", "ingest", "sync", "request")
        ), f"Tool name '{name}' does not start with a specific action verb."


def test_explicit_pydantic_schemas():
    """Verify strict validation and rejection of malformed inputs."""
    # Test valid input
    valid_auth = AuthCandidateInput(user_id="valid_user_123", candidate_name="Alice Smith")
    assert valid_auth.user_id == "valid_user_123"

    # Test invalid user_id pattern (contains invalid symbols)
    with pytest.raises(ValidationError):
        AuthCandidateInput(user_id="bad user $#%")

    # Test invalid user_id length (too short)
    with pytest.raises(ValidationError):
        AuthCandidateInput(user_id="ab")


def test_guided_error_handling_recovery():
    """Verify tool errors return structured recovery suggestions instead of raising uncaught exceptions."""
    # Pass an invalid empty item_id to evaluate_scenario_answer
    err_res = evaluate_scenario_answer_and_update_mastery(
        user_id="test_user",
        item_id="non_existent_item_999",
        submitted_answer="A",
    )
    assert err_res.get("status") == "error"
    assert "error_code" in err_res
    assert "message" in err_res
    assert "recovery_suggestion" in err_res
    assert len(err_res["recovery_suggestion"]) > 10


def test_end_to_end_tool_execution_flow():
    """Verify core tool flow: auth -> diagnostic -> drill -> submit -> report."""
    # 1. Auth
    auth = authenticate_or_register_candidate(user_id="unit_tester", candidate_name="Unit Tester")
    assert auth["status"] == "success"
    assert auth["user_id"] == "unit_tester"

    # 2. Diagnostic
    diag = fetch_diagnostic_assessment_batch(user_id="unit_tester", num_questions=3)
    assert diag["status"] == "success"
    assert len(diag["questions"]) == 3

    # 3. Adaptive drill
    drill = fetch_adaptive_drill_item(user_id="unit_tester")
    assert drill["status"] == "success"
    assert "item_id" in drill

    # 4. Answer submission
    sub = evaluate_scenario_answer_and_update_mastery(
        user_id="unit_tester",
        item_id=drill["item_id"],
        submitted_answer="B",
    )
    assert sub["status"] == "success"
    assert "is_correct" in sub
    assert "updated_domain_mastery" in sub

    # 5. Progress report
    rep = generate_certification_domain_progress_report(user_id="unit_tester")
    assert rep["status"] == "success"
    assert len(rep["domain_breakdown"]) == 6
