"""Phase 6 offline tests — the stack as code, read statically (no cloud, no terraform binary).

These parse your ``terraform/*.tf`` files and check that the TODO blocks
declare what Phases 4-5 deployed by hand. Run while editing:

    python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q

(25 points: 20 for the stack as code, 5 for the agent's approval boundary.)
"""

from __future__ import annotations

from autograder.points import points


def _env(service: dict) -> dict[str, str]:
    tmpl = service["template"][0]
    container = tmpl["containers"][0]
    return {e["name"]: e["value"] for e in container.get("env", [])}


# ------------------------------------ Cloud Run service (8) ------------------------------------ #
@points(6)
def test_service_env_and_image(tf):
    svc = tf[("google_cloud_run_v2_service", "chat")]
    tmpl = svc["template"][0]
    assert tmpl.get("containers"), "the service template declares no container"
    assert "var.image" in tmpl["containers"][0]["image"], "the container image should come from var.image"
    env = _env(svc)
    assert "local.model_url" in env.get("MODEL_URL", ""), "MODEL_URL should be local.model_url (the Phase-2 artifact)"
    assert "local.bq_table" in env.get("BQ_TABLE", ""), "BQ_TABLE should be local.bq_table (the table this stack rebuilds)"
    assert env.get("STORE_BACKEND") == "firestore", "STORE_BACKEND must be firestore — this is the Phase-5 image"


@points(4)
def test_service_scaling_is_free_tier_safe_and_scales_out(tf):
    tmpl = tf[("google_cloud_run_v2_service", "chat")]["template"][0]
    scaling = tmpl.get("scaling", [{}])[0]
    assert scaling.get("min_instance_count") == 0, "min_instance_count must be 0 (idle = free)"
    assert 2 <= scaling.get("max_instance_count", 0) <= 3, "max_instance_count should be 2-3: enough to scale out, capped for cost"
    conc = tmpl.get("max_instance_request_concurrency")
    assert conc is not None and conc <= 10, (
        "set max_instance_request_concurrency small (<= 10) so the load test forces scale-out; "
        f"got {conc}")


# ----------------------------------------- IAM (3) ----------------------------------------------- #
@points(4)
def test_custom_role_is_least_privilege(tf):
    role = tf[("google_project_iam_custom_role", "chat_bq_reader")]
    perms = set(role.get("permissions", []))
    assert perms == {"bigquery.tables.get", "bigquery.tables.getData"}, (
        f"the custom role should grant exactly the two table-read permissions, got {sorted(perms)}")


# -------------------------------------- monitoring (4) ------------------------------------------- #
@points(3)
def test_alert_policy_watches_5xx_for_this_service(tf):
    policy = tf[("google_monitoring_alert_policy", "chat_5xx")]
    cond = policy["conditions"][0]["condition_threshold"][0]
    f = cond.get("filter", "")
    assert "run.googleapis.com/request_count" in f, "alert filter should watch run.googleapis.com/request_count"
    assert "response_code_class" in f and "5xx" in f, "alert filter should restrict to 5xx responses"
    assert "var.service_name" in f, "alert filter should be scoped to resource.labels.service_name = var.service_name"
    assert cond.get("comparison") == "COMPARISON_GT" and cond.get("threshold_value") is not None, "set comparison + threshold"
    assert cond.get("duration"), "set a duration so a single blip does not page you"
    agg = cond.get("aggregations", [{}])[0]
    assert agg.get("per_series_aligner") == "ALIGN_RATE", "align request_count as a RATE — a raw count is meaningless across intervals"


@points(3)
def test_log_sink_is_scoped_and_has_its_own_identity(tf):
    sink = tf[("google_logging_project_sink", "requests_to_bq")]
    f = sink.get("filter", "")
    assert "cloud_run_revision" in f and "var.service_name" in f, "sink filter should be scoped to this service"
    assert "run.googleapis.com%2Frequests" in f, "sink filter should select the request log (run.googleapis.com%2Frequests)"
    assert sink.get("unique_writer_identity") is True, "unique_writer_identity = true, or the dataset IAM binding has nothing to bind"
    assert "bigquery.googleapis.com" in sink.get("destination", ""), "destination should be a BigQuery dataset"
    # The binding that lets the sink write — provided, but it must still reference the sink.
    member = tf[("google_bigquery_dataset_iam_member", "sink_writer")]["member"]
    assert "requests_to_bq.writer_identity" in member


# ------------------------------ the agent's approval boundary (5) ------------------------------ #
def _matches(patterns: list[str], command: str) -> bool:
    """Does any policy pattern cover this command? '*' matches one word (gcloud * delete)."""
    import fnmatch
    return any(fnmatch.fnmatch(command, f"{pat}*") or fnmatch.fnmatch(command, pat) for pat in patterns)


@points(5)
def test_agent_policy_boundary(policy):
    """agent/policy.json: destructive commands forbidden, state-changing ones need approval."""
    auto, confirm, forbidden = policy.get("auto", []), policy.get("confirm", []), policy.get("forbidden", [])
    for cmd in ("terraform destroy", "gcloud run services delete chat", "rm -rf x"):
        assert _matches(forbidden, cmd), f"{cmd!r} must be in `forbidden` — the agent may never run it"
        assert not _matches(auto, cmd), f"{cmd!r} is in `auto`; it must be forbidden"
    for cmd in ("terraform apply", "gcloud run services update chat"):
        assert _matches(confirm, cmd) or _matches(forbidden, cmd), f"{cmd!r} changes cloud state: it needs approval"
        assert not _matches(auto, cmd), f"{cmd!r} is auto-allowed; state changes need your approval"
    for cmd in ("terraform plan", "gcloud run services list"):
        assert _matches(auto, cmd), f"{cmd!r} is read-only and should be auto-allowed, or the agent cannot work"
