"""Phase 3 unit tests — offline, pure Python (no Spark, no cloud, no report).

Test your MapReduce primitives in ``mapreduce.py``, then the whole cloud job — map tasks,
shuffle files, reduce tasks — run against an in-memory stand-in for Cloud Storage. Run
while coding:

    python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q

(40 points.)
"""

from __future__ import annotations

import json

import pytest

import mapreduce as mr
from autograder.points import points

DOCS = [
    (0, "the cat sat on the mat"),
    (1, "the dog sat on the log"),
    (2, "cats chase dogs and dogs chase cats"),
]
# Content words after tokenize/stop-word removal:
#   doc0: cat sat mat   doc1: dog sat log   doc2: cats chase dogs dogs chase cats
EXPECTED = {"cat": 1, "sat": 2, "mat": 1, "dog": 1, "log": 1,
            "cats": 2, "chase": 2, "dogs": 2}


# ------------------------------- the three primitives (24) ------------------------------- #
@points(8)
def test_map_wc():
    assert mr.map_wc("cat cat dog") == [("cat", 1), ("cat", 1), ("dog", 1)]
    assert mr.map_wc("the on") == []          # all stop-words → nothing emitted


@points(8)
def test_shuffle():
    got = mr.shuffle([("a", 1), ("b", 1), ("a", 1)])
    assert got == {"a": [1, 1], "b": [1]}


@points(8)
def test_reduce_wc():
    assert mr.reduce_wc({"a": [1, 1, 1], "b": [1]}) == {"a": 3, "b": 1}


# ------------------------------ local reference runner (6) ------------------------------ #
@points(6)
def test_word_count_end_to_end():
    assert mr.word_count(DOCS) == EXPECTED


# --------------------------- the cloud job, simulated offline (10) --------------------------- #
class FakeGCS:
    """Just enough of Cloud Storage for the worker: a dict of key -> JSON text."""

    def __init__(self):
        self.objects: dict[str, str] = {}

    def read_json(self, bucket, key):
        return json.loads(self.objects[f"{bucket}/{key}"])

    def write_json(self, bucket, key, obj):
        self.objects[f"{bucket}/{key}"] = json.dumps(obj)


@points(10)
def test_cloud_job_matches_local_reference(monkeypatch):
    """Play the workflow's role: run every map task, then every reduce task, merge, compare.

    This is exactly what run_mr.py checks for real, minus the network — so if this passes
    and your deployment is right, the cloud job will produce the same counts.
    """
    import main
    import run_mr

    gcs = FakeGCS()
    monkeypatch.setattr(main, "read_json", gcs.read_json)
    monkeypatch.setattr(main, "write_json", gcs.write_json)

    docs = [(i, text) for i, text in DOCS] * 5          # 15 docs → several splits
    num_splits, num_reducers = 4, 3
    for i, split in enumerate(run_mr.make_splits(docs, num_splits)):
        gcs.write_json("b", f"job/input/split-{i:03d}.json", split)

    # MAP phase (the workflow runs these in parallel; order does not matter).
    for i in range(num_splits):
        body, status = main.handle({"task": "map", "bucket": "b", "job": "job",
                                    "split": i, "num_reducers": num_reducers})
        assert status == 200, body
    # Every map task wrote one shuffle file per reducer.
    shuffle_files = [k for k in gcs.objects if "/shuffle/" in k]
    assert len(shuffle_files) == num_splits * num_reducers

    # REDUCE phase.
    parts = []
    for r in range(num_reducers):
        body, status = main.handle({"task": "reduce", "bucket": "b", "job": "job",
                                    "partition": r, "num_splits": num_splits})
        assert status == 200, body
        parts.append(gcs.read_json("b", f"job/output/part-{r}.json"))

    assert run_mr.merge_outputs(parts) == mr.word_count(docs)
    # A word must land in exactly one partition — that is what makes the merge trivial.
    assert sum(len(p) for p in parts) == len(mr.word_count(docs))


def test_partition_is_stable_and_in_range():
    """Not graded — a sanity check on the provided partitioner."""
    for word in ("cat", "dog", "shakespeare"):
        assert 0 <= mr.partition(word, 4) < 4
        assert mr.partition(word, 4) == mr.partition(word, 4)


def test_worker_rejects_unknown_task():
    """Not graded — the worker answers 400, not 500, to a malformed request."""
    import main
    body, status = main.handle({"task": "sort"})
    assert status == 400 and "unknown task" in body["error"]


def test_chaos_fails_before_doing_work(monkeypatch):
    """Not graded — with chaos=1.0 the worker always 503s and touches no storage."""
    import main
    called = []
    monkeypatch.setattr(main, "read_json", lambda *a: called.append(a))
    body, status = main.handle({"task": "map", "chaos": 1.0, "bucket": "b", "job": "j",
                                "split": 0, "num_reducers": 1})
    assert status == 503 and not called
