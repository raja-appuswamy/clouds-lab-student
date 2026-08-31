"""FastAPI chat server — RAG + tiny-GPT inference + Firestore (provided).

On each request: retrieve top-k TF-IDF docs from BigQuery (Phase 3), build a RAG prompt
(your `rag.build_rag_prompt`), generate with the Phase-2 weights (NumPy inference), and store
both turns in Firestore (Phase 4 schema).

Environment variables (set at deploy time — see TASKS.md):
    MODEL_URL  public URL of your Phase-2 model.safetensors
    BQ_TABLE   your Phase-3 BigQuery table, e.g. project.eurecomgpt.tfidf
"""

from __future__ import annotations

import os
import urllib.request

from fastapi import FastAPI
from pydantic import BaseModel

import infer
import retrieval
import store
from rag import build_rag_prompt

app = FastAPI(title="eurecomgpt-chat")

_weights = None
_bq = None
_db = None


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


def db():
    global _db
    if _db is None:
        from google.cloud import firestore

        _db = firestore.Client()
    return _db


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/healthz")
def healthz():
    return "ok"


@app.post("/chat")
def chat(inp: ChatIn):
    retrieved = retrieval.retrieve(bq(), os.environ["BQ_TABLE"], inp.message, k=3)
    context = [text for _doc_id, text in retrieved]
    prompt = build_rag_prompt(inp.message, context)
    reply = infer.generate(weights(), prompt, max_new_tokens=80)

    store.ensure_session(db(), inp.session_id)
    store.store_turn(db(), inp.session_id, "user", inp.message)
    store.store_turn(db(), inp.session_id, "assistant", reply)

    return {
        "reply": reply,
        "retrieved": [doc_id for doc_id, _text in retrieved],
        "prompt_chars": len(prompt),
    }
