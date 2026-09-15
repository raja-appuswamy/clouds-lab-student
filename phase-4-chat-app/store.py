"""Where chat turns live (provided). Two backends behind one interface.

Phase 4 ships **only the in-memory backend**: turns are kept in a Python dict inside the
running container. That is deliberately the wrong place — the dict dies with the instance,
Cloud Run scales to zero when idle, and two instances never share it — and Phase 4's last task
makes you watch the history vanish. Phase 5 fixes it with the **Firestore backend**, wired to
the ``firestore_store`` module *you* write there (its transactional ``send_message``).

Selected at deploy time with the ``STORE_BACKEND`` environment variable:
    memory      (default) this container's RAM — Phase 4
    firestore   Firestore via firestore_store.py — Phase 5 (module present only in that image)

Every backend offers the same four calls, so ``server.py`` does not care which one it has.
"""

from __future__ import annotations

import datetime
import os


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class MemoryStore:
    """Per-instance dict. Fast, simple, and gone the moment the instance is."""

    name = "memory"

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def ensure_session(self, session_id: str) -> None:
        self._sessions.setdefault(
            session_id, {"id": session_id, "created_at": _utcnow(), "message_count": 0, "messages": []})

    def store_turn(self, session_id: str, role: str, text: str) -> None:
        self.ensure_session(session_id)
        s = self._sessions[session_id]
        s["messages"].append({"role": role, "text": text, "created_at": _utcnow()})
        s["message_count"] += 1

    def get_session(self, session_id: str) -> dict | None:
        s = self._sessions.get(session_id)
        return None if s is None else {k: v for k, v in s.items() if k != "messages"}

    def list_messages(self, session_id: str) -> list[dict]:
        return list(self._sessions.get(session_id, {}).get("messages", []))


class FirestoreStore:
    """Firestore, through the Phase-5 ``firestore_store`` module (your transaction)."""

    name = "firestore"

    def __init__(self):
        from google.cloud import firestore

        import firestore_store  # Phase 5 — copied into the image by phase-5-firestore/Dockerfile

        self._fs = firestore_store
        self._db = firestore.Client()

    def ensure_session(self, session_id: str) -> None:
        if self._fs.get_session(self._db, session_id) is None:
            self._fs.create_session(self._db, session_id)

    def store_turn(self, session_id: str, role: str, text: str) -> None:
        self._fs.send_message(self._db, session_id, role, text)   # atomic append + counter bump

    def get_session(self, session_id: str) -> dict | None:
        return self._fs.get_session(self._db, session_id)

    def list_messages(self, session_id: str) -> list[dict]:
        msgs = self._fs.list_messages(self._db, session_id)
        return sorted(msgs, key=lambda m: m.get("created_at", ""))


def make_store():
    backend = os.environ.get("STORE_BACKEND", "memory").lower()
    if backend == "firestore":
        return FirestoreStore()
    if backend == "memory":
        return MemoryStore()
    raise ValueError(f"STORE_BACKEND must be 'memory' or 'firestore', got {backend!r}")
