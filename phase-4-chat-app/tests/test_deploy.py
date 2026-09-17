"""Phase 4 deployment tests — live-curl your public Cloud Run chat server.

Reads ``chat_url`` from the report and exercises the real deployment (RAG + generation happen
server-side). Runs in your own GitHub Actions — the endpoint is public HTTP, no GCP
credentials needed. Keep it up until graded. (35 points.)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

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


def _post_chat(base: str, session_id: str, message: str):
    req = urllib.request.Request(
        base.rstrip("/") + "/chat",
        data=json.dumps({"session_id": session_id, "message": message}).encode(),
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
def test_health(report):
    status, body = _get(report.get("chat_url", "").rstrip("/") + "/health")
    assert status == 200, f"/health did not return 200 (got {status})"


@points(20)
def test_chat_responds(report):
    status, body = _post_chat(report["chat_url"], f"grade-{uuid.uuid4().hex[:6]}", "love and death and the king")
    assert status == 200, f"/chat did not return 200 (got {status}): {body}"
    assert isinstance(body.get("reply"), str) and body["reply"], "empty reply from the model"
    assert isinstance(body.get("retrieved"), list), "response should include a 'retrieved' list"


@points(5)
def test_history_reads_back(report):
    """Two turns in, two turns (x2 roles) out — from whichever instance answers."""
    base = report["chat_url"]
    session = f"grade-{uuid.uuid4().hex[:6]}"
    for msg in ("first question", "second question"):
        status, _ = _post_chat(base, session, msg)
        assert status == 200, f"/chat failed while seeding the session (got {status})"
    status, body = _get(f"{base.rstrip('/')}/sessions/{session}/messages")
    assert status == 200, f"/sessions/<id>/messages did not return 200 (got {status})"
    data = json.loads(body)
    assert data.get("message_count", 0) >= 4, (
        f"expected at least 4 stored messages (2 user + 2 assistant), got {data.get('message_count')}")
    assert all("role" in m and "text" in m for m in data.get("messages", [])), "messages need role + text"
