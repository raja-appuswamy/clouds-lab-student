# Phase 3 — Distributed data processing: MapReduce & Spark for RAG

**Goal:** prepare the retrieval corpus for your chat app two ways — classic **MapReduce**
and **Apache Spark** — then land the result in **Cloud Storage** and **BigQuery**. You build
a **TF-IDF index** that Phase 5's RAG step will query.

**Lecture map:** Lecture 4 (inter-node parallelism, RPC/network) · Lecture 5 (MapReduce) ·
Lecture 6 (Spark: RDDs, transformations vs actions, lineage).

Estimated time: ~8 hours. **Environment: Google Colab** (a CPU runtime is fine — Spark runs
locally in Colab). **Prerequisite:** Phase 0 (a GCP project + `gcloud`).

---

## What you build

1. **Word-count MapReduce** (`mapreduce.py`) with Python **multiprocessing** as a Hadoop
   stand-in — you implement the **map**, **shuffle**, and **reduce** primitives.
2. **PySpark TF-IDF** (`spark_tfidf.py`) — you implement the two key RDD stages (per-document
   term frequency, per-term document frequency) with `flatMap`/`map`/`reduceByKey`; the
   provided code joins them into a `{term, doc_id, tf, df, idf, tfidf}` table.
3. A Colab notebook drives both, writes the TF-IDF table to **Parquet**, uploads it to
   **Cloud Storage** (public), and loads it into **BigQuery** for retrieval queries.

TF-IDF definitions used throughout (keep them so your output matches the grader):
`tf` = raw term count in a document · `df` = #documents containing the term ·
`idf = ln(N / df)` · `tfidf = tf * idf`.

---

## Background reading (study before the tasks)

- **MapReduce** — the original Google paper (map, shuffle, reduce):
  <https://research.google/pubs/pub62/>; Hadoop overview:
  <https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html>
- **Apache Spark** — RDDs, **transformations vs actions**, lazy evaluation, **lineage**:
  <https://spark.apache.org/docs/latest/rdd-programming-guide.html>; PySpark:
  <https://spark.apache.org/docs/latest/api/python/>
- **TF-IDF** — what the index means: <https://en.wikipedia.org/wiki/Tf%E2%80%93idf>
- **Parquet** (columnar file format): <https://parquet.apache.org/docs/overview/>
- **BigQuery** — load from GCS, query: <https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet>

For the **writeup**, be able to explain: which steps are transformations vs actions; where
lineage recovers a lost partition without recomputing everything; and how the MapReduce and
Spark versions compare (lines of code, intermediate disk I/O, fault tolerance).

---

## How it's graded (Spark-free, fast)

- **Offline unit tests** grade your MapReduce primitives (pure Python — no Spark).
- **Output check**: the grader downloads your **TF-IDF Parquet** from its **public GCS URL**
  and checks the schema + values; a hidden test recomputes the exact table in pure Python
  and compares (tf/df are integers → exact). So your *Spark* result is graded by its output,
  not by running Spark in CI.
- **Report check**: `submission/phase3_report.json` records the MapReduce top terms, the
  Parquet URL + row count, and a BigQuery query result.
- The notebook + the transformations/actions/lineage **writeup** are graded by the instructor.

## Free-tier & safety

- Spark runs **in Colab** — nothing paid on GCP for compute.
- The TF-IDF Parquet (a few MB) goes to **Cloud Storage** (≪ 5 GB free); make that one object
  public so grading can read it.
- BigQuery storage + queries are far under the free 10 GiB / 1 TiB-query limits.

Step-by-step with commands is in **[TASKS.md](TASKS.md)**.
