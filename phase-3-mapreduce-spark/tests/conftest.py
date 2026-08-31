"""Test fixtures + import path setup for Phase 3."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

PHASE_DIR = Path(__file__).resolve().parents[1]        # phase-3-mapreduce-spark/
REPO_ROOT = PHASE_DIR.parent
REPORT_PATH = REPO_ROOT / "submission" / "phase3_report.json"

for p in (str(REPO_ROOT), str(PHASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def report() -> dict:
    """Load submission/phase3_report.json (written by the Colab notebook)."""
    if not REPORT_PATH.exists():
        pytest.fail(
            "submission/phase3_report.json not found — run the Colab notebook to the end "
            "(MapReduce, Spark TF-IDF, upload to GCS, load BigQuery). See TASKS.md."
        )
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"phase3_report.json is not valid JSON: {exc}")


@pytest.fixture(scope="session")
def parquet_table(report):
    """Download the TF-IDF Parquet from the report's public GCS URL and return it (pyarrow)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    url = report.get("tfidf", {}).get("parquet_gcs_url", "")
    if not url:
        pytest.fail("report has no tfidf.parquet_gcs_url — did the notebook upload the Parquet?")
    try:
        data = urllib.request.urlopen(url, timeout=60).read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        pytest.fail(f"could not fetch Parquet from {url}: {exc}")
    return pq.read_table(pa.BufferReader(data))
