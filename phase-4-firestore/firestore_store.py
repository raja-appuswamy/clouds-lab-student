"""Reusable Firestore store for chat sessions & messages (Phase 4).

Phases 5 and 6 ``import`` this module: Phase 5 records every chat turn with `send_message`;
Phase 6 builds 2PC / consistency / Raft work on the same schema.

Data model:
    sessions/{session_id}                     -> {id, created_at, message_count}
    sessions/{session_id}/messages/{auto_id}  -> {role, text, created_at}

You implement the transaction body ``_apply`` — the read-modify-write that must be atomic.
Develop against the in-memory ``fake_firestore`` (offline unit tests), then run against real
Firestore in ``run_phase4.py``. The same code works on both — the real client and the fake
expose the same methods.
"""

from __future__ import annotations

import datetime


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def create_session(db, session_id: str) -> None:
    """Create (or reset) a session document with a zeroed message counter (provided)."""
    db.collection("sessions").document(session_id).set(
        {"id": session_id, "created_at": _utcnow(), "message_count": 0}
    )


def _apply(transaction, session_ref, msg_ref, role: str, text: str, now: str) -> str:
    """Transaction body: append the message AND bump the session counter, atomically.

    Uses ``transaction`` for all reads/writes so the whole thing commits or aborts as a unit.
    Returns the new message id.
    """
    # TODO:
    #   1. read the session snapshot via session_ref.get(transaction=transaction)
    #   2. count = its "message_count" (0 if the field/doc is missing)
    #   3. transaction.set(msg_ref, {"role": role, "text": text, "created_at": now})
    #   4. transaction.update(session_ref, {"message_count": count + 1})
    #   5. return msg_ref.id
    raise NotImplementedError("Phase 4: implement _apply()")


def run_in_transaction(db, func):
    """Run ``func(transaction)`` in a Firestore transaction — works on real + fake (provided)."""
    txn = db.transaction()
    if getattr(txn, "_fake", False):
        return func(txn)
    from google.cloud import firestore  # imported lazily so offline tests need no GCP deps

    return firestore.transactional(func)(txn)


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
