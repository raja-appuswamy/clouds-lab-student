"""Phase 5 report tests — URLs + Firestore storage proof (public). (15 points.)"""

from __future__ import annotations

from autograder.points import points


@points(8)
def test_urls_recorded(report):
    assert ".run.app" in report.get("chat_url", ""), "chat_url should be a Cloud Run *.run.app URL"
    assert report.get("ui_url", "").startswith("http"), "ui_url should be your public chat UI URL"


@points(7)
def test_turns_stored_in_firestore(report):
    p = report.get("proof", {})
    replies = p.get("chat_replies", 0)
    assert replies > 0, "no chat turns were exchanged"
    # Each chat stores two messages (user + assistant), via the Phase-4 transaction.
    assert p.get("message_count", 0) == 2 * replies, (
        f"expected {2 * replies} stored messages, got {p.get('message_count')}"
    )
