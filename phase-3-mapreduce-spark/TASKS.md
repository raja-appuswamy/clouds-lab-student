# Phase 3 — Tasks & Deliverables

Read [README.md](README.md) first. You **code** the MapReduce + Spark stages (offline tests
for MapReduce), then **run** the pipeline in **Google Colab**. Work through in order.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests and the notebook are given in full;
> only cloud operations are withheld. Most of this phase is code, so there is little to recall
> here — the heavy command practice is in Phases 1 and 5.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

---

## Task 1 — Enable the APIs

**Objective.** The Cloud Storage and BigQuery APIs enabled on your project.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

**Verified by.** Tasks 6–7 fail without them.


---

## Task 2 — Implement the code and run the unit tests

Fill the TODOs:
- [mapreduce.py](mapreduce.py) — `map_wc`, `shuffle`, `reduce_wc` (the MapReduce primitives).
- [spark_tfidf.py](spark_tfidf.py) — `term_freq`, `doc_freq` (the two RDD stages).

**Taught in.** Lecture 5 *MapReduce* · Lecture 6 *Spark*

The **MapReduce** primitives have offline unit tests (pure Python — no Spark). This task is
code — commands given in full:

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

**Taught in.** Lecture 4 *Inter-node parallelism* · Lecture 5 *MapReduce*

---

## Task 5 — PySpark TF-IDF → Parquet

Run the Spark cells: they build the `{term, doc_id, tf, df, idf, tfidf}` table via RDD
transformations and write `tfidf.parquet`. Check the printed sample rows look right.

**Taught in.** Lecture 6 *Spark* — watch which steps are transformations and which force an
action; you need that distinction for Task 8.

---

## Task 6 — Upload the Parquet to Cloud Storage (public)

The notebook does this in Python, not `gcloud` — Colab is not logged into gcloud, so the cell
authenticates with `google.colab.auth.authenticate_user()` and then uses the Cloud Storage
**Python client**, granting public read through bucket IAM (`allUsers` →
`roles/storage.objectViewer`). **Set `PROJECT`** in that cell to your Phase-0 project id.

**Taught in.** Fundamentals M4 *Storage in the Cloud* · Lecture 8 *Distributed file systems* —
object storage is the distributed file system underneath this job; note in your writeup how it
differs from HDFS.

Your Parquet URL is `https://storage.googleapis.com/<PROJECT>-eurecomgpt/tfidf.parquet` —
confirm it downloads in a browser.

---

## Task 7 — Load into BigQuery and query

The notebook creates a dataset, loads the Parquet from GCS into a `tfidf` table, and runs a
top-by-tfidf query. (If it errors, ensure `bigquery.googleapis.com` is enabled — Task 1.)

**Taught in.** Elastic M4 *Managed Services* · Core Services M2 *Storage and Database
Services*

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

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (once the notebook has produced the report and the upload):

```bash
python -m pytest phase-3-mapreduce-spark/tests -p autograder.points -q
```

While coding, `phase-3-mapreduce-spark/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

