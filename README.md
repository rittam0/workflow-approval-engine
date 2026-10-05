# Workflow Approval Engine

A durable manual approval workflow for consequential automated actions. A human
decision is recorded synchronously and atomically; approved work is placed in a
PostgreSQL transactional outbox and executed by a separate worker.

The supported state transitions remain:

```text
PENDING -> APPROVED
PENDING -> REJECTED
```

Every create and decision writes the existing audit log. Approval also creates
an execution job in the same database transaction. Submission can come from the
browser, another application, or the optional AI-action client API; the product
remains a human approval workflow.

## Quick start

```bash
docker compose up -d --build
```

| Service | URL |
| --- | --- |
| Manual workflow UI | http://localhost:3000 |
| API and docs | http://localhost:8000 / http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

Configuration is environment-driven; see [.env.example](.env.example).

## Architecture

```text
Manual UI / API client
          |
          v
     FastAPI API -> PostgreSQL transactional outbox -> worker -> execution result
                         |                              |
                         +---- audit / execution events+
```

The API locks a pending workflow and commits its approval state, audit entry,
and `execution_jobs` row together. Workers claim due rows with PostgreSQL
`FOR UPDATE SKIP LOCKED`. A lease recovers abandoned claims, while the unique
idempotency key on `execution_results` prevents duplicate successful result
records. Failed executions use exponential backoff (1 then 2 seconds by default)
and become `DEAD_LETTERED` when a failure is recorded at attempt three or later.

## Delivery and recovery

Approval, audit and outbox insertion commit together: a rollback leaves no
approved workflow without its job. Concurrent PostgreSQL workers skip rows
locked by another worker. Claiming commits a token and a 30-second default
lease; an expired claim becomes eligible again, with a new token. A stale
worker cannot commit through an obsolete claim token. Execution holds the job
row lock until its result and completion event commit.

Execution attempts can repeat after failure or an abandoned lease. This is a
retryable, at-least-once attempt model, not exactly-once external execution.
If a downstream call succeeds but the worker dies before the database commit,
the next worker can call it again. The downstream service must honor the same
idempotency key to deduplicate that side effect. The included executor only
records a harmless database result (or raises a deterministic failure).

The retry limit is checked when recording an execution failure; repeated
crashes before failure recording can cause more than three claims. There is
no lease heartbeat, so a future long-running executor needs a lease policy
and downstream idempotency appropriate to its duration.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/workflows` | Create a pending workflow |
| `GET` | `/workflows` | List workflows, optionally by state |
| `GET` | `/workflows/{id}` | Workflow detail and decision audit trail |
| `POST` | `/workflows/{id}/approve` | Record a human approval |
| `POST` | `/workflows/{id}/reject` | Record a human rejection |
| `GET` | `/workflows/{id}/execution-job` | Read execution status and attempts |
| `POST` | `/ai-actions` | Submit an optional AI-proposed action for review |
| `GET` | `/ai-actions/{id}` | Read the proposal and server-owned risk evidence |
| `GET` | `/ai-actions/{id}/decision` | Read waiting, allowed, or denied status |

## Three-step failure demo

1. Create a workflow and copy its `id`:

   ```bash
   curl -sS -X POST http://localhost:8000/workflows \
     -H 'content-type: application/json' \
     -d '{"title":"Failure demo","owner_id":"alice"}'
   ```

2. Approve it with the harmless deterministic failure payload:

   ```bash
   curl -sS -X POST http://localhost:8000/workflows/WORKFLOW_ID/approve \
     -H 'content-type: application/json' \
     -d '{"actor_id":"bob","reason":"failure demo","simulate_failure":true}'
   ```

3. After about three seconds, inspect the terminal job (`attempt_count: 3`,
   `status: "DEAD_LETTERED"`) and worker metrics:

   ```bash
   curl -sS http://localhost:8000/workflows/WORKFLOW_ID/execution-job
   curl -sS http://localhost:9090/api/v1/query?query=execution_jobs_dead_lettered_total
   ```

## Verification

```bash
python -m pytest tests -v
cd frontend && npm run lint && npm run build
```

The focused backend tests cover transactional rollback, two-worker claiming,
bounded failure retries/dead-lettering, lease recovery and stale-token rejection,
unique successful result recording, and the
existing AI-action decision guard. These CI tests use SQLite with serialized
write locking; they do not establish PostgreSQL `SKIP LOCKED` behavior. The
recorded Docker benchmark exercises the PostgreSQL lifecycle with one worker.

## Benchmark

The benchmark measures create, approval, worker execution, and terminal job
status at client concurrency 1, 5, 10, 20, and 40. The recorded local
Docker/PostgreSQL/worker cohort ran 200 workflows per level, three runs per
level: all 3,000 completed successfully. It is not a production capacity claim:

```bash
python scripts/benchmark_api.py --base-url http://localhost:8000 --count 200
```

Measured PostgreSQL/Docker results are recorded in
[docs/benchmark.md](docs/benchmark.md). A separate deterministic cohort forced
failure for 10 workflows: 20 retries, 10 dead-lettered jobs, three attempts per
job, and zero successful execution results. Runs create durable records.

## Observability

Existing workflow, AI-action, and HTTP metrics are preserved. The worker
exposes counters for completed, retried, and dead-lettered jobs plus a
queue-depth gauge on its internal `:8001/metrics` endpoint; Prometheus scrapes
both API and worker, and the Compose stack includes Grafana dashboards.

## Known limitations

- Authentication and authorization are intentionally out of scope; IDs are
  supplied as plain strings.
- The AI decision endpoint is a control-plane guard; connected callers must
  honor its result.
- Schema creation uses SQLAlchemy metadata rather than a migration framework.
- The included executor records a harmless durable result; a real downstream
  integration must honor the supplied idempotency key.
