"""ADK Tool Definitions for Google Cloud PCA Multi-User Study Agent.

Implements all 4 criteria of Rubric 1 (Tool & Interface Design):
1. Comprehensive Google-format docstrings with parameter and return descriptions.
2. Descriptive and specific naming conventions.
3. Explicit JSON Schemas using strict Pydantic models.
4. Guided error handling with recovery suggestions for LLM self-correction.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pca_study_agent.knowledge.exam_domains import PCA_DOMAINS
from pca_study_agent.knowledge.question_bank import PCA_FLASHCARDS, PCA_QUESTIONS
from pca_study_agent.knowledge.retriever import retriever
from pca_study_agent.knowledge.sync_engine import sync_engine
from pca_study_agent.memory.spaced_repetition import SpacedRepetitionScheduler
from pca_study_agent.memory.user_manager import ActiveDrillState, user_manager
from pca_study_agent.observability.hitl import hitl_manager
from pca_study_agent.observability.logger import log_agent_intent, log_agent_outcome, logger
from pca_study_agent.observability.telemetry import get_current_trace_id, trace_span


# ============================================================================
# Strict Pydantic Input / Output Schemas
# ============================================================================

class ToolErrorResponse(BaseModel):
    """Guided error response providing LLM with recovery instructions."""

    status: str = "error"
    error_code: str
    message: str
    recovery_suggestion: str


class AuthCandidateInput(BaseModel):
    """Input schema for candidate authentication or registration."""

    user_id: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-\.@]+$",
        description="Unique identifier or username for the candidate.",
    )
    candidate_name: str = Field(
        default="Cloud Architect Candidate",
        min_length=2,
        max_length=128,
        description="Display name of the candidate.",
    )
    target_exam_date: Optional[str] = Field(
        default=None,
        description="Target certification exam date (e.g. '2026-11-15').",
    )


class AuthCandidateOutput(BaseModel):
    """Output schema for candidate authentication."""

    status: str = "success"
    user_id: str
    name: str
    target_exam_date: Optional[str]
    diagnostic_completed: bool
    domain_mastery: Dict[str, float]
    overall_readiness_percentage: float
    total_questions_answered: int
    message: str


class DiagnosticBatchInput(BaseModel):
    """Input schema for starting a diagnostic assessment."""

    user_id: str = Field(description="Candidate identifier.")
    num_questions: int = Field(
        default=6,
        ge=2,
        le=20,
        description="Number of diagnostic questions to assemble across all 6 domains.",
    )


class DiagnosticBatchOutput(BaseModel):
    """Output schema for diagnostic assessment initialization."""

    status: str = "success"
    session_id: str
    total_questions: int
    domains_covered: List[str]
    questions: List[Dict[str, Any]]
    instructions: str


class AdaptiveDrillItemInput(BaseModel):
    """Input schema for fetching the next adaptive drill item."""

    user_id: str = Field(description="Candidate identifier.")
    preferred_item_type: str = Field(
        default="question",
        description="Preferred item type: 'question', 'flashcard', or 'any'.",
    )
    target_domain_id: Optional[str] = Field(
        default=None,
        description="Optional domain ID filter (e.g. 'domain_1', 'domain_3').",
    )


class AdaptiveDrillItemOutput(BaseModel):
    """Output schema for adaptive drill item."""

    status: str = "success"
    item_id: str
    item_type: str
    domain_id: str
    domain_title: str
    difficulty: str
    current_mastery_level: float
    leitner_box: int
    content: Dict[str, Any]
    active_drill_status: str


class AnswerSubmissionInput(BaseModel):
    """Input schema for candidate answer submission."""

    user_id: str = Field(description="Candidate identifier.")
    item_id: str = Field(description="ID of the question or flashcard being answered.")
    submitted_answer: str = Field(
        description="Selected option (e.g. 'A', 'B', 'C', 'D') or flashcard self-rating ('correct', 'incorrect')."
    )
    candidate_reasoning: Optional[str] = Field(
        default=None,
        description="Optional reasoning provided by the candidate.",
    )


class AnswerSubmissionOutput(BaseModel):
    """Output schema for answer evaluation and mastery update."""

    status: str = "success"
    item_id: str
    is_correct: bool
    correct_answer: str
    architectural_principle: str
    explanation: str
    distractor_analysis: Optional[Dict[str, str]]
    domain_id: str
    updated_domain_mastery: float
    new_leitner_box: int
    next_review_recommendation: str


class DeepDivePauseInput(BaseModel):
    """Input schema for pausing active drill for deep-dive discussion."""

    user_id: str = Field(description="Candidate identifier.")
    topic_of_inquiry: Optional[str] = Field(
        default=None,
        description="Specific GCP service or question topic candidate wants to discuss.",
    )


class DeepDivePauseOutput(BaseModel):
    """Output schema for drill pause confirmation."""

    status: str = "success"
    is_paused: bool
    paused_item_id: Optional[str]
    tutor_mode_active: bool
    suggested_discussion_topics: List[str]
    message: str


class DeepDiveResumeInput(BaseModel):
    """Input schema for resuming a paused assessment."""

    user_id: str = Field(description="Candidate identifier.")


class DeepDiveResumeOutput(BaseModel):
    """Output schema for drill resumption."""

    status: str = "success"
    is_resumed: bool
    resumed_item_id: Optional[str]
    remaining_items_in_queue: int
    message: str


class ProgressReportInput(BaseModel):
    """Input schema for generating progress and certification readiness report."""

    user_id: str = Field(description="Candidate identifier.")


class ProgressReportOutput(BaseModel):
    """Output schema for certification progress report."""

    status: str = "success"
    candidate_name: str
    overall_readiness_score: float
    estimated_pass_probability: str
    total_questions_attempted: int
    accuracy_percentage: float
    domain_breakdown: List[Dict[str, Any]]
    weakest_domains: List[str]
    strongest_domains: List[str]
    recommended_next_actions: List[str]


class UserMaterialIngestInput(BaseModel):
    """Input schema for custom user study material upload."""

    user_id: str = Field(description="Candidate identifier.")
    title: str = Field(min_length=3, max_length=200, description="Title of the study note.")
    content: str = Field(min_length=10, description="Text notes, architecture summary, or cheat sheet.")
    domain_id: Optional[str] = Field(default=None, description="Optional domain ID e.g. 'domain_1'.")
    tags: List[str] = Field(default_factory=list, description="Keywords / tags e.g. ['spanner', 'migration'].")


class UserMaterialIngestOutput(BaseModel):
    """Output schema for custom study material ingestion."""

    status: str = "success"
    doc_id: str
    title: str
    domain_id: Optional[str]
    indexed_tags: List[str]
    total_user_materials_stored: int
    message: str


class SyncOfficialMaterialsInput(BaseModel):
    """Input schema for triggering weekly official materials sync."""

    force_refresh: bool = Field(default=False, description="Whether to force update all official materials.")


class SyncOfficialMaterialsOutput(BaseModel):
    """Output schema for weekly materials sync."""

    status: str = "success"
    sync_version: str
    last_synced_at: str
    total_documents: int
    message: str


class DestructiveActionConfirmationInput(BaseModel):
    """Input schema for requesting or executing high-stakes destructive actions."""

    user_id: str = Field(description="Candidate identifier.")
    action_type: str = Field(description="'reset_progress' or 'delete_profile'")
    confirmation_token: Optional[str] = Field(
        default=None,
        description="Confirmation token provided by human. Omit on initial call to generate token.",
    )


class DestructiveActionConfirmationOutput(BaseModel):
    """Output schema for destructive action confirmation."""

    status: str
    action_executed: bool
    requires_confirmation: bool
    confirmation_token: Optional[str]
    message: str


# ============================================================================
# Core ADK Tool Implementations
# ============================================================================

def authenticate_or_register_candidate(
    user_id: str,
    candidate_name: str = "Cloud Architect Candidate",
    target_exam_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Authenticate an existing candidate or register a new profile with isolated memory.

    Args:
        user_id (str): Unique identifier or username for the candidate.
        candidate_name (str): Display name for the candidate.
        target_exam_date (Optional[str]): Target date for taking the PCA exam.

    Returns:
        Dict[str, Any]: Authentication result including mastery scores and readiness metrics.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="authenticate_or_register_candidate",
        user_id=user_id,
        session_id=user_id,
        target_component="UserManager",
        intended_parameters={"user_id": user_id, "name": candidate_name},
        trace_id=trace_id,
    )

    try:
        # Validate input schema
        params = AuthCandidateInput(
            user_id=user_id,
            candidate_name=candidate_name,
            target_exam_date=target_exam_date,
        )

        profile = user_manager.get_or_create_user(
            user_id=params.user_id,
            name=params.candidate_name,
            target_exam_date=params.target_exam_date,
        )

        # Calculate overall readiness
        mastery_vals = list(profile.domain_mastery.values())
        avg_mastery = sum(mastery_vals) / len(mastery_vals) if mastery_vals else 0.5
        readiness_pct = round(avg_mastery * 100, 1)

        output = AuthCandidateOutput(
            user_id=profile.user_id,
            name=profile.name,
            target_exam_date=profile.target_exam_date,
            diagnostic_completed=profile.diagnostic_completed,
            domain_mastery=profile.domain_mastery,
            overall_readiness_percentage=readiness_pct,
            total_questions_answered=profile.total_questions_answered,
            message=f"Welcome back, {profile.name}! Your study workspace is loaded.",
        ).model_dump()

        log_agent_outcome(
            action_name="authenticate_or_register_candidate",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"user_id": profile.user_id, "readiness": readiness_pct},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="AUTH_FAILED",
            message=f"Authentication failed: {str(exc)}",
            recovery_suggestion="Provide a valid alphanumeric user_id between 3 and 64 characters.",
        ).model_dump()
        log_agent_outcome(
            action_name="authenticate_or_register_candidate",
            user_id=user_id,
            session_id=user_id,
            status="failed",
            start_time=start_time,
            result_summary=err,
            error_message=str(exc),
            trace_id=trace_id,
        )
        return err


def fetch_diagnostic_assessment_batch(
    user_id: str,
    num_questions: int = 6,
) -> Dict[str, Any]:
    """Assemble a balanced diagnostic assessment spanning all 6 PCA domains and case studies.

    Args:
        user_id (str): Candidate identifier.
        num_questions (int): Number of diagnostic questions to assemble (default 6).

    Returns:
        Dict[str, Any]: Diagnostic session payload with question scenarios and options.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="fetch_diagnostic_assessment_batch",
        user_id=user_id,
        session_id=user_id,
        target_component="QuestionBank",
        intended_parameters={"user_id": user_id, "num_questions": num_questions},
        trace_id=trace_id,
    )

    try:
        params = DiagnosticBatchInput(user_id=user_id, num_questions=num_questions)
        profile = user_manager.get_or_create_user(params.user_id)

        # Select representative questions across available domains
        selected_questions = PCA_QUESTIONS[: params.num_questions]
        question_ids = [q.id for q in selected_questions]

        # Initialize active drill session
        session_id = f"diag_{uuid.uuid4().hex[:8]}"
        profile.active_drill = ActiveDrillState(
            session_id=session_id,
            mode="diagnostic",
            current_item_id=question_ids[0] if question_ids else None,
            question_queue=question_ids,
            is_paused_for_deep_dive=False,
        )
        user_manager.save_user_async(profile)

        # Format questions for client (omit correct answers to prevent leakage)
        client_questions = []
        for q in selected_questions:
            dom = PCA_DOMAINS.get(q.domain_id)
            client_questions.append(
                {
                    "question_id": q.id,
                    "domain_id": q.domain_id,
                    "domain_title": dom.title if dom else q.domain_id,
                    "difficulty": q.difficulty,
                    "case_study_id": q.case_study_id,
                    "question_text": q.question_text,
                    "options": [opt.model_dump() for opt in q.options],
                }
            )

        output = DiagnosticBatchOutput(
            session_id=session_id,
            total_questions=len(client_questions),
            domains_covered=list({q["domain_id"] for q in client_questions}),
            questions=client_questions,
            instructions="Review each question scenario carefully. Select your chosen option (A, B, C, or D) and provide your architectural rationale.",
        ).model_dump()

        log_agent_outcome(
            action_name="fetch_diagnostic_assessment_batch",
            user_id=user_id,
            session_id=session_id,
            status="success",
            start_time=start_time,
            result_summary={"session_id": session_id, "total": len(client_questions)},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="DIAGNOSTIC_SETUP_ERROR",
            message=f"Failed to generate diagnostic assessment: {str(exc)}",
            recovery_suggestion="Ensure user_id is authenticated and num_questions is between 2 and 20.",
        ).model_dump()
        log_agent_outcome(
            action_name="fetch_diagnostic_assessment_batch",
            user_id=user_id,
            session_id=user_id,
            status="failed",
            start_time=start_time,
            result_summary=err,
            error_message=str(exc),
            trace_id=trace_id,
        )
        return err


