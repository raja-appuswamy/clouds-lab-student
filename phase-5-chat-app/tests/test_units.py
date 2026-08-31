"""Phase 5 unit tests — offline, pure Python (no cloud, no report).

Test your RAG helpers in ``rag.py``. Run while coding:

    python -m pytest phase-5-chat-app/tests/test_units.py -p autograder.points -q

(40 points.)
"""

from __future__ import annotations

import rag
from autograder.points import points

# doc1 total = 0.5 + 0.5 = 1.0 ; doc2 = 0.9 ; doc3 = 0.1  -> order [1, 2, 3]
ROWS = [("a", 1, 0.5), ("b", 1, 0.5), ("a", 2, 0.9), ("c", 3, 0.1)]


@points(15)
def test_rank_topk_orders_by_summed_tfidf():
    assert rag.rank_topk(ROWS, k=3) == [1, 2, 3]


@points(10)
def test_rank_topk_limits_to_k():
    top = rag.rank_topk(ROWS, k=2)
    assert top == [1, 2] and len(top) == 2


@points(15)
def test_build_rag_prompt():
    prompt = rag.build_rag_prompt("what is love", ["doc one", "doc two"])
    assert "Context:" in prompt
    assert "doc one" in prompt and "doc two" in prompt
    assert "User: what is love" in prompt
    assert prompt.rstrip().endswith("Assistant:")
