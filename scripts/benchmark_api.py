"""Benchmark the Workflow Approval Engine API.

The script uses only Python's standard library so benchmark runs are
reproducible from the repository without adding runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class RequestMetric:
    name: str
    ok: bool
    status: int | None
    latency_ms: float


@dataclass
class LifecycleMetric:
    ok: bool
    latency_ms: float
    create_ms: float | None
    approve_ms: float | None
    fetch_ms: float | None
    request_count: int
    error_count: int


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[int(index)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> tuple[dict[str, Any] | list[Any] | None, RequestMetric]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    started = time.perf_counter()
    status: int | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            raw = response.read()
            data = json.loads(raw.decode("utf-8")) if raw else None
            ok = 200 <= status < 400
    except urllib.error.HTTPError as exc:
        status = exc.code
        data = None
        ok = False
    except Exception:
        data = None
        ok = False

    elapsed_ms = (time.perf_counter() - started) * 1000
    return data, RequestMetric(path, ok, status, elapsed_ms)


def wait_for_health(base_url: str, timeout_seconds: float) -> float:
    started = time.perf_counter()
    deadline = started + timeout_seconds
    while time.perf_counter() < deadline:
        _, metric = request_json(base_url, "GET", "/health", timeout=2.0)
        if metric.ok:
            return (time.perf_counter() - started) * 1000
        time.sleep(0.25)
    raise RuntimeError(f"API did not become healthy within {timeout_seconds:.1f}s")


def run_lifecycle(base_url: str, index: int) -> tuple[LifecycleMetric, list[RequestMetric]]:
    run_id = uuid.uuid4().hex[:12]
    metrics: list[RequestMetric] = []
    started = time.perf_counter()

    workflow, metric = request_json(
        base_url,
        "POST",
        "/workflows",
        {
            "title": f"Benchmark workflow {index}-{run_id}",
            "description": "Automated benchmark workflow",
            "owner_id": "benchmark",
        },
    )
    metrics.append(metric)
    if not metric.ok or not isinstance(workflow, dict) or "id" not in workflow:
        return lifecycle_from(started, metrics), metrics

    workflow_id = workflow["id"]
    _, metric = request_json(
        base_url,
        "POST",
        f"/workflows/{workflow_id}/approve",
        {"actor_id": "benchmark-approver", "reason": "benchmark approval"},
    )
    metrics.append(metric)
    if not metric.ok:
        return lifecycle_from(started, metrics), metrics

    _, metric = request_json(base_url, "GET", f"/workflows/{workflow_id}")
    metrics.append(metric)
    return lifecycle_from(started, metrics), metrics


def lifecycle_from(started: float, metrics: list[RequestMetric]) -> LifecycleMetric:
    return LifecycleMetric(
        ok=all(metric.ok for metric in metrics) and len(metrics) == 3,
        latency_ms=(time.perf_counter() - started) * 1000,
        create_ms=metrics[0].latency_ms if len(metrics) >= 1 else None,
        approve_ms=metrics[1].latency_ms if len(metrics) >= 2 else None,
        fetch_ms=metrics[2].latency_ms if len(metrics) >= 3 else None,
        request_count=len(metrics),
        error_count=sum(1 for metric in metrics if not metric.ok),
    )


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "p50_ms": round(percentile(values, 0.50), 2),
        "p95_ms": round(percentile(values, 0.95), 2),
        "min_ms": round(min(values), 2) if values else 0.0,
        "max_ms": round(max(values), 2) if values else 0.0,
        "avg_ms": round(sum(values) / len(values), 2) if values else 0.0,
    }


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    cold_start_ms = None
    if args.cold_start_command:
        subprocess.run(args.cold_start_command, shell=True, check=True)
        cold_start_ms = round(wait_for_health(args.base_url, args.cold_start_timeout), 2)
    else:
        wait_for_health(args.base_url, args.cold_start_timeout)

    for index in range(args.warmup):
        run_lifecycle(args.base_url, index)

    started = time.perf_counter()
    lifecycles: list[LifecycleMetric] = []
    requests: list[RequestMetric] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(run_lifecycle, args.base_url, index)
            for index in range(args.workflows)
        ]
        for future in as_completed(futures):
            lifecycle, request_metrics = future.result()
            lifecycles.append(lifecycle)
            requests.extend(request_metrics)

    wall_seconds = time.perf_counter() - started
    request_count = sum(lifecycle.request_count for lifecycle in lifecycles)
    error_count = sum(lifecycle.error_count for lifecycle in lifecycles)

    create_values = [value for value in (item.create_ms for item in lifecycles) if value is not None]
    approve_values = [value for value in (item.approve_ms for item in lifecycles) if value is not None]
    fetch_values = [value for value in (item.fetch_ms for item in lifecycles) if value is not None]
    lifecycle_values = [item.latency_ms for item in lifecycles]
    all_request_values = [item.latency_ms for item in requests]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "workflows": args.workflows,
        "concurrency": args.concurrency,
        "warmup_workflows": args.warmup,
        "cold_start_ms": cold_start_ms,
        "steady_state": {
            "wall_seconds": round(wall_seconds, 3),
            "requests": request_count,
            "throughput_rps": round(request_count / wall_seconds, 2),
            "error_rate_percent": round((error_count / request_count) * 100, 2)
            if request_count
            else 0.0,
            "all_requests": summarize(all_request_values),
            "workflow_create": summarize(create_values),
            "workflow_approve": summarize(approve_values),
            "workflow_fetch": summarize(fetch_values),
            "workflow_lifecycle": summarize(lifecycle_values),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:18080")
    parser.add_argument("--workflows", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--cold-start-command", default=None)
    parser.add_argument("--cold-start-timeout", type=float, default=60.0)
    args = parser.parse_args()

    print(json.dumps(run_benchmark(args), indent=2))


if __name__ == "__main__":
    main()
