"""Run the Firestore store against REAL Firestore, demonstrate ACID, and prove persistence (provided).

Run in Cloud Shell (authenticated) after implementing `_apply` in firestore_store.py AND
redeploying the chat service with the Firestore-backed image (TASKS.md Tasks 3–4):

    python phase-5-firestore/run_phase5.py --chat-url https://chat-xxx.run.app

Three things happen:

1. **ACID contention test.** 20 concurrent sends two ways — through your transaction
   (`send_message`) and through a naive non-transactional read-modify-write. The transaction
   keeps the counter exact; the naive version loses updates.
2. **Persistence proof.** A session is written here, from Cloud Shell, straight into Firestore
   with your `send_message` — then read back through the *public chat endpoint*, i.e. by a
   Cloud Run container that has never seen this process. Phase 4's memory store could not do
   that; this is the difference between the two phases in one HTTP request.
3. **The chat writes through your code too.** One `/chat` call, then the session counter must
   have grown by exactly two (user + assistant) — via the transaction you wrote.

Writes submission/phase5_report.json.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import firestore_store as fs

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase5_report.json"


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


def _get_json(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


def _post_chat(chat_url: str, session_id: str, message: str) -> dict:
    req = urllib.request.Request(
        chat_url.rstrip("/") + "/chat",
        data=json.dumps({"session_id": session_id, "message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chat-url", required=True, help="your Cloud Run chat URL (Firestore-backed image)")
    a = ap.parse_args(argv)
    chat_url = a.chat_url.rstrip("/")

    from google.cloud import firestore

    project = subprocess.run(
        ["gcloud", "config", "get-value", "project"], capture_output=True, text=True
    ).stdout.strip()
    db = firestore.Client(project=project)
    tag = uuid.uuid4().hex[:6]
    n = 20

    # 1. ACID ------------------------------------------------------------------------ #
    print("1. ACID contention test (20 concurrent sends each way)...")
    with_final = _concurrent(db, f"acid-txn-{tag}", fs.send_message, n)
    without_final = _concurrent(db, f"acid-naive-{tag}", _naive_send, n)
    print(f"   with transaction:    counter = {with_final} / {n}  (should be {n})")
    print(f"   without transaction: counter = {without_final} / {n}  (lost {n - without_final})")

    # 2. Persistence: written here, read by Cloud Run ---------------------------------- #
    proof_id = f"proof-{tag}"
    texts = [f"written from Cloud Shell {i}" for i in range(5)]
    fs.create_session(db, proof_id)
    for t in texts:
        fs.send_message(db, proof_id, "user", t)
    status, hist = _get_json(f"{chat_url}/sessions/{proof_id}/messages")
    seen = [m.get("text") for m in hist.get("messages", [])]
    print(f"2. persistence: wrote {len(texts)} messages from Cloud Shell; the chat service "
          f"(store={hist.get('store')}, instance={hist.get('instance')}) reads back "
          f"{hist.get('message_count', 0)} — HTTP {status}")
    if hist.get("store") != "firestore":
        print("   !! the service is not on the Firestore store — redeploy with STORE_BACKEND=firestore (Task 4)")

    listed = len(fs.list_messages(db, proof_id))          # read back directly, before the chat turn

    # 3. The chat path goes through your transaction ---------------------------------- #
    before = fs.get_session(db, proof_id)["message_count"]
    reply = _post_chat(chat_url, proof_id, "the king and his crown")
    after = fs.get_session(db, proof_id)["message_count"]
    print(f"3. one /chat call: counter {before} -> {after} (should be +2, via your send_message)")

    report = {
        "phase": "5",
        "environment": {"cloud_shell": os.environ.get("CLOUD_SHELL") == "true"},
        "project": project,
        "chat_url": chat_url,
        "acid": {
            "with_txn": {"sent": n, "final_count": with_final},
            "without_txn": {"sent": n, "final_count": without_final},
        },
        "proof": {
            "session_id": proof_id,
            "messages_sent": len(texts),
            "message_texts": texts,
            "message_count": before,
            "messages_listed": listed,
            "via_chat_endpoint": {"status": status, "store": hist.get("store"),
                                  "message_count": hist.get("message_count", 0),
                                  "all_texts_seen": all(t in seen for t in texts)},
            "chat_turn": {"count_before": before, "count_after": after,
                          "store": reply.get("store"), "instance": reply.get("instance")},
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
