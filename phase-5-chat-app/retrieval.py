"""Retrieval over the Phase-3 BigQuery TF-IDF table (provided).

Tokenizes the query the SAME way Phase 3 did (so terms match the table), fetches the tfidf
rows for those terms from BigQuery, ranks documents with your ``rag.rank_topk``, and maps the
winning doc_ids back to their text via the same deterministic corpus split as Phase 3.
"""

from __future__ import annotations

import re
import urllib.request

from rag import rank_topk

TINY_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"

_WORD = re.compile(r"[a-z]+")
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "by", "for",
    "with", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that",
    "these", "those", "as", "i", "you", "he", "she", "we", "they", "not", "no", "do",
}
_CORPUS: dict[int, str] | None = None


def tokenize(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if len(w) >= 2 and w not in STOPWORDS]


def load_corpus(max_docs: int = 60, lines_per_doc: int = 40) -> dict[int, str]:
    """doc_id -> text, matching Phase 3's split (cached after first call)."""
    global _CORPUS
    if _CORPUS is not None:
        return _CORPUS
    text = urllib.request.urlopen(TINY_URL, timeout=30).read().decode("utf-8", "replace")
    lines = text.splitlines()
    docs: dict[int, str] = {}
    for i in range(0, len(lines), lines_per_doc):
        chunk = "\n".join(lines[i:i + lines_per_doc]).strip()
        if chunk:
            docs[len(docs)] = chunk
        if len(docs) >= max_docs:
            break
    _CORPUS = docs
    return docs


def query_tfidf(bq_client, table: str, terms) -> list[tuple[str, int, float]]:
    from google.cloud import bigquery

    job = bq_client.query(
        f"SELECT term, doc_id, tfidf FROM `{table}` WHERE term IN UNNEST(@terms)",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ArrayQueryParameter("terms", "STRING", list(terms))
        ]),
    )
    return [(r.term, r.doc_id, r.tfidf) for r in job.result()]


def retrieve(bq_client, table: str, query: str, k: int = 3) -> list[tuple[int, str]]:
    """Return the top-k ``(doc_id, text)`` for the query (empty if no content terms)."""
    terms = set(tokenize(query))
    if not terms:
        return []
    rows = query_tfidf(bq_client, table, terms)
    corpus = load_corpus()
    return [(doc_id, corpus.get(doc_id, "")) for doc_id in rank_topk(rows, k)]
