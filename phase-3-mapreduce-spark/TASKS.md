# Phase 3 — Tasks & Deliverables

Read [README.md](README.md) first. Two environments, in this order:

- **Cloud Shell** (Tasks 1–7): code the MapReduce primitives, run them **as a cloud job** —
  every map and reduce task is a Cloud Run function invocation, Cloud Storage is the shuffle,
  and Cloud Workflows is the job tracker — then code the Spark stages.
- **Colab** (Tasks 8–13): run the Spark TF-IDF half, land the table in Cloud Storage and
  BigQuery, and write the report. All coding is done before you open Colab; the notebook only
  runs your code.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests, the workflow definition, the
> driver script and the notebook are given in full; only cloud operations are withheld. The one
> exception is Cloud Workflows, which the Google Cloud track does not cover — that command is
> given.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

---

## Task 1 — Enable the APIs

**Objective.** These APIs enabled on your project: Cloud Storage, BigQuery, Cloud Run
functions (`cloudfunctions`), Cloud Run, Cloud Build, Artifact Registry, Workflows, and
Cloud Logging.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

**Verified by.** Tasks 4–5 fail without them.


---

## Task 2 — Implement the MapReduce primitives and run the unit tests

Fill the TODOs in [mapreduce.py](mapreduce.py) — `map_wc`, `shuffle`, `reduce_wc`. (The
Spark stages come later, in Task 7, once the MapReduce job has run in the cloud.)

**Taught in.** Lecture 5 *MapReduce*

Then read — do not edit — the three provided files that turn your primitives into a cloud job,
because Tasks 3–6 deploy them and the writeup asks about them:
- [main.py](main.py) — the **worker**: one function, two task types (`map`, `reduce`).
- [workflow.yaml](workflow.yaml) — the **job tracker**: fan-out, barrier, retry.
- [run_mr.py](run_mr.py) — the **client**: uploads splits, runs the job, checks the answer.

The unit tests cover your primitives *and* the whole cloud job simulated offline against an
in-memory stand-in for Cloud Storage — so a green run here means the only thing left to get
right is the deployment. This task is code — commands given in full:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-3-mapreduce-spark/requirements.txt
python -m pytest phase-3-mapreduce-spark/tests/test_units.py -p autograder.points -q
```

---

## Task 3 — An identity for the job

**Objective.** A service account named **`mr-runner`** with exactly two project-level roles:
`roles/run.invoker` (so the workflow may call the worker) and `roles/storage.objectAdmin` (so
the worker may read and write the shuffle files in your bucket). Both the worker and the
workflow will run *as* this account.

**Taught in.** Core Services M1 *Identity and Access Management*

**Verified by.** Task 6: without `run.invoker` the workflow's calls fail with `403`; without
`objectAdmin` the worker's first read fails with `403`. Check yourself that
`gcloud projects get-iam-policy` lists the account under both roles and no others.

Why not just make the worker public, as in Phase 1? Because this function *writes to your
bucket* on request. Anyone who found the URL could fill your storage. Least privilege: the
only caller is the workflow, so the only invoker is its service account.


---

## Task 4 — Deploy the worker function

**Objective.** A **2nd-gen** (Cloud Run) Python function named **`mr-worker`**, entry point
`mr_worker`, deployed from source `phase-3-mapreduce-spark/`, running as `mr-runner`, in the
same region as your Phase 1 deployments (`us-central1`) — you will reuse it for the workflow.
It must **not** be publicly invokable — the flag you added in Phase 1 is exactly the one to leave out. Use a timeout of 300s to ensure `mr-worker` can only run up to 5 minutes.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Phase 1 Task 7

**Verified by.** `curl -X POST <URL>` with no token answers **403** (not 200, not 401 with a
body from your code). If you get 200, you made it public — redeploy. The URL you will need
in Task 6 is in the deploy output and in `gcloud functions describe`.

[.gcloudignore](.gcloudignore) keeps the upload to `main.py`, `mapreduce.py` and
`requirements.txt` — look at it to see how much of this folder the worker does *not* need.
A `403` from `curl` is the *IAM* layer of Cloud Run refusing you before any of your code
runs; that is the behaviour you want.


---

## Task 5 — Deploy the workflow (command given)

Cloud Workflows is not in the Google Cloud track, so here is the command. `REGION` must be the
same as the function's; `SA` is `mr-runner@<PROJECT>.iam.gserviceaccount.com`:

```bash
gcloud workflows deploy mr-wordcount --location=$REGION \
  --source=phase-3-mapreduce-spark/workflow.yaml --service-account=$SA
