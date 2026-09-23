"""Phase 6 report tests — apply, load test, destroy, and the two writeups (public). (50 points.)"""

from __future__ import annotations

from autograder.points import points
from conftest import filled

REQUIRED_TYPES = {
    "google_cloud_run_v2_service", "google_cloud_run_v2_service_iam_member", "google_service_account",
    "google_project_iam_custom_role", "google_bigquery_dataset", "google_bigquery_job",
    "google_monitoring_alert_policy", "google_logging_metric", "google_logging_project_sink",
    "google_bigquery_dataset_iam_member",
}


@points(12)
def test_terraform_apply_recorded(report):
    tf = report.get("terraform", {})
    assert tf.get("resource_count", 0) >= 12, f"expected a full stack (>= 12 managed resources), got {tf.get('resource_count')}"
    missing = REQUIRED_TYPES - set(tf.get("resources_by_type", {}))
    assert not missing, f"state is missing resource types: {sorted(missing)}"
    assert ".run.app" in tf.get("outputs", {}).get("chat_url", ""), "no chat_url output recorded"
    assert tf.get("health", {}).get("status") == 200 and tf["health"].get("store") == "firestore", (
        "right after apply, /health should answer 200 with store=firestore")


@points(18)
def test_load_test_shows_elasticity(report):
    lt = report.get("loadtest", {})
    assert lt.get("requests", 0) >= 500, f"load test too small ({lt.get('requests')} requests) — run >= 500"
    assert lt.get("error_rate", 1) <= 0.05, f"error rate {lt.get('error_rate')} > 5% — the service fell over"
    lat = lt.get("latency_ms", {})
    assert 0 < lat.get("p50", 0) <= lat.get("p95", 0) <= lat.get("p99", 0), f"latency percentiles look wrong: {lat}"
    assert (lt.get("max_instances") or 0) >= 2, (
        f"peak instance count during the test was {lt.get('max_instances')} — the service did not scale out. "
        "Check max_instance_request_concurrency in main.tf and that loadtest.py waited for Monitoring.")


@points(10)
def test_stack_destroyed(report):
    d = report.get("destroyed")
    assert d, "no destroy recorded — run `terraform destroy`, then make_report.py destroyed (Task 8)"
    assert d.get("resources_remaining") == 0, f"{d.get('resources_remaining')} resources still in state after destroy"
    assert d.get("chat_url_status") in (0, 404), f"the destroyed service still answers HTTP {d.get('chat_url_status')}"


@points(5)
def test_supervision_log_complete(supervision):
    """submission/phase6_supervision.md: every slot filled, >= 4 approvals including a refusal."""
    assert supervision, "submission/phase6_supervision.md not found — copy supervision_template.md there (Task 8)"
    for slot in ("agent_tool", "agent_identity", "boundary_rationale", "approvals", "refusal",
                 "iam_403", "agent_mistake", "by_hand", "trust_boundary"):
        assert filled(supervision, slot), f"supervision log slot {slot!r} is still TODO"
    rows = [ln for ln in supervision["approvals"].splitlines()
            if ln.strip().startswith("|") and not ln.strip().startswith("|--") and "TODO" not in ln
            and not ln.strip().startswith("| #")]
    assert len(rows) >= 4, f"the approvals table needs at least 4 filled rows, found {len(rows)}"
    decisions = " ".join(rows).lower()
    assert " no " in decisions or "| no" in decisions or "refused" in decisions or "denied" in decisions, (
        "at least one approval row must be a refusal (Decision = no)")


@points(5)
def test_review_complete(review):
    """submission/phase6_review.md: three faults, each with where / what / fix, and a verdict."""
    assert review, "submission/phase6_review.md not found — copy review_template.md there (Task 7)"
    for letter in "abc":
        for part in ("where", "what", "fix"):
            assert filled(review, f"fault_{letter}_{part}"), f"review slot fault_{letter}_{part} is still TODO"
    assert filled(review, "verdict"), "review verdict is still TODO"
