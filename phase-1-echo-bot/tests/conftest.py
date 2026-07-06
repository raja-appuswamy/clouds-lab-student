"""Test fixtures + import path setup for Phase 1.

Makes the repo root (for ``autograder``) and the phase dir (for ``app``) importable,
and exposes the deployment report as a fixture.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-1-echo-bot/
REPO_ROOT = PHASE_DIR.parent                           # repo root
REPORT_PATH = REPO_ROOT / "submission" / "phase1_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase1_report.json, or fail if missing/invalid.

    Generate it with ``python phase-1-echo-bot/measure.py --vm ... --cloudrun ... --function ...``
    after you have deployed all three targets.
    """
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase1_report.json not found — deploy the three targets, then run "
            "`python phase-1-echo-bot/measure.py` (see TASKS.md)."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase1_report.json is not valid JSON: {exc}")
