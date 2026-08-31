"""Interactive Rich Terminal CLI for Google Cloud PCA Study Agent.

Features:
- Clean, focused display with API logs hidden by default (enabled with --verbose / -v / --debug).
- Continuous adaptive drill workflow: automatically serves the next question with each answer submission.
- Seamless `/pause` and `/resume` commands for deep-dive discussions on every question.
"""

from __future__ import annotations

import argparse
import logging
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from pca_study_agent.agent import root_agent
from pca_study_agent.tools import (
    authenticate_or_register_candidate,
    evaluate_scenario_answer_and_update_mastery,
    fetch_adaptive_drill_item,
    generate_certification_domain_progress_report,
    pause_assessment_session_for_deep_dive,
    resume_assessment_session,
)

console = Console()


def configure_cli_logging(verbose: bool = False) -> None:
    """Configure log level, hiding API logs unless verbose mode is requested."""
    if not verbose:
        # Suppress standard log output and structlog stdout output
        logging.getLogger().setLevel(logging.CRITICAL)
        for log_name in ["pca_study_agent", "httpx", "uvicorn", "opentelemetry"]:
            logging.getLogger(log_name).setLevel(logging.CRITICAL)


def run_continuous_drill(user_id: str, candidate_name: str) -> None:
    """Run a continuous adaptive drill loop with inline pause and discuss options."""
    console.print(
        Panel(
            "[bold cyan]⚡ Continuous Adaptive Drill Mode[/bold cyan]\n"
            "[dim]Targeting your weakest domains with Leitner Spaced Repetition.[/dim]\n"
            "[dim]Commands at any prompt: [bold]/pause[/bold] (Discuss with Architect) | [bold]/report[/bold] | [bold]/menu[/bold][/dim]",
            border_style="cyan",
        )
    )

    while True:
        try:
            # 1. Fetch next adaptive drill item
            drill_res = fetch_adaptive_drill_item(user_id=user_id, preferred_item_type="question")
            if drill_res.get("status") == "error":
                console.print(f"[bold red]Error fetching question: {drill_res.get('message')}[/bold red]")
                break

            item_id = drill_res.get("item_id")
            domain_title = drill_res.get("domain_title")
            leitner_box = drill_res.get("leitner_box", 1)
            content = drill_res.get("content", {})
            q_text = content.get("question_text", "")
            options = content.get("options", [])
            case_study = content.get("case_study_id")

            # 2. Render question panel
            cs_str = f" [bold yellow](Case Study: {case_study.replace('_', ' ').title()})[/bold yellow]" if case_study else ""
            header_str = f"[bold green]{domain_title}[/bold green] | [bold yellow]Leitner Box {leitner_box}[/bold yellow]{cs_str}"

            options_text = ""
            valid_keys = []
            for opt in options:
                k = opt.get("key")
                valid_keys.append(k.upper())
                options_text += f"\n  [bold cyan][{k}][/bold cyan] {opt.get('text')}"

            console.print(
                Panel(
                    f"[bold white]{q_text}[/bold white]\n{options_text}\n\n"
                    f"[dim]Type [bold]A, B, C, D[/bold] to submit | [bold]/pause[/bold] to discuss with Principal Architect | [bold]/menu[/bold] to exit[/dim]",
                    title=header_str,
                    border_style="blue",
                )
            )

            # 3. Prompt user for answer or command
            while True:
                user_choice = Prompt.ask(f"[bold green]{candidate_name}[/bold green]").strip()
                if not user_choice:
                    continue

                lower_choice = user_choice.lower()

                if lower_choice in ("/menu", "menu", "/exit", "exit", "/quit", "quit"):
                    console.print("\n[bold yellow]Returning to Main Menu...[/bold yellow]\n")
                    return

                elif lower_choice in ("/report", "report", "progress"):
                    rep = generate_certification_domain_progress_report(user_id=user_id)
                    console.print(
                        f"\n[bold cyan]Readiness Score:[/bold cyan] {rep.get('overall_readiness_score')}% | "
                        f"[bold green]Pass Probability:[/bold green] {rep.get('estimated_pass_probability')}\n"
                    )
                    continue

                elif lower_choice.startswith(("/flag", "flag", "report")):
                    from pca_study_agent.tools import flag_or_challenge_question
                    reason_notes = user_choice.replace("/flag", "").replace("flag", "").replace("report", "").strip() or "Candidate reported question as unclear/incorrect"
                    flag_res = flag_or_challenge_question(
                        user_id=user_id,
                        question_id=item_id,
                        reason="unclear_wording",
                        feedback_notes=reason_notes,
                    )
                    console.print(f"\n[bold yellow]🚩 Question '{item_id}' has been flagged and suspended from rotation. Moving to next question...[/bold yellow]\n")
                    break

                elif lower_choice.startswith(("/pause", "pause", "explain", "why")):
                    # Enter Socratic deep-dive mode
                    run_socratic_deep_dive(user_id=user_id, candidate_name=candidate_name, context_item=item_id)
                    # Once resumed, redisplay current question prompt
                    break

                elif user_choice.upper() in valid_keys:
                    # Submit and grade answer
                    eval_res = evaluate_scenario_answer_and_update_mastery(
                        user_id=user_id,
                        item_id=item_id,
                        submitted_answer=user_choice.upper(),
                    )
                    is_correct = eval_res.get("is_correct")
                    status_badge = "[bold green]✅ Correct Choice![/bold green]" if is_correct else "[bold red]❌ Suboptimal Choice[/bold red]"

                    feedback_text = (
                        f"{status_badge}\n\n"
                        f"[bold]Architectural Principle:[/bold] {eval_res.get('architectural_principle')}\n\n"
                        f"[bold]Explanation:[/bold] {eval_res.get('explanation')}\n"
                    )
                    if eval_res.get("distractor_analysis"):
                        feedback_text += "\n[bold]Distractor Analysis:[/bold]\n"
                        for k, r in eval_res["distractor_analysis"].items():
                            feedback_text += f"- Option {k}: {r}\n"

                    feedback_text += (
                        f"\n[dim]New Mastery: {int(eval_res.get('updated_domain_mastery', 0.5)*100)}% | "
                        f"{eval_res.get('next_review_recommendation')}[/dim]"
                    )

                    console.print(Panel(feedback_text, border_style="green" if is_correct else "red"))
                    console.print("[dim]Press Enter to advance to next question, or type /pause to deep-dive...[/dim]")
                    post_action = Prompt.ask("", default="").strip().lower()
                    if post_action.startswith(("/pause", "pause", "explain")):
                        run_socratic_deep_dive(user_id=user_id, candidate_name=candidate_name, context_item=item_id)
                    break
                else:
                    console.print("[yellow]Please enter A, B, C, D, or /pause /menu[/yellow]")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Drill paused.[/bold yellow]")
            return


