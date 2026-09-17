"""Retrieval-Augmented Generation helpers — the two functions you implement.

Where they sit
--------------
Every ``POST /chat`` runs this chain (all in this folder):

    server.chat()                                   the request handler
      -> retrieval.retrieve(bq, table, message, k=3)
           -> retrieval.tokenize(message)           same tokenizer as Phase 3 -> terms match the table
           -> retrieval.query_tfidf(...)            SELECT term, doc_id, tfidf FROM <Phase-3 table>
                                                    WHERE term IN (the query's terms)
           -> rag.rank_topk(rows, k)                YOU: which k documents match best?
           -> retrieval.load_corpus()               doc_id -> text (Phase 3's deterministic split)
      -> rag.build_rag_prompt(message, texts)       YOU: put those texts in front of the question
      -> infer.generate(weights, prompt)            the Phase-2 model answers
      -> store.store_turn(...)                      record both turns

Worked example
--------------
Message: "the king and his crown". ``tokenize`` drops stop-words -> terms ``{king, his, crown}``.
BigQuery returns every row of the TF-IDF table for those three terms — say::

    ("king",  12, 4.1)   ("king",  7, 2.9)   ("crown", 12, 3.3)
    ("crown", 31, 3.0)   ("his",   7, 0.4)   ("his",   12, 0.4)

``rank_topk`` sums per document — doc 12: 7.8, doc 7: 3.3, doc 31: 3.0 — and returns
``[12, 7, 31]``. ``retrieve`` maps those ids to their text; ``build_rag_prompt`` produces::

    Context:
    <text of doc 12>

    <text of doc 7>

    <text of doc 31>

    User: the king and his crown
    Assistant:

Both functions are pure — lists in, lists/strings out, no I/O — which is why the offline unit
tests can grade them with hand-written rows and no BigQuery:

    python -m pytest phase-4-chat-app/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations


def rank_topk(tfidf_rows: list[tuple[str, int, float]], k: int = 3) -> list[int]:
    """Rank documents for a query and return the top-k ``doc_id``s (best first).

    ``tfidf_rows`` are ``(term, doc_id, tfidf)`` triples, one per (query term, document) pair
    in which that term occurs. They are **already filtered to the query's terms** — the
    BigQuery ``WHERE term IN (...)`` did that — so this function never sees the query text,
    only the evidence for it. A row means "term appears in doc with this weight".

    Three steps:

    1. **Score each document by the SUM of its tfidf over the rows.** A document that
       contains several query terms, or contains them with high weight, accumulates a high
       score. (Sum, not max: two medium matches should beat one strong one.) This is a
       read-modify-write into a dict keyed by ``doc_id`` — the same shape as Phase 3's
       ``reduce_wc``.
    2. **Sort documents by score, highest first, ties broken by ascending ``doc_id``.** The
       tie-break makes the result deterministic; without it two equal-score documents could
       come out in either order and the tests (and your prompts) would be flaky.
    3. **Return the first ``k`` ids** — ids only, no scores. Fewer than ``k`` if fewer
       documents matched; an empty list if ``tfidf_rows`` is empty.

    Example: rows ``("king", 12, 4.1), ("king", 7, 2.9), ("crown", 12, 3.3)`` with ``k=2``
    -> scores {12: 7.4, 7: 2.9} -> ``[12, 7]``.
    """
    # TODO: sum tfidf per doc_id, sort by score descending (ties by doc_id), return top-k ids.
    raise NotImplementedError("Phase 4: implement rank_topk()")


def build_rag_prompt(query: str, context_texts: list[str]) -> str:
    """Build the model prompt: prepend the retrieved context, then the user's query.

    ``query`` is the user's message, verbatim. ``context_texts`` are the **full texts of the
    documents ``rank_topk`` chose**, best match first — ``retrieval.retrieve`` mapped the
    winning ``doc_id``s back to their text with ``load_corpus`` (each is one 40-line chunk of
    TinyShakespeare, Phase 3's document unit). Usually ``k`` = 3 of them; possibly fewer, or
    none at all if the message had no content words (then the prompt has an empty Context
    section and the model answers from its weights alone).

    This is the "augmented" in RAG: the model never saw these documents at inference time
    until you put them in front of the question. Return a string of the form::

        Context:
        <doc 1>

        <doc 2>

        User: <query>
        Assistant:

    — the texts joined by a blank line under a ``Context:`` header, then the query on a
    ``User:`` line, then a bare ``Assistant:`` line that the model continues from.
    """
    # TODO: join context_texts with blank lines under a "Context:" header, then add
    #       "User: <query>" and a final "Assistant:" line.
    raise NotImplementedError("Phase 4: implement build_rag_prompt()")
