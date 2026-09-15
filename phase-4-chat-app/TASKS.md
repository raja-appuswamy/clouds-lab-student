# Phase 4 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. You need your
Phase-2 public model URL and your Phase-3 BigQuery table already in place.

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

**Objective.** Cloud Run, Artifact Registry, Cloud Build and BigQuery are all enabled on your
project.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

**Verified by.** Nothing directly — every later task fails without this.


---

## Task 2 — Implement the RAG helpers and run the unit tests

Fill the TODOs in [rag.py](rag.py) — `rank_topk` and `build_rag_prompt`. This task is code,
not cloud operations — the commands are given in full.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest phase-4-chat-app/tests/test_units.py -p autograder.points -q
```

Then read — do not edit — [server.py](server.py) and [store.py](store.py). The server keeps
chat history in a **`MemoryStore`**: a Python dict inside the running container. Task 8 is
about what that implies.

---

## Task 3 — Build the chat image and push it

**Objective.** Your chat container built from `phase-4-chat-app/` and pushed to Artifact
Registry as `$IMAGE`. (The `eurecomgpt` repository already exists from Phase 1.)

**Taught in.** Fundamentals M5 *Containers in the Cloud* · Lecture 2

**Verified by.** Task 4 deploys this image; the live-curl tests fail if it is missing.


---

## Task 4 — Deploy to Cloud Run and grant it data access

**Objective.** A public Cloud Run service named `chat` in `$REGION`, scaling to zero, with
1 GiB of memory (the model needs it) on port 8080, and with `MODEL_URL` and `BQ_TABLE` set as
environment variables. Its service account must be able to run BigQuery jobs and read BigQuery
data — otherwise `/chat` returns 500.

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

Note the `"store": "memory"` and `"instance": "..."` fields in the reply — you will need them.


---

## Task 5 — Tighten it with a custom least-privilege role

`roles/bigquery.dataViewer` is far broader than this service needs — it can read every table
in the project. Replace it with a role that grants only what the chat server actually uses.

**Objective.** A **custom IAM role** in your project (suggested id `chatBigQueryReader`)
granting exactly `bigquery.tables.get` and `bigquery.tables.getData`, bound to the Cloud Run
service account **in place of** `roles/bigquery.dataViewer` — with `/chat` still answering
afterwards.

**Taught in.** Core Services M1 *Identity and Access Management*

**Verified by.** Not autograded — but if you over-tighten it, the live-curl test in Task 9
fails, so re-run the `curl` from Task 4 before you move on. Record the role id and its
permissions in your demo notes.


---

## Task 6 — Host the chat UI on Cloud Storage

**Objective.** `phase-4-chat-app/ui/index.html` served publicly from your `$BUCKET`, so that
`https://storage.googleapis.com/$BUCKET/index.html` opens in a browser. The bucket is already
public from Phases 2–3.

**Taught in.** Fundamentals M4 *Storage in the Cloud* · *Set Up an App Dev Environment* badge

**Verified by.** The UI URL you record in your report.

Open it, paste your `$CHAT_URL` into the field, and chat. Then press **Load history** — the
server reads your session back. Keep the tab open for Task 8.


---

## Task 7 — Generate the report (step 1 of 2)

The report harness is provided — commands given in full.

```bash
python phase-4-chat-app/make_report.py --chat-url $CHAT_URL --ui-url $UI_URL
```

It chats three times in a fresh session, immediately reads the history back from the server
(expect 6 messages, on the same `instance`), and writes `submission/phase4_report.json`. Do
not commit yet — Task 8 adds to it.

---

## Task 8 — Watch it forget

**Objective.** Force Cloud Run to replace the container that answered Task 7 with a **fresh
instance** — then ask the new one for the same session.

The reliable way is to deploy a **new revision** of the service (any change will do, e.g.
setting a throwaway environment variable). Cloud Run starts fresh containers for the new
revision and drains the old ones. Waiting for the service to scale to zero (about 15 minutes
idle) achieves the same thing, more slowly.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Lecture 2 — a Cloud Run revision
is immutable; a change means a new one.

**Verified by.** Step 2 of the report:

```bash
python phase-4-chat-app/make_report.py --recheck
```

You want: a **different `instance`** id, and **HTTP 404 — the server has no memory of your
session**. (If it says *SAME instance*, the old container is still serving; redeploy and try
again.) In the browser tab from Task 6, press **Load history** and watch the conversation you
had a minute ago come back empty.

This is what *stateless* means, and it is not a bug in Cloud Run — it is the contract. A
container's memory is scratch space; anything that must outlive a request needs to live
somewhere that outlives the container. **Phase 5 is that somewhere.**


---

## Task 9 — Commit, push, confirm green CI

Commit `rag.py` and `submission/phase4_report.json`, then push. The **`autograde-phase-4`**
workflow runs the offline tests + live-curls your chat server.

---

## Task 10 — Keep it running

**Do not tear the service down.** Phase 5 redeploys `chat` with a new image that adds
Firestore; the custom role from Task 5 stays too. At `--min-instances=0` an idle Cloud Run
service costs nothing. The Phase 5 sheet has the teardown for both.

## Deliverables

1. Filled `rag.py`.
2. A deployed, public **Cloud Run** chat server + the **chat UI** on Cloud Storage.
3. `submission/phase4_report.json` with both steps (before / after the fresh instance).
4. A **green** `autograde-phase-4` CI run + a 90-second demo recording that ends with
   *Load history* coming back empty.
5. In your demo notes: the custom role id from Task 5, its two permissions, and one sentence
   on what `roles/bigquery.dataViewer` would have allowed that it does not.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after
deploying and both `make_report.py` steps):

```bash
python -m pytest phase-4-chat-app/tests -p autograder.points -q
```

While coding, `phase-4-chat-app/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

