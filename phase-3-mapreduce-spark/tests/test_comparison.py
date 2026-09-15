"""Phase 3 writeup check — structure only, no points (public).

Runs the same checker you can run yourself on ``submission/phase3_comparison.md``: every
answer slot filled, section-1 numbers matching ``phase3_report.json``, each prose answer long
enough and on topic. The *content* is graded by the instructor; this only tells you the
writeup is complete and internally consistent before you submit it.

    python phase-3-mapreduce-spark/report_md.py submission/phase3_comparison.md submission/phase3_report.json
"""

from __future__ import annotations

from pathlib import Path

import pytest

import report_md
from autograder.points import points

COMPARISON_PATH = Path(__file__).resolve().parents[2] / "submission" / "phase3_comparison.md"


@points(0)
def test_comparison_writeup_complete(report):
    if not COMPARISON_PATH.exists():
        pytest.fail("submission/phase3_comparison.md not found — copy comparison_template.md there "
                    "and fill in the answer slots (TASKS.md Task 12).")
    findings = report_md.check_report(COMPARISON_PATH.read_text(encoding="utf-8"), report)
    failed = [f for f in findings if not f.ok]
    assert not failed, "writeup slots need attention:\n" + "\n".join(
        f"  - {f.slot}: {f.message}" for f in failed)
