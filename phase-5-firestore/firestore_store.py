"""Reusable Firestore store for chat sessions & messages (Phase 5).

This is what makes the chat app remember. Phase 4's server kept turns in a dict inside the
container and you watched them vanish; here the same server gets this module instead
(``STORE_BACKEND=firestore``), and Phase 6's Terraform rebuilds the service on top of this
same database.

Data model:
    sessions/{session_id}                     -> {id, created_at, message_count}
    sessions/{session_id}/messages/{auto_id}  -> {role, text, created_at}

Where your code sits
--------------------
Three callers reach ``send_message`` — and every one of them ends in ``_apply``, the function
you write:

    Phase-4 server, every /chat request (twice: the user turn, then the reply)
      server.chat()
        -> store.FirestoreStore.store_turn(session_id, role, text)     phase-4-chat-app/store.py
             -> firestore_store.send_message(db, session_id, role, text)
                  -> run_in_transaction(db, func)                       opens a transaction
                       -> firestore.transactional(func)(txn)            the client library...
                            -> _apply(txn, session_ref, msg_ref, role, text, now)   ...calls YOU

    run_phase5.py (Cloud Shell): the ACID demo and the persistence proof
      -> send_message(...) directly, 20 at a time from threads     -> _apply, under contention

    tests/test_units.py: offline, against fake_firestore
      -> send_message(...)                                          -> _apply, no network

``send_message`` (provided) does the setup — makes ``session_ref`` and a fresh ``msg_ref`` with
an auto-generated id, stamps ``now`` — and hands them to ``_apply`` inside a transaction.
``_apply`` does the four operations that must succeed or fail *together*: read the counter,
write the message, write the counter + 1, return the id. The split exists because Firestore
may run ``_apply`` **more than once**: if another writer changed the session between your read
and your commit, the library aborts, waits, and calls ``_apply`` again from the top. That retry
is what makes 20 concurrent sends end with a counter of exactly 20 — and it is why the body
must contain nothing but reads and writes through ``transaction``.

Develop against the in-memory ``fake_firestore`` (offline unit tests), then run against real
Firestore in ``run_phase5.py``. The same code works on both — the real client and the fake
expose the same methods — and the same file is copied into the chat image, so the server's
every turn goes through *your* transaction.
"""

from __future__ import annotations

import datetime
import random
import time


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def create_session(db, session_id: str) -> None:
    """Create (or reset) a session document with a zeroed message counter (provided)."""
    db.collection("sessions").document(session_id).set(
        {"id": session_id, "created_at": _utcnow(), "message_count": 0}
    )


def _apply(transaction, session_ref, msg_ref, role: str, text: str, now: str) -> str:
    """Transaction body: append the message AND bump the session counter, atomically.

    Called by the Firestore client library (via ``run_in_transaction``), not by you — possibly
    several times for one ``send_message`` if a concurrent writer forces a retry. It must do
    ONLY reads and writes through ``transaction``; no prints, no other side effects.

    Arguments — all prepared by ``send_message``:

    ``transaction``
        The open transaction. Every read goes through it (``ref.get(transaction=transaction)``)
        and every write is a method on it (``transaction.set(ref, data)``,
        ``transaction.update(ref, fields)``). Nothing is written when these lines run — the
        writes are queued and applied at commit, all or none. On the fake it is a
        ``FakeTransaction`` with the same three methods.
    ``session_ref``
        A ``DocumentReference`` to ``sessions/{session_id}``. Its document holds
        ``message_count`` — the field you read, add 1 to, and write back. It usually exists
        (``create_session`` or a previous send made it); treat a missing document or a missing
        field as a count of 0.
    ``msg_ref``
        A ``DocumentReference`` to ``sessions/{session_id}/messages/{auto_id}`` — a new id was
        generated but **no document exists yet**; ``transaction.set(msg_ref, ...)`` creates it.
    ``role``, ``text``
        The message: ``"user"`` or ``"assistant"``, and its content. Stored verbatim.
    ``now``
        An ISO-8601 UTC timestamp string, stamped once by ``send_message`` so a retried
        transaction stores the same time.

    Returns ``msg_ref.id`` (the auto-generated message id) — ``send_message`` passes it back
    to its caller.

    Why the read must be inside the transaction: ``run_phase5.py``'s "naive" version reads the
    counter *outside*, then writes — and two concurrent sends both read 5 and both write 6,
    losing an update. Inside the transaction, Firestore notices the conflict and retries one of
    them, so the second reads 6 and writes 7.
    """
    # TODO:
    #   1. read the session snapshot via session_ref.get(transaction=transaction)
    #   2. count = its "message_count" (0 if the field/doc is missing)
    #   3. transaction.set(msg_ref, {"role": role, "text": text, "created_at": now})
    #   4. transaction.update(session_ref, {"message_count": count + 1})
    #   5. return msg_ref.id
    raise NotImplementedError("Phase 5: implement _apply()")


def run_in_transaction(db, func, *, rounds: int = 6):
    """Run ``func(transaction)`` in a Firestore transaction — works on real + fake (provided).

    Firestore lets only one of two transactions that touch the same document commit; the
    others fail with ``ABORTED: cross-transaction contention`` and must start over. The client
    library retries five times back to back, then gives up with
    ``ValueError("Failed to commit transaction in 5 attempts")``. Twenty threads on one session
    document exceed that easily, so this wraps the library in ``rounds`` further tries with
    exponential backoff and jitter — the standard remedy for contention under optimistic
    concurrency. Every retry re-runs ``func`` from the top, which is why ``_apply`` must contain
    nothing but reads and writes through the transaction object.
    """
    txn = db.transaction()
    if getattr(txn, "_fake", False):
        return func(txn)
    from google.api_core import exceptions as gexc  # imported lazily so offline tests need no GCP deps
    from google.cloud import firestore

    delay = 0.05
    for attempt in range(rounds):
        try:
            return firestore.transactional(func)(txn)
        except (gexc.Aborted, ValueError) as exc:
            gave_up = isinstance(exc, gexc.Aborted) or "Failed to commit transaction" in str(exc)
            if not gave_up or attempt == rounds - 1:
                raise
            time.sleep(delay + random.uniform(0, delay))
            delay = min(delay * 2, 2.0)
            txn = db.transaction()


def send_message(db, session_id: str, role: str, text: str, now: str | None = None) -> str:
    """Atomically append a message to a session and increment its counter. Returns message id."""
    now = now or _utcnow()
    session_ref = db.collection("sessions").document(session_id)
    msg_ref = session_ref.collection("messages").document()
    return run_in_transaction(db, lambda t: _apply(t, session_ref, msg_ref, role, text, now))


def get_session(db, session_id: str) -> dict | None:
    """Return the session document, or None if it doesn't exist (provided)."""
    return db.collection("sessions").document(session_id).get().to_dict()


def list_messages(db, session_id: str) -> list[dict]:
    """Return all messages in a session (provided)."""
    coll = db.collection("sessions").document(session_id).collection("messages")
    return [snap.to_dict() for snap in coll.stream()]
