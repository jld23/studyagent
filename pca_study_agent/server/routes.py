"""FastAPI REST API Routes for PCA Study Agent.

Exposes typed, validated endpoints for multi-user registration, conversational chat,
diagnostic testing, adaptive drilling, deep-dive architectural discussions,
progress reporting, custom material uploads, and syllabus synchronization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from pca_study_agent.agent import root_agent
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
    topic_of_inquiry: Optional[str] = Field(default=None, description="Topic to discuss")


class ResumeRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")


class MaterialUploadRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    title: str = Field(min_length=3, max_length=200, description="Title of note")
    content: str = Field(min_length=10, description="Markdown/text note content")
    domain_id: Optional[str] = Field(default=None, description="Optional domain ID")
    tags: List[str] = Field(default_factory=list, description="Tags/keywords")


class ResetProgressRequest(BaseModel):
    user_id: str = Field(description="Candidate user ID")
    confirmation_token: Optional[str] = Field(default=None, description="HITL confirmation token")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/auth/register", summary="Register or Login Candidate Profile")
async def register_candidate(req: RegisterRequest) -> Dict[str, Any]:
    """Authenticate or register a candidate and retrieve their current readiness profile."""
    res = authenticate_or_register_candidate(
        user_id=req.user_id,
        candidate_name=req.candidate_name,
        target_exam_date=req.target_exam_date,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/chat", summary="Chat with Study Coordinator Multi-Agent")
async def chat_interaction(req: ChatRequest) -> Dict[str, Any]:
    """Interact with the root Coordinator, which intelligently routes to tools and specialists."""
    agent_response = root_agent.process_message(
        user_id=req.user_id,
        user_input=req.message,
        session_id=req.session_id,
    )
    return agent_response.model_dump()


@router.post("/assessment/start", summary="Start Initial Diagnostic Assessment")
async def start_diagnostic_assessment(req: AssessmentStartRequest) -> Dict[str, Any]:
    """Generate a multi-domain baseline assessment to evaluate candidate starting proficiency."""
    res = fetch_diagnostic_assessment_batch(user_id=req.user_id, num_questions=req.num_questions)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.get("/drill/next", summary="Fetch Next Adaptive Drill Item")
async def get_adaptive_drill_item(
    user_id: str = Query(..., description="Candidate user ID"),
    item_type: str = Query("question", description="'question' or 'flashcard'"),
    domain_id: Optional[str] = Query(None, description="Optional domain filter e.g. 'domain_1'"),
) -> Dict[str, Any]:
    """Retrieve the next spaced-repetition scenario question or flashcard targeting weakest domains."""
    res = fetch_adaptive_drill_item(
        user_id=user_id,
        preferred_item_type=item_type,
        target_domain_id=domain_id,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/submit", summary="Submit Answer and Update Mastery")
async def submit_drill_answer(req: DrillSubmitRequest) -> Dict[str, Any]:
    """Grade answer submission, return distractor analysis, and update Leitner box and domain mastery."""
    res = evaluate_scenario_answer_and_update_mastery(
        user_id=req.user_id,
        item_id=req.item_id,
        submitted_answer=req.submitted_answer,
        candidate_reasoning=req.candidate_reasoning,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/pause", summary="Pause Drill for Socratic Deep-Dive")
async def pause_drill(req: PauseRequest) -> Dict[str, Any]:
    """Pause the active assessment session and switch to Socratic Architect Tutor mode."""
    res = pause_assessment_session_for_deep_dive(
        user_id=req.user_id,
        topic_of_inquiry=req.topic_of_inquiry,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res)
    return res


@router.post("/drill/resume", summary="Resume Paused Drill")
async def resume_drill(req: ResumeRequest) -> Dict[str, Any]:
    """Resume a paused drill session and return to the active question queue."""
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
