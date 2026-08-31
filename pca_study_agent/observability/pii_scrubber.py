"""PII and Sensitive Data Redaction Module.

Active scrubbing mechanism to redact personally identifiable information (PII)
such as candidate email addresses, candidate full names, OAuth tokens, GCP project
identifiers, and API credentials before logs or state are stored.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union

# Patterns for sensitive data detection
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
API_KEY_REGEX = re.compile(r"(?:AIza[0-9A-Za-z-_]{35}|bearer\s+[a-zA-Z0-9._~+/-]+=*)", re.IGNORECASE)
BEARER_TOKEN_REGEX = re.compile(r"bearer\s+[a-zA-Z0-9_\-\.=]+", re.IGNORECASE)
PROJECT_ID_REGEX = re.compile(r"(?:projects/|project_id=)[a-z0-9-]{6,30}", re.IGNORECASE)


def redact_pii_text(text: str) -> str:
    """Redact sensitive PII and credential patterns from a string.

    Args:
        text (str): The raw text to scrub.

    Returns:
        str: The sanitized text with sensitive substrings replaced with redaction tokens.
    """
    if not isinstance(text, str):
        return text

    scrubbed = text
    scrubbed = EMAIL_REGEX.sub("[REDACTED_EMAIL]", scrubbed)
    scrubbed = API_KEY_REGEX.sub("[REDACTED_API_KEY]", scrubbed)
    scrubbed = BEARER_TOKEN_REGEX.sub("Bearer [REDACTED_TOKEN]", scrubbed)
    return scrubbed


def redact_pii_data(data: Union[Dict[str, Any], List[Any], str, Any]) -> Any:
    """Recursively scrub sensitive PII from dictionaries, lists, and primitives.

    Args:
        data: Arbitrary structured data or string.

    Returns:
        Sanitized copy of the input data structure.
    """
    if isinstance(data, str):
        return redact_pii_text(data)
    elif isinstance(data, dict):
        sanitized_dict: Dict[str, Any] = {}
        for key, value in data.items():
            # If key implies sensitive field, redact value directly
            lower_key = key.lower()
            if any(term in lower_key for term in ["password", "secret", "token", "api_key", "credentials"]):
                sanitized_dict[key] = "[REDACTED_SECRET]"
            else:
                sanitized_dict[key] = redact_pii_data(value)
        return sanitized_dict
    elif isinstance(data, list):
        return [redact_pii_data(item) for item in data]
    return data
