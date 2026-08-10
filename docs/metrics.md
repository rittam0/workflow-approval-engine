# Metrics

Prometheus continues to scrape the API metrics endpoint and also scrapes the
worker's internal `:8001/metrics` endpoint.

Existing business metrics:

- `workflow_created_total`
- `workflow_transition_total`
- `workflow_invalid_transition_total`

Execution metrics:

- `execution_jobs_completed_total`
- `execution_jobs_retried_total`
- `execution_jobs_dead_lettered_total`
- `execution_job_queue_depth`

## Measured verification

The 2026-08-10 benchmark completed 3,000/3,000 normal workflows across three
200-workflow runs at concurrency 1, 5, 10, 20, and 40. The highest median
throughput was 11.19 workflows/sec at concurrency 40; the worst p95 at that
level was 2,268.94 ms.

The separate 10-workflow deterministic failure run recorded 20 retries and 10
dead letters. PostgreSQL verification found exactly three attempts per job, 10
of 10 jobs `DEAD_LETTERED`, zero execution results for the failing cohort, and
zero duplicated execution-result idempotency keys globally.

The bundled Grafana dashboard adds four small stat panels for the execution
metrics. See [benchmark.md](benchmark.md) for the benchmark method and aggregate
results.
