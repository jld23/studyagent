"""Hybrid Semantic & Keyword Knowledge Retriever.

Grounded search engine querying across official PCA domains, official case
studies (Mountkirk Games, TerramEarth, EHR Healthcare, HRL), curated questions/flashcards,
and user-ingested study documents.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pca_study_agent.knowledge.case_studies import PCA_CASE_STUDIES
from pca_study_agent.knowledge.exam_domains import PCA_DOMAINS
from pca_study_agent.knowledge.question_bank import PCA_FLASHCARDS, PCA_QUESTIONS
from pca_study_agent.knowledge.sync_engine import sync_engine


class SearchResult(BaseModel):
    """Knowledge retrieval result."""

    title: str
    source_type: str = Field(description="'exam_domain', 'case_study', 'question_bank', 'flashcard', 'user_note'")
    domain_id: Optional[str] = None
    content_snippet: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeRetriever:
    """Retrieval engine for PCA architectural knowledge."""

    def search(
        self,
        query: str,
        domain_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search across all knowledge repositories.

        Args:
            query (str): The search query or technical concept.
            domain_filter (Optional[str]): Limit search to specific domain (e.g. 'domain_1').
            top_k (int): Maximum number of results to return.

        Returns:
            List[SearchResult]: Ranked search results.
        """
        keywords = set(re.findall(r"\w+", query.lower()))
        results: List[SearchResult] = []

        # 1. Search Case Studies
        for cs_id, cs in PCA_CASE_STUDIES.items():
            text_corpus = f"{cs.name} {cs.company_overview} {' '.join(cs.business_requirements)} {' '.join(cs.technical_requirements)} {json_dumps_safe(cs.recommended_gcp_architecture)}"
            score = self._score_text(keywords, text_corpus)
            if score > 0:
                results.append(
                    SearchResult(
                        title=f"Case Study: {cs.name}",
                        source_type="case_study",
                        domain_id=None,
                        content_snippet=f"{cs.company_overview} Target Architecture: {cs.recommended_gcp_architecture}",
                        relevance_score=score + 0.1,  # Boost case study relevance
                        metadata={"case_study_id": cs_id},
                    )
                )

        # 2. Search Exam Domains & Sub-Objectives
        for dom_id, dom in PCA_DOMAINS.items():
            if domain_filter and dom_id != domain_filter:
                continue
            for sub in dom.sub_objectives:
                text_corpus = f"{dom.title} {sub.title} {sub.description} {' '.join(sub.key_services)}"
                score = self._score_text(keywords, text_corpus)
                if score > 0:
                    results.append(
                        SearchResult(
                            title=f"Domain {dom.domain_number}: {sub.title}",
                            source_type="exam_domain",
                            domain_id=dom_id,
                            content_snippet=f"{sub.description} Key Services: {', '.join(sub.key_services)}",
                            relevance_score=score,
                            metadata={"sub_code": sub.code, "services": sub.key_services},
                        )
                    )

        # 3. Search Flashcards
        for fc in PCA_FLASHCARDS:
            if domain_filter and fc.domain_id != domain_filter:
                continue
            text_corpus = f"{fc.topic} {fc.front_prompt} {fc.back_solution} {fc.key_tradeoff}"
            score = self._score_text(keywords, text_corpus)
            if score > 0:
                results.append(
                    SearchResult(
                        title=f"Flashcard: {fc.topic}",
                        source_type="flashcard",
                        domain_id=fc.domain_id,
                        content_snippet=f"{fc.front_prompt} -> Solution: {fc.back_solution}",
                        relevance_score=score,
                        metadata={"flashcard_id": fc.id, "tradeoff": fc.key_tradeoff},
                    )
                )

        # 4. Search Ingested User Documents
        for udoc in sync_engine.get_all_documents():
            if domain_filter and udoc.domain_id and udoc.domain_id != domain_filter:
                continue
            text_corpus = f"{udoc.title} {udoc.content} {' '.join(udoc.tags)}"
            score = self._score_text(keywords, text_corpus)
            if score > 0:
                results.append(
                    SearchResult(
                        title=f"User Note: {udoc.title}",
                        source_type="user_note",
                        domain_id=udoc.domain_id,
                        content_snippet=udoc.content[:250] + ("..." if len(udoc.content) > 250 else ""),
                        relevance_score=score + 0.05,
                        metadata={"doc_id": udoc.doc_id, "tags": udoc.tags},
                    )
                )

        # Sort by relevance score descending
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]

    def _score_text(self, query_keywords: set[str], corpus: str) -> float:
        """Compute keyword match score against corpus."""
        if not query_keywords:
            return 0.0
        corpus_lower = corpus.lower()
        matches = sum(1 for kw in query_keywords if kw in corpus_lower and len(kw) > 2)
        return round(matches / len(query_keywords), 3)


def json_dumps_safe(data: Any) -> str:
    """Safe helper stringifier."""
    try:
        import json
        return json.dumps(data)
    except Exception:
        return str(data)


# Global Retriever instance
retriever = KnowledgeRetriever()
