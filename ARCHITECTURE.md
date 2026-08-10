# Workflow Approval Engine — Architecture

## Approval path

The FastAPI service enforces only `PENDING -> APPROVED` and
`PENDING -> REJECTED`. It locks the workflow row and writes the decision audit
entry in the same PostgreSQL transaction as the state change. Approval adds one
`execution_jobs` outbox row before that transaction commits; rejection does not.

Manual requests and AI-proposed actions use this same approval path. The
optional AI-action API records proposal evidence and a server-owned risk level,
then exposes `WAITING_FOR_HUMAN`, `ALLOWED`, or `DENIED`; it does not bypass the
human decision.

## Execution path

```text
Browser / API client
        |
        v
FastAPI approval API
        |
        v
PostgreSQL: workflow + audit + outbox (one transaction)
        |
        v
Worker claim (FOR UPDATE SKIP LOCKED + lease)
        |
        v
Idempotent execution result + execution event
```

The separate worker polls PostgreSQL directly. Concurrent workers skip locked
rows. Each claim increments `attempt_count` and carries a token and lease, so a
terminated worker's job becomes claimable again. A unique idempotency key on the
durable execution result prevents duplicate successful effects.

Failures use bounded exponential backoff. Attempts one and two create
`RETRY_SCHEDULED` events; attempt three creates a `DEAD_LETTERED` event. The
worker exports queue and outcome metrics for Prometheus.

## Existing layers preserved

- Next.js manual approval UI and AI-action submission client
- FastAPI endpoints and finite-state machine
- PostgreSQL workflow, AI-action, and audit tables
- Docker Compose deployment
- Prometheus and Grafana monitoring
