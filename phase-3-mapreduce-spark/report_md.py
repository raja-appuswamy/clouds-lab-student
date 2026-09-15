#!/usr/bin/env python3
"""Check `submission/phase3_comparison.md` against its template (provided).

The template (``comparison_template.md``) puts every answer between ``<!--answer:...-->``
markers; the shared engine in ``autograder/report_md.py`` parses them. The section-1 numbers
are cross-checked against ``submission/phase3_report.json``, the stage/retry counts are
range-checked, and each prose answer must reach a minimum length and mention the concepts
the question is actually about. Run it before you push:

    python phase-3-mapreduce-spark/report_md.py submission/phase3_comparison.md submission/phase3_report.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # repo root, for `autograder`

from autograder.report_md import Slot, check, parse  # noqa: E402,F401  (re-exported for callers)
from autograder import report_md as _engine           # noqa: E402

SLOTS: tuple[Slot, ...] = (
    # ---- 1. facts, cross-checked against phase3_report.json ------------------------- #
    Slot("num_map_tasks", "number", json_path=("mapreduce", "num_splits"), tol_abs=0),
    Slot("num_reduce_tasks", "number", json_path=("mapreduce", "num_reducers"), tol_abs=0),
    Slot("cloud_elapsed_s", "number", json_path=("mapreduce", "cloud_elapsed_s"), tol_abs=0.5),
    Slot("local_elapsed_s", "number", json_path=("mapreduce", "local_elapsed_s"), tol_abs=0.01),
    Slot("spark_elapsed_s", "number", json_path=("tfidf", "spark_elapsed_s"), tol_abs=0.5),
    # No ground truth for these two; plausibility only.
    Slot("num_stages", "number", min_value=3, max_value=10),
    Slot("chaos_retries", "number", min_value=0, max_value=100),

    # ---- 2. Spark ------------------------------------------------------------------- #
    Slot("transformations_vs_actions", "prose", min_words=45,
         must_have_tokens=("collect",), any_of_tokens=("flatMap", "reduceByKey", "join", "map")),
    Slot("lineage_recovery", "prose", min_words=35,
         any_of_tokens=("stage", "stages", "shuffle", "ShuffledRDD", "reduceByKey", "partition")),

    # ---- 3. Hadoop role mapping ------------------------------------------------------ #
    Slot("role_jobtracker", "text", any_of_tokens=("workflows", "workflow", "workflow.yaml")),
    Slot("role_workers", "text", any_of_tokens=("run", "function", "functions", "mr-worker", "main.py")),
    Slot("role_hdfs", "text", any_of_tokens=("storage", "gcs", "bucket", "gs")),
    Slot("role_partitioner", "text", any_of_tokens=("partition", "partition()", "crc32", "mapreduce.py")),
    Slot("barrier_location", "prose", min_words=20,
         any_of_tokens=("parallel", "map_phase", "reduce_phase", "branches")),
    Slot("idempotence", "prose", min_words=45,
         any_of_tokens=("overwrite", "overwrites", "overwriting", "overwritten",
                        "append", "appends", "appended", "duplicate", "duplicates", "double")),
    Slot("chaos_observations", "prose", min_words=35,
         any_of_tokens=("503", "retry", "retries", "retried", "retrying")),

    # ---- 4. three runtimes ------------------------------------------------------------ #
    Slot("three_runtimes", "prose", min_words=70,
         any_of_tokens=("overhead", "startup", "start-up", "jvm", "invocation", "invocations",
                        "latency", "scheduling", "cold")),
    Slot("breakeven_estimate", "prose", min_words=35, must_have_number=True),

    # ---- 5. object storage vs HDFS ---------------------------------------------------- #
    Slot("gcs_vs_hdfs", "prose", min_words=35,
         any_of_tokens=("locality", "replication", "replicated", "block", "blocks", "metadata",
                        "namenode", "consistency", "consistent", "object", "objects", "rename")),
)


def check_report(markdown: str, json_report: dict | None = None):
    """Phase-3 findings."""
    return check(markdown, SLOTS, json_report)


if __name__ == "__main__":
    raise SystemExit(_engine.main(
        SLOTS, usage="report_md.py submission/phase3_comparison.md [submission/phase3_report.json]"))
