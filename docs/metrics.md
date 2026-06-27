# Workflow Approval Engine Metrics

Generated: 2026-06-27

## Benchmark Method

Benchmark tooling lives in `scripts/benchmark_api.py` and uses only the Python
standard library.

Each workflow lifecycle performs:

1. `POST /workflows`
2. `POST /workflows/{id}/approve`
3. `GET /workflows/{id}`

The steady-state run warms the API first, then executes concurrent workflow
lifecycles and records request latency, lifecycle latency, throughput, and error
rate.

## Environment

- API: FastAPI/Uvicorn container
- Database: PostgreSQL container
- Compose network: `workflow-approval-engine_default`
- API internal URL: `http://app:8000`
- API host URL: `http://localhost:18080`
- Benchmark workload: 120 complete workflows, 12-way concurrency, 12 warmup workflows

## Reproduction Commands

Cold start to health:

```bash
cd /home/khrit/projects/workflow-approval-engine
python3 scripts/benchmark_api.py \
  --base-url http://localhost:18080 \
  --workflows 120 \
  --concurrency 12 \
  --warmup 12 \
  --cold-start-command 'docker compose restart app'
```

Steady state from inside the Docker Compose network:

```bash
cd /home/khrit/projects/workflow-approval-engine
docker run --rm \
  --network workflow-approval-engine_default \
  -v "$PWD:/workspace" \
  -w /workspace \
  python:3.10-slim \
  python scripts/benchmark_api.py \
    --base-url http://app:8000 \
    --workflows 120 \
    --concurrency 12 \
    --warmup 12
```

## Results

### Cold Start

Cold start measures time from `docker compose restart app` until `GET /health`
returns successfully.

| Metric | Value |
| --- | ---: |
| Cold start to healthy API | 17,496.36 ms |

### Steady State

Steady-state benchmark ran after 12 warmup workflows.

| Metric | Value |
| --- | ---: |
| Total workflows | 120 |
| Total API requests | 360 |
| Concurrency | 12 |
| Wall time | 33.805 s |
| Throughput | 10.65 requests/sec |
| Error rate | 0.00% |

### Request Latency

| Metric | p50 | p95 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| All API requests | 1,013.51 ms | 1,929.93 ms | 1,115.99 ms | 199.70 ms | 2,366.15 ms |
| Workflow creation | 1,089.74 ms | 1,825.60 ms | 1,179.30 ms | 655.63 ms | 2,366.15 ms |
| Workflow approval | 1,061.46 ms | 1,998.80 ms | 1,192.68 ms | 631.57 ms | 2,116.27 ms |
| Workflow detail fetch | 882.43 ms | 1,756.43 ms | 975.99 ms | 199.70 ms | 2,175.00 ms |

### Complete Workflow Lifecycle

Lifecycle latency measures `create -> approve -> fetch` for a single workflow.

| Metric | Value |
| --- | ---: |
| p50 lifecycle latency | 3,220.55 ms |
| p95 lifecycle latency | 4,700.49 ms |
| Average lifecycle latency | 3,350.76 ms |
| Min lifecycle latency | 2,159.62 ms |
| Max lifecycle latency | 5,346.18 ms |

## Notes

- The benchmark creates durable PostgreSQL records; use a disposable local
  database or reset volumes before comparing repeated runs.
- Host-to-container measurements were slower than compose-network measurements,
  so the steady-state table reports the compose-network run for cleaner
  service-to-service latency.
