"""Store chat turns in Firestore using the Phase-4 schema (provided).

Same ``sessions``/``messages`` model and transactional counter as Phase 4 — Phase 5 just
consumes it, so every chat turn is recorded atomically.
"""

from __future__ import annotations

import datetime


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def ensure_session(db, session_id: str) -> None:
    ref = db.collection("sessions").document(session_id)
    if not ref.get().exists:
        ref.set({"id": session_id, "created_at": _utcnow(), "message_count": 0})


def store_turn(db, session_id: str, role: str, text: str) -> str:
    """Append a turn and bump the session counter atomically (Phase-4 transaction)."""
    from google.cloud import firestore

    session_ref = db.collection("sessions").document(session_id)
    msg_ref = session_ref.collection("messages").document()

    @firestore.transactional
    def _txn(transaction):
        snap = session_ref.get(transaction=transaction)
        count = (snap.get("message_count") or 0) if snap.exists else 0
        transaction.set(msg_ref, {"role": role, "text": text, "created_at": _utcnow()})
        transaction.update(session_ref, {"message_count": count + 1})

    _txn(db.transaction())
    return msg_ref.id