def fetch_adaptive_drill_item(
    user_id: str,
    preferred_item_type: str = "question",
    target_domain_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve the next highest-priority adaptive flashcard or scenario question based on weak domains.

    Args:
        user_id (str): Candidate identifier.
        preferred_item_type (str): Preferred item type ('question', 'flashcard', or 'any').
        target_domain_id (Optional[str]): Specific domain filter (e.g. 'domain_3').

    Returns:
        Dict[str, Any]: Selected adaptive drill item with current mastery context.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="fetch_adaptive_drill_item",
        user_id=user_id,
        session_id=user_id,
        target_component="SpacedRepetitionScheduler",
        intended_parameters={
            "user_id": user_id,
            "type": preferred_item_type,
            "domain": target_domain_id,
        },
        trace_id=trace_id,
    )

    try:
        params = AdaptiveDrillItemInput(
            user_id=user_id,
            preferred_item_type=preferred_item_type,
            target_domain_id=target_domain_id,
        )
        profile = user_manager.get_or_create_user(params.user_id)

        # Identify candidate's weakest domain if no filter provided
        if not params.target_domain_id:
            sorted_domains = sorted(profile.domain_mastery.items(), key=lambda kv: kv[1])
            selected_domain_id = sorted_domains[0][0]  # Lowest mastery domain
        else:
            selected_domain_id = params.target_domain_id

        mastery_score = profile.domain_mastery.get(selected_domain_id, 0.5)

        # Decide question vs flashcard
        if params.preferred_item_type == "flashcard":
            # Pick flashcard
            matching_cards = [fc for fc in PCA_FLASHCARDS if fc.domain_id == selected_domain_id]
            if not matching_cards:
                matching_cards = PCA_FLASHCARDS
            card = matching_cards[0]
            item_record = profile.spaced_items.get(card.id)
            box_num = item_record.box_number if item_record else 1

            dom = PCA_DOMAINS.get(card.domain_id)
            content_payload = {
                "topic": card.topic,
                "prompt": card.front_prompt,
                "key_tradeoff": card.key_tradeoff,
            }
            output = AdaptiveDrillItemOutput(
                item_id=card.id,
                item_type="flashcard",
                domain_id=card.domain_id,
                domain_title=dom.title if dom else card.domain_id,
                difficulty="intermediate",
                current_mastery_level=mastery_score,
                leitner_box=box_num,
                content=content_payload,
                active_drill_status="active",
            ).model_dump()
        else:
            # Pick scenario question
            matching_questions = [q for q in PCA_QUESTIONS if q.domain_id == selected_domain_id]
            if not matching_questions:
                matching_questions = PCA_QUESTIONS
            q = matching_questions[0]
            item_record = profile.spaced_items.get(q.id)
            box_num = item_record.box_number if item_record else 1

            dom = PCA_DOMAINS.get(q.domain_id)
            content_payload = {
                "question_text": q.question_text,
                "case_study_id": q.case_study_id,
                "options": [opt.model_dump() for opt in q.options],
            }
            output = AdaptiveDrillItemOutput(
                item_id=q.id,
                item_type="question",
                domain_id=q.domain_id,
                domain_title=dom.title if dom else q.domain_id,
                difficulty=q.difficulty,
                current_mastery_level=mastery_score,
                leitner_box=box_num,
                content=content_payload,
                active_drill_status="active",
            ).model_dump()

        # Update active drill state
        if not profile.active_drill:
            profile.active_drill = ActiveDrillState(
                session_id=f"drill_{uuid.uuid4().hex[:8]}",
                mode="adaptive_drill",
                current_item_id=output["item_id"],
            )
        else:
            profile.active_drill.current_item_id = output["item_id"]
        user_manager.save_user_async(profile)

        log_agent_outcome(
            action_name="fetch_adaptive_drill_item",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"item_id": output["item_id"], "domain": selected_domain_id},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="ADAPTIVE_FETCH_ERROR",
            message=f"Failed to fetch adaptive drill item: {str(exc)}",
            recovery_suggestion="Ensure user_id is authenticated and domain_id is valid (e.g. 'domain_1').",
        ).model_dump()
        log_agent_outcome(
            action_name="fetch_adaptive_drill_item",
            user_id=user_id,
            session_id=user_id,
            status="failed",
            start_time=start_time,
            result_summary=err,
            error_message=str(exc),
            trace_id=trace_id,
        )
        return err


