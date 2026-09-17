"""Phase 7 report tests — apply, load test, Kubernetes, destroy (public). (50 points.)"""

from __future__ import annotations

from autograder.points import points

REQUIRED_TYPES = {
    "google_cloud_run_v2_service", "google_cloud_run_v2_service_iam_member", "google_service_account",
    "google_project_iam_custom_role", "google_bigquery_dataset", "google_bigquery_job",
    "google_monitoring_alert_policy", "google_logging_metric", "google_logging_project_sink",
    "google_bigquery_dataset_iam_member",
}


@points(10)
def test_terraform_apply_recorded(report):
    tf = report.get("terraform", {})
    assert tf.get("resource_count", 0) >= 12, f"expected a full stack (>= 12 managed resources), got {tf.get('resource_count')}"
    missing = REQUIRED_TYPES - set(tf.get("resources_by_type", {}))
    assert not missing, f"state is missing resource types: {sorted(missing)}"
    assert ".run.app" in tf.get("outputs", {}).get("chat_url", ""), "no chat_url output recorded"
    assert tf.get("health", {}).get("status") == 200 and tf["health"].get("store") == "firestore", (
        "right after apply, /health should answer 200 with store=firestore")


@points(15)
def test_load_test_shows_elasticity(report):
    lt = report.get("loadtest", {})
    assert lt.get("requests", 0) >= 500, f"load test too small ({lt.get('requests')} requests) — run >= 500"
    assert lt.get("error_rate", 1) <= 0.05, f"error rate {lt.get('error_rate')} > 5% — the service fell over"
    lat = lt.get("latency_ms", {})
    assert 0 < lat.get("p50", 0) <= lat.get("p95", 0) <= lat.get("p99", 0), f"latency percentiles look wrong: {lat}"
    assert (lt.get("max_instances") or 0) >= 2, (
        f"peak instance count during the test was {lt.get('max_instances')} — the service did not scale out. "
        "Check max_instance_request_concurrency in main.tf and that loadtest.py waited for Monitoring.")


@points(15)
def test_kubernetes_rollout(report):
    k = report.get("k8s", {})
    assert k.get("replicas", 0) >= 2 and k.get("ready_replicas", 0) == k.get("replicas"), (
        f"deployment not fully ready: {k.get('ready_replicas')}/{k.get('replicas')}")
    assert k.get("revision", 0) >= 2, "deployment revision < 2 — do the rolling update (Task 9)"
    assert k.get("service_type") == "NodePort" and k.get("node_port") == 30080, "Service should be NodePort 30080"
    assert k.get("distinct_instances", 0) >= 2, (
        f"{k.get('probes')} requests through the Service reached only {k.get('distinct_instances')} pod — "
        "were both replicas ready when make_report.py k8s ran?")
    assert "PLACEHOLDER" not in k.get("image", "PLACEHOLDER"), "deployment.yaml still has the image placeholder"


@points(10)
def test_stack_destroyed(report):
    d = report.get("destroyed")
    assert d, "no destroy recorded — run `terraform destroy`, then make_report.py destroyed (Task 11)"
    assert d.get("resources_remaining") == 0, f"{d.get('resources_remaining')} resources still in state after destroy"
    assert d.get("chat_url_status") in (0, 404), f"the destroyed service still answers HTTP {d.get('chat_url_status')}"
