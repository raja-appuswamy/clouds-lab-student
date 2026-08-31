"""Phase 3 report tests — the pipeline ran end to end (public).

Reads submission/phase3_report.json. (15 points.)
"""

from __future__ import annotations

from autograder.points import points


@points(8)
def test_pipeline_recorded(report):
    assert report.get("corpus", {}).get("num_docs", 0) > 1, "corpus should have many documents"
    assert report.get("mapreduce", {}).get("top_terms"), "no MapReduce top-terms recorded"
    url = report.get("tfidf", {}).get("parquet_gcs_url", "")
    assert url.startswith("https://storage.googleapis.com/"), f"bad parquet URL: {url!r}"
    assert report.get("tfidf", {}).get("num_rows", 0) > 0, "no TF-IDF row count recorded"


@points(7)
def test_bigquery_recorded(report):
    bq = report.get("bigquery", {})
    table = bq.get("table", "")
    assert table.count(".") >= 1, f"bigquery.table should be project.dataset.table, got {table!r}"
    assert bq.get("top_by_tfidf"), "no BigQuery top-by-tfidf query result recorded"
