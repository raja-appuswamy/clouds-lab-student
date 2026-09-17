"""Phase 5 deployment tests — persistence, proven through your public chat URL.

``run_phase5.py`` wrote a session straight into Firestore from Cloud Shell. These tests ask a
Cloud Run container — a different process, possibly started long after — to read it back over
public HTTP, then chat once and check the turns landed too. That is exactly what Phase 4's
in-memory store could not do. No GCP credentials needed. Keep the service up until graded.
(30 points.)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

from autograder.points import points

TIMEOUT = 120


def _get_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return 0, {"error": str(e)}


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


@points(5)
def test_service_is_on_firestore(report):
    status, body = _get_json(report.get("chat_url", "").rstrip("/") + "/health")
    assert status == 200, f"/health did not return 200 (got {status})"
    assert body.get("store") == "firestore", (
        f"the service reports store={body.get('store')!r} — redeploy with STORE_BACKEND=firestore")


@points(15)
def test_session_written_elsewhere_is_readable(report):
    """What Cloud Shell wrote, Cloud Run reads: the store outlives any one process."""
    proof = report.get("proof", {})
    sid, texts = proof.get("session_id"), proof.get("message_texts", [])
    assert sid and texts, "report has no proof session — run run_phase5.py"
    status, hist = _get_json(f"{report['chat_url'].rstrip('/')}/sessions/{sid}/messages")
    assert status == 200, f"/sessions/{sid}/messages returned {status} — the session is not visible to the service"
    seen = {m.get("text") for m in hist.get("messages", [])}
    missing = [t for t in texts if t not in seen]
    assert not missing, f"{len(missing)} of the messages written from Cloud Shell are missing: {missing[:2]}"


@points(10)
def test_chat_turns_persist(report):
    """A fresh session: chat twice, read back four messages (2 user + 2 assistant)."""
    base = report["chat_url"]
    session = f"grade-{uuid.uuid4().hex[:6]}"
    for msg in ("first question", "second question"):
        status, body = _post_chat(base, session, msg)
        assert status == 200, f"/chat failed (got {status}): {body}"
        assert body.get("store") == "firestore", f"chat reply says store={body.get('store')!r}"
    status, hist = _get_json(f"{base.rstrip('/')}/sessions/{session}/messages")
    assert status == 200 and hist.get("message_count") == 4, (
        f"expected message_count 4 after two chats, got {hist.get('message_count')} (HTTP {status})")
    roles = [m.get("role") for m in hist.get("messages", [])]
    assert roles.count("user") == 2 and roles.count("assistant") == 2, f"roles stored: {roles}"
