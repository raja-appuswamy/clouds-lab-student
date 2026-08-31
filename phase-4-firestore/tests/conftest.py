"""Test fixtures + import path setup for Phase 4."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-4-firestore/
REPO_ROOT = PHASE_DIR.parent
REPORT_PATH = REPO_ROOT / "submission" / "phase4_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase4_report.json (written by run_phase4.py against real Firestore)."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase4_report.json not found — run "
            "`python phase-4-firestore/run_phase4.py` (in Cloud Shell) first. See TASKS.md."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase4_report.json is not valid JSON: {exc}")