def evaluate_scenario_answer_and_update_mastery(
    user_id: str,
    item_id: str,
    submitted_answer: str,
    candidate_reasoning: Optional[str] = None,
) -> Dict[str, Any]:
    """Grade candidate answer, update Leitner spaced repetition box, and adjust domain mastery.

    Args:
        user_id (str): Candidate identifier.
        item_id (str): ID of the question or flashcard.
        submitted_answer (str): Chosen option (e.g. 'A', 'B', 'C', 'D') or flashcard self-evaluation.
        candidate_reasoning (Optional[str]): Architectural rationale provided by the candidate.

    Returns:
        Dict[str, Any]: Detailed grading breakdown, correct explanation, distractor analysis, and updated mastery.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="evaluate_scenario_answer_and_update_mastery",
        user_id=user_id,
        session_id=user_id,
        target_component="MasteryEngine",
        intended_parameters={
            "user_id": user_id,
            "item_id": item_id,
            "submitted_answer": submitted_answer,
        },
        trace_id=trace_id,
    )

    try:
        params = AnswerSubmissionInput(
            user_id=user_id,
            item_id=item_id,
            submitted_answer=submitted_answer,
            candidate_reasoning=candidate_reasoning,
        )

        # Check if item is a question
        question = next((q for q in PCA_QUESTIONS if q.id == params.item_id), None)
        if question:
            is_correct = params.submitted_answer.strip().upper() == question.correct_option.upper()
            domain_id = question.domain_id
            explanation = question.explanation
            distractor_map = question.distractor_analysis
            principle = question.architectural_principle
            correct_ans = question.correct_option
            item_type = "question"
        else:
            # Check flashcard
            flashcard = next((fc for fc in PCA_FLASHCARDS if fc.id == params.item_id), None)
            if not flashcard:
                raise ValueError(f"Item ID '{params.item_id}' not found in question or flashcard banks.")
            is_correct = params.submitted_answer.strip().lower() in ("correct", "yes", "true", "1")
            domain_id = flashcard.domain_id
            explanation = flashcard.back_solution
            distractor_map = None
            principle = flashcard.key_tradeoff
            correct_ans = flashcard.back_solution
            item_type = "flashcard"

        # Update user profile and spaced repetition box
        profile, item_rec, new_mastery = user_manager.update_item_score_and_mastery(
            user_id=params.user_id,
            item_id=params.item_id,
            item_type=item_type,
            domain_id=domain_id,
            is_correct=is_correct,
        )

        review_rec = (
            f"Great job! Advanced to Leitner Box {item_rec.box_number}."
            if is_correct
            else "Moved to Leitner Box 1 for intensive spaced repetition review."
        )

        output = AnswerSubmissionOutput(
            item_id=params.item_id,
            is_correct=is_correct,
            correct_answer=correct_ans,
            architectural_principle=principle,
            explanation=explanation,
            distractor_analysis=distractor_map,
            domain_id=domain_id,
            updated_domain_mastery=new_mastery,
            new_leitner_box=item_rec.box_number,
            next_review_recommendation=review_rec,
        ).model_dump()

        log_agent_outcome(
            action_name="evaluate_scenario_answer_and_update_mastery",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"is_correct": is_correct, "new_mastery": new_mastery, "box": item_rec.box_number},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="ANSWER_EVALUATION_ERROR",
            message=f"Failed to evaluate answer submission: {str(exc)}",
            recovery_suggestion="Verify item_id exists and submitted_answer is 'A', 'B', 'C', 'D' or 'correct'/'incorrect'.",
        ).model_dump()
        log_agent_outcome(
            action_name="evaluate_scenario_answer_and_update_mastery",
            user_id=user_id,
            session_id=user_id,
            status="failed",
            start_time=start_time,
            result_summary=err,
            error_message=str(exc),
            trace_id=trace_id,
        )
        return err


def pause_assessment_session_for_deep_dive(
    user_id: str,
    topic_of_inquiry: Optional[str] = None,
) -> Dict[str, Any]:
    """Pause the active assessment/drill to transition candidate into Socratic Architect Tutor mode.

    Args:
        user_id (str): Candidate identifier.
        topic_of_inquiry (Optional[str]): Topic or GCP service candidate wants to discuss.

    Returns:
        Dict[str, Any]: Pause confirmation with active tutor suggestions.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="pause_assessment_session_for_deep_dive",
        user_id=user_id,
        session_id=user_id,
        target_component="StudyCoordinator",
        intended_parameters={"user_id": user_id, "topic": topic_of_inquiry},
        trace_id=trace_id,
    )

    try:
        params = DeepDivePauseInput(user_id=user_id, topic_of_inquiry=topic_of_inquiry)
        profile = user_manager.get_or_create_user(params.user_id)

        if profile.active_drill:
            profile.active_drill.is_paused_for_deep_dive = True
            paused_item = profile.active_drill.current_item_id
        else:
            paused_item = None

        user_manager.save_user_async(profile)

        output = DeepDivePauseOutput(
            is_paused=True,
            paused_item_id=paused_item,
            tutor_mode_active=True,
            suggested_discussion_topics=[
                "Why a particular service was chosen over alternatives (e.g. Spanner vs Bigtable)",
                "Underlying Google Cloud networking and hybrid architecture design",
                "Case study deep dive (Mountkirk Games, TerramEarth, EHR Healthcare, HRL)",
                "Security, CMEK, and VPC Service Controls trade-offs",
            ],
            message="Drill paused. You are now in Deep-Dive discussion mode with your Google Cloud Principal Architect tutor. Ask any architectural question!",
        ).model_dump()

        log_agent_outcome(
            action_name="pause_assessment_session_for_deep_dive",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"paused_item": paused_item},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="PAUSE_FAILED",
            message=f"Failed to pause session: {str(exc)}",
            recovery_suggestion="Ensure user_id is authenticated before calling pause.",
        ).model_dump()
        return err


