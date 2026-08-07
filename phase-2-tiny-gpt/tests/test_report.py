"""Phase 2 report tests — check your measured parallelism results (public).

Reads submission/phase2_report.json (written by the notebook). (40 points.)
"""

from __future__ import annotations

from autograder.points import points


@points(15)
def test_all_measurements_present(report):
    att = report.get("attention", {})
    assert att.get("naive_ms") and att.get("vectorized_ms"), "attention timings missing"
    assert len(report.get("threads", {})) >= 3, "need a CPU threading sweep (>=3 points)"
    dev = report.get("devices", {})
    assert dev.get("cpu_ms") and dev.get("gpu_ms"), "cpu/gpu training timings missing"


@points(15)
def test_parallelism_helped(report):
    att = report["attention"]
    assert att["vectorized_ms"] < att["naive_ms"], "vectorized attention should beat the naive loop"
    dev = report["devices"]
    assert dev["gpu_ms"] < dev["cpu_ms"], "GPU training should beat CPU (use a GPU runtime)"


@points(10)
def test_training_and_model_recorded(report):
    tr = report.get("training", {})
    assert isinstance(tr.get("final_loss"), (int, float)), "no final_loss recorded"
    assert report.get("sample"), "no generated text sample recorded"
    url = report.get("model", {}).get("gcs_url", "")
    assert url.startswith("https://storage.googleapis.com/"), f"gcs_url looks wrong: {url!r}"
