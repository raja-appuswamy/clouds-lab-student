# Phase 4 — OLTP storage: Firestore sessions & messages

**Goal:** build the Firestore data model + **transactional message-send** that the rest of the
lab is built on. Phase 5 stores every chat turn here; Phase 6 runs its 2PC, consistency, and
Raft work over this exact schema. You package it as a reusable **`firestore_store`** module.

**Lecture map:** Lecture 7 (OLTP, ACID, transaction concurrency control).

Estimated time: ~4 hours. **Environment: Google Cloud Shell** (no Colab, no GPU — just the
Firestore client). **Prerequisite:** Phase 0 (a GCP project + `gcloud`).

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

Develop against the provided **in-memory `fake_firestore`** (fast, offline), then run the same
code against real Firestore in `run_phase4.py`, which also demonstrates ACID: 20 concurrent
sends through your transaction keep the counter exact, while a naive non-transactional version
loses updates.

---

## Background reading (study before the tasks)

- **Firestore** data model (collections, documents, subcollections):
  <https://firebase.google.com/docs/firestore/data-model>
- **Firestore transactions** (read-modify-write, retries, atomicity):
  <https://firebase.google.com/docs/firestore/manage-data/transactions>
- **ACID** & the lost-update anomaly:
  <https://en.wikipedia.org/wiki/ACID>, <https://en.wikipedia.org/wiki/Write%E2%80%93write_conflict>

Be able to explain why the counter update must be inside a transaction, and what "lost update"
means — you'll reproduce it in Phase 6A.

---

## How it's graded

- **Offline unit tests** grade your transaction logic against the fake Firestore (no cloud).
- **Report check**: `run_phase4.py` writes `submission/phase4_report.json` proving the store
  worked on *real* Firestore — the transactional counter stayed exact under 20 concurrent
  sends, and a proof session's counter matches its messages.
- A hidden test confirms the **non-transactional** path actually lost updates (the anomaly).

## Free-tier & safety

- Firestore Always-Free is 50k reads / 20k writes per day — this phase uses a few dozen.
- Nothing else is provisioned; delete the test sessions afterward if you like.

Step-by-step is in **[TASKS.md](TASKS.md)**.
