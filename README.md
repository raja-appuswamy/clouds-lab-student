# EurecomGPT — what you are building, and why in this order

**Read this once before Phase 1.** It is the map of the whole lab: the one system you build
over the semester, which piece each phase adds, and how every piece feeds the next. Each phase
folder has its own `README.md` (the concepts) and `TASKS.md` (the steps); this document is the
thread that runs through them.

---

## The end product

By Week 9 you will have built and deployed **your own chat application** — a browser page that
talks to a small language model *you trained*, answering with context retrieved from a corpus
*you indexed*, remembering every conversation in a database *you designed* — and then made it
survive the failures that break real distributed systems. All of it runs on Google Cloud's
**Always Free** tier: if you follow the task sheets, it costs nothing.

```
                       ┌──────────────────────────────────────────────────────────────┐
   you, in a browser   │  Cloud Run service  "chat"                         (Phase 4) │
  ───────────────────► │                                                              │
   ui/index.html       │   1. retrieve  ──► BigQuery  eurecomgpt.tfidf      (Phase 3) │
   on Cloud Storage    │   2. generate  ──► your GPT  model.safetensors     (Phase 2) │
      (Phase 4)        │   3. remember  ──► Firestore sessions/messages     (Phase 5) │
                       └──────────────────────────────────────────────────────────────┘
                                          ▲
        Phase 1 taught you how to build and deploy this box (containers, Cloud Run).
        Phase 6 makes what it writes correct under crashes and partitions (2PC, Raft).
        Phase 7 brings the whole thing up from zero and load-tests it.
```

Three arrows go *into* the chat service. Two of them point at things built *before* it
(Phases 2 and 3); the third points at something built *after* it — on purpose. That is the
shape of the semester: **Phases 2 and 3 build the components; Phase 4 assembles them into a
working app that cannot remember; Phase 5 gives it a memory; Phase 6 hardens the result;
Phase 7 proves it.** Phases 0 and 1 give you the tools and the deployment skills everything
else assumes.

---

## Phase by phase: what you build, what survives, who uses it

| Phase | You build | What survives into later phases | Used by |
|---|---|---|---|
| **0 — Setup** (Week 1) | A GCP project with billing + budget alert, `gcloud`, your GitHub repo with CI | The project, the bucket name `<project>-eurecomgpt`, a green CI pipeline | every phase |
| **1 — IaaS → serverless** (Week 2) | One echo bot deployed three ways: a VM, Cloud Run, a Cloud Run function; you measure cold starts | *Skills, not artifacts*: you can build a container image, push it, deploy it to Cloud Run, deploy a function — then you tear it all down | Phase 3 (deploys a function), Phase 4 (deploys the chat container the same way) |
| **2 — Train the model** (Weeks 3–4) | A byte-level GPT (~5M parameters) trained in Colab; along the way you measure SIMD, threads and GPU speed-ups | **`model.safetensors`**, public in your bucket | Phase 4 loads it at startup (`MODEL_URL`) |
| **3 — Index the corpus** (Week 5) | A word count run as a real **MapReduce job** — Cloud Run function workers, Cloud Storage shuffle, Cloud Workflows job tracker — then a **TF-IDF index** built with Spark | **BigQuery table `eurecomgpt.tfidf`** (+ the Parquet in your bucket) | Phase 4 queries it on every user message (`BQ_TABLE`) |
| **4 — The chat app** (Week 6) | A FastAPI server on Cloud Run that retrieves (Phase 3) → generates (Phase 2) → keeps the conversation *in the container's memory*, plus the browser UI on Cloud Storage. Ends with an experiment: force a fresh container and watch the history vanish | **A public chat URL** — the working product, minus a memory | Phase 5 redeploys it with a real store; Phase 7 demos it |
| **5 — Remember conversations** (Week 7) | The Firestore schema `sessions/{id}/messages` and a **transactional** `send_message` that cannot lose updates; the same chat server redeployed with Firestore as its store — and the Phase-4 experiment repeated, with the opposite result | The **`firestore_store`** module and the schema, and a chat app that remembers | Phase 6 runs its anomalies, 2PC and Raft over the schema |
| **6 — Make it correct** (Weeks 8–9) | Two-phase commit across Firestore and BigQuery; a toy Raft with leader election and log replication; reproductions of the consistency anomalies they prevent | A distributed-correctness report; an audit log in BigQuery | Phase 7 |
| **7 — Capstone** (Weeks 10–11) | **Supervise an AI agent** operating your stack: you give it a bounded identity and an approval boundary; it writes the Terraform from a spec — service, identity, data plane, alert, log sink — and runs the plan/apply loop under your approval; a **load test** with the instance count read from Cloud Monitoring; the same container on **Kubernetes** (`kind` in Cloud Shell); a **review** of another agent's Terraform with three planted faults; `terraform destroy` — by you | The supervision log, the review, the post-mortem, the demo | — |

Two things follow from the table that are easy to miss when you are inside one phase:

