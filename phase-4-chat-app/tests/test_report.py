"""Phase 4 report tests — URLs, and the statelessness observation (public). (15 points.)"""

from __future__ import annotations

from autograder.points import points


@points(8)
def test_urls_recorded(report):
    assert ".run.app" in report.get("chat_url", ""), "chat_url should be a Cloud Run *.run.app URL"
    assert report.get("ui_url", "").startswith("http"), "ui_url should be your public chat UI URL"


@points(7)
def test_statelessness_observed(report):
    """Step 1 saw the history on the same instance; step 2, on a fresh instance, did not."""
    before, after = report.get("before", {}), report.get("after")
    assert before.get("chat_replies", 0) > 0, "no chat turns were exchanged (run make_report.py step 1)"
    assert before.get("history_status") == 200 and before.get("message_count", 0) == 2 * before["chat_replies"], (
        "right after chatting, the same instance should read back 2 messages per chat")
    assert after, "no recheck recorded — force a fresh instance, then run make_report.py --recheck (Task 8)"
    assert after.get("instance") != before.get("instance"), (
        "the recheck hit the SAME instance — force a new one (redeploy a revision) and re-run --recheck")
    assert after.get("history_status") == 404 and after.get("message_count", 0) == 0, (
        f"a fresh in-memory instance should know nothing about the session, but the recheck got "
        f"HTTP {after.get('history_status')} with {after.get('message_count')} messages")
