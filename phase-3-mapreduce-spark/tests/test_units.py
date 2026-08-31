"""Phase 3 unit tests — offline, pure Python (no Spark, no report).

Test your MapReduce primitives in ``mapreduce.py``. Run while coding:

    python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q

(40 points.)
"""

from __future__ import annotations

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


@points(10)
def test_map_wc():
    assert mr.map_wc("cat cat dog") == [("cat", 1), ("cat", 1), ("dog", 1)]
    assert mr.map_wc("the on") == []          # all stop-words → nothing emitted


@points(10)
def test_shuffle():
    got = mr.shuffle([("a", 1), ("b", 1), ("a", 1)])
    assert got == {"a": [1, 1], "b": [1]}


@points(10)
def test_reduce_wc():
    assert mr.reduce_wc({"a": [1, 1, 1], "b": [1]}) == {"a": 3, "b": 1}


@points(10)
def test_word_count_end_to_end():
    assert mr.word_count(DOCS) == EXPECTED