```

Before you run it, read [workflow.yaml](workflow.yaml) top to bottom — it is short, and the
writeup (Task 12) asks about it. Find the three things a job tracker does: the **fan-out**
(`parallel` + `for`), the **barrier** between the map and reduce phases (where is it? there is
no explicit step), and the **fault tolerance** (`try` / `retry`). Note which HTTP statuses the
retry predicate covers, and that the worker's simulated crash returns one of them.

**Taught in.** Lecture 5 *MapReduce* — the JobTracker / ApplicationMaster.

---

## Task 6 — Run the job, watch it, break it

Run the client from the repo root. The worker URL is the one from Task 4:

```bash
python phase-3-mapreduce-spark/run_mr.py --project <PROJECT> --region <REGION> --worker-url <URL>
```

It uploads 12 input splits, starts an execution, prints a **console link**, waits, downloads
the 4 output partitions, and compares them with the local reference. You want:

```
cloud job: 2221 distinct words in 20.3s  |  local reference: 2221 in 41 ms  |  identical: True
wrote submission/phase3_mapreduce.json — commit it; the notebook reads it.
```

**Open the console link** while it runs: the execution view shows the `map_phase` branches
running concurrently, then `reduce_phase` starting only after the last one finishes.

Now break it. Run again with **`--chaos 0.3`** — roughly a third of task *attempts* now fail
with `503`. The job should still finish with `identical: True`. In the execution's log, find a
task that failed and was retried; in **Logs Explorer**, filter on the `mr-worker` function and
find the matching `simulated worker crash` entries. Note the retry count for your writeup.

**Taught in.** Core Services M4 *Resource Monitoring* (Cloud Logging) · Fundamentals M6

**Verified by.** `submission/phase3_mapreduce.json` with `"matches_local": true`, a public
`wordcount.json` in your bucket, and the CI checks in Task 13. Both files come from the *last*
run — a chaos run is fine as the one you submit, as long as it succeeded.

**Quotas.** Each run is ~16 workflow HTTP calls (2,000/month free) and ~65 Cloud Storage writes
(5,000/month free). A handful of runs is nothing; a loop of a hundred is not. Do not script it.

**Commit and push** `submission/phase3_mapreduce.json` before Task 8 — the notebook reads it
from your clone.


---

## Task 7 — Implement the Spark stages

Still in Cloud Shell. Fill the TODOs in [spark_tfidf.py](spark_tfidf.py) — `term_freq` and
`doc_freq`, the two RDD stages (`flatMap` / `map` / `reduceByKey`). They reuse the same
`tokenize` as your MapReduce, so both halves of the phase agree on what a term is. You do not
need Spark installed to write them; the docstrings state the exact input and output shapes.

One Python trap worth knowing before you write a `flatMap`: in
`flatMap(lambda doc: X for term in ...)` the `for` binds to the *argument*, not the lambda —
Python reads it as a generator whose element is a lambda, evaluates the iterable eagerly, and
fails with `NameError: name 'doc' is not defined`. Give the lambda's body its own brackets:
`lambda doc: [X for term in ...]`.

There is no offline Spark test — the stages are graded on the output you produce in Task 9.
**Commit and push** before going on: Colab will clone your repo, and it runs whatever is on
`main`.

**Taught in.** Lecture 6 *Spark*

---

## Task 8 — Open the notebook in Colab

Upload [notebook.ipynb](notebook.ipynb) to <https://colab.research.google.com> (a CPU
runtime is fine). Edit the `git clone` URL in the first cell to **your** repo. Run sections 0
and 1: section 1 loads your `phase3_mapreduce.json` and runs the local reference next to it —
read the elapsed times.

**If you later change code in Cloud Shell** (a Spark bug, say): commit, push, then in Colab
**Runtime → Restart session** and run again from section 0. The clone cell pulls when the repo
is already there, and the restart is needed because Python keeps already-imported modules in
memory — re-running the cell alone would not pick up your fix.

---

## Task 9 — PySpark TF-IDF → Parquet

Run the Spark cells: they build the `{term, doc_id, tf, df, idf, tfidf}` table via RDD
transformations and write `tfidf.parquet`. Check the printed sample rows look right: `tf` and
`df` are small integers, `idf` is `ln(60 / df)`, and a term appearing in every document has
`idf = 0`.

**Taught in.** Lecture 6 *Spark* — watch which steps are transformations and which force an
action; you need that distinction for Task 12.

---

## Task 10 — Upload the Parquet to Cloud Storage (public)

The notebook does this in Python, not `gcloud` — Colab is not logged into gcloud, so the cell
authenticates with `google.colab.auth.authenticate_user()` and then uses the Cloud Storage
**Python client**. The bucket already exists and is public: `run_mr.py` created it in Task 6.
**Set `PROJECT`** in that cell to your Phase-0 project id.

**Taught in.** Fundamentals M4 *Storage in the Cloud* · Lecture 8 *Distributed file systems* —
object storage is the distributed file system underneath *both* halves of this phase: the
MapReduce shuffle files and this Parquet. Note in your writeup how it differs from HDFS.

Your Parquet URL is `https://storage.googleapis.com/<PROJECT>-eurecomgpt/tfidf.parquet` —
confirm it downloads in a browser.

