# Phase 6 — Tasks & Deliverables

Read [README.md](README.md) first. You **implement** the protocols (offline tests), then
**run** the demos in **Google Cloud Shell**.

---

## Task 1 — Implement the protocols and run the offline tests

Fill the TODOs:
- [twopc.py](twopc.py) — `coordinator_decision`, `participant_outcome`.
- [raft.py](raft.py) — `start_election`, `handle_request_vote`, `has_majority`,
  `handle_append_entries`.

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

```bash
gcloud services enable firestore.googleapis.com bigquery.googleapis.com
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

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| 2PC commits when all vote yes | 8 | public unit test |
| 2PC aborts on any no | 8 | public unit test |
| 2PC blocks on coordinator crash | 9 | public unit test |
| Raft elects a single leader | 10 | public unit test |
| Raft re-elects after the leader is lost | 8 | public unit test |
| Raft partition prevents split brain | 10 | public unit test |
| Raft replicates + commits on majority | 7 | public unit test |
| transaction fixes the lost update (real Firestore) | 8 | public (report) |
| 2PC happy path + blocking (real Firestore/BigQuery) | 9 | public (report) |
| Raft partition elects no minority leader (real) | 8 | public (report) |
| coordinator crash left the decision unknown | 8 | **hidden** |
| Raft re-election + real project id | 7 | **hidden** |
| **Total** | **100** | |

The `phase6_correctness.md` report is assessed separately by the instructor. Public checks
(85 pts) you can verify after `run_phase6.py`; while coding, just use `tests/test_units.py`.
