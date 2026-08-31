"""Report writer for Phase 3 (provided)."""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase3_report.json"


def top_terms(counts: dict[str, int], n: int = 10) -> list[list]:
    """Top-n (term, count) pairs, highest first (ties broken by term for determinism)."""
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [[t, c] for t, c in ranked[:n]]


def write_report(*, corpus_info: dict, mapreduce: dict, tfidf: dict,
                 bigquery: dict, comparison: dict) -> Path:
    report = {
        "phase": "3",
        "environment": {"colab": "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ},
        "corpus": corpus_info,
        "mapreduce": mapreduce,
        "tfidf": tfidf,
        "bigquery": bigquery,
        "comparison": comparison,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    return REPORT_PATH
