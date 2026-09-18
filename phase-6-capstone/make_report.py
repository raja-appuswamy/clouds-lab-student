"""Build submission/phase6_report.json in stages, as the capstone progresses (provided).

Each subcommand adds one section; run them in this order (TASKS.md says when):

    python phase-6-capstone/make_report.py terraform    # after `terraform apply`
    python phase-6-capstone/make_report.py loadtest     # after loadtest.py
    python phase-6-capstone/make_report.py k8s          # after the kind rollout
    python phase-6-capstone/make_report.py destroyed    # after `terraform destroy`

`terraform` reads the state (`terraform show -json`) and the outputs — what was created, by
type — and live-checks the service. `k8s` reads the Deployment from kubectl and hits the
Service through localhost:30080 to count the distinct pods that answer. `destroyed` re-reads
the state and records that it is empty: the stack is gone, the data is not.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PHASE_DIR.parent
TF_DIR = PHASE_DIR / "terraform"
REPORT_PATH = REPO_ROOT / "submission" / "phase6_report.json"
LOADTEST_PATH = REPO_ROOT / "submission" / "phase6_loadtest.json"


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"$ {' '.join(cmd)}\n{r.stderr.strip()}", file=sys.stderr)
        raise SystemExit(2)
    return r.stdout


def _get_json(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 0, {"error": str(e)}


def _load() -> dict:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8")) if REPORT_PATH.exists() else {"phase": "7"}


def _save(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(REPO_ROOT)}")


def _tf_state() -> tuple[list[dict], dict]:
    """(managed resources from the state, outputs) via `terraform show -json`."""
    state = json.loads(_run(["terraform", "show", "-json"], cwd=TF_DIR))
    resources: list[dict] = []

    def walk(module: dict) -> None:
        for r in module.get("resources", []):
            if r.get("mode") == "managed":
                resources.append({"type": r["type"], "name": r["name"], "address": r["address"]})
        for child in module.get("child_modules", []):
            walk(child)

    root = state.get("values", {}).get("root_module", {})
    walk(root)
    outputs = {k: v.get("value") for k, v in state.get("values", {}).get("outputs", {}).items()}
    return resources, outputs


# ---------------------------------------------------------------------------- stages -- #
def stage_terraform(report: dict) -> dict:
    resources, outputs = _tf_state()
    by_type = collections.Counter(r["type"] for r in resources)
    chat_url = (outputs.get("chat_url") or "").rstrip("/")
    status, health = _get_json(f"{chat_url}/health") if chat_url else (0, {})
    print(f"terraform state: {len(resources)} managed resources")
    for t, n in sorted(by_type.items()):
        print(f"  {n:>2}  {t}")
    print(f"chat_url: {chat_url}  ->  /health {status} {health}")
    report["project"] = subprocess.run(["gcloud", "config", "get-value", "project"],
                                       capture_output=True, text=True).stdout.strip()
    report["terraform"] = {
        "resource_count": len(resources),
        "resources_by_type": dict(sorted(by_type.items())),
        "outputs": outputs,
        "health": {"status": status, "store": health.get("store"), "instance": health.get("instance")},
    }
    report["chat_url"] = chat_url
    return report


def stage_loadtest(report: dict) -> dict:
    if not LOADTEST_PATH.exists():
        print(f"{LOADTEST_PATH.relative_to(REPO_ROOT)} not found — run loadtest.py first", file=sys.stderr)
        raise SystemExit(2)
    report["loadtest"] = json.loads(LOADTEST_PATH.read_text(encoding="utf-8"))
    lt = report["loadtest"]
    print(f"load test: {lt['requests']} requests, p50 {lt['latency_ms']['p50']} ms, "
          f"p99 {lt['latency_ms']['p99']} ms, errors {lt['errors']}, peak instances {lt.get('max_instances')}")
    return report


def stage_k8s(report: dict, port: int = 30080, probes: int = 20) -> dict:
    dep = json.loads(_run(["kubectl", "get", "deployment", "chat", "-o", "json"]))
    svc = json.loads(_run(["kubectl", "get", "service", "chat", "-o", "json"]))
    pods = json.loads(_run(["kubectl", "get", "pods", "-l", "app=chat", "-o", "json"]))
    revision = int(dep["metadata"].get("annotations", {}).get("deployment.kubernetes.io/revision", "0"))
    image = dep["spec"]["template"]["spec"]["containers"][0]["image"]

    # Through the Service: which pods answer? kube-proxy spreads requests across ready pods.
    seen: collections.Counter = collections.Counter()
    for _ in range(probes):
        status, body = _get_json(f"http://localhost:{port}/health")
        if status == 200:
            seen[body.get("instance")] += 1
    print(f"deployment chat: {dep['status'].get('readyReplicas', 0)}/{dep['spec']['replicas']} ready, "
          f"revision {revision}, image {image}")
    print(f"{probes} requests via the Service reached {len(seen)} distinct pod(s): {dict(seen)}")

    report["k8s"] = {
        "replicas": dep["spec"]["replicas"],
        "ready_replicas": dep["status"].get("readyReplicas", 0),
        "revision": revision,
        "image": image,
        "service_type": svc["spec"].get("type"),
        "node_port": next((p.get("nodePort") for p in svc["spec"].get("ports", [])), None),
        "pods": [p["metadata"]["name"] for p in pods.get("items", [])],
        "probes": probes,
        "distinct_instances": len(seen),
        "instances_seen": dict(seen),
    }
    return report


def stage_destroyed(report: dict) -> dict:
    resources, _ = _tf_state()
    chat_url = report.get("chat_url", "")
    status, _ = _get_json(f"{chat_url}/health") if chat_url else (0, {})
    print(f"terraform state after destroy: {len(resources)} managed resources; "
          f"old chat_url answers HTTP {status} (0 = gone)")
    report["destroyed"] = {"resources_remaining": len(resources), "chat_url_status": status}
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("stage", choices=["terraform", "loadtest", "k8s", "destroyed"])
    a = ap.parse_args(argv)
    report = _load()
    report = {"terraform": stage_terraform, "loadtest": stage_loadtest,
              "k8s": stage_k8s, "destroyed": stage_destroyed}[a.stage](report)
    _save(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
