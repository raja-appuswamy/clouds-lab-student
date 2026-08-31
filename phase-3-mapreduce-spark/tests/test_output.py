"""Phase 3 output tests — validate the TF-IDF Parquet you uploaded to public GCS.

Downloads the Parquet from ``report.tfidf.parquet_gcs_url`` and checks it is a real TF-IDF
table. No Spark needed. Keep the GCS object public until graded. (30 points.)
"""

from __future__ import annotations

from autograder.points import points

EXPECTED_COLUMNS = {"term", "doc_id", "tf", "df", "idf", "tfidf"}


@points(15)
def test_parquet_schema(parquet_table):
    cols = set(parquet_table.column_names)
    assert EXPECTED_COLUMNS.issubset(cols), (
        f"TF-IDF table must have columns {sorted(EXPECTED_COLUMNS)}, got {sorted(cols)}"
    )


@points(15)
def test_parquet_values_sane(parquet_table):
    t = parquet_table
    assert t.num_rows >= 200, f"too few TF-IDF rows ({t.num_rows}) — did the full corpus run?"
    tf = t.column("tf").to_pylist()
    df = t.column("df").to_pylist()
    idf = t.column("idf").to_pylist()
    tfidf = t.column("tfidf").to_pylist()
    assert all(v >= 1 for v in tf), "tf must be a positive raw count"
    assert all(v >= 0 for v in idf), "idf must be non-negative (ln(N/df), df<=N)"
    assert all(v >= 0 for v in tfidf), "tfidf must be non-negative"
    assert max(df) > 1, "no term appears in more than one document — df looks wrong"
