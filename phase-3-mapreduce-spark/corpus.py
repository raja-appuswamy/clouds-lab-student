"""Corpus loader for Phase 3 (provided).

A retrieval corpus needs multiple *documents* (IDF is defined across documents). We build
a small, deterministic one by downloading TinyShakespeare and splitting it into fixed-size
chunks — enough to illustrate MapReduce + TF-IDF without needing the 200 MB Wikipedia dump
(scale is discussed in your report, not required to run).
"""

from __future__ import annotations

import urllib.request

TINY_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"


def load_documents(max_docs: int = 60, lines_per_doc: int = 40) -> list[tuple[int, str]]:
    """Download the corpus and split into ``[(doc_id, text), ...]`` (deterministic)."""
    text = urllib.request.urlopen(TINY_URL, timeout=30).read().decode("utf-8", "replace")
    lines = text.splitlines()
    docs: list[tuple[int, str]] = []
    for i in range(0, len(lines), lines_per_doc):
        chunk = "\n".join(lines[i:i + lines_per_doc]).strip()
        if chunk:
            docs.append((len(docs), chunk))
        if len(docs) >= max_docs:
            break
    return docs


def sample_documents() -> list[tuple[int, str]]:
    """A tiny inline corpus for quick local checks."""
    return [
        (0, "the cat sat on the mat"),
        (1, "the dog sat on the log"),
        (2, "cats chase dogs and dogs chase cats"),
    ]
