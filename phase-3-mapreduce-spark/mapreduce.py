"""Word-count MapReduce with Python multiprocessing — a stand-in for Hadoop.

This is the Lecture-5 core: you implement the three MapReduce primitives — **map**,
**shuffle**, **reduce** — and `word_count` wires them together (running the map phase
across worker processes, exactly as Hadoop farms map tasks across a cluster).

Pure Python, no heavy deps — run the offline unit tests as you go:

    python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

import multiprocessing
import re

_WORD = re.compile(r"[a-z]+")

# A small stop-word list so counts focus on content words (provided).
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "by", "for",
    "with", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that",
    "these", "those", "as", "i", "you", "he", "she", "we", "they", "not", "no", "do",
}


def tokenize(text: str) -> list[str]:
    """Lower-case, keep alphabetic words of length >= 2, drop stop-words (provided)."""
    return [w for w in _WORD.findall(text.lower()) if len(w) >= 2 and w not in STOPWORDS]


# --------------------------------------------------------------------------- #
# The three MapReduce primitives YOU implement
# --------------------------------------------------------------------------- #
def map_wc(text: str) -> list[tuple[str, int]]:
    """MAP: emit a ``(word, 1)`` pair for every token in one document."""
    # TODO: return a (word, 1) pair for each token in `text` (use tokenize()).
    raise NotImplementedError("Phase 3: implement map_wc()")


def shuffle(pairs: list[tuple[str, int]]) -> dict[str, list[int]]:
    """SHUFFLE: group the mapped pairs by key → ``{word: [1, 1, ...]}``."""
    # TODO: build a dict mapping each word to the list of its emitted values.
    raise NotImplementedError("Phase 3: implement shuffle()")


def reduce_wc(grouped: dict[str, list[int]]) -> dict[str, int]:
    """REDUCE: sum each key's values → ``{word: count}``."""
    # TODO: return {word: sum(values)} for each key in `grouped`.
    raise NotImplementedError("Phase 3: implement reduce_wc()")


# --------------------------------------------------------------------------- #
# Orchestration (provided): map phase runs across worker processes
# --------------------------------------------------------------------------- #
def word_count(documents: list[tuple[int, str]], workers: int = 1) -> dict[str, int]:
    """Full MapReduce word count over ``[(doc_id, text), ...]``.

    With ``workers > 1`` the MAP phase is farmed to a process pool (the "distributed"
    part); the shuffle + reduce then run locally. With ``workers == 1`` it stays
    sequential (what the unit tests use — deterministic, no process-pool overhead).
    """
    texts = [text for _, text in documents]
    if workers > 1:
        with multiprocessing.Pool(workers) as pool:
            mapped = pool.map(map_wc, texts)
    else:
        mapped = [map_wc(t) for t in texts]
    pairs = [pair for sublist in mapped for pair in sublist]
    return reduce_wc(shuffle(pairs))
