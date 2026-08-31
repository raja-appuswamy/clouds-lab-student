"""Phase 1 deployment tests — live-curl your three public endpoints.

These read the URLs from ``submission/phase1_report.json`` and hit each deployment with
a fresh random nonce, asserting it echoes back — so a passing test means that endpoint is
really up and running YOUR echo bot. They run in your own GitHub Actions (no GCP
credentials needed — the endpoints are public HTTP).

Run after deploying + measuring:

    python -m pytest phase-1-echo-bot/tests/test_deploy.py -p autograder.points -q

Requires the three targets to be reachable, so keep them up until you are graded. (40 points.)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

import pytest

from autograder.points import points

TIMEOUT = 30


def _live_echo(base: str) -> tuple[bool, str]:
    """GET {base}/echo?msg=<nonce>; return (echoed_ok, detail)."""
    if not base:
        return False, "no URL recorded in report"
    nonce = uuid.uuid4().hex[:8]
    url = f"{base.rstrip('/')}/echo?msg={nonce}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code} from {url}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"could not reach {url}: {exc}"
    try:
        got = json.loads(body).get("echo")
    except json.JSONDecodeError:
        return False, f"non-JSON response from {url}: {body[:120]!r}"
    return got == nonce, f"sent {nonce!r}, got echo={got!r}"


def _platform(report: dict, name: str) -> dict:
    plat = report.get("platforms", {}).get(name)
    if not plat:
        pytest.fail(f"no '{name}' entry in phase1_report.json — did you pass --{name} to measure.py?")
    return plat


@points(10)
def test_vm_echoes(report):
    ok, detail = _live_echo(_platform(report, "vm")["url"])
    assert ok, f"IaaS VM did not echo: {detail}"


@points(10)
def test_cloudrun_echoes(report):
    ok, detail = _live_echo(_platform(report, "cloudrun")["url"])
    assert ok, f"Cloud Run did not echo: {detail}"


@points(10)
def test_function_echoes(report):
    ok, detail = _live_echo(_platform(report, "function")["url"])
    assert ok, f"Cloud Function did not echo: {detail}"


@points(10)
def test_measurements_recorded(report):
    for name in ("vm", "cloudrun", "function"):
        plat = _platform(report, name)
        assert isinstance(plat.get("cold_ms"), (int, float)), f"{name}: no cold_ms measurement"
        assert plat.get("warm_ms"), f"{name}: no warm_ms samples — re-run measure.py without --cold-only"
