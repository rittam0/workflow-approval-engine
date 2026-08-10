"""
API integration tests using FastAPI TestClient + SQLite (in-memory).
No external Postgres required to run these — CI-friendly.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# SQLite in-memory — same schema, no Postgres dependency for tests
TEST_DB_URL = "sqlite://"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_wf(title="Test Workflow", owner="alice"):
    return client.post("/workflows", json={"title": title, "owner_id": owner})


def create_ai_action(action_type="ISSUE_REFUND"):
    return client.post(
        "/ai-actions",
        json={
            "summary": "Review an AI-proposed action",
            "action_type": action_type,
            "target": "order-1842",
            "payload": {"amount": 2499, "currency": "INR"},
            "agent_name": "refund-agent",
            "model_name": "test-model",
            "rationale": "A duplicate payment was detected",
            "owner_id": "alice",
        },
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_workflow():
    r = create_wf()
    assert r.status_code == 201
    assert r.json()["state"] == "PENDING"


def test_approve_workflow():
    wf_id = create_wf().json()["id"]
    r = client.post(f"/workflows/{wf_id}/approve", json={"actor_id": "bob", "reason": "LGTM"})
    assert r.status_code == 200
    assert r.json()["state"] == "APPROVED"
    job = client.get(f"/workflows/{wf_id}/execution-job")
    assert job.status_code == 200
    assert job.json()["status"] == "PENDING"
    assert job.json()["attempt_count"] == 0


def test_reject_workflow():
    wf_id = create_wf().json()["id"]
    r = client.post(f"/workflows/{wf_id}/reject", json={"actor_id": "carol"})
    assert r.status_code == 200
    assert r.json()["state"] == "REJECTED"
    assert client.get(f"/workflows/{wf_id}/execution-job").status_code == 404


def test_illegal_transition_returns_409():
    wf_id = create_wf().json()["id"]
    client.post(f"/workflows/{wf_id}/approve", json={"actor_id": "bob"})
    # Try to approve again — illegal
    r = client.post(f"/workflows/{wf_id}/approve", json={"actor_id": "bob"})
    assert r.status_code == 409


def test_audit_log_written_on_transition():
    wf_id = create_wf().json()["id"]
    client.post(f"/workflows/{wf_id}/approve", json={"actor_id": "bob", "reason": "checked"})
    detail = client.get(f"/workflows/{wf_id}").json()
    # Creation audit entry + approve entry = 2 entries
    assert len(detail["audit_entries"]) == 2
    approve_entry = detail["audit_entries"][-1]
    assert approve_entry["from_state"] == "PENDING"
    assert approve_entry["to_state"] == "APPROVED"
    assert approve_entry["actor_id"] == "bob"


def test_get_nonexistent_workflow():
    import uuid
    r = client.get(f"/workflows/{uuid.uuid4()}")
    assert r.status_code == 404


def test_list_workflows_filter_by_state():
    create_wf("W1")
    wf2_id = create_wf("W2").json()["id"]
    client.post(f"/workflows/{wf2_id}/approve", json={"actor_id": "bob"})

    pending = client.get("/workflows?state=PENDING").json()
    approved = client.get("/workflows?state=APPROVED").json()

    assert len(pending) == 1
    assert len(approved) == 1


def test_create_ai_action_uses_server_owned_risk_policy():
    r = create_ai_action("ISSUE_REFUND")
    assert r.status_code == 201
    action = r.json()
    assert action["risk_level"] == "HIGH"

    workflow = client.get(f"/workflows/{action['workflow_id']}").json()
    assert workflow["state"] == "PENDING"
    assert workflow["ai_action"]["id"] == action["id"]
    assert workflow["ai_action"]["payload"]["amount"] == 2499


def test_pending_ai_action_is_blocked():
    action = create_ai_action().json()
    decision = client.get(f"/ai-actions/{action['id']}/decision")
    assert decision.status_code == 200
    assert decision.json()["decision"] == "WAITING_FOR_HUMAN"
    assert decision.json()["allowed"] is False


def test_approved_ai_action_is_allowed():
    action = create_ai_action().json()
    client.post(
        f"/workflows/{action['workflow_id']}/approve",
        json={"actor_id": "human-reviewer", "reason": "Evidence checked"},
    )

    decision = client.get(f"/ai-actions/{action['id']}/decision").json()
    assert decision["decision"] == "ALLOWED"
    assert decision["allowed"] is True


def test_rejected_ai_action_is_denied():
    action = create_ai_action().json()
    client.post(
        f"/workflows/{action['workflow_id']}/reject",
        json={"actor_id": "human-reviewer", "reason": "Unsafe target"},
    )

    decision = client.get(f"/ai-actions/{action['id']}/decision").json()
    assert decision["decision"] == "DENIED"
    assert decision["allowed"] is False


def test_ai_caller_cannot_choose_its_own_risk_level():
    payload = {
        "summary": "Delete production record",
        "action_type": "DELETE_RECORD",
        "target": "customer-42",
        "payload": {},
        "agent_name": "cleanup-agent",
        "owner_id": "alice",
        "risk_level": "LOW",
    }
    r = client.post("/ai-actions", json=payload)
    assert r.status_code == 422


def test_missing_ai_action_returns_404():
    import uuid

    r = client.get(f"/ai-actions/{uuid.uuid4()}/decision")
    assert r.status_code == 404
