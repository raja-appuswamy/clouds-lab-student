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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import infer
import retrieval
import store
from rag import build_rag_prompt

app = FastAPI(title="eurecomgpt-chat")

INSTANCE = uuid.uuid4().hex[:8]     # one per process: new container => new id

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


@app.get("/healthz")
def healthz():
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