- **Your bucket and your BigQuery dataset accumulate.** `model.safetensors` (Phase 2),
  `tfidf.parquet` and `wordcount.json` (Phase 3), `index.html` (Phase 4) all live in
  `<project>-eurecomgpt`; the `eurecomgpt` dataset holds `tfidf` (Phase 3) and `audit`
  (Phase 6). Do not delete these between phases — Phase 4 will not start without the first
  two, and the autograder reads the public ones on every CI run.
- **Compute is torn down, data is kept.** VMs, Cloud Run services, functions and workflows are
  deleted at the end of the phase that created them (the task sheets say when) — with one
  deliberate exception: the `chat` service stays up from Phase 4 into Phase 5, which redeploys
  it. The artifacts above are what carry forward.

---

## Why this order

The phases follow the lectures, and the lectures follow the layers of a cloud system from the
bottom up:

1. **How compute is sold** (Lectures 1–2 → Phase 1). Before building anything, you deploy the
   same trivial program as a VM, a container and a function, and measure what each costs you in
   cold-start latency. Every later deployment decision refers back to this.
2. **How a single machine goes fast** (Lecture 3 → Phase 2). Vectorisation, threads, GPU. The
   deliverable is the model, but the lesson is *where parallelism stops helping* — a question
   that returns at cluster scale in Phase 3.
3. **How many machines process data** (Lectures 4–6 → Phase 3). MapReduce and Spark, with the
   MapReduce job actually spread across cloud functions so you can watch the scheduler, the
   shuffle and the retries — and see that on a small corpus the cluster is *slower*, and why.
4. **Putting it together** (Phase 4). Nothing new is taught; everything so far is used — and
   the result has a hole you can see: a service whose memory is a container's RAM forgets
   every conversation the moment Cloud Run replaces the container.
5. **How data is stored so nothing is lost** (Lecture 7 → Phase 5). The transaction you write
   here is what fills that hole, and it is the reason the chat history becomes trustworthy.
6. **What breaks when machines fail** (Lectures 9–11 → Phase 6). Consistency models, 2PC's
   blocking problem, Raft's split-brain prevention — implemented, then broken on purpose.
7. **Operating it — through an agent** (Phase 7). Everything you clicked or typed in Phases
   4–5 becomes code an AI agent writes and applies under your supervision; the elasticity
   Lecture 1 promised becomes a number from Cloud Monitoring; Kubernetes shows you what Cloud
   Run had been deciding on your behalf; and the phase's real subject is the boundary you set
   for the agent and the judgement you apply to what it produces.

---

## Two environments, one repo

- **Google Cloud Shell** is where you deploy and run cloud things: Phases 0, 1, 3 (MapReduce
  half), 4, 5, 6, 7 (including a Kubernetes cluster that runs *inside* Cloud Shell). It has `gcloud`, Docker, git and Python preinstalled and is free.
- **Google Colab** is where heavy compute happens: Phase 2 (GPU training) and the Spark half of
  Phase 3. There is no free GPU on GCP; Colab's is.

Everything you write lives in **one Git repository** — this one. Each phase is a folder; your
reports go in `submission/`; pushing runs that phase's autograder in your own GitHub Actions.
Colab clones this repo to get your code, so **commit and push before you open a notebook**.

## Using AI: reader, not operator — until Phase 7

You may use an AI assistant to **understand** anything in this repository: explain provided
code, read a stack trace, decode a `gcloud` error, walk you through the workflow YAML. That
use strengthens the lab. In Phases 0–6 you may not use it to **produce** the graded work — the
withheld `gcloud` commands, the functions marked `TODO`, the writeups — because those phases
exist to get the primitives into *your* hands, and an agent typing them defeats the purpose in
a way no grader can detect but you will feel in Phase 7. Phase 7 lifts the rule deliberately:
there, an agent operates your stack and the graded skill is how you supervise it. The line is
the same one a good engineer draws at work: use the tool to learn faster; do not let it learn
instead of you.

## How you are graded, in one paragraph

Every phase ships **public tests** you can run yourself (`python -m pytest <phase>/tests -p
autograder.points -q`) and a CI workflow that runs them on every push — including, in cloud
phases, live checks against *your own* deployed endpoints and public artifacts. The instructor
adds hidden tests and reads the writeups. A green CI badge is necessary, not sufficient.
Details per phase are in each `TASKS.md` under *How your work is checked*.

## The one rule about money

The lab is designed to cost **€0**. Phase 0 has you set a budget alert at €0.01; if it ever
fires, stop and find out why before doing anything else. The two easy ways to spend money by
accident are leaving a VM running (Phase 1) and deploying a Cloud Run service with
`min-instances` above 0. Each task sheet ends with a teardown task — do it.

---

*The instructor's design document for this lab is not in your repo; this page is the student
version of it. If something here disagrees with a phase's `TASKS.md`, the task sheet wins — tell
us and we will fix this page.*
