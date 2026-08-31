"""Generate submission/phase5_report.json (provided). Run in Cloud Shell after deploying.

    python phase-5-chat-app/make_report.py \\
        --chat-url https://chat-xxx.run.app \\
        --ui-url   https://storage.googleapis.com/<bucket>/index.html

Sends a few messages to your deployed chat server, then reads the session back from Firestore
to prove the turns were stored, and records everything in the report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase5_report.json"
QUESTIONS = ["love and death", "the king and his crown", "battle and war"]


def post_chat(chat_url: str, session_id: str, message: str) -> dict:
    req = urllib.request.Request(
        chat_url.rstrip("/") + "/chat",
        data=json.dumps({"session_id": session_id, "message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chat-url", required=True, help="Cloud Run chat service URL")
    ap.add_argument("--ui-url", required=True, help="public URL of your chat UI on Cloud Storage")
    args = ap.parse_args(argv)

    session = f"grade-{uuid.uuid4().hex[:6]}"
    replies = [post_chat(args.chat_url, session, q) for q in QUESTIONS]

    from google.cloud import firestore

    project = subprocess.run(
        ["gcloud", "config", "get-value", "project"], capture_output=True, text=True
    ).stdout.strip()
    sess = firestore.Client(project=project).collection("sessions").document(session).get().to_dict()

    report = {
        "phase": "5",
        "chat_url": args.chat_url,
        "ui_url": args.ui_url,
        "proof": {
            "session_id": session,
            "chat_replies": len(replies),
            "message_count": (sess or {}).get("message_count", 0),
        },
        "sample": {"question": QUESTIONS[0], "reply": replies[0].get("reply", ""),
                   "retrieved": replies[0].get("retrieved", [])},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
