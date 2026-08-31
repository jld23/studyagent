"""FastAPI REST API Routes for PCA Study Agent.

Exposes typed, validated endpoints for multi-user registration, conversational chat,
diagnostic testing, adaptive drilling, deep-dive architectural discussions,
progress reporting, custom material uploads, and syllabus synchronization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from pca_study_agent.agent import get_genai_client, root_agent
from pca_study_agent.config import settings
from pca_study_agent.tools import (
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

router = APIRouter(prefix="/api/v1", tags=["PCA Study Agent"])


# ============================================================================
# Request & Response API Models
# ============================================================================

class RegisterRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=64, description="Unique candidate ID")
    candidate_name: str = Field(default="Cloud Architect Candidate", description="Full name")
    target_exam_date: Optional[str] = Field(default=None, description="Target exam date YYYY-MM-DD")


class ChatRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    message: str = Field(min_length=1, description="Message or command for the study agent")
    session_id: Optional[str] = Field(default=None, description="Optional active session ID")


class AssessmentStartRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    num_questions: int = Field(default=6, ge=2, le=20, description="Questions count")


class DrillSubmitRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    item_id: str = Field(description="Item ID being answered")
    submitted_answer: str = Field(description="Option 'A', 'B', 'C', 'D' or flashcard rating")
    candidate_reasoning: Optional[str] = Field(default=None, description="Candidate reasoning")


class PauseRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    topic_of_inquiry: Optional[str] = Field(default=None, description="Topic or concept to explore")


class ResumeRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")


class MaterialUploadRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    title: str = Field(min_length=3, max_length=128, description="Material title")
    content: str = Field(min_length=10, description="Markdown or text content")
    domain_id: Optional[str] = Field(default=None, description="Associated domain ID")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")


class ResetProgressRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    confirmation_token: Optional[str] = Field(default=None, description="HITL confirmation token")


# ============================================================================
# Route Handlers
# ============================================================================

@router.get("/status/llm", summary="Check LLM Configuration Status")
async def get_llm_status() -> Dict[str, Any]:
    """Return whether Gemini LLM is configured and active in Google AI or Vertex AI mode."""
    client = get_genai_client()
    has_api_key = bool(
        settings.gemini_api_key
        and not settings.gemini_api_key.startswith("your_")
        and len(settings.gemini_api_key.strip()) > 10
    )
    has_gcp_project = bool(
        settings.gcp_project_id
        and not settings.gcp_project_id.startswith("your_")
        and len(settings.gcp_project_id.strip()) > 3
    )

    if has_api_key:
        mode = "google_ai"
        mode_desc = "Google AI Studio Mode (API Key)"
    elif has_gcp_project:
        mode = "vertex_ai"
        mode_desc = f"Vertex AI Mode with ADC (Project: {settings.gcp_project_id}, Region: {settings.gcp_location})"
    elif client is not None:
        mode = "auto_discovered"
        mode_desc = "Auto-Discovered ADC Environment"
    else:
        mode = "unconfigured"
        mode_desc = "Offline Knowledge Mode (No GEMINI_API_KEY or GCP_PROJECT_ID configured)"

    available = []
    if client is not None:
        from pca_study_agent.models_manager import list_available_gemini_models
        available = list_available_gemini_models(client)

    return {
        "llm_configured": client is not None,
        "mode": mode,
        "mode_description": mode_desc,
        "gcp_project_id": settings.gcp_project_id,
        "gcp_location": settings.gcp_location,
        "flash_model": settings.gemini_flash_model,
        "pro_model": settings.gemini_pro_model,
        "available_models": available,
        "message": (
            f"Live LLM is active in {mode_desc}."
            if client is not None
            else "Neither GEMINI_API_KEY nor GCP_PROJECT_ID configured. Set either in .env to activate live Gemini LLM reasoning."
        ),
    }


@router.post("/auth/register", summary="Authenticate or Register Candidate")
async def register_candidate(req: RegisterRequest) -> Dict[str, Any]:
    """Register or load a candidate profile with multi-user isolation."""
    res = authenticate_or_register_candidate(
        user_id=req.user_id,
        candidate_name=req.candidate_name,
        target_exam_date=req.target_exam_date,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/chat", summary="Send Message to Study Coordinator Agent")
async def send_chat_message(req: ChatRequest) -> Dict[str, Any]:
    """Send a message to the coordinator agent, executing safety guardrails and routing."""
    response = root_agent.process_message(
        user_id=req.user_id,
        user_input=req.message,
        session_id=req.session_id,
    )
    return response.model_dump()


@router.post("/assessment/start", summary="Start Diagnostic Assessment")
async def start_assessment(req: AssessmentStartRequest) -> Dict[str, Any]:
    """Start a comprehensive 6-domain baseline diagnostic assessment."""
    res = fetch_diagnostic_assessment_batch(
        user_id=req.user_id,
        num_questions=req.num_questions,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.get("/drill/next", summary="Fetch Next Adaptive Drill Item")
async def get_next_drill_item(
    user_id: str = Query(..., description="Candidate user ID"),
    item_type: str = Query("question", description="Preferred item type: question, flashcard, any"),
    target_domain_id: Optional[str] = Query(None, description="Optional target domain"),
) -> Dict[str, Any]:
    """Fetch the next adaptive drill item prioritized by Leitner spaced repetition."""
    res = fetch_adaptive_drill_item(
        user_id=user_id,
        preferred_item_type=item_type,
        target_domain_id=target_domain_id,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/submit", summary="Submit Answer and Update Mastery")
async def submit_drill_answer(req: DrillSubmitRequest) -> Dict[str, Any]:
    """Submit an answer to an active question or flashcard, updating spaced repetition mastery."""
    res = evaluate_scenario_answer_and_update_mastery(
        user_id=req.user_id,
        item_id=req.item_id,
        submitted_answer=req.submitted_answer,
        candidate_reasoning=req.candidate_reasoning,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/pause", summary="Pause Assessment for Deep-Dive Socratic Discussion")
async def pause_assessment(req: PauseRequest) -> Dict[str, Any]:
    """Pause the active assessment/drill to discuss trade-offs with the Principal Architect."""
    res = pause_assessment_session_for_deep_dive(
        user_id=req.user_id,
        topic_of_inquiry=req.topic_of_inquiry,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/resume", summary="Resume Paused Assessment Session")
async def resume_assessment(req: ResumeRequest) -> Dict[str, Any]:
    """Resume the active assessment or drill after completing a deep dive."""
    res = resume_assessment_session(user_id=req.user_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.get("/progress/report", summary="Generate 6-Domain Certification Progress Report")
async def get_progress_report(user_id: str = Query(..., description="Candidate user ID")) -> Dict[str, Any]:
    """Generate a comprehensive progress report mapped 1:1 against the 6 PCA certification domains."""
    res = generate_certification_domain_progress_report(user_id=user_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/materials/upload", summary="Ingest Custom Candidate Study Material")
async def upload_study_material(req: MaterialUploadRequest) -> Dict[str, Any]:
    """Upload custom study notes, cheat sheets, or architecture summaries for grounded retrieval."""
    res = ingest_user_study_material(
        user_id=req.user_id,
        title=req.title,
        content=req.content,
        domain_id=req.domain_id,
        tags=req.tags,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/materials/sync", summary="Sync Official Syllabus Materials")
async def trigger_materials_sync(force_refresh: bool = False) -> Dict[str, Any]:
    """Trigger periodic weekly synchronization check against official Google Cloud PCA syllabus."""
    res = sync_official_study_materials(force_refresh=force_refresh)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res)
    return res


@router.post("/admin/reset", summary="Reset Progress via HITL Confirmation")
async def reset_candidate_progress(req: ResetProgressRequest) -> Dict[str, Any]:
    """Request or confirm destructive progress reset requiring explicit Human-in-the-Loop token."""
    res = request_destructive_action_confirmation(
        user_id=req.user_id,
        action_type="reset_progress",
        confirmation_token=req.confirmation_token,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res