def run_socratic_deep_dive(user_id: str, candidate_name: str, context_item: str) -> None:
    """Interactive Socratic deep-dive chat with Principal Architect."""
    from pca_study_agent.agent import get_genai_client
    pause_assessment_session_for_deep_dive(user_id=user_id)

    client = get_genai_client()
    if not client:
        console.print(
            Panel(
                "[bold yellow]⚠️ Live Gemini LLM Not Configured (Running in Offline Knowledge Mode)[/bold yellow]\n"
                "[dim]To enable full dynamic conversational reasoning with Gemini 2.5 Pro on arbitrary questions,\n"
                "add your GEMINI_API_KEY to .env (e.g. echo 'GEMINI_API_KEY=your_key' >> .env)[/dim]",
                border_style="yellow",
            )
        )

    console.print(
        Panel(
            "[bold green]🎓 Socratic Architect Tutor (Deep-Dive Mode)[/bold green]\n"
            "[italic white]Ask any question about trade-offs, service comparisons, or underlying Google Cloud architecture.[/italic white]\n"
            "[dim]Type [bold]/resume[/bold] when ready to continue drilling.[/dim]",
            border_style="green",
        )
    )

    while True:
        try:
            inquiry = Prompt.ask(f"[bold cyan]{candidate_name} (Ask Tutor)[/bold cyan]").strip()
            if not inquiry:
                continue

            if inquiry.lower() in ("/resume", "resume", "continue", "back"):
                resume_assessment_session(user_id=user_id)
                console.print("\n[bold green]Resuming adaptive drill...[/bold green]\n")
                return

            response = root_agent.process_message(user_id=user_id, user_input=inquiry)
            console.print("\n" + "─" * 80)
            console.print(Markdown(response.response_text))
            console.print("─" * 80 + "\n")

        except (KeyboardInterrupt, EOFError):
            resume_assessment_session(user_id=user_id)
            return


