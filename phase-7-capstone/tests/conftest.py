"""Test fixtures + import path setup for Phase 7."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-7-capstone/
REPO_ROOT = PHASE_DIR.parent
TF_DIR = PHASE_DIR / "terraform"
K8S_DIR = PHASE_DIR / "k8s"
REPORT_PATH = REPO_ROOT / "submission" / "phase7_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _clean(v):
    """python-hcl2 keeps HCL's quotes on string literals and keys in some versions; drop them."""
    if isinstance(v, str):
        return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v
    if isinstance(v, dict):
        return {_clean(k): _clean(x) for k, x in v.items() if k != "__comments__"}
    if isinstance(v, list):
        return [_clean(x) for x in v]
    return v


@pytest.fixture(scope="session")
def tf() -> dict:
    """All resources across the phase's .tf files: {(type, name): body}."""
    import hcl2

    resources: dict[tuple[str, str], dict] = {}
    for path in sorted(TF_DIR.glob("*.tf")):
        with path.open(encoding="utf-8") as f:
            doc = _clean(hcl2.load(f))
        for block in doc.get("resource", []):
            for rtype, named in block.items():
                for name, body in named.items():
                    resources[(rtype, name)] = body
    return resources


@pytest.fixture(scope="session")
def deployment() -> dict:
    import yaml

    return yaml.safe_load((K8S_DIR / "deployment.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase7_report.json (built stage by stage by make_report.py)."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase7_report.json not found — run the make_report.py stages "
            "(terraform, loadtest, k8s, destroyed) as TASKS.md describes."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase7_report.json is not valid JSON: {exc}")
