"""Attention two ways — the vectorization (SIMD) lesson of Phase 2.

You implement the same math twice: once with explicit Python loops (``attention_naive``)
and once with vectorized NumPy matrix ops (``attention_vectorized``). They must return the
same result; in the Colab notebook you time both and see the speedup that vectorization
(and, under the hood, SIMD/AVX) buys you.

Pure NumPy — no torch — so the autograder runs it fast. Run the unit tests as you go:

    python -m pytest phase-2-tiny-gpt/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

import numpy as np


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable softmax along ``axis`` (provided)."""
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def attention_naive(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    """Scaled dot-product attention with **explicit loops** over positions.

    Q, K, V each have shape ``(T, d)``. Return shape ``(T, d)``:
        scores[i,j] = (Q[i] . K[j]) / sqrt(d);  weights = softmax(scores, axis=-1);
        out[i] = sum_j weights[i,j] * V[j]
    Loop over the query index ``i`` and key index ``j`` — do NOT use ``Q @ K.T``.
    """
    # TODO: implement with explicit i/j loops (no Q @ K.T).
    raise NotImplementedError("Phase 2: implement attention_naive()")


def attention_vectorized(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    """The same attention using vectorized matrix ops — no Python loops over positions."""
    # TODO: compute scores = Q @ K.T / sqrt(d); weights = softmax(scores); return weights @ V
    raise NotImplementedError("Phase 2: implement attention_vectorized()")
