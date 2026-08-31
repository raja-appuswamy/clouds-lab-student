"""Test fixtures + import path setup for Phase 0.

Ensures both the repo root (for the shared ``autograder`` package) and the phase
directory (for ``verify_setup``) are importable regardless of the working directory,
and exposes the student's submission report as a fixture.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-0-setup/
REPO_ROOT = PHASE_DIR.parent                           # repo root
REPORT_PATH = REPO_ROOT / "submission" / "phase0_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase0_report.json, or fail the test if it is missing/invalid."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase0_report.json not found — run "
            "`python phase-0-setup/verify_setup.py` from the repo root first."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase0_report.json is not valid JSON: {exc}")
