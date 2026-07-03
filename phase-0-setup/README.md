# Phase 0 — Setup

**Goal:** get your whole toolchain ready so that from Phase 1 onward you spend time on
cloud concepts, not installation. **Zero cloud compute is consumed in this phase** —
you only create accounts and configure local tools.

**Lecture map:** Lecture 1 (Introduction to Cloud Computing — the IaaS/PaaS/SaaS/FaaS
service models, the big-four providers, the cloud stack).

Estimated time: ~3 hours (mostly account creation and downloads).

---

## What you need before starting

You will create two free accounts:

1. **Google Cloud Platform (GCP)** — the cloud you deploy to.
2. **GitHub** — where your code lives and where autograding runs.

> ⚠️ **Free-tier safety — read this once, remember it all semester.** The entire lab is
> designed to stay inside the GCP *Always Free* tier. The traps that cost real money:
> - Always-Free quotas are **per billing account**, not per project — do **not** share a
>   billing account within a group.
> - Network **egress is free only within North America** — pick US regions when asked.
> - Cloud Run / Cloud Logging can silently burn quota if left running — always deploy
>   with `min-instances=0` (later phases) and set a **Cloud Budget alert at €0.01**.
> - **There is no free GPU/TPU on GCP.** All model training (Phase 2) happens in Google
>   Colab, never on a paid GCP VM.

---

## Background reading (study these before doing the tasks)

Cloud service models (the Lecture 1 backbone — know where each tool you install sits):
- GCP overview of IaaS/PaaS/SaaS: <https://cloud.google.com/learn/what-is-iaas>,
  <https://cloud.google.com/learn/paas-vs-iaas-vs-saas>
- GCP **Always Free** tier (skim the table; note the quotas for Compute Engine, Cloud
  Run, Cloud Storage, Firestore, BigQuery): <https://cloud.google.com/free/docs/free-cloud-features#free-tier>

Tools you will install:
- **gcloud CLI** (the Google Cloud SDK) — install & init:
  <https://cloud.google.com/sdk/docs/install> then <https://cloud.google.com/sdk/docs/initializing>
- **Python 3.11** and virtual environments:
  <https://www.python.org/downloads/release/python-3119/>,
  <https://docs.python.org/3/library/venv.html>
- **Docker Desktop** (used from Phase 1): <https://docs.docker.com/get-docker/>
- **git & GitHub basics** (clone, commit, push; making a repo public):
  <https://docs.github.com/en/get-started/quickstart/hello-world>

---

## How this lab works (applies to every phase)

1. You get a **skeleton** repository: full scaffolding, with a few functions left as
   `TODO` for you to implement.
2. You fill the TODOs, then run a **self-check script** (`verify_setup.py` in this phase)
   that inspects your work and writes a report into `submission/`.
3. The repo ships with **public tests** you can run locally (`pytest`) and that also run
   automatically in your **GitHub Actions CI** on every push — the green badge is part of
   your grade.
4. The instructor runs additional **hidden tests** for the final score.

The tasks and the exact point rubric are in [TASKS.md](TASKS.md).
