"""Test fixtures + import path setup for Phase 6."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-6-coordination/
REPO_ROOT = PHASE_DIR.parent
REPORT_PATH = REPO_ROOT / "submission" / "phase6_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase6_report.json (written by run_phase6.py against real GCP)."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase6_report.json not found — run "
            "`python phase-6-coordination/run_phase6.py` (in Cloud Shell) first. See TASKS.md."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase6_report.json is not valid JSON: {exc}")
