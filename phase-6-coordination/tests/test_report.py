"""Phase 6 report tests — the distributed-correctness demos on real GCP (public).

Reads submission/phase6_report.json (written by run_phase6.py). (25 points.)
"""

from __future__ import annotations

from autograder.points import points


@points(8)
def test_consistency_transaction_fixed_lost_update(report):
    c = report.get("consistency", {}).get("lost_update", {})
    assert c.get("sent", 0) >= 10, "run a meaningful contention test (>=10 writes)"
    assert c["with_txn"] == c["sent"], "the serializable transaction must keep the count exact"


@points(9)
def test_2pc_happy_path_and_blocking(report):
    tp = report.get("twopc", {})
    assert tp.get("happy", {}).get("decision") == "commit"
    assert tp["happy"].get("all_applied"), "on commit, every RM should have applied"
    assert tp.get("coordinator_crash", {}).get("blocked_rms", 0) >= 1, (
        "a coordinator crash after prepare must BLOCK prepared RMs (2PC's blocking problem)"
    )


@points(8)
def test_raft_partition_prevents_split_brain(report):
    r = report.get("raft", {})
    assert r.get("normal", {}).get("num_leaders") == 1, "exactly one leader in the normal case"
    part = r.get("partition", {})
    assert part.get("minority_leader") is None, "the minority partition must NOT elect a leader"
    assert part.get("majority_leader") is not None, "the majority partition should elect a leader"