def run_interactive_cli() -> None:
    """Launch the interactive CLI study session."""
    parser = argparse.ArgumentParser(description="Google Cloud PCA Study Agent CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose API and debug logging")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-u", "--user", default="alex_architect", help="Candidate user ID")
    parser.add_argument("-n", "--name", default="Alex", help="Candidate name")
    args = parser.parse_args()

    configure_cli_logging(verbose=args.verbose or args.debug)

    console.print(
        Panel.fit(
            "[bold cyan]Google Cloud Professional Cloud Architect (PCA) Study Agent[/bold cyan]\n"
            "[italic white]Powered by Google ADK & Gemini Multi-Agent Architecture[/italic white]",
            border_style="blue",
        )
    )

    # Startup Model Discovery & Validation
    from pca_study_agent.config import settings
    from pca_study_agent.models_manager import validate_and_resolve_models

    res_flash, res_pro, available_models, warning_msg = validate_and_resolve_models(
        flash_model=settings.gemini_flash_model,
        pro_model=settings.gemini_pro_model,
        interactive=True,
    )
    settings.gemini_flash_model = res_flash
    settings.gemini_pro_model = res_pro

    if available_models:
        console.print(
            f"[dim]🤖 LLM Active | Flash Model: [bold green]{res_flash}[/bold green] | Pro Model: [bold green]{res_pro}[/bold green][/dim]"
        )

    auth_res = authenticate_or_register_candidate(user_id=user_id, candidate_name=candidate_name)
    console.print(f"\n[bold green]{auth_res.get('message')}[/bold green]\n")

    # Main Command Menu Loop
    while True:
        try:
            console.print(
                "[dim]Options: [bold]/drill[/bold] (Continuous Drill) | [bold]/start[/bold] (Diagnostic) | [bold]/pause[/bold] (Discuss) | [bold]/report[/bold] | [bold]/quit[/bold][/dim]"
            )
            user_input = Prompt.ask(f"[bold cyan]{candidate_name}[/bold cyan]").strip()
            if not user_input:
                continue

            lower_input = user_input.lower()

            if lower_input in ("/quit", "exit", "quit", "q"):
                console.print("\n[bold green]Good luck with your Google Cloud PCA Exam! Session saved.[/bold green]\n")
                break

            elif lower_input in ("/drill", "drill", "practice"):
                run_continuous_drill(user_id=user_id, candidate_name=candidate_name)

            elif lower_input.startswith(("/pause", "pause", "explain", "tutor")):
                run_socratic_deep_dive(user_id=user_id, candidate_name=candidate_name, context_item="general")

            elif lower_input.startswith(("/report", "progress", "score")):
                rep = generate_certification_domain_progress_report(user_id=user_id)
                console.print(
                    f"\n[bold cyan]Readiness Score:[/bold cyan] {rep.get('overall_readiness_score')}% | "
                    f"[bold green]Pass Probability:[/bold green] {rep.get('estimated_pass_probability')}\n"
                )

            else:
                response = root_agent.process_message(user_id=user_id, user_input=user_input)
                console.print("\n" + "─" * 80)
                console.print(Markdown(response.response_text))
                console.print("─" * 80 + "\n")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold green]Session ended. Goodbye![/bold green]")
            break


if __name__ == "__main__":
    run_interactive_cli()
