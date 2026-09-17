"""Generate submission/phase4_report.json (provided). Run in Cloud Shell after deploying.

Two steps, because the point of the second one is that time (or a redeploy) passes in between:

    # 1. chat a few times, read the history back from the SAME instance, record it
    python phase-4-chat-app/make_report.py --chat-url https://chat-xxx.run.app \\
        --ui-url https://storage.googleapis.com/<bucket>/index.html

    # 2. after forcing a fresh container (TASKS.md Task 8): ask for the same session again
    python phase-4-chat-app/make_report.py --recheck

Step 1 proves the app works end to end (RAG + generation + an in-memory history that reads
back). Step 2 shows what "stateless" means: the new container has never heard of your session.
Both observations go in the report; Phase 5 is what makes the second one stop happening.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "submission" / "phase4_report.json"
QUESTIONS = ["love and death", "the king and his crown", "battle and war"]


def post_chat(chat_url: str, session_id: str, message: str) -> dict:
    req = urllib.request.Request(
        chat_url.rstrip("/") + "/chat",
        data=json.dumps({"session_id": session_id, "message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def get_history(chat_url: str, session_id: str) -> tuple[int, dict]:
    """Return (status, body). 404 = this instance has no memory of the session."""
    try:
        with urllib.request.urlopen(f"{chat_url.rstrip('/')}/sessions/{session_id}/messages", timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


def step_chat(chat_url: str, ui_url: str) -> dict:
    session = f"grade-{uuid.uuid4().hex[:6]}"
    replies = [post_chat(chat_url, session, q) for q in QUESTIONS]
    status, hist = get_history(chat_url, session)
    print(f"chatted {len(replies)} times in session {session} on instance {replies[-1].get('instance')}")
    print(f"history read-back: HTTP {status}, {hist.get('message_count', 0)} messages "
          f"from instance {hist.get('instance')} (store: {hist.get('store')})")
    return {
        "phase": "4",
        "chat_url": chat_url,
        "ui_url": ui_url,
        "before": {                       # same instance, seconds later
            "session_id": session,
            "chat_replies": len(replies),
            "instance": replies[-1].get("instance"),
            "store": replies[-1].get("store"),
            "history_status": status,
            "message_count": hist.get("message_count", 0),
        },
        "sample": {"question": QUESTIONS[0], "reply": replies[0].get("reply", ""),
                   "retrieved": replies[0].get("retrieved", [])},
    }


def step_recheck(report: dict) -> dict:
    before = report["before"]
    status, hist = get_history(report["chat_url"], before["session_id"])
    try:
        with urllib.request.urlopen(report["chat_url"].rstrip("/") + "/health", timeout=60) as r:
            instance = json.loads(r.read()).get("instance")
    except (urllib.error.URLError, OSError, ValueError):
        instance = hist.get("instance")
    report["after"] = {                   # a fresh instance, later
        "instance": instance,
        "history_status": status,
        "message_count": hist.get("message_count", 0),
    }
    same = instance == before["instance"]
    print(f"recheck of session {before['session_id']}: HTTP {status}, "
          f"{report['after']['message_count']} messages; instance {instance} "
          f"({'SAME instance as before — force a new one and re-run' if same else 'a different instance'})")
    if not same and status == 404:
        print("=> the new container has no memory of the session. That is what stateless means; "
              "Phase 5 fixes it.")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chat-url", help="Cloud Run chat service URL (step 1)")
    ap.add_argument("--ui-url", help="public URL of your chat UI on Cloud Storage (step 1)")
    ap.add_argument("--recheck", action="store_true", help="step 2: re-read the recorded session")
    args = ap.parse_args(argv)

    if args.recheck:
        if not REPORT_PATH.exists():
            ap.error("no report yet — run step 1 first")
        report = step_recheck(json.loads(REPORT_PATH.read_text(encoding="utf-8")))
    else:
        if not (args.chat_url and args.ui_url):
            ap.error("--chat-url and --ui-url are required for step 1")
        report = step_chat(args.chat_url, args.ui_url)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}"
          + ("" if args.recheck else " — now do Task 8, then run again with --recheck."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
