# Phase 5 — Inference + RAG-powered chat app

**Goal:** the AI use case becomes real. Deploy a **chat app** that retrieves context from your
Phase-3 corpus (RAG), generates with your Phase-2 model, stores every turn in your Phase-4
Firestore, and serves a browser UI — all on the free tier.

**Lecture map:** Lecture 1 (SaaS/PaaS) · Lecture 2 (serverless/Cloud Run) · Lecture 7 (OLTP).

Estimated time: ~8–10 hours (it's the integration phase). **Environment: Google Cloud Shell**
(build + deploy). **Prerequisites:** Phase 2 (a public `model.safetensors`), Phase 3 (the
BigQuery `tfidf` table), Phase 4 (Firestore).

---

## What you build

A **FastAPI chat server** (deployed to Cloud Run) that on each request:
1. **retrieves** the top-k TF-IDF documents for the query from **BigQuery** (Phase 3),
2. **builds a RAG prompt** prepending that context,
3. **generates** a reply with your **Phase-2 weights** — via **NumPy inference** (no torch, so
   the image stays small), loaded from your public model URL,
4. **stores** both turns in **Firestore** (Phase-4 schema).

Plus a minimal **chat UI** (`ui/index.html`) hosted as a Cloud Storage static site.

**You implement** the two RAG pieces in [rag.py](rag.py): `rank_topk` (score + rank the
retrieved docs) and `build_rag_prompt` (assemble the prompt). Everything else — NumPy
inference, the BigQuery query, the Firestore writes, the FastAPI wiring, the UI — is provided.

```
Browser UI (Cloud Storage)  ──►  Cloud Run: FastAPI chat
                                   ├─ BigQuery  (Phase-3 TF-IDF)  → retrieve
                                   ├─ NumPy GPT (Phase-2 weights) → generate
                                   └─ Firestore (Phase-4 schema)  → store turns
```

---

## Background reading

- **Cloud Run** (deploy a container, env vars, concurrency): <https://cloud.google.com/run/docs>
- **FastAPI**: <https://fastapi.tiangolo.com/> · **RAG** overview:
  <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **BigQuery client** (parameterised queries):
  <https://cloud.google.com/bigquery/docs/reference/libraries>
- **Cloud Storage static website** hosting:
  <https://cloud.google.com/storage/docs/hosting-static-website>

---

## How it's graded

- **Offline unit tests** grade `rank_topk` and `build_rag_prompt` (pure Python).
- **Live checks** curl your **public Cloud Run** URL: `/healthz` and a real `/chat` request
  (which exercises retrieval + generation + storage end to end).
- **Report check**: `make_report.py` records your URLs and proves turns were stored in
  Firestore (the counter equals 2× the chats, via the Phase-4 transaction).

## Free-tier & safety

- Deploy Cloud Run with **`--min-instances=0`** (≈ €0 idle). NumPy inference keeps the image
  under the 0.5 GB Artifact Registry free tier.
- Keep the service up until graded, then **tear it down** (see TASKS.md).

Step-by-step with commands is in **[TASKS.md](TASKS.md)**.
