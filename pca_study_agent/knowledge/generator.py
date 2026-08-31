"""Dynamic Scenario Question Generator using Gemini LLM.

Generates realistic, rigorous Google Cloud Professional Cloud Architect (PCA)
exam questions adhering to the Google Cloud Well-Architected Framework and
official PCA Case Studies, strictly formatted into Pydantic ExamQuestion schemas.
"""

from __future__ import annotations

import json
import random
import uuid
from typing import Any, Dict, Optional

from google.genai import types as genai_types
from pydantic import ValidationError

from pca_study_agent.config import settings
from pca_study_agent.knowledge.case_studies import PCA_CASE_STUDIES
from pca_study_agent.knowledge.exam_domains import PCA_DOMAINS
from pca_study_agent.knowledge.question_bank import ExamQuestion, QuestionOption
from pca_study_agent.observability.logger import logger

QUESTION_GENERATION_SYSTEM_INSTRUCTION = """
You are an expert Google Cloud Authorized Trainer and Lead Curriculum Developer for the Google Cloud Professional Cloud Architect (PCA) exam.
Your task is to generate realistic, scenario-based multiple-choice practice questions.

STRICT GUIDELINES:
1. Scenario-Based Structure: Pose a complex business or technical challenge. Force trade-offs (e.g. cost-effectiveness vs extreme latency, zero-RPO disaster recovery vs simplicity, multi-region Spanner vs Bigtable).
2. Well-Architected Framework: Incorporate operational excellence, security, reliability, performance efficiency, and cost optimization.
3. Plausible Distractors: Incorrect options must be highly realistic Google Cloud services that are sub-optimal for the specific prompt constraints or represent common architectural anti-patterns.
4. Output Schema: You MUST respond ONLY with a raw JSON object strictly adhering to the specified schema, without any conversational preamble or markdown backticks.
"""

GENERATION_JSON_SCHEMA: Dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "domain_id": {"type": "STRING"},
        "sub_objective_code": {"type": "STRING"},
        "difficulty": {"type": "STRING"},
        "case_study_id": {"type": "STRING"},
        "question_text": {"type": "STRING"},
        "options": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "key": {"type": "STRING"},
                    "text": {"type": "STRING"},
                },
                "required": ["key", "text"],
            },
        },
        "correct_option": {"type": "STRING"},
        "architectural_principle": {"type": "STRING"},
        "explanation": {"type": "STRING"},
        "distractor_analysis": {
            "type": "OBJECT",
            "properties": {
                "A": {"type": "STRING"},
                "B": {"type": "STRING"},
                "C": {"type": "STRING"},
                "D": {"type": "STRING"},
            },
        },
    },
    "required": [
        "domain_id",
        "sub_objective_code",
        "difficulty",
        "question_text",
        "options",
        "correct_option",
        "architectural_principle",
        "explanation",
        "distractor_analysis",
    ],
}


