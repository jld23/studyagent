"""Human-in-the-Loop (HITL) Action Confirmation Hooks.

Enforces strict human confirmation gates before executing high-stakes or
destructive actions such as resetting candidate progress history, wiping
mastery databases, or overriding exam readiness milestones.
"""

from __future__ import annotations

import secrets
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PendingAction(BaseModel):
    """Data model for an action awaiting explicit human approval."""

    token: str
    user_id: str
    action_type: str = Field(description="Type of action e.g., 'reset_progress', 'delete_profile'")
    details: Dict[str, Any]
    created_at: float = Field(default_factory=time.time)
    expires_at: float


class HITLManager:
    """In-memory store and verification manager for high-stakes pending actions."""

    def __init__(self, token_ttl_seconds: int = 300) -> None:
        self._pending: Dict[str, PendingAction] = {}
        self._token_ttl = token_ttl_seconds

    def create_confirmation_request(
        self,
        user_id: str,
        action_type: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a pending action requiring explicit human confirmation.

        Args:
            user_id (str): Candidate identifier.
            action_type (str): Destructive or high-stakes action name.
            details (Dict[str, Any]): Action parameters and impact description.

        Returns:
            Dict[str, Any]: Confirmation prompt instructions and token for the user.
        """
        token = secrets.token_hex(4).upper()  # e.g., 'A8F2E491'
        expires = time.time() + self._token_ttl
        pending = PendingAction(
            token=token,
            user_id=user_id,
            action_type=action_type,
            details=details,
            expires_at=expires,
        )
        self._pending[token] = pending

        return {
            "requires_confirmation": True,
            "action_type": action_type,
            "warning": f"CAUTION: '{action_type}' is a high-stakes action. Explicit confirmation is required.",
            "impact": details.get("impact_summary", "This action will alter or delete persistent user data."),
            "confirmation_token": token,
            "expires_in_seconds": self._token_ttl,
            "instructions": f"To execute this action, provide confirmation token '{token}'.",
        }

    def validate_and_consume_token(
        self,
        user_id: str,
        token: str,
    ) -> Tuple[bool, Optional[PendingAction], str]:
        """Validate and consume a human confirmation token.

        Args:
            user_id (str): Candidate identifier.
            token (str): The confirmation token entered by the user.

        Returns:
            Tuple[bool, Optional[PendingAction], str]: (is_valid, pending_action, message)
        """
        token = token.strip().upper()
        if token not in self._pending:
            return False, None, "Invalid or unrecognized confirmation token."

        pending = self._pending[token]
        if pending.user_id != user_id:
            return False, None, "Confirmation token does not belong to the current user."

        if time.time() > pending.expires_at:
            del self._pending[token]
            return False, None, "Confirmation token has expired. Please re-initiate the action request."

        # Valid: consume and remove token
        del self._pending[token]
        return True, pending, "Human confirmation verified successfully."


# Global HITL Manager instance
hitl_manager = HITLManager()
