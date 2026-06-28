# Workflow Approval Engine Metrics

Generated: 2026-06-29

## Test Results

Command:

```bash
python -m pytest tests -v
```

Result:

```text
13 passed, 1 warning in 52.68s
```

Failure fixed during this refresh:

- Added the direct `prometheus-client` dependency to `requirements.txt` because
  `app/metrics.py` imports `prometheus_client.Counter` directly.

## Benchmark Method

Benchmark tooling lives in `scripts/benchmark_api.py`.

The current benchmark scenario runs concurrent workflow lifecycle requests
through the public REST API. Each lifecycle performs:

1. `POST /workflows`
2. `POST /workflows/{id}/approve`

This exercises workflow creation, PostgreSQL persistence, FSM transition
validation, workflow approval, state persistence, and audit-log writes.

## Environment

- API: FastAPI/Uvicorn container
- Database: PostgreSQL container
- Frontend: Next.js/React container
- Observability: Prometheus and Grafana containers
- Compose project: `workflow-approval-engine`
- API URL used for measured runs: `http://localhost:8000`

Current Compose stack was healthy before benchmarking.

## Warmup

Command:

```bash
python scripts/benchmark_api.py --base-url http://localhost:8000 --count 25 --concurrency 5
```

Measured warmup output:

| Workflows | Concurrency | Successful | Failed | Error rate | Throughput | Mean latency | p50 latency | p95 latency | p99 latency |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 25 | 5 | 25 | 0 | 0.0% | 1.3 workflows/sec | 3,033.94 ms | 1,380.40 ms | 10,047.90 ms | 10,132.06 ms |

## Steady-State Benchmark Commands

```bash
python scripts/benchmark_api.py --base-url http://localhost:8000 --count 100 --concurrency 20
python scripts/benchmark_api.py --base-url http://localhost:8000 --count 250 --concurrency 20
python scripts/benchmark_api.py --base-url http://localhost:8000 --count 500 --concurrency 20
```

## Steady-State Results

| Workflows | Concurrency | Successful | Failed | Error rate | Throughput | Mean latency | p50 latency | p95 latency | p99 latency |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 20 | 100 | 0 | 0.0% | 3.35 workflows/sec | 5,112.57 ms | 4,922.87 ms | 7,127.41 ms | 7,211.89 ms |
| 250 | 20 | 250 | 0 | 0.0% | 3.17 workflows/sec | 5,746.81 ms | 4,978.23 ms | 14,661.24 ms | 15,057.13 ms |
| 500 | 20 | 500 | 0 | 0.0% | 3.8 workflows/sec | 5,055.51 ms | 4,935.19 ms | 6,375.92 ms | 7,560.14 ms |

## Resume Metrics

- Automated tests: 13 passing pytest tests covering workflow creation, approval,
  rejection, invalid transitions, filtering, 404 handling, FSM behavior, and
  audit-log validation.
- Benchmark scale: 500 concurrent workflow lifecycles completed with 500/500
  successes and 0.0% error rate at 20-way concurrency.
- Best measured steady-state throughput in this refresh: 3.8 workflows/sec for
  500 workflow lifecycles, with p50 latency 4,935.19 ms and p95 latency
  6,375.92 ms.

## Notes

- Benchmark results are local Docker Compose measurements and will vary by
  machine, Docker Desktop resources, and existing database volume size.
- Benchmark runs create durable PostgreSQL records. Use a disposable database
  volume or reset volumes before strict apples-to-apples comparisons.
- The benchmark reports workflow lifecycle throughput, not raw HTTP
  requests/sec.
