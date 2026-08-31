"""Integration Tests for FastAPI REST Endpoints & Complete User Lifecycle.

Tests all REST API routes end-to-end using httpx / FastAPI test client:
1. Health & Welcome endpoints
2. Candidate registration & profile retrieval
3. Multi-turn chat with coordinator
4. Starting diagnostic assessment
5. Fetching adaptive drill items & submitting answers
6. Pausing drill for deep-dive and resuming
7. Generating 6-domain certification progress report
8. Custom material upload & weekly sync
9. HITL progress reset
"""

import pytest
from httpx import ASGITransport, AsyncClient

from pca_study_agent.server.app import app


@pytest.mark.asyncio
async def test_server_health_and_root():
    """Verify health check and root landing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health check
        res_health = await client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        # Root web UI landing
        res_root = await client.get("/")
        assert res_root.status_code == 200
        assert "Google Cloud PCA" in res_root.text


@pytest.mark.asyncio
async def test_full_candidate_lifecycle_api():
    """Verify full candidate API journey: Register -> Diagnostic -> Drill -> Submit -> Pause -> Resume -> Report."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_id = "integration_candidate_1"

        # 1. Register Candidate
        res_reg = await client.post(
            "/api/v1/auth/register",
            json={"user_id": user_id, "candidate_name": "Integration Candidate"},
        )
        assert res_reg.status_code == 200
        assert res_reg.json()["user_id"] == user_id

        # 2. Chat with Coordinator
        res_chat = await client.post(
            "/api/v1/chat",
            json={"user_id": user_id, "message": "Can you explain how the study agent works?"},
        )
        assert res_chat.status_code == 200
        assert "response_text" in res_chat.json()

        # 3. Start Diagnostic Assessment
        res_diag = await client.post(
            "/api/v1/assessment/start",
            json={"user_id": user_id, "num_questions": 4},
        )
        assert res_diag.status_code == 200
        assert res_diag.json()["total_questions"] == 4
        assert len(res_diag.json()["questions"]) == 4

        # 4. Fetch Next Adaptive Drill Item
        res_drill = await client.get(f"/api/v1/drill/next?user_id={user_id}&item_type=question")
        assert res_drill.status_code == 200
        item_id = res_drill.json()["item_id"]

        # 5. Submit Answer
        res_sub = await client.post(
            "/api/v1/drill/submit",
            json={
                "user_id": user_id,
                "item_id": item_id,
                "submitted_answer": "B",
                "candidate_reasoning": "Cloud Spanner provides global multi-region write scalability.",
            },
        )
        assert res_sub.status_code == 200
        assert "is_correct" in res_sub.json()
        assert "updated_domain_mastery" in res_sub.json()

        # 6. Pause for Deep-Dive
        res_pause = await client.post(
            "/api/v1/drill/pause",
            json={"user_id": user_id, "topic_of_inquiry": "Cloud Spanner TrueTime"},
        )
        assert res_pause.status_code == 200
        assert res_pause.json()["is_paused"] is True

        # 7. Resume Drill
        res_resume = await client.post(
            "/api/v1/drill/resume",
            json={"user_id": user_id},
        )
        assert res_resume.status_code == 200
        assert res_resume.json()["is_resumed"] is True

        # 8. Get Certification Progress Report
        res_rep = await client.get(f"/api/v1/progress/report?user_id={user_id}")
        assert res_rep.status_code == 200
        report = res_rep.json()
        assert len(report["domain_breakdown"]) == 6
        assert "overall_readiness_score" in report

        # 9. Upload Custom Study Material
        res_mat = await client.post(
            "/api/v1/materials/upload",
            json={
                "user_id": user_id,
                "title": "My Spanner Cheat Sheet",
                "content": "Cloud Spanner requires 3 regions for dual-region witness quorum.",
                "domain_id": "domain_1",
                "tags": ["spanner", "high-availability"],
            },
        )
        assert res_mat.status_code == 200
        assert res_mat.json()["title"] == "My Spanner Cheat Sheet"

        # 10. Trigger Weekly Sync
        res_sync = await client.post("/api/v1/materials/sync")
        assert res_sync.status_code == 200
        assert res_sync.json()["status"] == "success"

        # 11. Request HITL Reset Challenge
        res_reset_req = await client.post(
            "/api/v1/admin/reset",
            json={"user_id": user_id},
        )
        assert res_reset_req.status_code == 200
        assert res_reset_req.json()["requires_confirmation"] is True
        token = res_reset_req.json()["confirmation_token"]

        # Confirm HITL Reset
        res_reset_conf = await client.post(
            "/api/v1/admin/reset",
            json={"user_id": user_id, "confirmation_token": token},
        )
        assert res_reset_conf.status_code == 200
        assert res_reset_conf.json()["action_executed"] is True

        # 12. Flag / Report Question API
        res_flag = await client.post(
            "/api/v1/questions/flag",
            json={
                "user_id": user_id,
                "question_id": item_id,
                "reason": "unclear_wording",
                "feedback_notes": "Integration test dispute notes.",
            },
        )
        assert res_flag.status_code == 200
        assert res_flag.json()["is_suspended"] is True

        # 13. List Flagged Questions
        res_list_flagged = await client.get("/api/v1/questions/flagged")
        assert res_list_flagged.status_code == 200
        assert res_list_flagged.json()["total_flagged"] >= 1

        # 14. Admin Resolve Question
        res_resolve = await client.post(
            "/api/v1/questions/resolve",
            json={
                "admin_user_id": "admin_test",
                "question_id": item_id,
                "action": "approve",
                "resolution_notes": "Approved by lead auditor.",
            },
        )
        assert res_resolve.status_code == 200
        assert res_resolve.json()["status"] == "success"

