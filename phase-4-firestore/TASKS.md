# Phase 4 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first.

---

## Task 1 — Enable Firestore and create the database

```bash
gcloud services enable firestore.googleapis.com
# Create a Native-mode Firestore database (one per project; nam5 = US multi-region).
gcloud firestore databases create --location=nam5
```

---

## Task 2 — Implement the transaction, run the offline tests

Fill the TODO in [firestore_store.py](firestore_store.py) — the `_apply` transaction body
(read the counter, append the message, bump the counter). Test it offline against the
in-memory fake Firestore (no cloud needed):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt phase-4-firestore/requirements.txt
python -m pytest phase-4-firestore/tests/test_units.py -p autograder.points -q
```

---

## Task 3 — Run it against real Firestore (ACID demo)

```bash
python phase-4-firestore/run_phase4.py
```

This fires 20 concurrent sends through your transaction and through a naive non-transactional
version, prints the counters (transaction = exact; naive = lost updates), and writes
`submission/phase4_report.json`. Confirm the transactional counter equals 20.

---

## Task 4 — Commit, push, confirm green CI

Commit your `firestore_store.py` and `submission/phase4_report.json`, then push. The
**`autograde-phase-4`** workflow runs the offline tests + checks your report.

```bash
python -m pytest phase-4-firestore/tests -p autograder.points -q   # full public suite
```

## Deliverables

1. Filled `firestore_store.py` (the `_apply` transaction body).
2. `submission/phase4_report.json` from a real Firestore run.
3. A **green** `autograde-phase-4` CI run.

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| `send_message` appends messages + counts them | 20 | public unit test (fake Firestore) |
| counter never drifts from message count | 20 | public unit test |
| message fields (role/text/created_at) stored | 10 | public unit test |
| `send_message` returns the new message id | 10 | public unit test |
| transaction kept the counter exact on real Firestore | 15 | public (report) |
| real Firestore write proof (counter = messages) | 10 | public (report) |
| non-transactional path lost updates (the anomaly) | 10 | **hidden** |
| project id is a real GCP id | 5 | **hidden** |
| **Total** | **100** | |

Public checks (85 pts) you can verify yourself after running `run_phase4.py`; while coding,
just use `tests/test_units.py`.
