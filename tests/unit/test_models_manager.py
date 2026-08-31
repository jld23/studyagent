"""Unit Tests for Model Discovery, Startup Validation, and Interactive Selector.

Verifies:
1. Discovery and parsing of available Gemini models.
2. Immediate flagging and fallback resolution when an invalid model identifier is supplied.
3. Successful pass-through when valid models are supplied.
"""

from unittest.mock import MagicMock, patch
from pca_study_agent.models_manager import list_available_gemini_models, validate_and_resolve_models


def test_list_available_gemini_models_filtering():
    """Verify list_available_gemini_models filters out non-generative models."""
    mock_client = MagicMock()
    mock_model_1 = MagicMock()
    mock_model_1.name = "publishers/google/models/gemini-2.5-pro"
    mock_model_2 = MagicMock()
    mock_model_2.name = "publishers/google/models/gemini-2.5-flash"
    mock_model_3 = MagicMock()
    mock_model_3.name = "publishers/google/models/gemini-embedding-001"  # Should be excluded
    mock_model_4 = MagicMock()
    mock_model_4.name = "publishers/google/models/bert-base"  # Should be excluded

    mock_client.models.list.return_value = [mock_model_1, mock_model_2, mock_model_3, mock_model_4]

    models = list_available_gemini_models(mock_client)
    assert "gemini-2.5-pro" in models
    assert "gemini-2.5-flash" in models
    assert "gemini-embedding-001" not in models
    assert "bert-base" not in models


def test_validate_and_resolve_models_valid_input():
    """Verify validate_and_resolve_models returns configured models when valid."""
    with patch("pca_study_agent.models_manager.list_available_gemini_models") as mock_list:
        mock_list.return_value = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-3.1-pro-preview"]

        flash, pro, available, warning = validate_and_resolve_models(
            flash_model="gemini-2.5-flash",
            pro_model="gemini-2.5-pro",
            interactive=False,
        )

        assert flash == "gemini-2.5-flash"
        assert pro == "gemini-2.5-pro"
        assert warning is None
        assert len(available) == 3


def test_validate_and_resolve_models_invalid_input_flagged():
    """Verify validate_and_resolve_models flags invalid model and resolves to best working model."""
    with patch("pca_study_agent.models_manager.list_available_gemini_models") as mock_list:
        mock_list.return_value = ["gemini-2.5-pro", "gemini-2.5-flash"]

        flash, pro, available, warning = validate_and_resolve_models(
            flash_model="gemini-nonexistent-flash",
            pro_model="gemini-invalid-pro",
            interactive=False,
        )

        assert flash == "gemini-2.5-flash"
        assert pro == "gemini-2.5-pro"
        assert warning is not None
        assert "not available" in warning
