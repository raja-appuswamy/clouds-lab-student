# Phase 4 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests and provided scripts are given in
> full; only cloud operations are withheld.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

---

## Task 1 — Enable Firestore and create the database

**Objective.** The Firestore API enabled, and a **Native-mode** Firestore database in your
project. There is one database per project, and the location is permanent — use the `nam5`
US multi-region.

**Taught in.** Core Services M2 *Storage and Database Services* · Lecture 7

**Verified by.** Task 3 writes to it; `run_phase4.py` fails immediately without it.

> Native mode vs Datastore mode is a one-way choice. If the console offers you both, you want
> Native — the client library this phase uses expects it.


---

## Task 2 — Implement the transaction, run the offline tests

Fill the TODO in [firestore_store.py](firestore_store.py) — the `_apply` transaction body
(read the counter, append the message, bump the counter). Test it offline against the
in-memory fake Firestore (no cloud needed). This task is code — commands given in full.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt phase-4-firestore/requirements.txt
python -m pytest phase-4-firestore/tests/test_units.py -p autograder.points -q
```

---

## Task 3 — Run it against real Firestore (ACID demo)

The runner is provided — commands given in full.

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

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after running `run_phase4.py`):

```bash
python -m pytest phase-4-firestore/tests -p autograder.points -q
```

While coding, `phase-4-firestore/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