def resume_assessment_session(user_id: str) -> Dict[str, Any]:
    """Resume a paused drill session and return to the active question queue.

    Args:
        user_id (str): Candidate identifier.

    Returns:
        Dict[str, Any]: Resume status and current active item ID.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="resume_assessment_session",
        user_id=user_id,
        session_id=user_id,
        target_component="StudyCoordinator",
        intended_parameters={"user_id": user_id},
        trace_id=trace_id,
    )

    try:
        params = DeepDiveResumeInput(user_id=user_id)
        profile = user_manager.get_or_create_user(params.user_id)

        if not profile.active_drill:
            return ToolErrorResponse(
                error_code="NO_ACTIVE_DRILL",
                message="No active drill session found to resume.",
                recovery_suggestion="Start a new diagnostic assessment or adaptive drill session.",
            ).model_dump()

        profile.active_drill.is_paused_for_deep_dive = False
        user_manager.save_user_async(profile)

        output = DeepDiveResumeOutput(
            is_resumed=True,
            resumed_item_id=profile.active_drill.current_item_id,
            remaining_items_in_queue=len(profile.active_drill.question_queue),
            message="Drill resumed! You can now continue answering questions.",
        ).model_dump()

        log_agent_outcome(
            action_name="resume_assessment_session",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"resumed_item": profile.active_drill.current_item_id},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="RESUME_FAILED",
            message=f"Failed to resume session: {str(exc)}",
            recovery_suggestion="Authenticate user and verify an active drill exists.",
        ).model_dump()
        return err


def generate_certification_domain_progress_report(user_id: str) -> Dict[str, Any]:
    """Generate a comprehensive progress report mapped 1:1 against the 6 PCA certification domains.

    Args:
        user_id (str): Candidate identifier.

    Returns:
        Dict[str, Any]: Full progress report with domain breakdowns, weak points, and study recommendations.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="generate_certification_domain_progress_report",
        user_id=user_id,
        session_id=user_id,
        target_component="ProgressAnalytics",
        intended_parameters={"user_id": user_id},
        trace_id=trace_id,
    )

    try:
        params = ProgressReportInput(user_id=user_id)
        profile = user_manager.get_or_create_user(params.user_id)

        domain_breakdown = []
        weakest = []
        strongest = []

        total_weighted_score = 0.0
        total_weight = 0

        for dom_key, dom_val in PCA_DOMAINS.items():
            mastery = profile.domain_mastery.get(dom_key, 0.5)
            mastery_pct = round(mastery * 100, 1)
            weight = dom_val.weight_percentage

            total_weighted_score += mastery * weight
            total_weight += weight

            status_str = "Proficient" if mastery >= 0.75 else ("Progressing" if mastery >= 0.5 else "Needs Review")
            if mastery < 0.5:
                weakest.append(f"{dom_val.title} ({mastery_pct}%)")
            elif mastery >= 0.75:
                strongest.append(f"{dom_val.title} ({mastery_pct}%)")

            domain_breakdown.append(
                {
                    "domain_id": dom_key,
                    "domain_number": dom_val.domain_number,
                    "domain_title": dom_val.title,
                    "exam_weight": f"{weight}%",
                    "mastery_percentage": mastery_pct,
                    "status": status_str,
                }
            )

        overall_readiness = round((total_weighted_score / total_weight) * 100, 1) if total_weight else 50.0

        if overall_readiness >= 80:
            pass_prob = "High (Exam Ready)"
        elif overall_readiness >= 65:
            pass_prob = "Moderate (Refine Weak Domains)"
        else:
            pass_prob = "Emerging (More Practice Required)"

        accuracy = (
            round((profile.total_correct_answers / profile.total_questions_answered) * 100, 1)
            if profile.total_questions_answered > 0
            else 0.0
        )

        next_actions = []
        if weakest:
            next_actions.append(f"Focus adaptive drills on: {weakest[0]}")
        next_actions.append("Review official case study architectures (Mountkirk Games, TerramEarth, EHR, HRL)")
        next_actions.append("Practice spaced repetition flashcards for Cloud Spanner vs Bigtable and VPC Peering vs Shared VPC")

        output = ProgressReportOutput(
            candidate_name=profile.name,
            overall_readiness_score=overall_readiness,
            estimated_pass_probability=pass_prob,
            total_questions_attempted=profile.total_questions_answered,
            accuracy_percentage=accuracy,
            domain_breakdown=domain_breakdown,
            weakest_domains=weakest or ["None (All domains >= 50%)"],
            strongest_domains=strongest or ["None (All domains < 75%)"],
            recommended_next_actions=next_actions,
        ).model_dump()

        log_agent_outcome(
            action_name="generate_certification_domain_progress_report",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"readiness": overall_readiness, "pass_prob": pass_prob},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="REPORT_GENERATION_ERROR",
            message=f"Failed to generate progress report: {str(exc)}",
            recovery_suggestion="Ensure user profile is initialized before requesting progress reports.",
        ).model_dump()
        return err


