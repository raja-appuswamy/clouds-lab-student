"""Word-count MapReduce — the primitives you implement, run two ways.

This is the Lecture-5 core: you implement the three MapReduce primitives — **map**,
**shuffle**, **reduce**. They are then executed:

* **locally** by ``word_count`` (provided) — one process, the reference answer; and
* **in the cloud** by ``main.py`` + ``workflow.yaml`` — each map task is a Cloud Run
  function invocation, Cloud Storage is the shuffle medium, and Cloud Workflows is the
  job tracker that fans tasks out and retries the ones that fail (what Hadoop's JobTracker
  does across a cluster). ``run_mr.py`` drives a job and checks cloud == local.

Pure Python, no heavy deps — run the offline unit tests as you go:

    python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

import re
import zlib

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


def partition(word: str, num_reducers: int) -> int:
    """Which reducer owns ``word`` (provided) — Hadoop's *Partitioner*.

    Every map task must send the same word to the same reducer, or the counts for that
    word end up split across two output files. So the hash has to be stable across
    processes and machines: ``zlib.crc32`` is; Python's built-in ``hash()`` is NOT (it is
    salted per process — see PYTHONHASHSEED), which is a classic distributed-systems bug.
    """
    return zlib.crc32(word.encode("utf-8")) % num_reducers


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
# Local reference runner (provided)
# --------------------------------------------------------------------------- #
def word_count(documents: list[tuple[int, str]]) -> dict[str, int]:
    """Full MapReduce word count over ``[(doc_id, text), ...]`` in ONE process.

    Map every document, shuffle all the pairs, reduce — the same three calls the cloud
    workers make, minus the network. This is the reference the cloud job is checked
    against (``run_mr.py`` asserts the two agree) and what the unit tests use.
    """
    pairs = [pair for _, text in documents for pair in map_wc(text)]
    return reduce_wc(shuffle(pairs))
