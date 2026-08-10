"""Execution worker entrypoint for the PostgreSQL transactional outbox."""

import logging
import os
import signal
import time

from prometheus_client import start_http_server
from sqlalchemy.exc import OperationalError

from app.database import Base, SessionLocal, engine
from app.execution import claim_next_job, process_claimed_job, queue_depth
from app.metrics import (
    execution_job_queue_depth,
    execution_jobs_completed_total,
    execution_jobs_dead_lettered_total,
    execution_jobs_retried_total,
)


logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
running = True


def run_once(lease_seconds: float = 30, backoff_base_seconds: float = 1) -> str:
    with SessionLocal() as db:
        claimed = claim_next_job(db, lease_seconds=lease_seconds)
    if claimed is None:
        return "idle"

    with SessionLocal() as db:
        result = process_claimed_job(
            db,
            claimed,
            backoff_base_seconds=backoff_base_seconds,
        )

    if result == "completed":
        execution_jobs_completed_total.inc()
    elif result == "retried":
        execution_jobs_retried_total.inc()
    elif result == "dead_lettered":
        execution_jobs_dead_lettered_total.inc()
    return result


def update_queue_depth() -> None:
    with SessionLocal() as db:
        execution_job_queue_depth.set(queue_depth(db))


def stop(*_args) -> None:
    global running
    running = False


def main() -> None:
    poll_seconds = float(os.environ.get("WORKER_POLL_SECONDS", "0.25"))
    lease_seconds = float(os.environ.get("WORKER_LEASE_SECONDS", "30"))
    backoff_seconds = float(os.environ.get("WORKER_BACKOFF_BASE_SECONDS", "1"))
    metrics_port = int(os.environ.get("WORKER_METRICS_PORT", "8001"))

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    Base.metadata.create_all(bind=engine)
    start_http_server(metrics_port)
    logger.info("execution worker started; metrics on :%s", metrics_port)

    while running:
        try:
            result = run_once(lease_seconds, backoff_seconds)
            update_queue_depth()
            if result == "idle":
                time.sleep(poll_seconds)
        except OperationalError:
            logger.exception("database unavailable; retrying")
            time.sleep(min(5, max(1, poll_seconds)))
        except Exception:
            logger.exception("worker loop failed; retrying")
            time.sleep(min(5, max(1, poll_seconds)))


if __name__ == "__main__":
    main()
