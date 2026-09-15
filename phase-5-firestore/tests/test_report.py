"""Phase 5 report tests — proof you ran the store against REAL Firestore (public).

Reads submission/phase5_report.json (written by run_phase5.py). (15 points.)
"""

from __future__ import annotations

from autograder.points import points


@points(10)
def test_transaction_kept_counter_correct(report):
    w = report.get("acid", {}).get("with_txn", {})
    assert w.get("sent", 0) >= 10, "run at least 10 concurrent sends in the ACID test"
    assert w["final_count"] == w["sent"], (
        f"with the transaction the counter must equal the sends "
        f"({w.get('final_count')} != {w.get('sent')})"
    )


@points(5)
def test_firestore_write_proof(report):
    p = report.get("proof", {})
    assert p.get("messages_sent", 0) > 0, "no messages were sent to Firestore"
    assert p["message_count"] == p["messages_sent"] == p.get("messages_listed"), (
        "session counter / messages sent / messages read back must all agree"
    )
    turn = p.get("chat_turn", {})
    assert turn.get("count_after") == turn.get("count_before", -1) + 2, (
        "one /chat call should raise the session counter by exactly 2 (user + assistant), "
        f"got {turn.get('count_before')} -> {turn.get('count_after')}")
    assert report.get("project"), "no GCP project recorded"
