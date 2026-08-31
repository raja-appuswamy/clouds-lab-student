"""Run the three distributed-correctness demos on REAL GCP and write the report (provided).

Run in Cloud Shell after implementing twopc.py + raft.py:

    python phase-6-coordination/run_phase6.py

- 6A: reproduce a lost update on Firestore, then fix it with a serializable transaction.
- 6B: a 2PC across three resource managers — messages (Firestore), quota (Firestore), audit
      (BigQuery) — using YOUR coordinator_decision / participant_outcome. Runs the happy path
      and a coordinator-crash path (which blocks the prepared RMs).
- 6C: Raft leader election with node state persisted to Firestore — normal election,
      re-election after the leader is unreachable, and a network partition (no split brain).

Writes submission/phase6_report.json. (Production would run 6B's coordinator as a Cloud
Function and 6C's nodes as three Cloud Run services; here they run from one Cloud Shell
process against the real datastores.)
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import raft
import sim
import twopc

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase6_report.json"


def demo_6a(db) -> dict:
    """Lost update (naive) vs a serializable transaction, on real Firestore."""
    from google.cloud import firestore

    tag, n = uuid.uuid4().hex[:6], 15

    def txn_send(sid, _i):
        ref = db.collection("sessions").document(sid)

        @firestore.transactional
        def _t(t):
            s = ref.get(transaction=t)
            c = (s.get("count") or 0) if s.exists else 0
            t.update(ref, {"count": c + 1})

        _t(db.transaction())

    def naive_send(sid, _i):
        ref = db.collection("sessions").document(sid)
        c = ref.get().get("count") or 0
        time.sleep(0.02)
        ref.update({"count": c + 1})

    def run(sid, fn):
        db.collection("sessions").document(sid).set({"count": 0})
        with concurrent.futures.ThreadPoolExecutor(10) as ex:
            list(ex.map(lambda i: fn(sid, i), range(n)))
        return db.collection("sessions").document(sid).get().get("count")

    return {"lost_update": {"sent": n, "with_txn": run(f"6a-txn-{tag}", txn_send),
                            "without_txn": run(f"6a-naive-{tag}", naive_send)}}


def demo_6b(db, bq, audit_table: str) -> dict:
    """2PC across messages (Firestore) + quota (Firestore) + audit (BigQuery)."""
    tag = uuid.uuid4().hex[:6]
    quota_ref = db.collection("quota").document(f"q-{tag}")
    quota_ref.set({"remaining": 5})

    # Phase 1: each RM prepares and votes.
    votes = [
        "yes",                                              # messages RM: always ready
        "yes" if (quota_ref.get().get("remaining") or 0) > 0 else "no",   # quota RM
        "yes",                                              # audit RM
    ]
    decision = twopc.coordinator_decision(votes)
    all_applied = False
    if decision == "commit":
        (db.collection("sessions").document(f"tx-{tag}")
         .collection("messages").document().set({"role": "user", "text": "2pc turn"}))
        quota_ref.update({"remaining": (quota_ref.get().get("remaining") or 0) - 1})
        bq.insert_rows_json(audit_table, [{"session": f"tx-{tag}", "event": "commit"}])
        all_applied = True
    happy = {"decision": decision, "all_applied": all_applied}

    # Coordinator crashes after prepare, before disseminating the decision.
    crash_votes = ["yes", "yes", "yes"]
    outcomes = [twopc.participant_outcome(v, None) for v in crash_votes]
    crash = {"decision": None, "blocked_rms": outcomes.count("blocked")}
    return {"happy": happy, "coordinator_crash": crash}


def demo_6c(db) -> dict:
    """Raft election with per-node durable state persisted to Firestore."""
    def persist(cluster, phase):
        for nd in cluster.nodes:
            db.collection("raft").document(f"{phase}-{nd.id}").set(
                {"term": nd.current_term, "voted_for": nd.voted_for, "state": nd.state}
            )

    c = sim.RaftCluster(3)
    leader = c.elect(0)
    persist(c, "normal")
    normal = {"leader": leader, "num_leaders": len(c.leaders())}

    reelected = c.elect(1, down={0})     # old leader unreachable
    persist(c, "reelection")
    reelection = {"leader": reelected, "term": c.nodes[1].current_term}

    cp = sim.RaftCluster(3, minority={0})
    minority_leader = cp.elect(0)
    majority_leader = cp.elect(1)
    persist(cp, "partition")
    partition = {"minority_leader": minority_leader, "majority_leader": majority_leader}

    return {"normal": normal, "reelection": reelection, "partition": partition}


def main() -> int:
    from google.cloud import bigquery, firestore

    project = subprocess.run(
        ["gcloud", "config", "get-value", "project"], capture_output=True, text=True
    ).stdout.strip()
    db = firestore.Client(project=project)
    bq = bigquery.Client(project=project)

    dataset = f"{project}.eurecomgpt"
    bq.create_dataset(bigquery.Dataset(dataset), exists_ok=True)
    audit_table = f"{dataset}.audit"
    try:
        bq.get_table(audit_table)
    except Exception:
        bq.create_table(bigquery.Table(audit_table, schema=[
            bigquery.SchemaField("session", "STRING"),
            bigquery.SchemaField("event", "STRING"),
        ]))

    print("6A: consistency (lost update vs transaction)...")
    consistency = demo_6a(db)
    print("6B: 2PC across Firestore + BigQuery...")
    twopc_res = demo_6b(db, bq, audit_table)
    print("6C: Raft election / re-election / partition...")
    raft_res = demo_6c(db)

    report = {
        "phase": "6",
        "environment": {"cloud_shell": os.environ.get("CLOUD_SHELL") == "true"},
        "project": project,
        "consistency": consistency,
        "twopc": twopc_res,
        "raft": raft_res,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
