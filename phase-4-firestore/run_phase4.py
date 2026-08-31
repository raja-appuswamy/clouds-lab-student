"""Run the Firestore store against REAL Firestore + demonstrate ACID (provided).

Run in Cloud Shell (authenticated) after implementing `_apply` in firestore_store.py:

    python phase-4-firestore/run_phase4.py

It fires concurrent sends two ways — through your transaction (`send_message`) and through a
naive non-transactional read-modify-write — and shows the transaction keeps the counter exact
while the naive version loses updates under contention. Writes submission/phase4_report.json.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import firestore_store as fs

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase4_report.json"


def _naive_send(db, session_id: str, role: str, text: str) -> None:
    """NON-transactional read-modify-write — the anti-pattern that loses updates."""
    ref = db.collection("sessions").document(session_id)
    count = ref.get().get("message_count") or 0
    time.sleep(0.02)  # widen the race window so lost updates are reliably visible
    ref.collection("messages").document().set({"role": role, "text": text, "created_at": fs._utcnow()})
    ref.update({"message_count": count + 1})


def _concurrent(db, session_id: str, send_fn, n: int, workers: int = 10) -> int:
    fs.create_session(db, session_id)
    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda i: send_fn(db, session_id, "user", f"m{i}"), range(n)))
    return fs.get_session(db, session_id)["message_count"]


def main() -> int:
    from google.cloud import firestore

    project = subprocess.run(
        ["gcloud", "config", "get-value", "project"], capture_output=True, text=True
    ).stdout.strip()
    db = firestore.Client(project=project)
    tag = uuid.uuid4().hex[:6]
    n = 20

    print("Running ACID contention test (20 concurrent sends each way)...")
    with_final = _concurrent(db, f"acid-txn-{tag}", fs.send_message, n)
    without_final = _concurrent(db, f"acid-naive-{tag}", _naive_send, n)
    print(f"  with transaction:    counter = {with_final} / {n}  (should be {n})")
    print(f"  without transaction: counter = {without_final} / {n}  (lost {n - without_final})")

    # A clean proof session written purely through send_message.
    proof_id = f"proof-{tag}"
    fs.create_session(db, proof_id)
    k = 5
    for i in range(k):
        fs.send_message(db, proof_id, "user", f"hi {i}")
    sess = fs.get_session(db, proof_id)

    report = {
        "phase": "4",
        "environment": {"cloud_shell": os.environ.get("CLOUD_SHELL") == "true"},
        "project": project,
        "acid": {
            "with_txn": {"sent": n, "final_count": with_final},
            "without_txn": {"sent": n, "final_count": without_final},
        },
        "proof": {
            "session_id": proof_id,
            "messages_sent": k,
            "message_count": sess["message_count"],
            "messages_listed": len(fs.list_messages(db, proof_id)),
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