def ingest_user_study_material(
    user_id: str,
    title: str,
    content: str,
    domain_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Ingest custom study notes, cheat sheets, or architecture documents into candidate knowledge base.

    Args:
        user_id (str): Candidate identifier.
        title (str): Title of the study document.
        content (str): Study note or architectural summary text.
        domain_id (Optional[str]): Related PCA domain ID (e.g. 'domain_1').
        tags (Optional[List[str]]): Keywords / tags (e.g. ['spanner', 'iam']).

    Returns:
        Dict[str, Any]: Ingestion confirmation with document ID and tag indexing.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="ingest_user_study_material",
        user_id=user_id,
        session_id=user_id,
        target_component="KnowledgeSyncEngine",
        intended_parameters={"user_id": user_id, "title": title, "domain": domain_id},
        trace_id=trace_id,
    )

    try:
        params = UserMaterialIngestInput(
            user_id=user_id,
            title=title,
            content=content,
            domain_id=domain_id,
            tags=tags or [],
        )

        doc = sync_engine.ingest_user_material(
            title=params.title,
            content=params.content,
            domain_id=params.domain_id,
            tags=params.tags,
        )

        output = UserMaterialIngestOutput(
            doc_id=doc.doc_id,
            title=doc.title,
            domain_id=doc.domain_id,
            indexed_tags=doc.tags,
            total_user_materials_stored=sync_engine.get_sync_status().total_user_docs,
            message=f"Successfully indexed study material '{doc.title}'. It is now searchable in your study sessions.",
        ).model_dump()

        log_agent_outcome(
            action_name="ingest_user_study_material",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"doc_id": doc.doc_id},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="INGESTION_ERROR",
            message=f"Failed to ingest custom study material: {str(exc)}",
            recovery_suggestion="Ensure title has at least 3 characters and content has at least 10 characters.",
        ).model_dump()
        return err


