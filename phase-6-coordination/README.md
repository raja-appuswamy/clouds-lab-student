# Phase 6 — Distributed coordination: 2PC & a toy Raft

**Goal:** make the chat app correct under partial failure — the hardest lecture material put
into practice. You implement the **two-phase commit** and **Raft** protocols, prove they
behave correctly (including under coordinator crashes and network partitions), and reproduce
the consistency anomalies they defend against.

**Lecture map:** Lecture 9 (consistency models, CAP) · Lecture 10 (2PC) · Lecture 11 (Raft).

Estimated time: ~12 hours over two weeks — the heaviest phase (it carries the most grade
weight). **Environment: Google Cloud Shell.** **Prerequisite:** Phase 4 (Firestore).

---

## What you build

Two protocol implementations, each a handful of pure functions the offline **simulator**
drives through failure scenarios:

- **`twopc.py`** — `coordinator_decision` (commit iff all vote yes) and `participant_outcome`
  (commit / abort / **blocked** when the coordinator crashes — 2PC's blocking problem).
- **`raft.py`** — `start_election`, `handle_request_vote` (the rule that prevents two leaders
  in a term), `has_majority`, and `handle_append_entries` (log replication).

Then `run_phase6.py` exercises all three lecture ideas on **real GCP**:
- **6A — consistency:** reproduce a lost update on Firestore, then fix it with a transaction.
- **6B — 2PC across services:** a distributed commit over messages (Firestore), quota
  (Firestore), and an audit log (BigQuery), plus a coordinator-crash run that blocks.
- **6C — Raft:** leader election with node state persisted to Firestore — normal election,
  re-election after the leader is lost, and a partition (no split brain).

---

## Background reading (study before the tasks)

- **CAP theorem & consistency models** (linearizable → sequential → causal → eventual):
  <https://en.wikipedia.org/wiki/CAP_theorem>, <https://jepsen.io/consistency>
- **Two-phase commit** and why it **blocks** on coordinator failure:
  <https://en.wikipedia.org/wiki/Two-phase_commit_protocol>
- **Raft** — the paper + the visualization (leader election, log replication, safety):
  <https://raft.github.io/>, <https://raft.github.io/raft.pdf>

For the **distributed-correctness report**, be able to explain, for each anomaly/failure:
the before/after, which point on the consistency ladder it sits at, and which lecture idea
fixes it.

---

## How it's graded

- **Offline unit tests** run your 2PC + Raft through the simulator — happy path, abort,
  coordinator crash (blocking), single-leader election, re-election, and partition
  (split-brain prevention). This is the rigorous, protocol-correctness part.
- **Report check**: `submission/phase6_report.json` (from `run_phase6.py`) records the
  real-GCP demos — the transaction fixing the lost update, the 2PC happy/blocking outcomes,
  and the Raft election/partition results.

## Free-tier & safety

- A few dozen Firestore writes + a couple of BigQuery inserts — far under the free tier.

Step-by-step is in **[TASKS.md](TASKS.md)**.
