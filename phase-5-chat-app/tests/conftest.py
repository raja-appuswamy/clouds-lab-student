"""Test fixtures + import path setup for Phase 5."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-5-chat-app/
REPO_ROOT = PHASE_DIR.parent
REPORT_PATH = REPO_ROOT / "submission" / "phase5_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase5_report.json (written by make_report.py)."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase5_report.json not found — deploy the chat app, then run "
            "`python phase-5-chat-app/make_report.py --chat-url ... --ui-url ...`. See TASKS.md."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase5_report.json is not valid JSON: {exc}")
