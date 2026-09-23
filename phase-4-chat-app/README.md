# Phase 4 — Inference + RAG-powered chat app

> New to the lab, or unsure how this phase fits? Read the **[project map](../README.md)** first — it shows what every phase builds and which later phases depend on it.

**Goal:** the AI use case becomes real. Deploy a **chat app** that retrieves context from your
Phase-3 corpus (RAG), generates with your Phase-2 model, and serves a browser UI — all on the
free tier. Then discover what it *cannot* do yet: remember.

**Lecture map:** Lecture 1 (SaaS/PaaS) · Lecture 2 (serverless/Cloud Run).

This is the integration phase. **Environment: Google Cloud Shell** (build + deploy).
**Prerequisites:** Phase 2 (a public `model.safetensors`), Phase 3 (the BigQuery `tfidf`
table).

---

## What you build

A **FastAPI chat server** (deployed to Cloud Run) that on each request:
1. **retrieves** the top-k TF-IDF documents for the query from **BigQuery** (Phase 3),
2. **builds a RAG prompt** prepending that context,
3. **generates** a reply with your **Phase-2 weights** — via **NumPy inference** (no torch, so
   the image stays small), loaded from your public model URL,
4. **records** both turns in the server's store — which, in this phase, is a **dict in the
   container's memory**.

Plus a minimal **chat UI** (`ui/index.html`) hosted as a Cloud Storage static site, with a
*Load history* button that asks the server what it remembers of a session.

**You implement** the two RAG pieces in [rag.py](rag.py): `rank_topk` (score + rank the
retrieved docs) and `build_rag_prompt` (assemble the prompt). Everything else — NumPy
inference, the BigQuery query, the store, the FastAPI wiring, the UI — is provided.

### One request, step by step

Where your two functions sit in the path a message takes — read the four files in this order:

| Step | File · function | What happens |
|---|---|---|
| 1 | [server.py](server.py) `chat()` | receives `{"session_id", "message"}` |
| 2 | [retrieval.py](retrieval.py) `tokenize()` | lower-cases, drops stop-words — **the same tokenizer as Phase 3**, so query terms match table terms |
| 3 | [retrieval.py](retrieval.py) `query_tfidf()` | `SELECT term, doc_id, tfidf FROM <your tfidf table> WHERE term IN (those terms)` — BigQuery filters; nothing is scored yet |
| 4 | **[rag.py](rag.py) `rank_topk()`** — *yours* | sums tfidf per `doc_id`, sorts, returns the `k` best ids |
| 5 | [retrieval.py](retrieval.py) `load_corpus()` | maps ids back to text with Phase 3's deterministic 60-document split |
| 6 | **[rag.py](rag.py) `build_rag_prompt()`** — *yours* | `Context:` + those texts + `User: <message>` + `Assistant:` |
| 7 | [infer.py](infer.py) `generate()` | the Phase-2 weights complete the prompt (NumPy) |
| 8 | [store.py](store.py) `store_turn()` ×2 | user turn and reply recorded — in this phase, in memory |

Steps 4 and 6 are pure functions — rows in, ids out; strings in, string out — which is why
they have offline unit tests and the rest of the path does not. The module docstring in
`rag.py` walks a concrete message ("the king and his crown") through all eight steps.

```
Browser UI (Cloud Storage)  ──►  Cloud Run: FastAPI chat
                                   ├─ BigQuery  (Phase-3 TF-IDF)  → retrieve
                                   ├─ NumPy GPT (Phase-2 weights) → generate
                                   └─ MemoryStore (this container) → record  ← Phase 5 replaces this
```

### The lesson hiding in the last line

Cloud Run gives you containers, not a machine: it starts them when requests arrive, runs
several when traffic is high, and stops them all when it is idle. A dict inside one container
is therefore the wrong place for anything you want to keep. The last task of this phase makes
you see it happen — you chat, force Cloud Run to hand you a fresh container, ask for your
history, and get *nothing*. That observation is the motivation for Phase 5, where the same
server gets a store that outlives its containers.

---

## Background reading

- **Cloud Run** (deploy a container, env vars, revisions, scaling to zero):
  <https://cloud.google.com/run/docs> — in particular *Container instance lifecycle* and
  *About revisions*.
- **FastAPI**: <https://fastapi.tiangolo.com/> · **RAG** overview:
  <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **BigQuery client** (parameterised queries):
  <https://cloud.google.com/bigquery/docs/reference/libraries>
- **Cloud Storage static website** hosting:
  <https://cloud.google.com/storage/docs/hosting-static-website>

---

## How it's graded

- **Offline unit tests** grade `rank_topk` and `build_rag_prompt` (pure Python).
- **Live checks** curl your **public Cloud Run** URL: `/health`, a real `/chat` request (which
  exercises retrieval + generation end to end), and `/sessions/{id}/messages` reading back
  what was just said.
- **Report check**: `make_report.py` records your URLs and the two-step statelessness
  observation — history present on the instance that wrote it, absent on a fresh one.

## Free-tier & safety

- Deploy Cloud Run with **`--min-instances=0`** (≈ €0 idle). NumPy inference keeps the image
  under the 0.5 GB Artifact Registry free tier.
- Leave the service **up** at the end of this phase: Phase 5 redeploys it with Firestore. Idle
  at `min-instances=0` it costs nothing.

The tasks, what each one must achieve and how it is checked are in **[TASKS.md](TASKS.md)**.
The `gcloud` commands are deliberately not given — you performed these operations in the Google
Cloud modules named under each task.
