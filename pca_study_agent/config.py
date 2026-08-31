"""Configuration and Secure Secret Management for PCA Study Agent.

Ensures zero hardcoded credentials and dynamically supports:
1. Google AI Mode (API Key from Google AI Studio / Gemini API)
2. Vertex AI Mode (Application Default Credentials / ADC with GCP_PROJECT_ID)

Supports single unified `GEMINI_MODEL` or fine-grained `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


def _load_env_file() -> None:
    """Load .env file into os.environ (using python-dotenv or fallback parser)."""
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        # Built-in lightweight fallback parser
        for candidate_path in [Path(".env"), Path.home() / ".env"]:
            if candidate_path.exists():
                try:
                    for line in candidate_path.read_text().splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            key = k.strip()
                            val = v.strip().strip("'\"")
                            if key and key not in os.environ:
                                os.environ[key] = val
                except Exception:
                    pass


# Trigger environment file load
_load_env_file()


class Settings(BaseModel):
    """Application settings and configuration parameters."""

    # Project metadata
    app_name: str = "Google Cloud PCA Study Agent"
    app_version: str = "0.1.0"
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    # Gemini model configurations
    gemini_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    gemini_model: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_MODEL"))
    gemini_flash_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_FLASH_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )
    gemini_pro_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_PRO_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    )

    # Google Cloud / Vertex AI settings
    gcp_project_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    gcp_location: str = Field(
        default_factory=lambda: os.getenv("GCP_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    )

    # Legacy / alias properties for backward compatibility
    @property
    def google_cloud_project(self) -> Optional[str]:
        return self.gcp_project_id

    @property
    def google_cloud_location(self) -> str:
        return self.gcp_location

    use_gcp_secret_manager: bool = Field(
        default_factory=lambda: os.getenv("USE_GCP_SECRET_MANAGER", "false").lower() in ("true", "1", "yes")
    )
    secret_manager_key_name: str = Field(
        default_factory=lambda: os.getenv("SECRET_MANAGER_KEY_NAME", "pca-study-agent-gemini-key")
    )

    # Server settings
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_otel_tracing: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_OTEL_TRACING", "true").lower() in ("true", "1", "yes")
    )

    # Data directory paths
    data_dir: Path = Field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    user_profiles_dir: Path = Field(default_factory=lambda: Path(os.getenv("USER_PROFILES_DIR", "data/user_profiles")))
    study_materials_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("STUDY_MATERIALS_DIR", "data/study_materials"))
    )

    def ensure_directories(self) -> None:
        """Create necessary data storage directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.user_profiles_dir.mkdir(parents=True, exist_ok=True)
        self.study_materials_dir.mkdir(parents=True, exist_ok=True)

    def resolve_secrets(self) -> None:
        """Resolve API keys and credentials from Secret Manager if enabled."""
        if self.use_gcp_secret_manager and self.gcp_project_id:
            try:
                from google.cloud import secretmanager  # type: ignore

                client = secretmanager.SecretManagerServiceClient()
                secret_path = f"projects/{self.gcp_project_id}/secrets/{self.secret_manager_key_name}/versions/latest"
                response = client.access_secret_version(request={"name": secret_path})
                secret_payload = response.payload.data.decode("UTF-8").strip()
                if secret_payload:
                    self.gemini_api_key = secret_payload
            except Exception:
                # Fall back to environment variable if Secret Manager lookup fails
                pass


# Global singleton settings instance
settings = Settings()
settings.ensure_directories()
settings.resolve_secrets()