---

## Task 11 — Load into BigQuery and query

The notebook creates a dataset, loads the Parquet from GCS into a `tfidf` table, and runs a
top-by-tfidf query. (If it errors, ensure `bigquery.googleapis.com` is enabled — Task 1.)

**Taught in.** Elastic M4 *Managed Services* · Core Services M2 *Storage and Database
Services*

---

## Task 12 — Write the comparison (writeup)

Write `submission/phase3_comparison.md` (~1 page), answering:

1. **Spark.** Which steps in `spark_tfidf.py` are **transformations** and which are
   **actions**? Where does **lineage** let Spark recover a lost partition without recomputing
   everything?
2. **Your cloud MapReduce.** Map the pieces onto Hadoop: what played the *JobTracker*, the
   *workers*, *HDFS*, the *Partitioner*? Where exactly is the barrier between the map and
   reduce phases in `workflow.yaml`? Why must a map task be **idempotent** for the retry policy
   to be safe — what would go wrong if it appended instead of overwriting? What did the chaos
   run show?
3. **Three runtimes, one job.** Compare wall time for the local reference, the cloud
   MapReduce, and local Spark. Explain the differences, and estimate the corpus size at which
   the cloud job would break even.

---

## Task 13 — Write the report, commit, push

The last notebook cell writes `submission/phase3_report.json`. Commit your `mapreduce.py`,
`spark_tfidf.py`, `submission/phase3_mapreduce.json`, `submission/phase3_report.json`, and
`submission/phase3_comparison.md`, then push. The **`autograde-phase-3`** workflow runs the
unit tests, fetches your public `wordcount.json` and Parquet, and checks the report.

```bash
python -m pytest phase-3-mapreduce-spark/tests -p autograder.points -q   # full public suite
```

---

## Task 14 — Tear down (after your grade is in)

Nothing here costs money while idle — the function scales to zero, an idle workflow is free,
and the bucket is a few MB. Still, once graded: delete the **workflow**, the **function** (which
also removes its Cloud Run service and its container image from Artifact Registry), and the
`mr-*` job folders in the bucket. Keep `wordcount.json` and `tfidf.parquet` **public until you
are graded** — the autograder fetches them on every CI run. Then check the billing report
shows €0.00 for the month, as in Phase 1.

**Taught in.** Fundamentals M6 · Phase 1 Task 11


---

## Deliverables

1. Filled `mapreduce.py` and `spark_tfidf.py`.
2. A deployed `mr-worker` function + `mr-wordcount` workflow that produced
   `submission/phase3_mapreduce.json` with `"matches_local": true`.
3. The completed **Colab notebook** (with outputs).
4. `submission/phase3_report.json`, a **public** `wordcount.json` and `tfidf.parquet` in Cloud
   Storage, and the `tfidf` table in BigQuery.
5. `submission/phase3_comparison.md` — the writeup (Task 12).
6. A **green** `autograde-phase-3` CI run.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (once the
notebook has produced the report and the uploads):

```bash
python -m pytest phase-3-mapreduce-spark/tests -p autograder.points -q
```

While coding, `phase-3-mapreduce-spark/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

