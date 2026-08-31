"""A tiny in-memory stand-in for google-cloud-firestore (provided).

Just enough of the API surface that ``firestore_store`` uses, so you can develop and unit-
test your transaction logic offline — no GCP credentials, no network. The real Firestore
client (``google.cloud.firestore.Client``) exposes the same methods, so code that works
here works against the real thing.

NOTE: this fake applies transaction writes immediately (single-threaded); it verifies your
read-modify-write *logic*, not real concurrency. The actual ACID/contention behaviour you
demonstrate against real Firestore in ``run_phase4.py``.
"""

from __future__ import annotations


class _Node:
    """One document: ``fields`` is None until it exists; ``subs`` holds subcollections."""

    def __init__(self):
        self.fields = None
        self.subs: dict[str, dict[str, "_Node"]] = {}


class FakeSnapshot:
    def __init__(self, doc_id: str, node: _Node):
        self.id = doc_id
        self._node = node

    @property
    def exists(self) -> bool:
        return self._node.fields is not None

    def get(self, field: str):
        return (self._node.fields or {}).get(field)

    def to_dict(self):
        return dict(self._node.fields) if self._node.fields is not None else None


class FakeDocRef:
    def __init__(self, db: "FakeFirestore", docs: dict, doc_id: str, node: _Node):
        self._db = db
        self._docs = docs
        self.id = doc_id
        self._node = node

    def get(self, transaction=None) -> FakeSnapshot:
        return FakeSnapshot(self.id, self._node)

    def set(self, data: dict) -> None:
        self._node.fields = dict(data)

    def update(self, data: dict) -> None:
        self._node.fields = {**(self._node.fields or {}), **data}

    def collection(self, name: str) -> "FakeCollection":
        return FakeCollection(self._db, self._node.subs.setdefault(name, {}))


class FakeCollection:
    def __init__(self, db: "FakeFirestore", docs: dict[str, _Node]):
        self._db = db
        self._docs = docs

    def document(self, doc_id: str | None = None) -> FakeDocRef:
        if doc_id is None:
            doc_id = self._db._next_id()
        node = self._docs.setdefault(doc_id, _Node())
        return FakeDocRef(self._db, self._docs, doc_id, node)

    def stream(self):
        return [FakeSnapshot(i, n) for i, n in self._docs.items() if n.fields is not None]


class FakeTransaction:
    """Mimics google's transaction object; writes apply immediately in this fake."""

    _fake = True

    def get(self, ref: FakeDocRef) -> FakeSnapshot:
        return ref.get()

    def set(self, ref: FakeDocRef, data: dict) -> None:
        ref.set(data)

    def update(self, ref: FakeDocRef, data: dict) -> None:
        ref.update(data)


class FakeFirestore:
    def __init__(self):
        self._root: dict[str, dict[str, _Node]] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"auto-{self._counter:06d}"

    def collection(self, name: str) -> FakeCollection:
        return FakeCollection(self, self._root.setdefault(name, {}))

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()
