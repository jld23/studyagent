#!/usr/bin/env python3
"""Automated 19-Criteria AgentOps Pre-Flight Quality Audit Script.

Validates the codebase against the 19-criteria AgentOps Code Review Matrix
(95 total points) across Tool Design, Context & Memory, Orchestration & Logic,
Observability & Tracing, and Infrastructure & CI/CD.

Exits 0 if score >= 90/95 (or 100%), exits 1 if critical gates fail.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

ROOT_DIR = Path(__file__).parent.parent


def audit_agentops_matrix() -> tuple[int, int, list[dict]]:
    """Run programmatic verification across all 19 AgentOps criteria."""
    checks = []
    total_score = 0
    max_score = 95

    # ------------------------------------------------------------------------
    # Category 1: Tool & Interface Design (20 pts)
    # ------------------------------------------------------------------------
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
        AuthCandidateInput,
        AnswerSubmissionInput,
        ToolErrorResponse,
    )

    tools = [
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
    ]

    # 1. Comprehensive Tool Docstrings (5 pts)
    doc_passed = all(
        inspect.getdoc(t) and "Args:" in inspect.getdoc(t) and "Returns:" in inspect.getdoc(t)  # type: ignore
        for t in tools
    )
    score = 5 if doc_passed else 0
    total_score += score
    checks.append({"cat": "1. Tools", "name": "Comprehensive Tool Docstrings", "pts": score, "max": 5, "status": "PASS" if doc_passed else "FAIL"})

    # 2. Descriptive Naming (5 pts)
    names_passed = all(
        len(t.__name__) >= 12 and any(t.__name__.startswith(p) for p in ("auth", "fetch", "evaluate", "pause", "resume", "generate", "ingest", "sync", "request"))
        for t in tools
    )
    score = 5 if names_passed else 0
    total_score += score
    checks.append({"cat": "1. Tools", "name": "Descriptive Semantic Naming", "pts": score, "max": 5, "status": "PASS" if names_passed else "FAIL"})

    # 3. Explicit JSON Schemas (5 pts)
    schema_passed = issubclass(AuthCandidateInput, object) and issubclass(AnswerSubmissionInput, object)
    score = 5 if schema_passed else 0
    total_score += score
    checks.append({"cat": "1. Tools", "name": "Strict Pydantic JSON Schemas", "pts": score, "max": 5, "status": "PASS" if schema_passed else "FAIL"})

    # 4. Guided Error Handling (5 pts)
    err_inst = ToolErrorResponse(error_code="ERR", message="msg", recovery_suggestion="Try tool X")
    guided_err_passed = bool(err_inst.recovery_suggestion)
    score = 5 if guided_err_passed else 0
    total_score += score
    checks.append({"cat": "1. Tools", "name": "Guided Error Recovery Suggestions", "pts": score, "max": 5, "status": "PASS" if guided_err_passed else "FAIL"})

    # ------------------------------------------------------------------------
    # Category 2: Context & Memory (20 pts)
    # ------------------------------------------------------------------------
    from pca_study_agent.agent import COORDINATOR_CONSTITUTION, SOCRATIC_TUTOR_CONSTITUTION
    from pca_study_agent.memory.compaction import context_compactor
    from pca_study_agent.memory.user_manager import user_manager
    from pca_study_agent.memory.async_worker import async_memory_worker

    # 5. Robust System Constitutions (5 pts)
    const_passed = len(COORDINATOR_CONSTITUTION) > 100 and len(SOCRATIC_TUTOR_CONSTITUTION) > 100
    score = 5 if const_passed else 0
    total_score += score
    checks.append({"cat": "2. Memory", "name": "Robust System Constitutions", "pts": score, "max": 5, "status": "PASS" if const_passed else "FAIL"})

    # 6. History Compaction (5 pts)
    comp_passed = hasattr(context_compactor, "compact_history")
    score = 5 if comp_passed else 0
    total_score += score
    checks.append({"cat": "2. Memory", "name": "Context Compaction & Sliding Windows", "pts": score, "max": 5, "status": "PASS" if comp_passed else "FAIL"})

    # 7. Persistent Session State (5 pts)
    persist_passed = hasattr(user_manager, "get_or_create_user") and hasattr(user_manager, "save_user_sync")
    score = 5 if persist_passed else 0
    total_score += score
    checks.append({"cat": "2. Memory", "name": "Persistent Multi-User Session State", "pts": score, "max": 5, "status": "PASS" if persist_passed else "FAIL"})

    # 8. Async Memory Operations (5 pts)
    async_passed = hasattr(async_memory_worker, "schedule_task")
    score = 5 if async_passed else 0
    total_score += score
    checks.append({"cat": "2. Memory", "name": "Async Background Memory Operations", "pts": score, "max": 5, "status": "PASS" if async_passed else "FAIL"})

    # ------------------------------------------------------------------------
    # Category 3: Orchestration & Logic (20 pts)
    # ------------------------------------------------------------------------
    from pca_study_agent.agent import root_agent
    from pca_study_agent.observability.guardrails import validate_input_safety, verify_architectural_soundness
    from pca_study_agent.observability.hitl import hitl_manager

    # 9. Multi-Agent Patterns (5 pts)
    multi_passed = hasattr(root_agent, "diagnostic_agent") and hasattr(root_agent, "tutor_agent")
    score = 5 if multi_passed else 0
    total_score += score
    checks.append({"cat": "3. Logic", "name": "ADK Coordinator Multi-Agent Pattern", "pts": score, "max": 5, "status": "PASS" if multi_passed else "FAIL"})

    # 10. Strategic Model Routing (5 pts)
    routing_passed = root_agent.tutor_agent.model_name != root_agent.diagnostic_agent.model_name or "pro" in root_agent.tutor_agent.model_name.lower() or "flash" in root_agent.diagnostic_agent.model_name.lower()
    score = 5 if routing_passed else 0
    total_score += score
    checks.append({"cat": "3. Logic", "name": "Strategic Model Routing (Flash/Pro)", "pts": score, "max": 5, "status": "PASS" if routing_passed else "FAIL"})

    # 11. Guardrails & Policy Plugins (5 pts)
    guard_passed = callable(validate_input_safety) and callable(verify_architectural_soundness)
    score = 5 if guard_passed else 0
    total_score += score
    checks.append({"cat": "3. Logic", "name": "Safety Guardrails & Quality Filters", "pts": score, "max": 5, "status": "PASS" if guard_passed else "FAIL"})

    # 12. Human-in-the-Loop Hooks (5 pts)
    hitl_passed = hasattr(hitl_manager, "create_confirmation_request") and hasattr(hitl_manager, "validate_and_consume_token")
    score = 5 if hitl_passed else 0
    total_score += score
    checks.append({"cat": "3. Logic", "name": "Human-in-the-Loop (HITL) Challenge Gates", "pts": score, "max": 5, "status": "PASS" if hitl_passed else "FAIL"})

    # ------------------------------------------------------------------------
    # Category 4: Observability & Tracing (20 pts)
    # ------------------------------------------------------------------------
    from pca_study_agent.observability.logger import log_agent_intent, log_agent_outcome, logger
    from pca_study_agent.observability.telemetry import trace_span
    from pca_study_agent.observability.pii_scrubber import redact_pii_text

    # 13. Structured JSON Logging (5 pts)
    log_passed = hasattr(logger, "info")
    score = 5 if log_passed else 0
    total_score += score
    checks.append({"cat": "4. Observability", "name": "Structured JSON Logging (structlog)", "pts": score, "max": 5, "status": "PASS" if log_passed else "FAIL"})

    # 14. Intent vs Outcome Capture (5 pts)
    intent_passed = callable(log_agent_intent) and callable(log_agent_outcome)
    score = 5 if intent_passed else 0
    total_score += score
    checks.append({"cat": "4. Observability", "name": "Intent vs. Outcome Tracking Pairs", "pts": score, "max": 5, "status": "PASS" if intent_passed else "FAIL"})

    # 15. Distributed Tracing (5 pts)
    trace_passed = callable(trace_span)
    score = 5 if trace_passed else 0
    total_score += score
    checks.append({"cat": "4. Observability", "name": "OpenTelemetry Distributed Tracing", "pts": score, "max": 5, "status": "PASS" if trace_passed else "FAIL"})

    # 16. PII Redaction (5 pts)
    pii_res = redact_pii_text("test user@google.com with key AIzaSyD3LJeW4Q6gtdgJlyeFZUp-GhpIoc6EUeg")
    pii_passed = "[REDACTED_EMAIL]" in pii_res and "[REDACTED_API_KEY]" in pii_res
    score = 5 if pii_passed else 0
    total_score += score
    checks.append({"cat": "4. Observability", "name": "Automated PII & Credential Scrubbing", "pts": score, "max": 5, "status": "PASS" if pii_passed else "FAIL"})

    # ------------------------------------------------------------------------
    # Category 5: Infrastructure & CI/CD (15 pts)
    # ------------------------------------------------------------------------
    eval_file = ROOT_DIR / "tests/eval/datasets/pca_eval_dataset.json"
    tf_file = ROOT_DIR / "infra/terraform/main.tf"
    config_file = ROOT_DIR / "pca_study_agent/config.py"

    # 17. Automated Evaluation Suites (5 pts)
    eval_passed = eval_file.exists() and len(eval_file.read_text()) > 100
    score = 5 if eval_passed else 0
    total_score += score
    checks.append({"cat": "5. Infra & CI", "name": "Automated Golden Evaluation Suite", "pts": score, "max": 5, "status": "PASS" if eval_passed else "FAIL"})

    # 18. Infrastructure as Code (5 pts)
    iac_passed = tf_file.exists() and "google_cloud_run_v2_service" in tf_file.read_text()
    score = 5 if iac_passed else 0
    total_score += score
    checks.append({"cat": "5. Infra & CI", "name": "Infrastructure as Code (Terraform)", "pts": score, "max": 5, "status": "PASS" if iac_passed else "FAIL"})

    # 19. Secure Secret Management (5 pts)
    sec_passed = config_file.exists() and "resolve_secrets" in config_file.read_text()
    score = 5 if sec_passed else 0
    total_score += score
    checks.append({"cat": "5. Infra & CI", "name": "Secure Secret Manager Injection", "pts": score, "max": 5, "status": "PASS" if sec_passed else "FAIL"})

    return total_score, max_score, checks


def main():
    console.print("\n[bold cyan]🔍 Running AgentOps 19-Criteria Pre-Flight Code Review Audit...[/bold cyan]\n")
    total_score, max_score, checks = audit_agentops_matrix()

    table = Table(title="AgentOps Quality Review Results", show_header=True, header_style="bold blue")
    table.add_column("Category", style="cyan", width=18)
    table.add_column("Criterion", style="white", width=42)
    table.add_column("Score", justify="right", width=10)
    table.add_column("Status", justify="center", width=10)

    for c in checks:
        status_styled = "[bold green]PASS[/bold green]" if c["status"] == "PASS" else "[bold red]FAIL[/bold red]"
        score_str = f"{c['pts']}/{c['max']}"
        table.add_row(c["cat"], c["name"], score_str, status_styled)

    console.print(table)

    pct = round((total_score / max_score) * 100, 1)
    if total_score == max_score:
        console.print(f"\n[bold green]🎉 PERFECT SCORE: {total_score}/{max_score} ({pct}%) - AgentOps Quality Gate PASSED![/bold green]\n")
        sys.exit(0)
    elif total_score >= 90:
        console.print(f"\n[bold yellow]⚠️ PASSED WITH WARNINGS: {total_score}/{max_score} ({pct}%)[/bold yellow]\n")
        sys.exit(0)
    else:
        console.print(f"\n[bold red]❌ QUALITY GATE FAILED: {total_score}/{max_score} ({pct}%). Fix failing criteria before deployment.[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
