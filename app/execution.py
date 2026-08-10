"""PostgreSQL-backed execution job claiming and idempotent processing."""

from dataclasses import dataclass
from datetime import timedelta
import uuid

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from app.models import ExecutionEvent, ExecutionJob, ExecutionResult, utcnow


PENDING = "PENDING"
PROCESSING = "PROCESSING"
COMPLETED = "COMPLETED"
DEAD_LETTERED = "DEAD_LETTERED"
MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class ClaimedJob:
    id: uuid.UUID
    claim_token: uuid.UUID


def claim_next_job(db: Session, lease_seconds: float = 30) -> ClaimedJob | None:
    """Claim one due job, using SKIP LOCKED on PostgreSQL.

    The conditional UPDATE is retained as a second guard and makes the same
    routine safe in SQLite-backed tests, where row-level locking is unavailable.
    """

    # SQLite has no row-level SKIP LOCKED support. Its write lock provides a
    # deterministic serialized equivalent for the lightweight test suite.
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")

    now = utcnow()
    eligible = or_(
        and_(ExecutionJob.status == PENDING, ExecutionJob.available_at <= now),
        and_(ExecutionJob.status == PROCESSING, ExecutionJob.available_at <= now),
    )
    candidate = (
        db.query(ExecutionJob.id)
        .filter(eligible)
        .order_by(ExecutionJob.available_at, ExecutionJob.created_at)
        .with_for_update(skip_locked=True)
        .first()
    )
    if candidate is None:
        db.rollback()
        return None

    token = uuid.uuid4()
    claimed = db.execute(
        update(ExecutionJob)
        .where(ExecutionJob.id == candidate.id, eligible)
        .values(
            status=PROCESSING,
            attempt_count=ExecutionJob.attempt_count + 1,
            claim_token=token,
            claimed_at=now,
            available_at=now + timedelta(seconds=lease_seconds),
        )
    )
    if claimed.rowcount != 1:
        db.rollback()
        return None

    job = db.query(ExecutionJob).filter(ExecutionJob.id == candidate.id).one()
    db.add(
        ExecutionEvent(
            job_id=job.id,
            workflow_id=job.workflow_id,
            event_type="ATTEMPT_STARTED",
            attempt=job.attempt_count,
            detail="Job claimed by worker",
        )
    )
    db.commit()
    return ClaimedJob(id=job.id, claim_token=token)


def process_claimed_job(
    db: Session,
    claimed: ClaimedJob,
    backoff_base_seconds: float = 1,
) -> str:
    """Execute a claimed job and return completed, retried, dead_lettered, or skipped."""

    job = (
        db.query(ExecutionJob)
        .filter(ExecutionJob.id == claimed.id)
        .with_for_update()
        .first()
    )
    if (
        job is None
        or job.status != PROCESSING
        or job.claim_token != claimed.claim_token
    ):
        db.rollback()
        return "skipped"

    try:
        _execute_downstream(job)
    except Exception as exc:
        return _record_failure(db, job, exc, backoff_base_seconds)

    existing_result = (
        db.query(ExecutionResult)
        .filter(ExecutionResult.idempotency_key == job.idempotency_key)
        .first()
    )
    if existing_result is None:
        db.add(
            ExecutionResult(
                job_id=job.id,
                workflow_id=job.workflow_id,
                idempotency_key=job.idempotency_key,
            )
        )

    job.status = COMPLETED
    job.completed_at = utcnow()
    job.last_error = None
    job.claim_token = None
    db.add(
        ExecutionEvent(
            job_id=job.id,
            workflow_id=job.workflow_id,
            event_type="COMPLETED",
            attempt=job.attempt_count,
            detail="Idempotent execution result committed",
        )
    )
    db.commit()
    return "completed"


def queue_depth(db: Session) -> int:
    return (
        db.query(ExecutionJob)
        .filter(ExecutionJob.status.in_([PENDING, PROCESSING]))
        .count()
    )


def _execute_downstream(job: ExecutionJob) -> None:
    if job.simulate_failure:
        raise RuntimeError("simulated downstream failure")


def _record_failure(
    db: Session,
    job: ExecutionJob,
    exc: Exception,
    backoff_base_seconds: float,
) -> str:
    job.last_error = str(exc)
    job.claim_token = None

    if job.attempt_count >= MAX_ATTEMPTS:
        job.status = DEAD_LETTERED
        event_type = "DEAD_LETTERED"
        detail = f"Attempt {job.attempt_count} failed: {exc}"
        result = "dead_lettered"
    else:
        delay = backoff_base_seconds * (2 ** (job.attempt_count - 1))
        job.status = PENDING
        job.available_at = utcnow() + timedelta(seconds=delay)
        event_type = "RETRY_SCHEDULED"
        detail = f"Attempt {job.attempt_count} failed; retry in {delay:g}s: {exc}"
        result = "retried"

    db.add(
        ExecutionEvent(
            job_id=job.id,
            workflow_id=job.workflow_id,
            event_type=event_type,
            attempt=job.attempt_count,
            detail=detail,
        )
    )
    db.commit()
    return result
