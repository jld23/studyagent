"""FastAPI Application for Google Cloud PCA Multi-User Study Agent.

Includes OpenAPI documentation, lifespan startup tasks, CORS configuration,
health check endpoints, static web client serving, and REST API routing.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pca_study_agent.config import settings
from pca_study_agent.observability.logger import logger
from pca_study_agent.server.routes import router as api_v1_router

STATIC_DIR = Path(__file__).parent / "static"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    from pca_study_agent.models_manager import validate_and_resolve_models

    settings.ensure_directories()
    settings.resolve_secrets()

    # Validate and resolve configured model IDs on startup
    res_flash, res_pro, available_models, warning_msg = validate_and_resolve_models(
        flash_model=settings.gemini_flash_model,
        pro_model=settings.gemini_pro_model,
        interactive=False,
    )
    settings.gemini_flash_model = res_flash
    settings.gemini_pro_model = res_pro

    logger.info(
        "PCA Study Agent Server Starting",
        version=settings.app_version,
        environment=settings.environment,
        flash_model=settings.gemini_flash_model,
        pro_model=settings.gemini_pro_model,
        available_models_count=len(available_models),
        validation_warning=warning_msg,
    )
    yield
    logger.info("PCA Study Agent Server Shutting Down")


app = FastAPI(
    title="Google Cloud Professional Cloud Architect (PCA) Study Agent",
    description=(
        "An intelligent, multi-user, adaptive study agent built with Google ADK and Gemini. "
        "Provides diagnostic assessments, adaptive spaced repetition drills, deep-dive Socratic architectural "
        "discussions, progress tracking across the 6 official PCA certification domains, and study material ingestion."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register API routes
app.include_router(api_v1_router)


@app.get("/health", summary="Service Health Check")
async def health_check() -> dict[str, str]:
    """Return health status and version metadata."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/", summary="Web Application & Dashboard", include_in_schema=False)
async def web_ui():
    """Serve the interactive web interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Welcome to the Google Cloud Professional Cloud Architect Study Agent API!",
        "documentation_url": "/docs",
        "status_url": "/health",
    }
