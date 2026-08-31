"""Phase 2 unit tests — offline, NumPy only (no torch, no report).

**Ungraded smoke check (0 points).** The model code (`attention_numpy.py`, `model.py`)
ships as a working solution, so implementing it is optional and not graded. These tests
just confirm the attention code you're using is correct — useful fast feedback if you did
the optional implementation from ``templates/``:

    python -m pytest phase-2-tiny-gpt/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

import numpy as np

import attention_numpy as an
from autograder.points import points


def _reference(Q, K, V):
    """Independent scaled dot-product attention (used only to check yours)."""
    d = Q.shape[1]
    s = (Q @ K.T) / np.sqrt(d)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s)
    w = w / w.sum(axis=-1, keepdims=True)
    return w @ V


def _qkv(T=12, d=8, seed=0):
    rng = np.random.default_rng(seed)
    return (rng.standard_normal((T, d)) for _ in range(3))


@points(0)
def test_naive_matches_reference():
    Q, K, V = _qkv()
    np.testing.assert_allclose(an.attention_naive(Q, K, V), _reference(Q, K, V), atol=1e-10)


@points(0)
def test_vectorized_matches_reference():
    Q, K, V = _qkv(seed=1)
    np.testing.assert_allclose(an.attention_vectorized(Q, K, V), _reference(Q, K, V), atol=1e-10)


@points(0)
def test_naive_and_vectorized_agree():
    Q, K, V = _qkv(T=20, d=16, seed=2)
    np.testing.assert_allclose(
        an.attention_naive(Q, K, V), an.attention_vectorized(Q, K, V), atol=1e-10
    )


@points(0)
def test_output_shape_and_rows_sum_like_softmax():
    Q, K, V = _qkv(T=7, d=5, seed=3)
    out = an.attention_vectorized(Q, K, V)
    assert out.shape == (7, 5)
    # Each output row is a convex combination of value rows, so it lies within their range.
    assert out.max() <= V.max() + 1e-9 and out.min() >= V.min() - 1e-9
