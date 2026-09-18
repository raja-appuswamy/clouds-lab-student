# Phase 4 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. You need your
Phase-2 public model URL and your Phase-3 BigQuery table already in place.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task, and recalling them is the point of the
> exercise. Code, tests and provided scripts are given in full; only cloud operations are
> withheld. The one exception is Task 5 (the custom IAM role), marked *(commands given)*.
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

Fill the TODOs in [rag.py](rag.py) — `rank_topk` and `build_rag_prompt`. Before you start,
read the README's *One request, step by step* table and the module docstring at the top of
`rag.py`: together they show where your two functions sit in the path a message takes (the
BigQuery query has already filtered the rows to the query's terms when `rank_topk` sees them)
and walk one message through the whole chain. This task is code, not cloud operations — the
commands are given in full.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-4-chat-app/requirements.txt
python -m pytest phase-4-chat-app/tests/test_units.py -p autograder.points -q
```

The tests need only pytest; the phase's own requirements are the *server's* — installing them
lets you run it locally before you build any image, which is the quickest way to see a stack
trace instead of a Cloud Run 500:

```bash
MODEL_URL=$MODEL_URL BQ_TABLE=$BQ_TABLE uvicorn --app-dir phase-4-chat-app server:app --port 8080
curl -s localhost:8080/health
```

(`/chat` works locally too — Cloud Shell's own credentials reach BigQuery.)

**To try the UI locally**, use Cloud Shell's **Web Preview** (the ⧉ button → *Preview on port
8080*). The server serves `ui/index.html` at `/` when run from the source tree, so the page and
the API share one origin — the API field is pre-filled — and you can chat and *Load history*
before any image exists. Do not type `localhost` into the API field of a previewed page: in your
browser, localhost is your laptop, not Cloud Shell.

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

## Task 5 — Tighten it with a custom least-privilege role *(commands given)*

`roles/bigquery.dataViewer` is far broader than this service needs — it can read every table
in the project. Replace it with a role that grants only what the chat server actually uses:
`bigquery.tables.get` and `bigquery.tables.getData`. The app does not need this step to work;
it is here because least privilege is the one IAM habit worth practising by hand, and Phase 6
turns the same role into Terraform.

**Objective.** A **custom IAM role** `chatBigQueryReader` with exactly those two permissions,
bound to the Cloud Run service account **in place of** `roles/bigquery.dataViewer` — with
`/chat` still answering afterwards. `CR_SA` is the service account you found in Task 4.

```bash
gcloud iam roles create chatBigQueryReader --project=$PROJECT     --title="Chat BigQuery Reader"     --permissions=bigquery.tables.get,bigquery.tables.getData     --stage=GA
gcloud projects add-iam-policy-binding $PROJECT     --member="serviceAccount:$CR_SA" --role="projects/$PROJECT/roles/chatBigQueryReader"
gcloud projects remove-iam-policy-binding $PROJECT     --member="serviceAccount:$CR_SA" --role="roles/bigquery.dataViewer"
# IAM changes take a few seconds to propagate; then confirm the service still answers
curl -s -X POST $CHAT_URL/chat -H 'Content-Type: application/json'      -d '{"session_id":"cli","message":"love and the king"}'
```

Read the three commands before running them: *create* the role, *add* the new binding, *remove*
the old one — in that order, so the service is never without a role that lets it read. Try the
`curl` in between the last two if you want to see that the custom role alone is sufficient.

**Taught in.** Core Services M1 *Identity and Access Management*

**Verified by.** Not autograded — but if the role were missing a permission, the live-curl test
in Task 9 would fail, so the `curl` above is the check. Before moving on, be able to say in one
sentence what `roles/bigquery.dataViewer` would have allowed that this role does not.

---

## Task 6 — Host the chat UI on Cloud Storage

**Objective.** `phase-4-chat-app/ui/index.html` served publicly from your `$BUCKET`, so that
`https://storage.googleapis.com/$BUCKET/index.html` opens in a browser. The bucket is already
public from Phases 2–3.

**Taught in.** Fundamentals M4 *Storage in the Cloud* · *Set Up an App Dev Environment* badge

**Verified by.** The UI URL you record in your report.

Then use it — the page is static and does not know where your service is, so **you must tell
it**:

1. Print your service URL in Cloud Shell: `echo $CHAT_URL` (from Task 4).
2. Open the UI URL in a browser. Paste `$CHAT_URL` into the **first field** — the one with the
   placeholder *Cloud Run URL, e.g. https://chat-xxx.run.app*. The page remembers it.
3. Type a message and press **Send**. The reply's footer shows `store: memory` and the
   `instance` id that answered.
4. Press **Load history** — the server reads your session back.

If *Send* answers "No API URL set", step 2 was skipped. If it answers "Failed to fetch", open
the browser console (F12): a CORS error means the deployed image predates the current
`server.py`; a 500 means the service account is missing a BigQuery role (Task 4). Keep the tab
open for Task 8.


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
instance** — then ask the new one for the same session, and see that it has never heard of it.

**How to tell containers apart.** Every reply from the server — `/chat`, `/health`, the
history — carries an `instance` field: an 8-character id such as `a781c7f8`, minted when that
container's process started. Same container → same id on every reply. New container → new id.
You can see it in three places:

- in the **UI**: each reply's grey footer line ends with `instance: …`, and *Load history* prints
  `… · instance: …` under the messages;
- from **Cloud Shell**: `curl -s $CHAT_URL/health` prints it;
- in the **report** written by `make_report.py`.

**Before you change anything**, note the id you are currently talking to: press *Load history*
in the Task 6 tab (or run the `curl`). Step 1 of the report recorded the same id as
`before.instance`.

**Now replace the container.** The reliable way is to deploy a **new revision** of the service —
any change will do, e.g. a throwaway environment variable:
`--update-env-vars=BOUNCE=$(date +%s)`. Cloud Run starts fresh containers for the new revision
and drains the old ones over a few seconds. (Waiting for the service to scale to zero — about
15 minutes idle — achieves the same thing, more slowly.)

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Lecture 2 — a Cloud Run revision
is immutable; a change means a new one.

**Then look, in this order:**

1. `curl -s $CHAT_URL/health` — the `instance` id should now be **different** from the one you
   noted. If it is the same, the old container is still draining; wait ten seconds and retry.
2. In the UI tab, press **Load history**. Instead of your conversation you get
   *(server has no memory of this session)* — that line is the UI's rendering of an **HTTP 404**
   from `/sessions/<id>/messages`. The container answering you was born after your session and
   has an empty `MemoryStore`.
3. Record it:

   ```bash
   python phase-4-chat-app/make_report.py --recheck
   ```

   It prints both ids and the status — you want *a different instance* and *HTTP 404* — and
   stores them as `after.instance` / `after.history_status`. If it prints *SAME instance as
   before*, go back to step 1.

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
4. A **green** `autograde-phase-4` CI run.

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

