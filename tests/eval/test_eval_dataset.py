"""Automated Evaluation Runner for PCA Golden Dataset.

Statically measures agent architectural accuracy, distractor distinction, and
domain coverage against the golden evaluation dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from pca_study_agent.knowledge.question_bank import PCA_QUESTIONS
from pca_study_agent.knowledge.retriever import retriever
from pca_study_agent.observability.guardrails import verify_architectural_soundness


@pytest.fixture
def eval_dataset() -> list[dict]:
    dataset_file = Path(__file__).parent / "datasets" / "pca_eval_dataset.json"
    return json.loads(dataset_file.read_text(encoding="utf-8"))


def test_golden_eval_dataset_coverage(eval_dataset: list[dict]):
    """Verify golden dataset contains scenarios covering all 6 PCA domains."""
    domain_ids = {item["domain_id"] for item in eval_dataset}
    expected_domains = {"domain_1", "domain_2", "domain_3", "domain_4", "domain_5", "domain_6"}
    assert domain_ids == expected_domains, f"Golden dataset missing domains: {expected_domains - domain_ids}"


def test_eval_dataset_retriever_precision(eval_dataset: list[dict]):
    """Verify retriever correctly locates expected services for all golden scenarios."""
    for case in eval_dataset:
        scenario = case["scenario"]
        expected_svc = case["expected_service"].lower()

        results = retriever.search(query=scenario, top_k=3)
        combined_text = " ".join([r.title.lower() + " " + r.content_snippet.lower() for r in results])

        # Expect at least partial match of the key service keywords
        key_tokens = [w for w in expected_svc.split() if len(w) > 3]
        match_found = any(token in combined_text for token in key_tokens)
        assert match_found, f"Eval case '{case['eval_id']}' failed to retrieve service '{expected_svc}'"


def test_eval_guardrail_soundness(eval_dataset: list[dict]):
    """Verify architectural soundness verification passes for all scenario criteria."""
    for case in eval_dataset:
        explanation = f"Recommended architecture: {case['expected_service']}. {case['criteria']}"
        res = verify_architectural_soundness(explanation)
        assert res["is_grounded"] is True
        assert res["quality_score"] >= 0.5
