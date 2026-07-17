"""Phase 2 model-artifact tests — validate your uploaded weights, torch-free.

Reads the ``model.gcs_url`` from your report and range-downloads just the **safetensors
header** (a few KB), then checks the tensor shapes describe the right ~5M-param GPT. No
full download, no torch — so it's fast even across a whole class.

Requires your GCS object to be public and reachable — keep it up until graded. (25 points.)
"""

from __future__ import annotations

import json
import math
import struct
import urllib.error
import urllib.request

import pytest

from config import CONFIG, expected_param_count
from autograder.points import points

RANGE_BYTES = 65535


def _fetch(url: str, first: int, last: int) -> bytes:
    req = urllib.request.Request(url, headers={"Range": f"bytes={first}-{last}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _safetensors_header(url: str) -> dict:
    """Return the parsed safetensors header dict (tensor name -> metadata)."""
    try:
        head = _fetch(url, 0, RANGE_BYTES)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        pytest.fail(f"could not fetch model from {url}: {exc}")
    if len(head) < 8:
        pytest.fail(f"model at {url} is too small to be a safetensors file")
    n = struct.unpack("<Q", head[:8])[0]
    if 8 + n > len(head):                      # header bigger than our first read
        head = _fetch(url, 0, 8 + n - 1)
    try:
        return json.loads(head[8:8 + n].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        pytest.fail(f"not a valid safetensors header at {url}: {exc}")


@pytest.fixture(scope="session")
def header(report) -> dict:
    url = report.get("model", {}).get("gcs_url", "")
    if not url:
        pytest.fail("report has no model.gcs_url — did the notebook upload the model?")
    h = _safetensors_header(url)
    h.pop("__metadata__", None)
    return h


@points(10)
def test_param_count_is_a_tiny_gpt(header):
    params = sum(math.prod(meta["shape"]) for meta in header.values())
    assert 3_000_000 <= params <= 7_000_000, f"expected ~5M params, got {params:,}"


@points(15)
def test_architecture_matches_spec(header):
    # Token embedding of the right size.
    tok = header.get("tok_emb.weight")
    assert tok, "no tok_emb.weight tensor in the model"
    assert tok["shape"] == [CONFIG.vocab_size, CONFIG.n_embd], (
        f"tok_emb.weight should be [{CONFIG.vocab_size}, {CONFIG.n_embd}], got {tok['shape']}"
    )
    # Exactly n_layer transformer blocks.
    block_ids = {name.split(".")[1] for name in header if name.startswith("blocks.")}
    assert len(block_ids) == CONFIG.n_layer, (
        f"expected {CONFIG.n_layer} blocks, found {len(block_ids)}"
    )
    # An output head over the vocabulary.
    head = header.get("head.weight")
    assert head and head["shape"][0] == CONFIG.vocab_size, "missing/!wrong lm head (head.weight)"
    # Sanity: total is close to the analytic count for this exact architecture.
    params = sum(math.prod(m["shape"]) for m in header.values())
    assert abs(params - expected_param_count()) / expected_param_count() < 0.05
