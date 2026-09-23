# Phase 5 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. Your Phase-4 `chat`
service must still be deployed — this phase redeploys it.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests and provided scripts are given in
> full; only cloud operations are withheld. The one exception is the Cloud Build config in
> Task 3, which the Google Cloud track does not cover — that command is given.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

Set these once per shell session (same values as Phase 4, plus a new image tag):

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/chat:v2      # v2: with Firestore
export CHAT_URL=$(gcloud run services describe chat --region=$REGION --format='value(status.url)')
```

---

## Task 1 — Enable Firestore and create the database

**Objective.** The Firestore API enabled, and a **Native-mode** Firestore database in your
project. There is one database per project, and the location is permanent — use the `nam5`
US multi-region.

**Taught in.** Core Services M2 *Storage and Database Services* · Lecture 7

**Verified by.** Task 4 writes to it; `run_phase5.py` fails immediately without it.

> Native mode vs Datastore mode is a one-way choice. If the console offers you both, you want
> Native — the client library this phase uses expects it.


---

## Task 2 — Implement the transaction, run the offline tests

Fill the TODO in [firestore_store.py](firestore_store.py) — the `_apply` transaction body
(read the counter, append the message, bump the counter). Before you start, read the README's
*One message, step by step* table and the two docstrings in `firestore_store.py` — the module's,
which shows who calls `send_message` and how it reaches `_apply`, and `_apply`'s own, which
describes every argument you receive (`transaction`, `session_ref`, `msg_ref`, `role`, `text`,
`now`) and what you must return. The one idea to hold on to: Firestore may run your function
**more than once** for a single send, so it must contain only reads and writes through
`transaction`. Test it offline against the in-memory fake Firestore (no cloud needed). This
task is code — commands given in full.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-5-firestore/requirements.txt
python -m pytest phase-5-firestore/tests/test_units.py -p autograder.points -q
```

Then look at how Phase 4's server will use it: [`../phase-4-chat-app/store.py`](../phase-4-chat-app/store.py)
has a `FirestoreStore` class whose `store_turn` is one call to **your** `send_message`. The
server does not change at all — only which store it is given.

**Taught in.** Lecture 7 *OLTP, ACID, transactions*

---

## Task 3 — Build the Firestore-backed chat image (command given)

The image is the Phase-4 server plus your `firestore_store.py`, so it needs files from two
folders. `gcloud builds submit <dir> --tag` cannot do that (the Dockerfile must sit at the top
of the context), so this phase uses a **Cloud Build config** with the repo root as context —
not in the Google Cloud track, so here is the command:

```bash
gcloud builds submit . --config=phase-5-firestore/cloudbuild.yaml --substitutions=_IMAGE=$IMAGE
```

Read [Dockerfile](Dockerfile) and [cloudbuild.yaml](cloudbuild.yaml) (both short) — note what
is copied from where, and that `STORE_BACKEND=firestore` is baked in. The root
`.gcloudignore` keeps the upload to the source files the build needs.

**Taught in.** Fundamentals M5 *Containers in the Cloud* · Lecture 2

**Verified by.** Task 4 deploys this image.

---

## Task 4 — Redeploy `chat` on the new image and let it reach Firestore

**Objective.** The existing `chat` service updated to `$IMAGE` (a new revision — Phase 4 Task 8
was practice for this), keeping its `MODEL_URL` / `BQ_TABLE` environment and its flags; and its
service account granted the role that lets it read and write Firestore — without which every
`/chat` returns 500.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Core Services M1 *IAM* · Lecture 2

**Verified by.** `curl $CHAT_URL/health` answers `"store": "firestore"`, and the live tests in
Task 7. Check it before going on:

```bash
curl -s $CHAT_URL/health
curl -s -X POST $CHAT_URL/chat -H 'Content-Type: application/json' \
     -d '{"session_id":"cli","message":"love and the king"}'
```


---

## Task 5 — Watch it remember

Repeat Phase 4's experiment, and get the opposite result. Chat a few times (the UI from Phase 4
still works — the same URL), then force a **fresh instance** exactly as in Phase 4 Task 8, and
press **Load history**. The conversation is still there, served by a container that never saw
you type it, because it was never in the container in the first place.

**Taught in.** Lecture 2 · Lecture 7 — this is the stateless-service + durable-store pattern.

**Verified by.** Task 6's `run_phase5.py` records the same observation in a checkable way: it
writes a session into Firestore *from Cloud Shell* and the *service* reads it back.

---

## Task 6 — Run the ACID demo and the persistence proof

The runner is provided — commands given in full.

```bash
python phase-5-firestore/run_phase5.py --chat-url $CHAT_URL
```

It fires 20 concurrent sends through your transaction and through a naive non-transactional
version (transaction = exact; naive = lost updates), writes a proof session straight into
Firestore and reads it back through your public chat endpoint, sends one `/chat` and checks the
counter rose by exactly two, and writes `submission/phase5_report.json`. Confirm the
transactional counter equals 20 and the service reports `store=firestore`.

**Taught in.** Lecture 7 — lost updates are the anomaly; the transaction is the fix.

---

## Task 7 — Commit, push, confirm green CI

Commit your `firestore_store.py` and `submission/phase5_report.json`, then push. The
**`autograde-phase-5`** workflow runs the offline tests, live-curls your service to confirm the
Cloud-Shell-written session is readable and that chat turns persist, and checks your report.

```bash
python -m pytest phase-5-firestore/tests -p autograder.points -q   # full public suite
```

---

## Task 8 — Tear down, once your CI is green

Wait until `autograde-phase-5` has gone green and everything is pushed — that run live-curls
your service and is your evidence. A later push after teardown re-runs the workflow and turns
it red, so finish your pushes first.

**Commands given in full — never guess at teardown.** Phase 6 creates its own service (`chat-tf`)
from the `chat:v2` image with Terraform; it needs the Firestore database and the image, not this
service or its custom role. Keep the Firestore database, the `chat:v2` image, and the Phase-2/3
objects in your bucket.

```bash
gcloud run services delete chat --region=$REGION --quiet
gcloud iam roles delete chatBigQueryReader --project=$PROJECT --quiet
```

## Deliverables

1. Filled `firestore_store.py` (the `_apply` transaction body).
2. The `chat` service redeployed on the Firestore-backed image, still public.
3. `submission/phase5_report.json` from a real Firestore run.
4. A **green** `autograde-phase-5` CI run.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after
redeploying and running `run_phase5.py`):

```bash
python -m pytest phase-5-firestore/tests -p autograder.points -q
```

While coding, `phase-5-firestore/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

