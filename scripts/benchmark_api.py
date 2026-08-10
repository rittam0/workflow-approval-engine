"""Measure complete create -> approve -> worker terminal-state lifecycles."""

import argparse
import asyncio
import time

import httpx


async def run_lifecycle(client, index, timeout, simulate_failure):
    try:
        create = await client.post(
            "/workflows",
            json={
                "title": f"benchmark-{index}",
                "description": "benchmark",
                "owner_id": "benchmark-user",
            },
        )
        if create.status_code != 201:
            return False, 0, 0, False, f"create:{create.status_code}"

        workflow_id = create.json()["id"]
        approve = await client.post(
            f"/workflows/{workflow_id}/approve",
            json={
                "actor_id": "benchmark-approver",
                "reason": "benchmark",
                "simulate_failure": simulate_failure,
            },
        )
        approved_at = time.perf_counter()
        if approve.status_code != 200:
            return False, 0, 0, False, f"approve:{approve.status_code}"

        deadline = approved_at + timeout
        while time.perf_counter() < deadline:
            response = await client.get(f"/workflows/{workflow_id}/execution-job")
            if response.status_code != 200:
                return False, 0, 0, False, f"job:{response.status_code}"
            job = response.json()
            if job["status"] in ("COMPLETED", "DEAD_LETTERED"):
                latency_ms = (time.perf_counter() - approved_at) * 1000
                retries = max(0, job["attempt_count"] - 1)
                dead_lettered = job["status"] == "DEAD_LETTERED"
                return not dead_lettered, latency_ms, retries, dead_lettered, ""
            await asyncio.sleep(0.05)

        return False, 0, 0, False, "completion:timeout"
    except Exception as exc:
        return False, 0, 0, False, exc.__class__.__name__


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    return values[int((p / 100) * (len(values) - 1))]


async def run_level(args, concurrency):
    started = time.perf_counter()
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(
        max_connections=max(2, concurrency * 2),
        max_keepalive_connections=max(1, concurrency),
    )

    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=args.timeout,
        limits=limits,
    ) as client:

        async def bounded(index):
            async with semaphore:
                should_fail = (
                    args.simulate_failure_every > 0
                    and (index + 1) % args.simulate_failure_every == 0
                )
                return await run_lifecycle(
                    client,
                    f"c{concurrency}-{index}",
                    args.timeout,
                    should_fail,
                )

        results = await asyncio.gather(*(bounded(i) for i in range(args.count)))

    elapsed = time.perf_counter() - started
    successes = [result for result in results if result[0]]
    latencies = [result[1] for result in successes]
    dead_letters = sum(1 for result in results if result[3])
    retries = sum(result[2] for result in results)
    return {
        "concurrency": concurrency,
        "successful": len(successes),
        "error_rate": (len(results) - len(successes)) / len(results) * 100,
        "throughput": len(successes) / elapsed,
        "p95": percentile(latencies, 95),
        "retries": retries,
        "dead_letters": dead_letters,
    }


async def main_async(args):
    levels = [args.concurrency] if args.concurrency else [1, 5, 10, 20, 40]
    results = []
    for concurrency in levels:
        results.append(await run_level(args, concurrency))

    print(
        "| concurrency | successful workflows | error rate | workflows/sec | "
        "p95 approval-to-completion | retries | dead-letter count |"
    )
    print("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for result in results:
        p95 = "not measured" if result["p95"] is None else f'{result["p95"]:.2f} ms'
        print(
            f'| {result["concurrency"]} | {result["successful"]} | '
            f'{result["error_rate"]:.2f}% | {result["throughput"]:.2f} | '
            f'{p95} | {result["retries"]} | {result["dead_letters"]} |'
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--count", type=int, default=40, help="workflows per concurrency level")
    parser.add_argument(
        "--concurrency",
        type=int,
        help="run one level; omit to run 1, 5, 10, 20, and 40",
    )
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument(
        "--simulate-failure-every",
        type=int,
        default=0,
        help="make every Nth approval use the deterministic failure payload",
    )
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
