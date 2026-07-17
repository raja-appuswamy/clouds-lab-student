"""Test fixtures + import path setup for Phase 2 (torch-free)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-2-tiny-gpt/
REPO_ROOT = PHASE_DIR.parent
REPORT_PATH = REPO_ROOT / "submission" / "phase2_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase2_report.json, or fail if missing/invalid.

    Produced by running the Colab notebook (which calls experiments.write_report).
    """
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase2_report.json not found — run the Colab notebook to the end "
            "(it trains, uploads the model, and writes the report). See TASKS.md."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase2_report.json is not valid JSON: {exc}")
