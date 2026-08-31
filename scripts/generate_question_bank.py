#!/usr/bin/env python3
"""Batch Question Bank Generator for Google Cloud PCA Study Agent.

Generates realistic scenario-based questions across all 6 PCA certification domains
and 4 case studies, validating each question via strict Pydantic models and saving
them into the persistent question bank repository.
"""

from __future__ import annotations

import argparse
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from pca_study_agent.knowledge.exam_domains import PCA_DOMAINS
from pca_study_agent.knowledge.generator import generate_pca_question
from pca_study_agent.knowledge.questions_repository import questions_repo

console = Console()

CASE_STUDY_POOL = ["mountkirk_games", "terramearth", "ehr_healthcare", "helicopter_racing_league", None]


def generate_batch(count: int = 10, target_domain: str | None = None) -> None:
    """Generate a batch of PCA exam questions and save them into the repository."""
    console.print(f"\n[bold cyan]🚀 Initializing Question Bank Batch Generation ({count} questions)...[/bold cyan]\n")

    domains = [target_domain] if target_domain else list(PCA_DOMAINS.keys())
    generated_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Generating scenario questions...", total=count)

        for i in range(count):
            dom_id = domains[i % len(domains)]
            cs_id = CASE_STUDY_POOL[i % len(CASE_STUDY_POOL)]
            progress.update(task, description=f"[cyan]Generating {dom_id} (Case Study: {cs_id or 'General'})...")

            try:
                question = generate_pca_question(
                    domain_id=dom_id,
                    case_study_id=cs_id,
                    difficulty="expert" if i % 2 == 0 else "intermediate",
                )
                questions_repo.save_question(question)
                generated_count += 1
            except Exception as exc:
                console.print(f"[bold red]Failed generating question #{i+1}:[/bold red] {exc}")

            progress.advance(task)

    console.print(f"\n[bold green]🎉 Successfully generated and saved {generated_count} questions![/bold green]\n")

    # Display breakdown table
    table = Table(title="Updated Question Bank Summary", border_style="cyan")
    table.add_column("Domain #", style="dim")
    table.add_column("Domain Title", style="bold")
    table.add_column("Total Active Questions", justify="right", style="green")

    for dom_id, dom_info in PCA_DOMAINS.items():
        active = questions_repo.get_active_questions(domain_id=dom_id)
        table.add_row(dom_id, dom_info.title, str(len(active)))

    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch generate PCA scenario questions")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of questions to generate")
    parser.add_argument("-d", "--domain", type=str, default=None, help="Target specific domain (e.g. domain_1)")
    args = parser.parse_args()

    generate_batch(count=args.count, target_domain=args.domain)
