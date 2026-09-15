#!/usr/bin/env python3
"""Check `submission/phase1_report.md` against its template (provided).

The template (``report_template.md``) puts every answer between ``<!--answer:...-->`` markers;
the shared engine in ``autograder/report_md.py`` parses them. Numbers are cross-checked
against ``submission/phase1_report.json`` — the only check that catches invented figures.

    python phase-1-echo-bot/report_md.py submission/phase1_report.md submission/phase1_report.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # repo root, for `autograder`

from autograder.report_md import Slot, check, parse  # noqa: E402,F401  (re-exported for callers)
from autograder import report_md as _engine           # noqa: E402

SLOTS: tuple[Slot, ...] = (
    Slot("image_size_mb", "number"),
    Slot("vpc_name", "text"),
    Slot("subnet_name", "text"),
    Slot("vm_cold_ms", "number", json_path=("platforms", "vm", "cold_ms")),
    Slot("vm_warm_median_ms", "number", json_path=("platforms", "vm", "stats", "median")),
    Slot("cloudrun_cold_ms", "number", json_path=("platforms", "cloudrun", "cold_ms")),
    Slot("cloudrun_warm_median_ms", "number", json_path=("platforms", "cloudrun", "stats", "median")),
    Slot("function_cold_ms", "number", json_path=("platforms", "function", "cold_ms")),
    Slot("function_warm_median_ms", "number", json_path=("platforms", "function", "stats", "median")),
    Slot("latency_plot", "verbatim"),
    Slot("scaling_behaviour", "prose", min_words=55),
    Slot("deployment_effort", "prose", min_words=70),
    Slot("run_services_list", "verbatim", must_have_tokens=("echo-bot", "echo")),
    Slot("convergence_explanation", "prose", min_words=90),
)


def check_report(markdown: str, json_report: dict | None = None):
    """Phase-1 findings — same signature the old module had."""
    return check(markdown, SLOTS, json_report)


if __name__ == "__main__":
    raise SystemExit(_engine.main(
        SLOTS, usage="report_md.py submission/phase1_report.md [submission/phase1_report.json]"))
