"""
API integration tests using FastAPI TestClient + SQLite (in-memory).
No external Postgres required to run these — CI-friendly.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# SQLite in-memory — same schema, no Postgres dependency for tests
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
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


def test_reject_workflow():
    wf_id = create_wf().json()["id"]
    r = client.post(f"/workflows/{wf_id}/reject", json={"actor_id": "carol"})
    assert r.status_code == 200
    assert r.json()["state"] == "REJECTED"


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
