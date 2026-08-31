"""PySpark TF-IDF pipeline — the Lecture-6 reimplementation of the corpus prep.

You implement the two key RDD stages — per-document **term frequency** and per-term
**document frequency** — using Spark transformations (`flatMap`, `map`, `reduceByKey`).
`build_tfidf_rows` (provided) joins them and emits the final TF-IDF table.

Definitions (keep them exactly, so your output matches the grader):
    tf(t, d)  = raw count of term t in document d
    df(t)     = number of documents containing t
    idf(t)    = ln(N / df(t))            # N = number of documents
    tfidf     = tf * idf

Graded on the OUTPUT you produce (the Parquet you upload), so run it in Colab and check the
table — there are no offline unit tests for the Spark stages (Spark needs its runtime).
"""

from __future__ import annotations

import math

from mapreduce import tokenize   # reuse the same tokenizer as the MapReduce word count


def term_freq(docs_rdd):
    """TF stage. Input RDD of ``(doc_id, text)``; return RDD of ``((term, doc_id), tf)``.

    Emit a ``((term, doc_id), 1)`` for every token (use ``tokenize``), then sum per key.
    """
    # TODO: flatMap each (doc_id, text) to ((term, doc_id), 1) pairs via tokenize(text),
    #       then reduceByKey to sum the counts.
    raise NotImplementedError("Phase 3: implement term_freq()")


def doc_freq(tf_rdd):
    """DF stage. Input RDD of ``((term, doc_id), tf)``; return RDD of ``(term, df)``.

    Each ``(term, doc_id)`` key is one document containing the term, so map to
    ``(term, 1)`` and sum per term.
    """
    # TODO: map each ((term, doc_id), tf) to (term, 1), then reduceByKey to get (term, df).
    raise NotImplementedError("Phase 3: implement doc_freq()")


def build_tfidf_rows(docs_rdd, num_docs: int) -> list[dict]:
    """Join TF and DF and emit TF-IDF rows (provided).

    Returns a list of ``{term, doc_id, tf, df, idf, tfidf}`` dicts (an ``action`` —
    ``collect`` — triggers the whole lazy lineage).
    """
    tf = term_freq(docs_rdd)                       # ((term, doc_id), tf)
    df = doc_freq(tf)                              # (term, df)
    tf_by_term = tf.map(lambda kv: (kv[0][0], (kv[0][1], kv[1])))  # (term, (doc_id, tf))
    joined = tf_by_term.join(df)                   # (term, ((doc_id, tf), df))

    def to_row(rec):
        term, ((doc_id, tf_val), df_val) = rec
        idf = math.log(num_docs / df_val)
        return {"term": term, "doc_id": doc_id, "tf": tf_val,
                "df": df_val, "idf": idf, "tfidf": tf_val * idf}

    return joined.map(to_row).collect()


def save_parquet(rows: list[dict], path: str) -> str:
    """Write TF-IDF rows to a Parquet file (provided). Returns the path."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    cols = ["term", "doc_id", "tf", "df", "idf", "tfidf"]
    table = pa.table({c: [r[c] for r in rows] for c in cols})
    pq.write_table(table, path)
    return path
