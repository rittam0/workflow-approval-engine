# End-to-end lifecycle benchmark

Measured on 2026-08-10 with the Docker Compose FastAPI API, PostgreSQL 14, and
one execution worker. Each run sent 200 workflows through create, synchronous
approval, outbox claim, execution-result commit, and terminal-status polling at
each concurrency level. Three runs were recorded per level.

Command, run three times:

```bash
docker compose run --rm app python scripts/benchmark_api.py \
  --base-url http://app:8000 --count 200
```

The table reports median throughput across the three runs and the worst
(highest) observed p95 approval-to-completion latency. All 3,000 workflows
completed successfully with no retries or dead letters.

| concurrency | workflows per run | successful across runs | error rate | median workflows/sec | worst p95 approval-to-completion | retries | dead-letter count |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 200 | 600 | 0.00% | 3.40 | 307.22 ms | 0 | 0 |
| 5 | 200 | 600 | 0.00% | 8.87 | 609.52 ms | 0 | 0 |
| 10 | 200 | 600 | 0.00% | 10.53 | 807.07 ms | 0 | 0 |
| 20 | 200 | 600 | 0.00% | 10.91 | 1,024.26 ms | 0 | 0 |
| 40 | 200 | 600 | 0.00% | 11.19 | 2,268.94 ms | 0 | 0 |

## Deterministic failure verification

Ten failing workflows were submitted concurrently:

```bash
docker compose run --rm app python scripts/benchmark_api.py \
  --base-url http://app:8000 --count 10 --concurrency 10 \
  --simulate-failure-every 1
```

Measured result: 20 retries and 10 dead-lettered jobs. Direct PostgreSQL checks
of that 10-job cohort confirmed:

- every job had `attempt_count = 3` and three `ATTEMPT_STARTED` events;
- all 10 jobs reached `DEAD_LETTERED`, each with one dead-letter event;
- no job reached `COMPLETED` and the cohort produced zero execution results;
- the complete `execution_results` table contained zero duplicated idempotency
  keys.

These are local-machine measurements, not production capacity claims.
