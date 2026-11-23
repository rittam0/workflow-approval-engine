"""Tests that only mean something on real PostgreSQL.

The main suite runs on SQLite, which has no row-level locks, so it cannot
prove that FOR UPDATE SKIP LOCKED works. These tests run against a real
PostgreSQL database and are skipped unless TEST_POSTGRES_URL is set:

    TEST_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/workflows_test \
        python -m pytest tests/test_postgres.py -v

CI runs them against a PostgreSQL service container.
"""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import service
from app.database import Base
from app.execution import claim_next_job, process_claimed_job
from app.models import ExecutionEvent, ExecutionJob, ExecutionResult

POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="set TEST_POSTGRES_URL to run PostgreSQL tests"
)


@pytest.fixture
def sessions():
    engine = create_engine(POSTGRES_URL, pool_size=20, max_overflow=0)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def approve(factory, title):
    with factory() as db:
        workflow = service.create_workflow(db, title, None, "owner")
        service.transition_workflow(db, workflow.id, "approve", "approver")
        return workflow.id


def test_skip_locked_moves_past_a_row_another_worker_holds(sessions):
    """Worker B must skip a job that worker A has locked, not wait for it."""
    approve(sessions, "first")
    approve(sessions, "second")

    holder = sessions()
    try:
        # Worker A locks the oldest job and keeps its transaction open.
        locked_id = (
            holder.query(ExecutionJob.id)
            .order_by(ExecutionJob.available_at, ExecutionJob.created_at)
            .with_for_update()
            .first()
            .id
        )

        # Worker B runs with a lock timeout: if SKIP LOCKED were missing,
        # it would block on A's row and fail instead of returning.
        with sessions() as db:
            db.connection().exec_driver_sql("SET lock_timeout = '2s'")
            claimed = claim_next_job(db)

        assert claimed is not None
        assert claimed.id != locked_id
    finally:
        holder.rollback()
        holder.close()


def test_eight_workers_complete_every_job_exactly_once(sessions):
    """Many workers racing over one queue: no job lost, none run twice."""
    job_count = 60
    for index in range(job_count):
        approve(sessions, f"job {index}")

    def worker():
        done = 0
        while True:
            with sessions() as db:
                claimed = claim_next_job(db)
            if claimed is None:
                return done
            with sessions() as db:
                if process_claimed_job(db, claimed) == "completed":
                    done += 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        completed_per_worker = list(pool.map(lambda _i: worker(), range(8)))

    assert sum(completed_per_worker) == job_count
    with sessions() as db:
        assert db.query(ExecutionJob).filter_by(status="COMPLETED").count() == job_count
        assert db.query(ExecutionResult).count() == job_count
        # Every job was claimed exactly once: one ATTEMPT_STARTED event each.
        assert (
            db.query(ExecutionEvent).filter_by(event_type="ATTEMPT_STARTED").count()
            == job_count
        )
