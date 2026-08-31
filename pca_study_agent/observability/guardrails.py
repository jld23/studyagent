"""Guardrails, Policy Enforcement, and Output Quality Verification.

Implements safety filters, prompt-injection defense, GCP architectural
accuracy validation, and self-evaluation plugins to guarantee grounded,
factual, and high-quality responses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# Disallowed prompt injection, jailbreak, and system exfiltration keywords
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?(instructions|guidelines|rules|prompts)",
    r"system\s+prompt\s+override",
    r"reveal\s+(internal|system|hidden)\s+(prompts|instructions|constitution)",
    r"bypass\s+safety\s+filter",
    r"\b(dan|jailbreak)\b",
    r"roleplay\s+as\s+(an\s+)?unrestricted",
    r"what\s+(is|are)\s+your\s+(exact\s+)?(system\s+prompt|instructions|constitution)",
    r"(print|show|output|repeat|dump|leak)\s+(your\s+)?(initial\s+|system\s+)?(prompt|instructions|constitution)",
    r"developer\s+mode\s+output",
    r"act\s+as\s+an\s+unfiltered",
    r"disregard\s+(all\s+)?(previous\s+)?(instructions|guidelines|rules)",
]

# Patterns that detect system instruction leakage or credential exfiltration in LLM outputs
EXFILTRATION_PATTERNS = [
    r"COORDINATOR_CONSTITUTION",
    r"SOCRATIC_TUTOR_CONSTITUTION",
    r"DIAGNOSTIC_CONSTITUTION",
    r"You are the Google Cloud PCA Study Coordinator",
    r"CONSTITUTION & OPERATIONAL PRINCIPLES",
    r"GEMINI_API_KEY\s*=\s*['\"]?[a-zA-Z0-9_\-]{10,}",
    r"AIza[0-9A-Za-z-_]{30,40}",
    r"(?:BEGIN|END)\s+(?:PRIVATE\s+KEY|CERTIFICATE|RSA\s+PRIVATE\s+KEY)",
]


def validate_input_safety(prompt: str) -> Tuple[bool, str]:
    """Validate user prompt against adversarial injections, jailbreaks, and policy violations.

    Args:
        prompt (str): Raw candidate input prompt.

    Returns:
        Tuple[bool, str]: (is_safe, failure_reason)
    """
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, "Input rejected by safety policy: adversarial prompt injection or jailbreak pattern detected."
    return True, "Input is safe."


def validate_output_safety(response_text: str) -> Tuple[bool, str]:
    """Validate generated LLM output to prevent system prompt leakage or credential exfiltration.

    Args:
        response_text (str): Generated response text from LLM.

    Returns:
        Tuple[bool, str]: (is_safe, sanitized_or_original_text)
    """
    if not isinstance(response_text, str):
        return True, response_text

    for pattern in EXFILTRATION_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return (
                False,
                "### 🎓 Google Cloud PCA Study Agent\n\n"
                "I am specialized exclusively in Google Cloud Professional Cloud Architect (PCA) preparation. "
                "Please ask a Google Cloud architecture question or type `/resume` to continue your drill.",
            )

    return True, response_text

# Google Cloud architectural facts and canonical mappings
KNOWN_GCP_SERVICES = {
    "compute engine",
    "google kubernetes engine",
    "gke",
    "cloud run",
    "cloud functions",
    "cloud storage",
    "persistent disk",
    "filestore",
    "cloud sql",
    "cloud spanner",
    "cloud bigtable",
    "bigquery",
    "firestore",
    "memorystore",
    "dataproc",
    "dataflow",
    "pub/sub",
    "cloud vpc",
    "cloud armor",
    "cloud kms",
    "secret manager",
    "vpc service controls",
    "security command center",
    "cloud monitoring",
    "cloud logging",
    "cloud trace",
    "cloud deploy",
    "cloud build",
}


def validate_input_safety(prompt: str) -> Tuple[bool, str]:
    """Validate user prompt against adversarial injections and policy violations.

    Args:
        prompt (str): Raw candidate input prompt.

    Returns:
        Tuple[bool, str]: (is_safe, failure_reason)
    """
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, "Input rejected by safety policy: adversarial pattern detected."
    return True, "Input is safe."


def verify_architectural_soundness(content: str) -> Dict[str, Any]:
    """Verify that generated explanations reference genuine GCP architectural concepts.

    Args:
        content (str): Candidate response or agent explanation.

    Returns:
        Dict[str, Any]: Verification summary with soundness score and referenced services.
    """
    lower_content = content.lower()
    referenced_services: List[str] = [svc for svc in KNOWN_GCP_SERVICES if svc in lower_content]

    # Evaluate groundedness
    is_grounded = len(referenced_services) > 0 or len(content.split()) < 20
    return {
        "is_grounded": is_grounded,
        "referenced_services": referenced_services,
        "quality_score": min(1.0, 0.5 + (0.1 * len(referenced_services))),
    }


def self_eval_explanation(
    question: str,
    correct_answer: str,
    explanation: str,
) -> Dict[str, Any]:
    """Self-evaluate the completeness and educational quality of an explanation.

    Args:
        question (str): The PCA scenario question.
        correct_answer (str): The correct option or architectural choice.
        explanation (str): The generated deep-dive explanation.

    Returns:
        Dict[str, Any]: Quality evaluation result containing criteria scores.
    """
    has_tradeoff_analysis = any(term in explanation.lower() for term in ["whereas", "unlike", "trade-off", "instead", "because", "advantage"])
    has_gcp_rationale = any(term in explanation.lower() for term in ["best practice", "scalability", "resilience", "cost", "security", "sla"])

    passed = has_tradeoff_analysis and has_gcp_rationale
    return {
        "status": "pass" if passed else "needs_improvement",
        "has_tradeoff_analysis": has_tradeoff_analysis,
        "has_gcp_rationale": has_gcp_rationale,
        "rubric_fidelity": 1.0 if passed else 0.7,
    }
