"""Model Discovery, Startup Validation, and Interactive Selector.

Validates configured Gemini Flash and Pro model identifiers against the active
GenAI provider (Vertex AI or Google AI Studio) on startup, discovers available
publisher models, flags invalid configurations, and offers interactive selection.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from pca_study_agent.config import settings
from pca_study_agent.observability.logger import logger

console = Console()

# Non-generative or non-chat models to filter out from candidate lists
EXCLUDED_KEYWORDS = ["embedding", "robotics", "tts", "imageclassification", "transcribe", "vehicle", "occupancy", "bert"]


def list_available_gemini_models(client: Optional[Any] = None) -> List[str]:
    """Fetch all available Gemini text/reasoning models for the active client.

    Args:
        client: Optional GenAI client instance. If None, initializes client.

    Returns:
        List[str]: Clean list of available Gemini model IDs (e.g. ['gemini-2.5-pro', ...]).
    """
    if client is None:
        from pca_study_agent.agent import get_genai_client
        client = get_genai_client()

    if client is None:
        return []

    discovered: List[str] = []
    try:
        raw_models = client.models.list()
        for m in raw_models:
            full_name = getattr(m, "name", str(m))
            clean_id = full_name.split("/")[-1]
            lower_id = clean_id.lower()
            if "gemini" in lower_id and not any(k in lower_id for k in EXCLUDED_KEYWORDS):
                discovered.append(clean_id)
    except Exception as exc:
        logger.warning("Failed to query available models from GenAI provider", error=str(exc))

    # Return sorted unique list
    return sorted(list(set(discovered)))


def validate_and_resolve_models(
    flash_model: str,
    pro_model: str,
    interactive: bool = False,
) -> Tuple[str, str, List[str], Optional[str]]:
    """Validate model IDs against available models on startup.

    If an invalid model is detected:
    - Flags the issue immediately with descriptive warnings.
    - In interactive mode: Prompts user to select from available valid models.
    - In non-interactive mode: Automatically resolves to the best available models.

    Args:
        flash_model: Configured Flash model identifier.
        pro_model: Configured Pro model identifier.
        interactive: If True, allow interactive terminal prompt selection.

    Returns:
        Tuple[str, str, List[str], Optional[str]]:
            (resolved_flash_model, resolved_pro_model, available_models, warning_message)
    """
    from pca_study_agent.agent import get_genai_client
    client = get_genai_client()

    if client is None:
        return flash_model, pro_model, [], "No GenAI credentials configured. Running in offline knowledge mode."

    available_models = list_available_gemini_models(client)
    if not available_models:
        # Unable to list models (e.g. permission or quota restriction), return as-is
        return flash_model, pro_model, [], None

    resolved_flash = flash_model
    resolved_pro = pro_model
    warnings: List[str] = []

    # 1. Validate Flash Model
    if flash_model not in available_models:
        warnings.append(f"Configured Flash model '{flash_model}' is not available in your project/location.")
        # Find best Flash candidate
        flash_candidates = [m for m in available_models if "flash" in m and "lite" not in m]
        if not flash_candidates:
            flash_candidates = available_models

        if interactive and len(available_models) > 1:
            console.print(f"\n[bold yellow]⚠️ Flash Model '{flash_model}' not found.[/bold yellow]")
            console.print("[dim]Select a valid model for fast quizzes and scoring:[/dim]")
            for idx, candidate in enumerate(available_models, start=1):
                marker = " [bold green](Recommended Flash)[/bold green]" if "2.5-flash" in candidate else ""
                console.print(f"  [{idx}] {candidate}{marker}")
            choice = Prompt.ask("Choose Flash Model Number", default="1")
            try:
                c_idx = int(choice) - 1
                if 0 <= c_idx < len(available_models):
                    resolved_flash = available_models[c_idx]
            except ValueError:
                resolved_flash = flash_candidates[0] if flash_candidates else available_models[0]
        else:
            resolved_flash = next((m for m in flash_candidates if "2.5-flash" in m), flash_candidates[0] if flash_candidates else "gemini-2.5-flash")

    # 2. Validate Pro Model
    if pro_model not in available_models:
        warnings.append(f"Configured Pro model '{pro_model}' is not available in your project/location.")
        pro_candidates = [m for m in available_models if "pro" in m]
        if not pro_candidates:
            pro_candidates = available_models

        if interactive and len(available_models) > 1:
            console.print(f"\n[bold yellow]⚠️ Pro Model '{pro_model}' not found.[/bold yellow]")
            console.print("[dim]Select a valid model for deep-dive Socratic architectural reasoning:[/dim]")
            for idx, candidate in enumerate(available_models, start=1):
                marker = " [bold green](Recommended Pro)[/bold green]" if "2.5-pro" in candidate else ""
                console.print(f"  [{idx}] {candidate}{marker}")
            choice = Prompt.ask("Choose Pro Model Number", default="1")
            try:
                c_idx = int(choice) - 1
                if 0 <= c_idx < len(available_models):
                    resolved_pro = available_models[c_idx]
            except ValueError:
                resolved_pro = pro_candidates[0] if pro_candidates else available_models[0]
        else:
            resolved_pro = next((m for m in pro_candidates if "2.5-pro" in m), pro_candidates[0] if pro_candidates else "gemini-2.5-pro")

    warning_msg = " | ".join(warnings) if warnings else None
    if warning_msg:
        logger.warning(
            "Model validation warning on startup",
            configured_flash=flash_model,
            resolved_flash=resolved_flash,
            configured_pro=pro_model,
            resolved_pro=resolved_pro,
            available_models_count=len(available_models),
        )

    return resolved_flash, resolved_pro, available_models, warning_msg
