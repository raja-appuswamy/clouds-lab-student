# Phase 6 — Tasks & Deliverables

Read [README.md](README.md) first. You **implement** the protocols (offline tests), then
**run** the demos in **Google Cloud Shell**.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests and provided scripts are given in
> full; only cloud operations are withheld. Nearly all of this phase is offline protocol code, so there is little to recall here.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

---

## Task 1 — Implement the protocols and run the offline tests

Fill the TODOs:
- [twopc.py](twopc.py) — `coordinator_decision`, `participant_outcome`.
- [raft.py](raft.py) — `start_election`, `handle_request_vote`, `has_majority`,
  `handle_append_entries`.

**Taught in.** Lecture 9 *Consistency & CAP* · Lecture 10 *Two-phase commit* · Lecture 11 *Paxos and Raft*

The simulator drives them through the failure scenarios (pure Python — no cloud):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt phase-6-coordination/requirements.txt
python -m pytest phase-6-coordination/tests/test_units.py -p autograder.points -q
```

Get all 60 points here before touching the cloud — the failure cases (2PC blocking, Raft
split-brain) are the whole point.

---

## Task 2 — Run the demos on real GCP

**Objective.** The Firestore and BigQuery APIs enabled on your project, then the provided
runner executed against them.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

**Verified by.** The report the run produces, checked by the report tests.

Enable the two APIs yourself. The runner is provided — command given in full:

```bash
python phase-6-coordination/run_phase6.py
```


This runs 6A (lost update vs transaction on Firestore), 6B (2PC across Firestore + BigQuery,
happy path + coordinator crash), and 6C (Raft election / re-election / partition with node
state in Firestore), writing `submission/phase6_report.json`. Confirm the printed results:
the transaction keeps the count exact, the coordinator crash blocks the RMs, and the minority
partition elects no leader.

---

## Task 3 — Write the distributed-correctness report

Write `submission/phase6_correctness.md`: for each anomaly/failure (lost update; 2PC happy /
coordinator-crash / RM-crash; Raft election / leader loss / partition), show the before/after,
name where it sits on the CAP + linearizable/sequential/eventual ladder, and cite the lecture
idea that fixes it.

---

## Task 4 — Commit, push, confirm green CI

Commit `twopc.py`, `raft.py`, `submission/phase6_report.json`, and
`submission/phase6_correctness.md`, then push. The **`autograde-phase-6`** workflow runs the
simulator tests + checks your report.

```bash
python -m pytest phase-6-coordination/tests -p autograder.points -q   # full public suite
```

## Deliverables

1. Filled `twopc.py` and `raft.py`.
2. `submission/phase6_report.json` from a real-GCP run.
3. `submission/phase6_correctness.md` — the before/after distributed-correctness report.
4. A **green** `autograde-phase-6` CI run.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after running `run_phase6.py`):

```bash
python -m pytest phase-6-coordination/tests -p autograder.points -q
```

While coding, `phase-6-coordination/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

