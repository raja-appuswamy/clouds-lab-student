"""FastAPI chat server — RAG + tiny-GPT inference + a pluggable turn store (provided).

On each ``/chat`` request: retrieve the top-k TF-IDF docs from BigQuery (Phase 3), build a RAG
prompt (your ``rag.build_rag_prompt``), generate with the Phase-2 weights (NumPy inference),
and record both turns in the store. ``/sessions/{id}/messages`` reads a session back — in
Phase 4 from this instance's memory, in Phase 5 from Firestore.

Environment variables (set at deploy time — see TASKS.md):
    MODEL_URL       public URL of your Phase-2 model.safetensors
    BQ_TABLE        your Phase-3 BigQuery table, e.g. project.eurecomgpt.tfidf
    STORE_BACKEND   memory (default, Phase 4) | firestore (Phase 5)

Every response carries ``instance`` — an id minted when this process started. Watch it: when it
changes between two requests, you are talking to a different container, and anything the old
one kept in memory is gone.
"""

from __future__ import annotations

import os
import urllib.request
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import infer
import retrieval
import store
from rag import build_rag_prompt

app = FastAPI(title="eurecomgpt-chat")

# The UI is served from a DIFFERENT origin (storage.googleapis.com) than this API (*.run.app),
# so the browser sends a CORS preflight before every POST /chat. Without these headers the
# preflight fails and the UI shows "Failed to fetch" while curl works fine. Public API, any
# origin may call it — same policy as --allow-unauthenticated.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

INSTANCE = uuid.uuid4().hex[:8]     # one per process: new container => new id
UI_FILE = Path(__file__).resolve().parent / "ui" / "index.html"   # present locally, not in the image

_weights = None
_bq = None
_store = None


def weights():
    global _weights
    if _weights is None:
        data = urllib.request.urlopen(os.environ["MODEL_URL"], timeout=60).read()
        _weights = infer.load_weights(data)
    return _weights


def bq():
    global _bq
    if _bq is None:
        from google.cloud import bigquery

        _bq = bigquery.Client()
    return _bq


def turns():
    global _store
    if _store is None:
        _store = store.make_store()
    return _store


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/")
def root():
    """Serve the chat UI when running from the source tree (local testing in Cloud Shell).

    In the deployed image ``ui/`` is not copied — the UI lives on Cloud Storage — so this
    answers with a pointer instead.
    """
    if UI_FILE.exists():
        return FileResponse(UI_FILE)
    return {"service": "eurecomgpt-chat", "ui": "hosted on Cloud Storage (Task 6)", "try": "/health"}


@app.get("/health")   # not /healthz: Cloud Run's front end intercepts that path and answers 404 itself
def health():
    return {"status": "ok", "store": os.environ.get("STORE_BACKEND", "memory"), "instance": INSTANCE}


@app.post("/chat")
def chat(inp: ChatIn):
    retrieved = retrieval.retrieve(bq(), os.environ["BQ_TABLE"], inp.message, k=3)
    context = [text for _doc_id, text in retrieved]
    prompt = build_rag_prompt(inp.message, context)
    reply = infer.generate(weights(), prompt, max_new_tokens=80)

    s = turns()
    s.ensure_session(inp.session_id)
    s.store_turn(inp.session_id, "user", inp.message)
    s.store_turn(inp.session_id, "assistant", reply)

    return {
        "reply": reply,
        "retrieved": [doc_id for doc_id, _text in retrieved],
        "prompt_chars": len(prompt),
        "store": s.name,
        "instance": INSTANCE,
    }


@app.get("/sessions/{session_id}/messages")
def history(session_id: str):
    s = turns()
    session = s.get_session(session_id)
    if session is None:
        # Unknown here. In Phase 4 that also happens to every session the PREVIOUS instance knew.
        raise HTTPException(status_code=404, detail=f"no session {session_id!r} in the {s.name} store")
    return {
        "session_id": session_id,
        "message_count": session.get("message_count", 0),
        "messages": s.list_messages(session_id),
        "store": s.name,
        "instance": INSTANCE,
    }
