"""Phase 3 report tests — the pipeline ran end to end (public).

Reads submission/phase3_report.json, plus the public ``wordcount.json`` your cloud
MapReduce job published. (23 points.)
"""

from __future__ import annotations

import re

from autograder.points import points

EXECUTION = re.compile(r"^projects/[^/]+/locations/[^/]+/workflows/[^/]+/executions/[^/]+$")


@points(8)
def test_cloud_mapreduce_recorded(report):
    mr = report.get("mapreduce", {})
    assert EXECUTION.match(mr.get("execution", "")), (
        f"mapreduce.execution should name a Cloud Workflows execution, got {mr.get('execution')!r}")
    assert mr.get("state") == "SUCCEEDED", f"workflow execution state is {mr.get('state')!r}"
    assert mr.get("num_splits", 0) > 1 and mr.get("num_reducers", 0) > 1, (
        "the job should have several map tasks and several reduce tasks")
    assert len(mr.get("map_tasks", [])) == mr["num_splits"], "one map-task record per split expected"
    assert len(mr.get("reduce_tasks", [])) == mr["num_reducers"], "one reduce-task record per partition expected"
    assert mr.get("matches_local") is True, "cloud counts did not match the local reference"


@points(7)
def test_public_wordcount_matches_report(report, public_wordcount):
    mr = report["mapreduce"]
    assert len(public_wordcount) == mr.get("vocab_size"), "vocab_size differs from the published counts"
    ranked = sorted(public_wordcount.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    assert [list(x) for x in mr.get("top_terms", [])[:10]] == [[t, c] for t, c in ranked], (
        "top_terms in the report differ from the published wordcount.json")


@points(4)
def test_tfidf_recorded(report):
    assert report.get("corpus", {}).get("num_docs", 0) > 1, "corpus should have many documents"
    url = report.get("tfidf", {}).get("parquet_gcs_url", "")
    assert url.startswith("https://storage.googleapis.com/"), f"bad parquet URL: {url!r}"
    assert report.get("tfidf", {}).get("num_rows", 0) > 0, "no TF-IDF row count recorded"


@points(4)
def test_bigquery_recorded(report):
    bq = report.get("bigquery", {})
    table = bq.get("table", "")
    assert table.count(".") >= 1, f"bigquery.table should be project.dataset.table, got {table!r}"
    assert bq.get("top_by_tfidf"), "no BigQuery top-by-tfidf query result recorded"