def generate_pca_question(
    domain_id: str = "domain_1",
    case_study_id: Optional[str] = None,
    difficulty: str = "expert",
) -> ExamQuestion:
    """Generate a high-quality PCA scenario question on-demand using Gemini LLM.

    Args:
        domain_id: Certification domain ID ('domain_1' to 'domain_6').
        case_study_id: Optional case study ID ('mountkirk_games', 'terramearth', 'ehr_healthcare', 'helicopter_racing_league').
        difficulty: Difficulty level ('beginner', 'intermediate', 'expert').

    Returns:
        ExamQuestion: Validated Pydantic exam question object.
    """
    from pca_study_agent.agent import get_genai_client
    client = get_genai_client()

    dom = PCA_DOMAINS.get(domain_id)
    dom_title = dom.title if dom else domain_id
    cs = PCA_CASE_STUDIES.get(case_study_id) if case_study_id else None
    cs_context = f"Ground the question in the case study: '{cs.name}' ({cs.company_overview})." if cs else "Generate an enterprise enterprise scenario."

    prompt = (
        f"Generate 1 rigorous scenario-based question for Google Cloud PCA Exam.\n"
        f"Target Domain: {domain_id} ({dom_title})\n"
        f"Difficulty: {difficulty}\n"
        f"{cs_context}\n\n"
        f"Requirements:\n"
        f"- Exactly 4 options (A, B, C, D) with 1 clear correct option.\n"
        f"- Detailed explanation and individual distractor analysis for all 3 incorrect options.\n"
        f"- Format as raw JSON conforming to the schema."
    )

    if client:
        # Try configured model with fallback models
        models_to_try = [settings.gemini_pro_model, settings.gemini_flash_model, "gemini-2.5-pro", "gemini-2.5-flash"]
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=QUESTION_GENERATION_SYSTEM_INSTRUCTION,
                        temperature=0.4,
                        response_mime_type="application/json",
                        response_schema=GENERATION_JSON_SCHEMA,
                        automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )
                if response and response.text:
                    clean_text = response.text.strip()
                    if clean_text.startswith("```"):
                        clean_text = clean_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

                    raw_json = json.loads(clean_text)
                    raw_json["id"] = f"q_pca_dyn_{uuid.uuid4().hex[:8]}"
                    raw_json["domain_id"] = domain_id
                    raw_json["difficulty"] = difficulty
                    if case_study_id:
                        raw_json["case_study_id"] = case_study_id

                    # Parse into Pydantic ExamQuestion
                    validated_q = ExamQuestion(**raw_json)
                    logger.info("Successfully generated dynamic PCA question", question_id=validated_q.id, domain_id=domain_id)
                    return validated_q
            except Exception as exc:
                logger.warning("Dynamic question generation attempt failed", model=model_name, error=str(exc))

    # Offline / Fallback Question Generator
    return _generate_fallback_question(domain_id, case_study_id, difficulty)


def _generate_fallback_question(
    domain_id: str,
    case_study_id: Optional[str],
    difficulty: str,
) -> ExamQuestion:
    """Generate a deterministically constructed scenario question when LLM is offline."""
    qid = f"q_pca_dyn_{uuid.uuid4().hex[:8]}"
    dom = PCA_DOMAINS.get(domain_id)
    dom_title = dom.title if dom else domain_id

    return ExamQuestion(
        id=qid,
        domain_id=domain_id,
        sub_objective_code=f"{domain_id.replace('domain_', '')}.1",
        difficulty=difficulty,
        case_study_id=case_study_id,
        question_text=(
            f"An enterprise client is implementing an architectural solution for {dom_title}. "
            "They require high availability across multiple regions, automated failover, and minimal operational overhead. "
            "Which architectural design should you recommend according to Google Cloud best practices?"
        ),
        options=[
            QuestionOption(key="A", text="Deploy managed regional services behind a Global External Application Load Balancer with Cloud Armor WAF enabled."),
            QuestionOption(key="B", text="Deploy unmanaged Compute Engine VMs across two zones with manual DNS routing."),
            QuestionOption(key="C", text="Provision a single large VM instance with local SSD scratch disks."),
            QuestionOption(key="D", text="Use Cloud Storage Standard buckets with public read ACLs without load balancers."),
        ],
        correct_option="A",
        architectural_principle=f"High Availability & Managed Resilience in {dom_title}",
        explanation=(
            "Using managed regional services behind a Global External Application Load Balancer ensures traffic is automatically "
            "routed to the closest healthy backend region, providing seamless multi-region redundancy and DDoS protection."
        ),
        distractor_analysis={
            "B": "Manual DNS failover introduces high RTO (minutes to hours) and lacks health-checked automated rerouting.",
            "C": "A single VM represents a single point of failure with no multi-zone redundancy.",
            "D": "Direct public Cloud Storage buckets lack global anycast load balancing, WAF security, and dynamic backend logic.",
        },
    )
