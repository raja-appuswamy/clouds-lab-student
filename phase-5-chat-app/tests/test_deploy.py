"""Phase 5 deployment tests — live-curl your public Cloud Run chat server.

Reads ``chat_url`` from the report and exercises the real deployment (RAG + generation +
Firestore storage all happen server-side). Runs in your own GitHub Actions — the endpoint is
public HTTP, no GCP credentials needed. Keep it up until graded. (35 points.)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

import pytest

from autograder.points import points

TIMEOUT = 120


def _get(url: str):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, str(e)


def _post_chat(base: str, message: str):
    req = urllib.request.Request(
        base.rstrip("/") + "/chat",
        data=json.dumps({"session_id": f"grade-{uuid.uuid4().hex[:6]}", "message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return 0, {"error": str(e)}


@points(10)
def test_healthz(report):
    status, body = _get(report.get("chat_url", "").rstrip("/") + "/healthz")
    assert status == 200, f"/healthz did not return 200 (got {status})"


@points(25)
def test_chat_responds(report):
    status, body = _post_chat(report["chat_url"], "love and death and the king")
    assert status == 200, f"/chat did not return 200 (got {status}): {body}"
    assert isinstance(body.get("reply"), str) and body["reply"], "empty reply from the model"
    assert isinstance(body.get("retrieved"), list), "response should include a 'retrieved' list"
