# Workflow Approval Engine Benchmark

Benchmark scenario: full workflow lifecycle execution through the public REST API.

Each lifecycle performs:
1. Create workflow
2. Persist workflow in PostgreSQL
3. Approve workflow
4. Persist state transition
5. Write audit log entry

| Total workflows | Concurrency | Successful | Failed | Error rate | Throughput | p95 latency | p99 latency |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 20 | 500 | 0 | 0.0% | 18.84 workflows/sec | 1418.23 ms | 1575.98 ms |

## Interpretation

The system completed 500 full workflow lifecycles with 20 concurrent workers and zero failed transitions. The benchmark covers persistence, approval-state transition, and audit-log writes rather than a single endpoint.
