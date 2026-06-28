import argparse
import asyncio
import statistics
import time

import httpx


async def run_lifecycle(client, index):
    start = time.perf_counter()

    create = await client.post(
        "/workflows",
        json={
            "title": f"benchmark-{index}",
            "description": "benchmark",
            "owner_id": "benchmark-user",
        },
    )

    if create.status_code != 201:
        return False, 0, f"create:{create.status_code}"

    workflow_id = create.json()["id"]

    approve = await client.post(
        f"/workflows/{workflow_id}/approve",
        json={
            "actor_id": "benchmark-approver",
            "reason": "benchmark",
        },
    )

    latency_ms = (time.perf_counter() - start) * 1000

    if approve.status_code != 200:
        return False, latency_ms, f"approve:{approve.status_code}"

    return True, latency_ms, ""


def percentile(values, p):
    values = sorted(values)
    if not values:
        return 0
    index = int((p / 100) * (len(values) - 1))
    return values[index]


async def main_async(args):
    started = time.perf_counter()

    async with httpx.AsyncClient(base_url=args.base_url, timeout=20) as client:
        results = await asyncio.gather(
            *(run_lifecycle(client, i) for i in range(args.count))
        )

    elapsed = time.perf_counter() - started

    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    latencies = [r[1] for r in successes]

    print("workflows:", args.count)
    print("successful:", len(successes))
    print("failed:", len(failures))
    print("error_rate:", round((len(failures) / args.count) * 100, 2), "%")
    print("throughput:", round(len(successes) / elapsed, 2), "workflows/sec")
    print("mean_ms:", round(statistics.mean(latencies), 2) if latencies else 0)
    print("p50_ms:", round(percentile(latencies, 50), 2))
    print("p95_ms:", round(percentile(latencies, 95), 2))
    print("p99_ms:", round(percentile(latencies, 99), 2))

    if failures:
        print("failure_sample:", failures[0][2])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()

    asyncio.run(main_async(args))


main()
