# Phase 5 — OLTP storage: make the chat app remember

> New to the lab, or unsure how this phase fits? Read the **[project map](../README.md)** first — it shows what every phase builds and which later phases depend on it.

**Goal:** give the Phase-4 chat app a memory that outlives its containers. You build the
Firestore data model + a **transactional message-send**, then redeploy the *same* chat server
with Firestore as its store — and repeat Phase 4's forget-experiment with the opposite result.
Phase 6 runs its 2PC, consistency and Raft work over this exact schema.

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
means — you'll reproduce it in Phase 6A.

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
- The redeployed Cloud Run service stays at `min-instances=0` (≈ €0 idle). Tear it down after
  grading (TASKS.md); keep the Firestore data for Phase 6.

Step-by-step is in **[TASKS.md](TASKS.md)**.
