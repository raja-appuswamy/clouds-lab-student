"""Phase 1 deployment tests — live-curl your three public endpoints.

These read the URLs from ``submission/phase1_report.json`` and hit each deployment with
a fresh random nonce, asserting it echoes back — so a passing test means that endpoint is
really up and running YOUR echo bot. They run in your own GitHub Actions (no GCP
credentials needed — the endpoints are public HTTP).

Each deployment is checked **twice**: once with ``GET /echo?msg=<nonce>`` (the query-string
branch of ``extract_message``) and once with ``POST /echo`` carrying ``{"message": <nonce>}``
(the JSON-body branch). Both branches ship in every deployment, so both are graded there.

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


def _read_echo(req: urllib.request.Request | str, nonce: str, what: str) -> tuple[bool, str]:
    """Send ``req``, parse the JSON body, and check it echoed ``nonce`` back."""
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:120] if exc.fp else ""
        return False, f"HTTP {exc.code} from {what} {detail!r}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"could not reach {what}: {exc}"
    try:
        got = json.loads(body).get("echo")
    except json.JSONDecodeError:
        return False, f"non-JSON response from {what}: {body[:120]!r}"
    return got == nonce, f"sent {nonce!r}, got echo={got!r}"


def _live_echo_get(base: str) -> tuple[bool, str]:
    """GET {base}/echo?msg=<nonce> — the query-string branch."""
    if not base:
        return False, "no URL recorded in report"
    nonce = uuid.uuid4().hex[:8]
    url = f"{base.rstrip('/')}/echo?msg={nonce}"
    return _read_echo(url, nonce, url)


def _live_echo_post(base: str) -> tuple[bool, str]:
    """POST {base}/echo with {"message": <nonce>} — the JSON-body branch.

    The Content-Type header is required: the route uses ``request.get_json(silent=True)``,
    which returns None without it, and the service then answers 400.
    """
    if not base:
        return False, "no URL recorded in report"
    nonce = uuid.uuid4().hex[:8]
    url = f"{base.rstrip('/')}/echo"
    req = urllib.request.Request(
        url,
        data=json.dumps({"message": nonce}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return _read_echo(req, nonce, f"POST {url}")


def _platform(report: dict, name: str) -> dict:
    plat = report.get("platforms", {}).get(name)
    if not plat:
        pytest.fail(f"no '{name}' entry in phase1_report.json — did you pass --{name} to measure.py?")
    return plat


# ------------------------------- IaaS VM (10) -------------------------------- #
@points(5)
def test_vm_echoes_get(report):
    ok, detail = _live_echo_get(_platform(report, "vm")["url"])
    assert ok, f"IaaS VM did not echo a GET: {detail}"


@points(5)
def test_vm_echoes_post(report):
    ok, detail = _live_echo_post(_platform(report, "vm")["url"])
    assert ok, f"IaaS VM did not echo a JSON POST: {detail}"


# ------------------------------ Cloud Run (10) ------------------------------- #
@points(5)
def test_cloudrun_echoes_get(report):
    ok, detail = _live_echo_get(_platform(report, "cloudrun")["url"])
    assert ok, f"Cloud Run did not echo a GET: {detail}"


@points(5)
def test_cloudrun_echoes_post(report):
    ok, detail = _live_echo_post(_platform(report, "cloudrun")["url"])
    assert ok, f"Cloud Run did not echo a JSON POST: {detail}"


# --------------------------- Cloud Function (10) ----------------------------- #
@points(5)
def test_function_echoes_get(report):
    ok, detail = _live_echo_get(_platform(report, "function")["url"])
    assert ok, f"Cloud Function did not echo a GET: {detail}"


@points(5)
def test_function_echoes_post(report):
    ok, detail = _live_echo_post(_platform(report, "function")["url"])
    assert ok, f"Cloud Function did not echo a JSON POST: {detail}"


# ------------------------------ measurements (10) ---------------------------- #
@points(10)
def test_measurements_recorded(report):
    for name in ("vm", "cloudrun", "function"):
        plat = _platform(report, name)
        assert isinstance(plat.get("cold_ms"), (int, float)), f"{name}: no cold_ms measurement"
        assert plat.get("warm_ms"), f"{name}: no warm_ms samples — re-run measure.py without --cold-only"