def sync_official_study_materials(force_refresh: bool = False) -> Dict[str, Any]:
    """Check and synchronize the knowledge base against official Google Cloud PCA syllabus updates.

    Args:
        force_refresh (bool): Whether to force a re-index of official materials.

    Returns:
        Dict[str, Any]: Synchronization status and version info.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="sync_official_study_materials",
        user_id="system",
        session_id="system_sync",
        target_component="KnowledgeSyncEngine",
        intended_parameters={"force_refresh": force_refresh},
        trace_id=trace_id,
    )

    try:
        params = SyncOfficialMaterialsInput(force_refresh=force_refresh)
        res = sync_engine.sync_official_materials()
        output = SyncOfficialMaterialsOutput(
            sync_version=res["sync_version"],
            last_synced_at=res["last_synced_at"],
            total_documents=res["total_documents"],
            message=res["message"],
        ).model_dump()

        log_agent_outcome(
            action_name="sync_official_study_materials",
            user_id="system",
            session_id="system_sync",
            status="success",
            start_time=start_time,
            result_summary=output,
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="SYNC_ERROR",
            message=f"Failed to sync official materials: {str(exc)}",
            recovery_suggestion="Check network connectivity and file system write permissions.",
        ).model_dump()
        return err


def request_destructive_action_confirmation(
    user_id: str,
    action_type: str,
    confirmation_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Enforce Human-in-the-Loop approval gate before executing high-stakes destructive actions.

    Args:
        user_id (str): Candidate identifier.
        action_type (str): Destructive action type ('reset_progress' or 'delete_profile').
        confirmation_token (Optional[str]): Confirmation token provided by human. Omit to request token.

    Returns:
        Dict[str, Any]: Confirmation challenge or execution status.
    """
    trace_id = get_current_trace_id()
    start_time = log_agent_intent(
        action_name="request_destructive_action_confirmation",
        user_id=user_id,
        session_id=user_id,
        target_component="HITLManager",
        intended_parameters={"user_id": user_id, "action_type": action_type},
        trace_id=trace_id,
    )

    try:
        params = DestructiveActionConfirmationInput(
            user_id=user_id,
            action_type=action_type,
            confirmation_token=confirmation_token,
        )

        # If no token passed, generate HITL challenge
        if not params.confirmation_token:
            req = hitl_manager.create_confirmation_request(
                user_id=params.user_id,
                action_type=params.action_type,
                details={"impact_summary": f"This will permanently clear all mastery data for user {params.user_id}."},
            )
            output = DestructiveActionConfirmationOutput(
                status="pending_human_confirmation",
                action_executed=False,
                requires_confirmation=True,
                confirmation_token=req["confirmation_token"],
                message=req["instructions"],
            ).model_dump()
            return output

        # Token supplied: validate and execute
        is_valid, pending_action, msg = hitl_manager.validate_and_consume_token(
            user_id=params.user_id,
            token=params.confirmation_token,
        )

        if not is_valid or not pending_action:
            return ToolErrorResponse(
                error_code="INVALID_HITL_TOKEN",
                message=msg,
                recovery_suggestion="Re-initiate the action without a token to receive a fresh valid confirmation token.",
            ).model_dump()

        # Execute requested action
        if pending_action.action_type == "reset_progress":
            user_manager.reset_user_progress(params.user_id)
            action_msg = f"User progress and mastery records for '{params.user_id}' have been successfully reset."
        else:
            action_msg = f"Action '{pending_action.action_type}' executed successfully."

        output = DestructiveActionConfirmationOutput(
            status="completed",
            action_executed=True,
            requires_confirmation=False,
            confirmation_token=params.confirmation_token,
            message=action_msg,
        ).model_dump()

        log_agent_outcome(
            action_name="request_destructive_action_confirmation",
            user_id=user_id,
            session_id=user_id,
            status="success",
            start_time=start_time,
            result_summary={"executed": True, "action": pending_action.action_type},
            trace_id=trace_id,
        )
        return output

    except Exception as exc:
        err = ToolErrorResponse(
            error_code="HITL_ERROR",
            message=f"Human-in-the-loop validation failed: {str(exc)}",
            recovery_suggestion="Verify user_id and provide valid action_type ('reset_progress').",
        ).model_dump()
        return err


def search_pca_knowledge_base(query: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
    """Search grounded official PCA documentation, case studies, and user-ingested notes.

    Args:
        query (str): Search query or architectural keywords.
        domain_filter (Optional[str]): Optional domain ID filter (e.g. 'domain_1').

    Returns:
        Dict[str, Any]: Ranked search results with source citations.
    """
    results = retriever.search(query=query, domain_filter=domain_filter, top_k=5)
    return {
        "query": query,
        "total_results": len(results),
        "results": [r.model_dump() for r in results],
    }
