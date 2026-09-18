"""Phase 5 unit tests — offline, against the in-memory fake Firestore (no report, no cloud).

Test your transaction body (`_apply`, driven by `send_message`). Run while coding:

    python -m pytest phase-5-firestore/tests/test_units.py -p autograder.points -q

(40 points.)
"""

from __future__ import annotations

import firestore_store as fs
from autograder.points import points
from fake_firestore import FakeFirestore


@points(12)
def test_send_message_appends_and_counts():
    db = FakeFirestore()
    fs.create_session(db, "s1")
    fs.send_message(db, "s1", "user", "hello")
    fs.send_message(db, "s1", "assistant", "hi there")
    fs.send_message(db, "s1", "user", "bye")
    assert fs.get_session(db, "s1")["message_count"] == 3
    msgs = fs.list_messages(db, "s1")
    assert len(msgs) == 3
    assert {m["text"] for m in msgs} == {"hello", "hi there", "bye"}
    assert {m["role"] for m in msgs} == {"user", "assistant"}


@points(12)
def test_counter_matches_message_count():
    # The invariant the whole store relies on: the counter never drifts from the message count.
    db = FakeFirestore()
    fs.create_session(db, "s")
    for i in range(10):
        fs.send_message(db, "s", "user", f"m{i}")
    assert fs.get_session(db, "s")["message_count"] == len(fs.list_messages(db, "s")) == 10


@points(8)
def test_message_fields_stored():
    db = FakeFirestore()
    fs.create_session(db, "s")
    fs.send_message(db, "s", "user", "hello", now="2026-01-01T00:00:00")
    m = fs.list_messages(db, "s")[0]
    assert m["role"] == "user" and m["text"] == "hello" and m["created_at"] == "2026-01-01T00:00:00"


@points(8)
def test_send_message_returns_id():
    db = FakeFirestore()
    fs.create_session(db, "s")
    mid = fs.send_message(db, "s", "user", "x")
    assert isinstance(mid, str) and mid
