# Phase 3 — Tasks & Deliverables

Read [README.md](README.md) first. You **code** the MapReduce + Spark stages (offline tests
for MapReduce), then **run** the pipeline in **Google Colab**. Work through in order.

---

## Task 1 — Enable the APIs

In Cloud Shell (or once from any authenticated shell):

```bash
gcloud services enable storage.googleapis.com bigquery.googleapis.com
```

---

## Task 2 — Implement the code and run the unit tests

Fill the TODOs:
- [mapreduce.py](mapreduce.py) — `map_wc`, `shuffle`, `reduce_wc` (the MapReduce primitives).
- [spark_tfidf.py](spark_tfidf.py) — `term_freq`, `doc_freq` (the two RDD stages).

The **MapReduce** primitives have offline unit tests (pure Python — no Spark):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-3-mapreduce-spark/requirements.txt
python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q
```

The **Spark** stages are graded on the output you produce (there's no offline Spark test);
you'll verify them by running the notebook and checking the TF-IDF table.

---

## Task 3 — Open the notebook in Colab

Upload [notebook.ipynb](notebook.ipynb) to <https://colab.research.google.com> (a CPU
runtime is fine). Edit the `git clone` URL in the first cell to **your** repo.

---

## Task 4 — MapReduce word count

Run the MapReduce cell. It farms the MAP phase across worker processes (`workers=4`) and
prints the top terms. Note map/shuffle/reduce for your writeup.

---

## Task 5 — PySpark TF-IDF → Parquet

Run the Spark cells: they build the `{term, doc_id, tf, df, idf, tfidf}` table via RDD
transformations and write `tfidf.parquet`. Check the printed sample rows look right.

---

## Task 6 — Upload the Parquet to Cloud Storage (public)

The notebook authenticates Colab (`google.colab.auth.authenticate_user()` — Colab is not
logged into gcloud) and uploads via the Cloud Storage **Python client**, granting public
read through bucket IAM (`allUsers` → `roles/storage.objectViewer`). **Set `PROJECT`** in
that cell to your Phase-0 project id. Your Parquet URL is
`https://storage.googleapis.com/<PROJECT>-eurecomgpt/tfidf.parquet` — confirm it downloads
in a browser.

---

## Task 7 — Load into BigQuery and query

The notebook creates a dataset, loads the Parquet from GCS into a `tfidf` table, and runs a
top-by-tfidf query. (If it errors, ensure `bigquery.googleapis.com` is enabled — Task 1.)

---

## Task 8 — Write the comparison (writeup)

Write `submission/phase3_comparison.md`: which steps are **transformations** vs **actions**;
where **lineage** helps recover from failure; and MapReduce vs Spark (lines of code,
intermediate I/O, fault-tolerance story).

---

## Task 9 — Write the report, commit, push

The last notebook cell writes `submission/phase3_report.json`. Commit your `mapreduce.py`,
`spark_tfidf.py`, `submission/phase3_report.json`, and `submission/phase3_comparison.md`,
then push. The **`autograde-phase-3`** workflow runs the MapReduce tests + validates your
public Parquet + checks the report.

```bash
python -m pytest phase-3-mapreduce-spark/tests -p autograder.points -q   # full public suite
```

## Deliverables

1. Filled `mapreduce.py` and `spark_tfidf.py`.
2. The completed **Colab notebook** (with outputs).
3. `submission/phase3_report.json` and a **public** `tfidf.parquet` in Cloud Storage + the
   `tfidf` table in BigQuery.
4. `submission/phase3_comparison.md` — the transformations/actions/lineage writeup.
5. A **green** `autograde-phase-3` CI run.

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| `map_wc` emits (word, 1) pairs | 10 | public unit test |
| `shuffle` groups by key | 10 | public unit test |
| `reduce_wc` sums per key | 10 | public unit test |
| `word_count` end-to-end | 10 | public unit test |
| TF-IDF Parquet has the right schema | 15 | public (GCS Parquet) |
| TF-IDF values are sane (tf/df/idf/tfidf) | 15 | public (GCS Parquet) |
| pipeline recorded (corpus, top terms, Parquet URL) | 8 | public (report) |
| BigQuery table + query result recorded | 7 | public (report) |
| MapReduce counts match the reference | 7 | **hidden** |
| TF-IDF table matches the reference exactly | 8 | **hidden** |
| **Total** | **100** | |

The notebook and the writeup are assessed separately by the instructor. Public checks
(75 pts) you can verify yourself once the notebook has produced the report + upload.
