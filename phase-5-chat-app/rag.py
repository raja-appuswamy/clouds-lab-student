"""Retrieval-Augmented Generation helpers — the two pieces you implement.

The server (provided) queries BigQuery for the TF-IDF rows of the query's terms, then calls
``rank_topk`` to pick the best documents and ``build_rag_prompt`` to prepend them to the
user's message. Both are pure functions — offline unit tests cover them:

    python -m pytest phase-5-chat-app/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations


def rank_topk(tfidf_rows: list[tuple[str, int, float]], k: int = 3) -> list[int]:
    """Rank documents for a query and return the top-k ``doc_id``s (best first).

    ``tfidf_rows`` are ``(term, doc_id, tfidf)`` triples — already filtered to the query's
    terms (the BigQuery query does that). Score each document by the **sum** of its tfidf
    over those terms, then return the ``k`` highest-scoring ``doc_id``s.
    """
    # TODO: sum tfidf per doc_id, sort by score descending (ties by doc_id), return top-k ids.
    raise NotImplementedError("Phase 5: implement rank_topk()")


def build_rag_prompt(query: str, context_texts: list[str]) -> str:
    """Build the model prompt: prepend the retrieved context, then the user's query.

    Return a string of the form::

        Context:
        <doc 1>

        <doc 2>

        User: <query>
        Assistant:
    """
    # TODO: join context_texts with blank lines under a "Context:" header, then add
    #       "User: <query>" and a final "Assistant:" line.
    raise NotImplementedError("Phase 5: implement build_rag_prompt()")
