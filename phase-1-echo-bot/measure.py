#!/usr/bin/env python3
"""Measure your three deployments and write the Phase 1 submission report.

Provided for you — no TODOs. After you have deployed the echo bot to all three targets
(IaaS VM, Cloud Run, Cloud Function), run:

    python phase-1-echo-bot/measure.py \\
        --vm       http://<VM_EXTERNAL_IP>:8080 \\
        --cloudrun https://<service>-<hash>-<region>.run.app \\
        --function https://<region>-<project>.cloudfunctions.net/echo

For each URL it: (1) checks correctness by echoing a random nonce, (2) times a first
request (an approximate *cold* start) and a burst of *warm* requests, and (3) writes
``submission/phase1_report.json`` plus a short summary + ASCII latency chart.

Note on cold starts: a true cold start needs the instance to have scaled to zero (Cloud
Run/Functions with min-instances=0 do this after ~15 min idle). For an honest cold
number, leave the service idle first, then run with ``--cold-only``. Otherwise the "cold"
sample is just the first request and may already be warm — discuss this in your report.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase1_report.json"
TIMEOUT = 30


def _get(url: str) -> tuple[int, str, float]:
    """GET url; return (status, body, elapsed_ms). status 0 on network error."""
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace")
            elapsed = (time.perf_counter() - start) * 1000.0
            return resp.status, body, elapsed
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), (time.perf_counter() - start) * 1000.0
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, "", (time.perf_counter() - start) * 1000.0


def _echo_url(base: str, msg: str) -> str:
    return f"{base.rstrip('/')}/echo?msg={msg}"


def probe(base: str, warm: int, cold_only: bool) -> dict:
    """Probe one deployment: correctness + cold + warm latencies."""
    nonce = uuid.uuid4().hex[:8]
    status, body, cold_ms = _get(_echo_url(base, nonce))

    echo_ok = False
    if status == 200:
        try:
            echo_ok = json.loads(body).get("echo") == nonce
        except json.JSONDecodeError:
            echo_ok = False

    warm_ms: list[float] = []
    if not cold_only:
        for _ in range(warm):
            s, _b, ms = _get(_echo_url(base, uuid.uuid4().hex[:8]))
            if s == 200:
                warm_ms.append(round(ms, 1))

    stats = {}
    if warm_ms:
        stats = {
            "min": round(min(warm_ms), 1),
            "median": round(statistics.median(warm_ms), 1),
            "p95": round(sorted(warm_ms)[max(0, int(len(warm_ms) * 0.95) - 1)], 1),
            "max": round(max(warm_ms), 1),
        }

    return {
        "url": base,
        "echo_ok": echo_ok,
        "status": status,
        "cold_ms": round(cold_ms, 1),
        "warm_ms": warm_ms,
        "stats": stats,
    }


def _ascii_bar(value: float, scale: float, width: int = 40) -> str:
    n = int(round((value / scale) * width)) if scale > 0 else 0
    return "#" * min(n, width)


def _print_summary(platforms: dict) -> None:
    print("\nPhase 1 — deployment measurements")
    print("-" * 60)
    medians = [p["stats"].get("median", 0) for p in platforms.values() if p["stats"]]
    scale = max(medians) if medians else 1.0
    for name, p in platforms.items():
        ok = "OK  " if p["echo_ok"] else "FAIL"
        med = p["stats"].get("median")
        cold = p["cold_ms"]
        print(f"[{ok}] {name:<9} cold={cold:>7.1f}ms  warm_median="
              f"{(str(med) + 'ms') if med is not None else 'n/a':>9}")
        if med is not None:
            print(f"            {_ascii_bar(med, scale)}")
    print("-" * 60)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vm", help="IaaS VM base URL, e.g. http://34.x.x.x:8080")
    ap.add_argument("--cloudrun", help="Cloud Run base URL (https://...run.app)")
    ap.add_argument("--function", help="Cloud Function base URL")
    ap.add_argument("--warm", type=int, default=20, help="number of warm requests (default 20)")
    ap.add_argument("--cold-only", action="store_true", help="only the cold request; skip warm burst")
    args = ap.parse_args(argv)

    targets = {"vm": args.vm, "cloudrun": args.cloudrun, "function": args.function}
    given = {k: v for k, v in targets.items() if v}
    if not given:
        ap.error("provide at least one of --vm/--cloudrun/--function")

    for name in ("vm", "cloudrun", "function"):
        if not targets[name]:
            print(f"warning: no --{name} URL given; it will be missing from the report.")

    platforms = {name: probe(base, args.warm, args.cold_only) for name, base in given.items()}
    _print_summary(platforms)

    try:
        import os

        cloud_shell = os.environ.get("CLOUD_SHELL") == "true"
    except Exception:
        cloud_shell = False

    report = {"phase": "1", "environment": {"cloud_shell": cloud_shell}, "platforms": platforms}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
