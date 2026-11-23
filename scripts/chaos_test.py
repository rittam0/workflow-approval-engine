"""Crash test: kill workers at random while they process jobs, then audit.

What it does:
  1. Starts W worker processes with a short lease.
  2. Feeds N approved workflows in gradually over the test window, like real
     traffic (each approval writes one execution job).
  3. Every few seconds, SIGKILLs a random worker (no cleanup, like a power cut)
     and starts a replacement.
  4. Stops killing, waits for the queue to drain, then checks the database:
     every job completed, no duplicate results, and how many jobs had to be
     recovered after their worker died.

Usage (needs PostgreSQL; SQLite has no row locks):
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/workflows \
        python scripts/chaos_test.py
"""

import argparse
import os
import random
import signal
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func  # noqa: E402

from app import service  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import ExecutionEvent, ExecutionJob, ExecutionResult  # noqa: E402


def start_worker(port: int, lease: float) -> subprocess.Popen:
    env = dict(os.environ, WORKER_LEASE_SECONDS=str(lease), WORKER_METRICS_PORT=str(port))
    return subprocess.Popen(
        [sys.executable, "-m", "app.worker"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def pending_jobs() -> int:
    with SessionLocal() as db:
        return db.query(ExecutionJob).filter(ExecutionJob.status != "COMPLETED").count()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=125, help="how long to keep feeding and killing")
    parser.add_argument("--kill-every", type=float, default=1.5)
    parser.add_argument("--lease", type=float, default=3, help="seconds before a dead worker's job is reclaimed")
    args = parser.parse_args()

    print("Resetting tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def feed() -> None:
        pause = args.seconds / args.jobs
        with SessionLocal() as db:
            for index in range(args.jobs):
                workflow = service.create_workflow(db, f"chaos {index}", None, "owner")
                service.transition_workflow(db, workflow.id, "approve", "approver")
                time.sleep(pause)

    ports = [9100 + index for index in range(args.workers)]
    workers = {port: start_worker(port, args.lease) for port in ports}
    kills = 0
    deadline = time.time() + args.seconds
    feeder = threading.Thread(target=feed)
    feeder.start()
    print(f"Feeding {args.jobs} workflows to {args.workers} workers over {args.seconds}s, "
          f"killing one worker every {args.kill_every}s...")
    try:
        while time.time() < deadline:
            time.sleep(args.kill_every)
            port = random.choice(ports)
            workers[port].send_signal(signal.SIGKILL)
            workers[port].wait()
            kills += 1
            workers[port] = start_worker(port, args.lease)

        feeder.join()
        print("Stopped killing; waiting for the queue to drain...")
        drain_deadline = time.time() + 120
        while pending_jobs() > 0 and time.time() < drain_deadline:
            time.sleep(1)
    finally:
        for process in workers.values():
            process.terminate()
        for process in workers.values():
            process.wait()

    with SessionLocal() as db:
        total = db.query(ExecutionJob).count()
        completed = db.query(ExecutionJob).filter_by(status="COMPLETED").count()
        results = db.query(ExecutionResult).count()
        distinct_results = db.query(func.count(func.distinct(ExecutionResult.idempotency_key))).scalar()
        attempts = (
            db.query(ExecutionEvent.job_id, func.count())
            .filter(ExecutionEvent.event_type == "ATTEMPT_STARTED")
            .group_by(ExecutionEvent.job_id)
            .all()
        )
        recovered = sum(1 for _job, count in attempts if count > 1)

    print()
    print(f"Worker kills (SIGKILL):        {kills}")
    print(f"Jobs completed:                {completed}/{total}")
    print(f"Lost jobs:                     {total - completed}")
    print(f"Duplicate results:             {results - distinct_results}")
    print(f"Jobs recovered after a crash:  {recovered}")
    ok = completed == total and results == distinct_results == total
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
