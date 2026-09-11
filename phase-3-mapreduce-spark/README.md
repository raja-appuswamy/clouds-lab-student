# Phase 3 — Distributed data processing: MapReduce & Spark for RAG

**Goal:** prepare the retrieval corpus for your chat app two ways — classic **MapReduce**
and **Apache Spark** — then land the result in **Cloud Storage** and **BigQuery**. You build
a **TF-IDF index** that Phase 5's RAG step will query.

**Lecture map:** Lecture 4 (inter-node parallelism, RPC/network) · Lecture 5 (MapReduce) ·
Lecture 6 (Spark: RDDs, transformations vs actions, lineage).

**Environment:** **Google Cloud Shell** for the MapReduce half (it runs as a real cloud job),
then **Google Colab** for the Spark half (a CPU runtime is fine — Spark runs locally in Colab).
**Prerequisite:** Phase 1 (you have deployed a Cloud Run function before).

---

## What you build

1. **Word-count MapReduce** (`mapreduce.py`) — you implement the **map**, **shuffle**, and
   **reduce** primitives. Then you run them **as a cloud job**, with the pieces of Hadoop
   mapped onto GCP services (all provided, you deploy them):
   - *workers* → a **Cloud Run function** (`main.py`) invoked once per map / reduce task;
   - *HDFS / the shuffle* → **Cloud Storage** — mappers write one partition file per reducer,
     reducers fetch their partition from every mapper;
   - *JobTracker* → a **Cloud Workflows** definition (`workflow.yaml`) that fans the tasks out
     in parallel, waits for all mappers before starting reducers, and **retries** failed tasks;
   - *client* → `run_mr.py`, which uploads the input splits, runs the job and checks that the
     distributed answer equals the single-process one. A `--chaos` flag makes tasks fail at
     random so you can watch the retry policy save the job.
2. **PySpark TF-IDF** (`spark_tfidf.py`) — you implement the two key RDD stages (per-document
   term frequency, per-term document frequency) with `flatMap`/`map`/`reduceByKey`; the
   provided code joins them into a `{term, doc_id, tf, df, idf, tfidf}` table.
3. A Colab notebook picks up the MapReduce result, runs the Spark half, writes the TF-IDF
   table to **Parquet**, uploads it to **Cloud Storage** (public), and loads it into
   **BigQuery** for retrieval queries.

TF-IDF definitions used throughout (keep them so your output matches the grader):
`tf` = raw term count in a document · `df` = #documents containing the term ·
`idf = ln(N / df)` · `tfidf = tf * idf`.

---

## Background reading (study before the tasks)

- **MapReduce** — the original Google paper (map, shuffle, reduce):
  <https://research.google/pubs/pub62/>; Hadoop overview:
  <https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html>
- **Cloud Workflows** (the job tracker you deploy) — `parallel`, `for`, `try`/`retry`:
  <https://cloud.google.com/workflows/docs/reference/syntax/parallel-steps>
- **Apache Spark** — RDDs, **transformations vs actions**, lazy evaluation, **lineage**:
  <https://spark.apache.org/docs/latest/rdd-programming-guide.html>; PySpark:
  <https://spark.apache.org/docs/latest/api/python/>
- **TF-IDF** — what the index means: <https://en.wikipedia.org/wiki/Tf%E2%80%93idf>
- **Parquet** (columnar file format): <https://parquet.apache.org/docs/overview/>
- **BigQuery** — load from GCS, query: <https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet>

For the **writeup**, be able to explain: which steps are transformations vs actions; where
lineage recovers a lost partition without recomputing everything; which GCP service played
which Hadoop role in your cloud job, and why map tasks must be idempotent for retries to be
safe; and why the cloud job is *slower* than one process on this corpus — and at what scale
that flips.

---

## How it's graded (Spark-free, fast)

- **Offline unit tests** grade your MapReduce primitives, and run the whole cloud job — map
  tasks, shuffle files, reduce tasks — against an in-memory Cloud Storage stand-in.
- **Cloud job check**: the grader fetches the **public `wordcount.json`** your job published and
  checks it against the report; a hidden test compares the full table to the reference.
- **Output check**: the grader downloads your **TF-IDF Parquet** from its **public GCS URL**
  and checks the schema + values; a hidden test recomputes the exact table in pure Python
  and compares (tf/df are integers → exact). So your *Spark* result is graded by its output,
  not by running Spark in CI.
- **Report check**: `submission/phase3_report.json` records the Workflows execution, its
  task records, the Parquet URL + row count, and a BigQuery query result.
- The notebook + the transformations/actions/lineage **writeup** are graded by the instructor.

## Free-tier & safety

- The MapReduce job uses **Cloud Run functions** (2M invocations/month free), **Cloud
  Workflows** (2,000 external calls/month free — each run is ~16) and **Cloud Storage** writes
  (5,000/month free — each run is ~65). Run it a handful of times, not in a loop. Nothing
  costs anything while idle: the function scales to zero and an idle workflow is free.
- Spark runs **in Colab** — nothing paid on GCP for compute.
- The TF-IDF Parquet and `wordcount.json` (a few MB) go to **Cloud Storage** (≪ 5 GB free);
  they must stay public so grading can read them.
- BigQuery storage + queries are far under the free 10 GiB / 1 TiB-query limits.

Step-by-step with commands is in **[TASKS.md](TASKS.md)**.
