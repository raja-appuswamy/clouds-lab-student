# Phase 5 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. You need your
Phase-2 public model URL, Phase-3 BigQuery table, and Phase-4 Firestore already in place.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task, and recalling them is the point of the
> exercise. Code, tests and provided scripts are given in full; only cloud operations are
> withheld.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help` (e.g. `gcloud run --help`); then the CLI reference at
> <https://cloud.google.com/sdk/gcloud/reference>. Worked commands are released after the
> submission deadline.

Set these once per shell session:

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/chat:v1
export MODEL_URL=https://storage.googleapis.com/$PROJECT-eurecomgpt/model.safetensors  # Phase 2
export BQ_TABLE=$PROJECT.eurecomgpt.tfidf                                               # Phase 3
export BUCKET=$PROJECT-eurecomgpt
```

---

## Task 1 — Enable the APIs

**Objective.** Cloud Run, Artifact Registry, Cloud Build, BigQuery and Firestore are all
enabled on your project.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

**Verified by.** Nothing directly — every later task fails without this.


---

## Task 2 — Implement the RAG helpers and run the unit tests

Fill the TODOs in [rag.py](rag.py) — `rank_topk` and `build_rag_prompt`. This task is code,
not cloud operations — the commands are given in full.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest phase-5-chat-app/tests/test_units.py -p autograder.points -q
```

---

## Task 3 — Build the chat image and push it

**Objective.** Your chat container built from `phase-5-chat-app/` and pushed to Artifact
Registry as `$IMAGE`. (The `eurecomgpt` repository already exists from Phase 1.)

**Taught in.** Fundamentals M5 *Containers in the Cloud* · Lecture 2

**Verified by.** Task 4 deploys this image; the live-curl tests fail if it is missing.


---

## Task 4 — Deploy to Cloud Run and grant it data access

**Objective.** A public Cloud Run service named `chat` in `$REGION`, scaling to zero, with
1 GiB of memory (the model needs it) on port 8080, and with `MODEL_URL` and `BQ_TABLE` set as
environment variables. Its service account must be able to run BigQuery jobs, read BigQuery
data, and read/write Firestore — otherwise `/chat` returns 500.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Core Services M1 *IAM* ·
Lecture 2

**Verified by.** A live-curl test against the `*.run.app` URL in your report.

Three sub-problems: deploy the service with the right flags and environment; find out which
service account it actually runs as; bind the roles that account needs. Then confirm it
answers before moving on:

```bash
curl -s -X POST $CHAT_URL/chat -H 'Content-Type: application/json' \
     -d '{"session_id":"cli","message":"love and the king"}'
```


---

## Task 5 — Tighten it with a custom least-privilege role

`roles/bigquery.dataViewer` is far broader than this service needs — it can read every table
in the project. Replace it with a role that grants only what the chat server actually uses.

**Objective.** A **custom IAM role** in your project (suggested id `chatBigQueryReader`)
granting exactly `bigquery.tables.get` and `bigquery.tables.getData`, bound to the Cloud Run
service account **in place of** `roles/bigquery.dataViewer` — with `/chat` still answering
afterwards.

**Taught in.** Core Services M1 *Identity and Access Management*

**Verified by.** Not autograded — but if you over-tighten it, the live-curl test in Task 8
fails, so re-run the `curl` from Task 4 before you move on. Record the role id and its
permissions in your report.


---

## Task 6 — Host the chat UI on Cloud Storage

**Objective.** `phase-5-chat-app/ui/index.html` served publicly from your `$BUCKET`, so that
`https://storage.googleapis.com/$BUCKET/index.html` opens in a browser. The bucket is already
public from Phases 2–3.

**Taught in.** Fundamentals M4 *Storage in the Cloud* · *Set Up an App Dev Environment* badge

**Verified by.** The UI URL you record in your report.

Open it, paste your `$CHAT_URL` into the field, and chat.


---

## Task 7 — Generate the report

The report harness is provided — commands given in full.

```bash
python phase-5-chat-app/make_report.py --chat-url $CHAT_URL --ui-url $UI_URL
```

This chats a few times and reads Firestore back to prove the turns were stored, writing
`submission/phase5_report.json`.

---

## Task 8 — Commit, push, confirm green CI

Commit `rag.py` and `submission/phase5_report.json`, then push. The **`autograde-phase-5`**
workflow runs the offline tests + live-curls your chat server.

---

## Task 9 — Tear down (after you're graded)

**Commands given in full — never guess at teardown.**

```bash
gcloud run services delete chat --region=$REGION --quiet
gcloud iam roles delete chatBigQueryReader --project=$PROJECT --quiet
```

## Deliverables

1. Filled `rag.py`.
2. A deployed, public **Cloud Run** chat server + the **chat UI** on Cloud Storage.
3. `submission/phase5_report.json`.
4. A **green** `autograde-phase-5` CI run + a 90-second demo recording.
5. In your demo notes: the custom role id from Task 5, its two permissions, and one sentence
   on what `roles/bigquery.dataViewer` would have allowed that it does not.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after deploying and running `make_report.py`):

```bash
python -m pytest phase-5-chat-app/tests -p autograder.points -q
```

While coding, `phase-5-chat-app/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

