"""Focused transactional outbox and worker coordination tests."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import service
from app.database import Base
from app.execution import DEAD_LETTERED, claim_next_job, process_claimed_job
from app.models import AuditLog, ExecutionEvent, ExecutionJob, ExecutionResult, Workflow


@pytest.fixture
def sessions(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'execution.db'}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    yield factory
    engine.dispose()


def approve(factory, simulate_failure=False):
    with factory() as db:
        workflow = service.create_workflow(db, "Execute me", None, "owner")
        workflow_id = workflow.id
        service.transition_workflow(
            db,
            workflow_id,
            "approve",
            "approver",
            simulate_failure=simulate_failure,
        )
        return workflow_id


def test_approval_state_audit_and_job_are_atomic(sessions):
    with sessions() as db:
        workflow = service.create_workflow(db, "Atomic", None, "owner")
        workflow_id = workflow.id

        @event.listens_for(db, "before_commit", once=True)
        def fail_commit(_session):
            raise RuntimeError("forced commit failure")

        with pytest.raises(RuntimeError, match="forced commit failure"):
            service.transition_workflow(db, workflow_id, "approve", "approver")
        db.rollback()

    with sessions() as db:
        assert db.get(Workflow, workflow_id).state == "PENDING"
        assert db.query(AuditLog).filter_by(workflow_id=workflow_id).count() == 1
        assert db.query(ExecutionJob).filter_by(workflow_id=workflow_id).count() == 0


def test_two_workers_cannot_claim_or_execute_one_job_twice(sessions):
    workflow_id = approve(sessions)

    def claim():
        with sessions() as db:
            return claim_next_job(db)

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _index: claim(), range(2)))

    claimed = [item for item in claims if item is not None]
    assert len(claimed) == 1

    with sessions() as db:
        assert process_claimed_job(db, claimed[0]) == "completed"
    with sessions() as db:
        assert process_claimed_job(db, claimed[0]) == "skipped"
        assert db.query(ExecutionResult).filter_by(workflow_id=workflow_id).count() == 1


def test_failure_retries_then_dead_letters(sessions):
    workflow_id = approve(sessions, simulate_failure=True)
    outcomes = []

    for _attempt in range(3):
        with sessions() as db:
            claimed = claim_next_job(db)
        assert claimed is not None
        with sessions() as db:
            outcomes.append(process_claimed_job(db, claimed, backoff_base_seconds=0))

    assert outcomes == ["retried", "retried", "dead_lettered"]
    with sessions() as db:
        job = db.query(ExecutionJob).filter_by(workflow_id=workflow_id).one()
        assert job.status == DEAD_LETTERED
        assert job.attempt_count == 3
        assert "simulated downstream failure" in job.last_error
        assert db.query(ExecutionResult).filter_by(workflow_id=workflow_id).count() == 0
        assert (
            db.query(ExecutionEvent)
            .filter_by(job_id=job.id, event_type="RETRY_SCHEDULED")
            .count()
            == 2
        )
        assert (
            db.query(ExecutionEvent)
            .filter_by(job_id=job.id, event_type="DEAD_LETTERED")
            .count()
            == 1
        )


def test_success_completes_once(sessions):
    workflow_id = approve(sessions)
    with sessions() as db:
        claimed = claim_next_job(db)
    assert claimed is not None

    with sessions() as db:
        assert process_claimed_job(db, claimed) == "completed"
    with sessions() as db:
        assert process_claimed_job(db, claimed) == "skipped"
        job = db.query(ExecutionJob).filter_by(workflow_id=workflow_id).one()
        assert job.status == "COMPLETED"
        assert job.attempt_count == 1
        assert job.completed_at is not None
        assert db.query(ExecutionResult).filter_by(job_id=job.id).count() == 1
        assert (
            db.query(ExecutionEvent)
            .filter_by(job_id=job.id, event_type="COMPLETED")
            .count()
            == 1
        )
