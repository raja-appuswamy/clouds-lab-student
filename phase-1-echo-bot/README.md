# Phase 1 — From IaaS to Serverless: a containerized echo bot

**Goal:** deploy one tiny web service **three ways** — on an IaaS VM, on a container PaaS
(Cloud Run), and as a serverless function (Cloud Functions) — and measure the trade-offs
first-hand (image size, cold start, scaling, cost, effort).

**Lecture map:** Lecture 1 (IaaS / PaaS / SaaS / FaaS service models) · Lecture 2
(virtualization → containers → serverless; Docker; cold start; autoscaling).

Estimated time: ~6 hours. Do everything in **Google Cloud Shell** (see the top-level
README). **Prerequisite:** Phase 0 complete — a GCP project with billing active and
`gcloud` configured.

---

## What you build

A ~50-line Flask **echo bot** (`app.py`): `GET /echo?msg=hello` → `{"echo":"hello","length":5}`.
The *same* app is packaged in a **multi-stage Docker image** and deployed to the VM and to
Cloud Run; `main.py` re-exposes the identical logic as a Cloud Function. You then run a
provided `measure.py` to benchmark all three and write your submission report.

```
            same echo logic
   ┌──────────────┬──────────────┬───────────────┐
   │  IaaS VM     │  Cloud Run   │ Cloud Function│
   │ (e2-micro,   │ (container   │ (gen2, source │
   │  you run     │  PaaS,       │  deploy,      │
   │  the         │  autoscaled) │  FaaS)        │
   │  container)  │              │               │
   └──────────────┴──────────────┴───────────────┘
```

---

## Background reading (study before the tasks)

Service models & the continuum (Lecture 1):
- IaaS vs PaaS vs SaaS: <https://cloud.google.com/learn/paas-vs-iaas-vs-saas>
- Serverless / FaaS overview: <https://cloud.google.com/discover/what-is-serverless>

Containers & serverless (Lecture 2):
- Docker multi-stage builds: <https://docs.docker.com/build/building/multi-stage/>
- Why gunicorn for Flask in a container: <https://flask.palletsprojects.com/en/latest/deploying/gunicorn/>
- **Cloud Run** (container PaaS): <https://cloud.google.com/run/docs/overview/what-is-cloud-run>
- **Cloud Functions (2nd gen)** (FaaS): <https://cloud.google.com/functions/docs/concepts/version-comparison>
- **Artifact Registry** (image storage): <https://cloud.google.com/artifact-registry/docs/overview>
- **Cold starts** — what they are and why min-instances matters:
  <https://cloud.google.com/run/docs/tips/general#using_minimum_instances_to_reduce_cold_starts>
- **Compute Engine** VMs & the free `e2-micro`: <https://cloud.google.com/free/docs/free-cloud-features#compute>

Key concepts to be able to explain afterwards:
- **Cold start**: the latency of the *first* request when no instance is warm (boot + image
  pull + process start). IaaS VM: paid by keeping it warm 24×7. Cloud Run / Functions with
  `min-instances=0`: near-zero cost but a cold start on the first hit after idle.
- **Image size**: a multi-stage build ships only the runtime + your app (target < 400 MB),
  which speeds cold starts and stays within Artifact Registry's free 0.5 GB.
- **Scaling & cost model**: VM = one fixed box you manage and pay for continuously; Cloud
  Run = scales 0→N per request, pay per vCPU-second; Functions = same, per invocation.

---

## Free-tier & safety notes

- Deploy Cloud Run and the Function with **`--min-instances=0`** so they cost ~€0 idle.
- One `e2-micro` in `us-central1`/`us-west1`/`us-east1` is Always-Free 24×7 — use one of
  those regions. Keep only **one** VM.
- **Keep all three deployments up until you are graded** (the CI live-curls them), then run
  the **teardown** commands in [TASKS.md](TASKS.md) to free quota.
- Cloud Build (used to build the image) is free to 2,500 min/month — you'll use seconds.

The concrete step-by-step, with every command, is in **[TASKS.md](TASKS.md)**.
