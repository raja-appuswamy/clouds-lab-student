"""Phase 6 live tests — the Terraform-managed service, while it is up.

Reads ``chat_url`` (Terraform's output, recorded by ``make_report.py terraform``) and curls it.
These run in your CI **between** `terraform apply` and `terraform destroy` — once you have
destroyed the stack (Task 11) they will fail, by design: the last push before destroy is the
one that should be green here, and the report tests cover the destroy. (10 points.)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

import pytest

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


def _skip_if_destroyed(report):
    if report.get("destroyed", {}).get("resources_remaining") == 0:
        pytest.skip("stack already destroyed (Task 11) — live checks no longer apply")


@points(3)
def test_terraform_service_is_up_on_firestore(report):
    _skip_if_destroyed(report)
    status, body = _get_json(report.get("chat_url", "").rstrip("/") + "/health")
    assert status == 200, f"/health on the Terraform-managed service returned {status}"
    assert body.get("store") == "firestore", f"service reports store={body.get('store')!r}; the env in main.tf is wrong"


@points(7)
def test_terraform_service_chats(report):
    _skip_if_destroyed(report)
    base = report["chat_url"].rstrip("/")
    req = urllib.request.Request(
        base + "/chat",
        data=json.dumps({"session_id": f"grade-{uuid.uuid4().hex[:6]}", "message": "love and the king"}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            status, body = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        status, body = e.code, {}
    assert status == 200, (f"/chat returned {status} — the service account lacks a role, or the rebuilt "
                           f"BigQuery table is missing (check `terraform apply` output)")
    assert body.get("reply") and isinstance(body.get("retrieved"), list), "no reply / retrieved docs"
