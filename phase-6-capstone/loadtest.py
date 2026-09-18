"""Load test the Terraform-managed chat service and watch it scale (provided).

    python phase-6-capstone/loadtest.py --url https://chat-tf-xxx.run.app --clients 20 --seconds 120

`clients` threads each loop for `seconds`, hitting the two cheap endpoints (``/health`` and
``/sessions/<id>/messages``) plus one ``/chat`` every 25 requests, so the service does real
work without burning through the model's inference budget. Every request's latency and status
are recorded.

Then the script asks **Cloud Monitoring** what Cloud Run did about it: the maximum value of
``run.googleapis.com/container/instance_count`` for the service over the test window. With
``max_instance_request_concurrency = 5`` in main.tf and 20 concurrent clients, you should see
it climb to the ``max_instance_count`` you set — that is elasticity, measured rather than
asserted. Monitoring data lags by a minute or two, so the script waits before querying.

Writes ``submission/phase6_loadtest.json``; make_report.py folds it into the report.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "submission" / "phase6_loadtest.json"


def _one(url: str, body: dict | None = None) -> tuple[int, float]:
    """Return (status, seconds). Status 0 = could not connect."""
    t0 = time.perf_counter()
    try:
        if body is None:
            req = urllib.request.Request(url)
        else:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            r.read()
            return r.status, time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        return e.code, time.perf_counter() - t0
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, time.perf_counter() - t0


def _client(base: str, deadline: float, out: list, lock: threading.Lock, cid: int) -> None:
    session = f"load-{cid}-{uuid.uuid4().hex[:4]}"
    i = 0
    while time.time() < deadline:
        if i % 25 == 0:
            status, dt = _one(f"{base}/chat", {"session_id": session, "message": "the king and his crown"})
            kind = "chat"
        elif i % 2 == 0:
            status, dt = _one(f"{base}/health")
            kind = "health"
        else:
            status, dt = _one(f"{base}/sessions/{session}/messages")
            kind = "history"
        with lock:
            out.append((kind, status, dt))
        i += 1


def _percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))
    return xs[k]


def max_instances(project: str, service: str, start: datetime, end: datetime) -> int | None:
    """Max of run.googleapis.com/container/instance_count for the service over [start, end]."""
    try:
        from google.cloud import monitoring_v3
    except ImportError:
        print("google-cloud-monitoring not installed — skipping the instance-count query", flush=True)
        return None
    client = monitoring_v3.MetricServiceClient()
    interval = monitoring_v3.TimeInterval(
        start_time={"seconds": int(start.timestamp())}, end_time={"seconds": int(end.timestamp())})
    agg = monitoring_v3.Aggregation(
        alignment_period={"seconds": 60},
        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MAX,
        cross_series_reducer=monitoring_v3.Aggregation.Reducer.REDUCE_SUM,   # active + idle states
        group_by_fields=["resource.labels.service_name"],
    )
    series = client.list_time_series(request={
        "name": f"projects/{project}",
        "filter": (f'metric.type = "run.googleapis.com/container/instance_count" '
                   f'AND resource.labels.service_name = "{service}"'),
        "interval": interval,
        "aggregation": agg,
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    })
    peak = 0
    for ts in series:
        for pt in ts.points:
            peak = max(peak, int(pt.value.int64_value or pt.value.double_value or 0))
    return peak


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", required=True, help="Terraform output chat_url")
    ap.add_argument("--clients", type=int, default=20)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--service", default="chat-tf", help="Cloud Run service name (var.service_name)")
    ap.add_argument("--settle", type=int, default=120, help="seconds to wait for Monitoring before querying")
    a = ap.parse_args(argv)
    base = a.url.rstrip("/")
    project = subprocess.run(["gcloud", "config", "get-value", "project"],
                             capture_output=True, text=True).stdout.strip()

    print(f"load test: {a.clients} clients x {a.seconds}s against {base}", flush=True)
    results: list = []
    lock = threading.Lock()
    start = datetime.now(timezone.utc)
    deadline = time.time() + a.seconds
    threads = [threading.Thread(target=_client, args=(base, deadline, results, lock, i), daemon=True)
               for i in range(a.clients)]
    for t in threads:
        t.start()
    while any(t.is_alive() for t in threads):
        time.sleep(5)
        with lock:
            n = len(results)
        print(f"  {n} requests so far", flush=True)
    end = datetime.now(timezone.utc)

    lat = {k: [dt for kind, s, dt in results if kind == k and s == 200] for k in ("health", "history", "chat")}
    all_ok = [dt for _, s, dt in results if s == 200]
    errors = sum(1 for _, s, _ in results if s != 200)
    summary = {
        "url": base, "service": a.service, "project": project,
        "clients": a.clients, "seconds": a.seconds,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "requests": len(results), "errors": errors,
        "error_rate": round(errors / max(1, len(results)), 4),
        "throughput_rps": round(len(results) / max(1, (end - start).total_seconds()), 1),
        "latency_ms": {
            "p50": round(_percentile(all_ok, 50) * 1000, 1),
            "p95": round(_percentile(all_ok, 95) * 1000, 1),
            "p99": round(_percentile(all_ok, 99) * 1000, 1),
            "max": round(max(all_ok) * 1000, 1) if all_ok else 0,
        },
        "by_endpoint": {k: {"n": len(v), "p50_ms": round(_percentile(v, 50) * 1000, 1),
                            "p99_ms": round(_percentile(v, 99) * 1000, 1)} for k, v in lat.items()},
    }
    print(json.dumps({k: summary[k] for k in ("requests", "errors", "throughput_rps", "latency_ms")}, indent=2))

    print(f"waiting {a.settle}s for Cloud Monitoring to catch up, then reading instance_count...", flush=True)
    time.sleep(a.settle)
    peak = max_instances(project, a.service, start - timedelta(minutes=1), datetime.now(timezone.utc))
    summary["max_instances"] = peak
    print(f"peak instances during the test: {peak}  (max_instance_count in main.tf caps this)")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
