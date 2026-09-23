# Phase 5 — OLTP storage: make the chat app remember

> New to the lab, or unsure how this phase fits? Read the **[project map](../README.md)** first — it shows what every phase builds and which later phases depend on it.

**Goal:** give the Phase-4 chat app a memory that outlives its containers. You build the
Firestore data model + a **transactional message-send**, then redeploy the *same* chat server
with Firestore as its store — and repeat Phase 4's forget-experiment with the opposite result.
Phase 6's agent-built stack runs the same server against this same database.

**Lecture map:** Lecture 7 (OLTP, ACID, transaction concurrency control) · Lecture 2 (Cloud Run
revisions).

**Environment: Google Cloud Shell.** **Prerequisite:** Phase 4 (the `chat` service, still
deployed).

---

## What you build

A `firestore_store` module over this schema:

```
sessions/{session_id}                     -> {id, created_at, message_count}
sessions/{session_id}/messages/{auto_id}  -> {role, text, created_at}
```

You implement **`_apply`** — the body of `send_message`, a Firestore **transaction** that
*atomically* appends a message **and** increments the session's `message_count`. The read-
modify-write on the counter is exactly where lost updates happen without a transaction, so
this is the OLTP/ACID lesson in miniature.

Develop against the provided **in-memory `fake_firestore`** (fast, offline). Then the module
is copied into the Phase-4 chat image alongside the server, which selects the Firestore store
with `STORE_BACKEND=firestore` — every turn the app records goes through *your* transaction.
Finally `run_phase5.py` runs the ACID demo on real Firestore (20 concurrent sends: transaction
exact, naive version loses updates) and proves persistence by writing a session from Cloud Shell
and reading it back through the public chat endpoint.

```
Browser UI  ──►  Cloud Run: FastAPI chat (unchanged)
                   ├─ BigQuery  (Phase-3 TF-IDF)  → retrieve
                   ├─ NumPy GPT (Phase-2 weights) → generate
                   └─ FirestoreStore → your send_message → Firestore   ← this phase
```

### One message, step by step

Where your function sits in the path a turn takes from the server to the database:

| Step | File · function | What happens |
|---|---|---|
| 1 | `phase-4-chat-app/server.py` `chat()` | after generating the reply, calls `store_turn` twice — user turn, then assistant turn |
| 2 | `phase-4-chat-app/store.py` `FirestoreStore.store_turn()` | one line: `firestore_store.send_message(db, session_id, role, text)` |
| 3 | [firestore_store.py](firestore_store.py) `send_message()` — provided | builds `session_ref` (`sessions/{id}`) and a fresh `msg_ref` (`sessions/{id}/messages/{auto_id}`, no document yet), stamps `now` |
| 4 | [firestore_store.py](firestore_store.py) `run_in_transaction()` — provided | opens a Firestore transaction and hands your function to the client library; if Firestore aborts the commit because another transaction touched the same session (`ABORTED: cross-transaction contention`), it waits — exponential backoff with jitter — and starts over |
| 5 | **[firestore_store.py](firestore_store.py) `_apply()`** — *yours* | inside the transaction: read the session's `message_count`, `set` the message document, `update` the counter to +1, return the message id. **May be called more than once** — if another writer touched the session first, Firestore aborts and retries from the top |
| 6 | Firestore commit | both writes land, or neither |

`run_phase5.py` and the offline tests call `send_message` directly (step 3 onward) — the
contention demo fires it from 20 threads at once, which is exactly the retry in step 5 doing
its job. The module docstring in `firestore_store.py` shows the same chain as a call tree, and
`_apply`'s docstring describes each argument.

---

## Background reading (study before the tasks)

- **Firestore** data model (collections, documents, subcollections):
  <https://firebase.google.com/docs/firestore/data-model>
- **Firestore transactions** (read-modify-write, retries, atomicity):
  <https://firebase.google.com/docs/firestore/manage-data/transactions>
- **ACID** & the lost-update anomaly:
  <https://en.wikipedia.org/wiki/ACID>, <https://en.wikipedia.org/wiki/Write%E2%80%93write_conflict>
- **Cloud Run revisions** (why a redeploy gives you fresh containers):
  <https://cloud.google.com/run/docs/managing/revisions>

Be able to explain why the counter update must be inside a transaction, and what "lost update"
means — the ACID demo in this phase reproduces it on real Firestore.

---

## How it's graded

- **Offline unit tests** grade your transaction logic against the fake Firestore (no cloud).
- **Live checks** curl your public chat URL: the service reports `store: firestore`; a session
  that `run_phase5.py` wrote **from Cloud Shell** is readable through the service (the store
  outlives any one process — what Phase 4 could not do); and two chats in a fresh session read
  back as four persisted messages.
- **Report check**: `run_phase5.py` writes `submission/phase5_report.json` proving the store
  worked on *real* Firestore — the transactional counter stayed exact under 20 concurrent
  sends, and one `/chat` raised a session counter by exactly two.
- A hidden test confirms the **non-transactional** path actually lost updates (the anomaly).

## Free-tier & safety

- Firestore Always-Free is 50k reads / 20k writes per day — this phase uses a few dozen.
- The redeployed Cloud Run service stays at `min-instances=0` (≈ €0 idle). Tear it down once
  your `autograde-phase-5` run is green (TASKS.md Task 8); keep the Firestore database and the
  `chat:v2` image — Phase 6 builds on both.

The tasks, what each one must achieve and how it is checked are in **[TASKS.md](TASKS.md)**.
The `gcloud` commands are deliberately not given — you performed these operations in the Google
Cloud modules named under each task. Teardown commands *are* given in full.
