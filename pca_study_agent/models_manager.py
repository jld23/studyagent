"""Model Discovery, Startup Validation, and Interactive Selector.

Validates configured Gemini Flash and Pro model identifiers against the active
GenAI provider (Vertex AI or Google AI Studio) on startup, discovers available
publisher models, flags invalid configurations, and offers streamlined selection.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt

from pca_study_agent.config import settings
from pca_study_agent.observability.logger import logger

console = Console()

# Non-generative models to filter out from candidate lists
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

    return sorted(list(set(discovered)))


def validate_and_resolve_models(
    flash_model: str,
    pro_model: str,
    interactive: bool = False,
) -> Tuple[str, str, List[str], Optional[str]]:
    """Validate model IDs against available models on startup.

    If both models are already valid, returns immediately without prompts.
    If an invalid model is detected:
    - In interactive mode: Prompts user to select from available valid models.
    - In non-interactive mode: Automatically resolves to the best available matching models.

    Args:
        flash_model: Configured Flash model identifier.
        pro_model: Configured Pro model identifier.
        interactive: If True, allow interactive terminal prompt selection on error.

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
        return flash_model, pro_model, [], None

    # If both configured models are already in the available list, pass through with zero prompts!
    if flash_model in available_models and pro_model in available_models:
        return flash_model, pro_model, available_models, None

    resolved_flash = flash_model
    resolved_pro = pro_model
    warnings: List[str] = []

    # Identify best defaults from available models
    best_pro = next((m for m in available_models if "2.5-pro" in m), next((m for m in available_models if "pro" in m), available_models[0]))
    best_flash = next((m for m in available_models if "2.5-flash" in m and "lite" not in m), next((m for m in available_models if "flash" in m), available_models[0]))

    if flash_model not in available_models or pro_model not in available_models:
        warnings.append(f"Configured model not available in your project/location (Flash: '{flash_model}', Pro: '{pro_model}').")

        if interactive:
            console.print(f"\n[bold yellow]⚠️ Configured model not found in your GCP Project/Location.[/bold yellow]")
            console.print(f"[dim]Available Gemini Models:[/dim]")
            for idx, candidate in enumerate(available_models, start=1):
                marker = " [bold green](Recommended)[/bold green]" if candidate in (best_pro, best_flash) else ""
                console.print(f"  [{idx}] {candidate}{marker}")

            choice = Prompt.ask(
                f"Select model (or press Enter for auto [Flash={best_flash}, Pro={best_pro}])",
                default="auto",
            ).strip()

            if choice.lower() != "auto":
                try:
                    c_idx = int(choice) - 1
                    if 0 <= c_idx < len(available_models):
                        selected = available_models[c_idx]
                        resolved_flash = selected
                        resolved_pro = selected
                except ValueError:
                    resolved_flash = best_flash
                    resolved_pro = best_pro
            else:
                resolved_flash = best_flash
                resolved_pro = best_pro
        else:
            resolved_flash = best_flash
            resolved_pro = best_pro

    warning_msg = " | ".join(warnings) if warnings else None
    return resolved_flash, resolved_pro, available_models, warning_msg
