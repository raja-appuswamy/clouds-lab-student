"""Parallelism experiments + report writer (provided — no TODOs).

Helpers the notebook uses to time attention (naive vs vectorized), sweep CPU threads,
compare devices, and write ``submission/phase2_report.json``.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase2_report.json"


def time_ms(fn, *args, repeats: int = 5) -> float:
    """Median wall-clock milliseconds over ``repeats`` calls of ``fn(*args)``."""
    samples = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn(*args)
        samples.append((time.perf_counter() - t) * 1000.0)
    return round(statistics.median(samples), 3)


def time_attention(fn, T: int = 256, d: int = 64, repeats: int = 5) -> float:
    rng = np.random.default_rng(0)
    Q, K, V = (rng.standard_normal((T, d)) for _ in range(3))
    return time_ms(lambda: fn(Q, K, V), repeats=repeats)


def threading_sweep(step_fn, threads=(1, 2, 4, 8)) -> dict:
    """Time ``step_fn()`` under torch.set_num_threads(t) for each t. Returns {t: ms}."""
    import torch

    out = {}
    for t in threads:
        torch.set_num_threads(int(t))
        step_fn()  # warmup
        out[str(t)] = time_ms(step_fn, repeats=3)
    return out


def write_report(*, attention: dict, threads: dict, devices: dict,
                 training: dict, sample_text: str, gcs_url: str) -> Path:
    report = {
        "phase": "2",
        "environment": {"colab": "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ},
        "attention": attention,
        "threads": threads,
        "devices": devices,
        "training": training,
        "sample": sample_text,
        "model": {"gcs_url": gcs_url},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    return REPORT_PATH
