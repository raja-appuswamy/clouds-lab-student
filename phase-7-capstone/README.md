# Phase 7 — Capstone: the whole stack as code, under load, on Kubernetes, and gone

> New to the lab, or unsure how this phase fits? Read the **[project map](../README.md)** first — it shows what every phase builds and which later phases depend on it.

**Goal:** operate what you built. Bring the entire chat stack up **from zero with Terraform** —
service, identity, data plane, monitoring — load-test it and measure the elasticity you were
promised in Lecture 1, run the same container on **Kubernetes** and feel what Cloud Run was
doing for you, write the post-mortem, destroy everything, and demo it.

**Lecture map:** synthesis — no new lecture. Lecture 1 (elasticity economics) · Lecture 2
(containers, revisions) · Lecture 7 (the store you now recreate as code).

**Environment: Google Cloud Shell** (Boost mode for the Kubernetes part). **Prerequisites:**
Phases 2–5 artifacts still in place — `model.safetensors` and `tfidf.parquet` in your bucket,
the Firestore database, the Phase-5 image `chat:v2` in Artifact Registry. Two weeks.

---

## What you build

1. **The stack, as code** ([terraform/](terraform/)). Twenty-odd resources: the APIs, a
   least-privilege service account with the custom role from Phase 4, the Cloud Run service with
   its scaling and environment, a BigQuery dataset whose TF-IDF table is **loaded from your
   Phase-3 Parquet by a Terraform resource**, and the observability — an alerting policy on 5xx
   rate, a log-based metric, a log sink that lands every request log in BigQuery, and the IAM
   binding that lets it. You fill four TODO blocks; `terraform apply` on an empty project gives
   you a working, monitored service, and `terraform destroy` leaves only the data.
2. **Elasticity, measured** ([loadtest.py](loadtest.py)). Twenty concurrent clients for two
   minutes, then a query to the Cloud Monitoring API for the peak instance count. With
   `max_instance_request_concurrency = 5`, Cloud Run must scale out — and you have the number.
3. **The same container on Kubernetes** ([k8s/](k8s/)), in a `kind` cluster inside Cloud Shell:
   a Deployment with two replicas, a readiness probe and resource limits; a NodePort Service;
   a rolling update. Twenty requests through the Service reach two different pods — and `/chat`
   fails, because a pod has no Google identity. Both are the lesson.
4. **A post-mortem** ([postmortem_template.md](postmortem_template.md)): what Terraform managed
   and what it deliberately did not, what broke, why the service scaled the way it did, a
   *costed* GKE Autopilot vs Cloud Run comparison at 1× and 1,000× load, and what breaks first
   at 1,000×.
5. **Teardown, proven**, and a 15-minute demo — apply from zero on stage, destroy on stage.

```
terraform apply ──► APIs · SA + roles · Cloud Run "chat-tf" · BigQuery (tfidf ← Parquet) · alert · log metric · log sink
      │                                          ▲
      │        loadtest.py ─── 20 clients ───────┘ ───► Monitoring: instance_count peaks at 3
      │
      └── NOT managed: bucket + artifacts, Firestore DB, the image      (data outlives infrastructure)

kind create cluster ──► Deployment (2 pods) ──► Service :30080 ──► two instance ids; /chat has no identity
```

---

## Background reading (study before the tasks)

- **Terraform on Google Cloud** — the google provider, `google_cloud_run_v2_service`,
  `google_bigquery_job`, `google_logging_project_sink`:
  <https://registry.terraform.io/providers/hashicorp/google/latest/docs>
- **Cloud Run scaling** — instance count, concurrency, and why they trade against latency:
  <https://cloud.google.com/run/docs/about-instance-autoscaling>
- **Cloud Monitoring** — alerting policies, log-based metrics, sinks to BigQuery:
  <https://cloud.google.com/monitoring/alerts>, <https://cloud.google.com/logging/docs/export/configure_export_v2>
- **kind** — Kubernetes in Docker: <https://kind.sigs.k8s.io/docs/user/quick-start/>
- **Kubernetes Deployments** — replicas, probes, rolling updates:
  <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/>
- **Pricing** for the comparison: <https://cloud.google.com/run/pricing>,
  <https://cloud.google.com/kubernetes-engine/pricing>

---

## How it's graded

- **Offline static checks** parse your `terraform/*.tf` and `k8s/deployment.yaml` — the TODO
  blocks declare what Phases 4–5 deployed by hand (env, scaling, custom role, alert filter, sink
  filter, replicas, probe, resources).
- **Live checks** curl the Terraform-managed service while it exists (they skip once your report
  records the destroy — so push once *before* destroying).
- **Report checks** read `submission/phase7_report.json`, built in four stages by
  `make_report.py`: the apply (resource types, health), the load test (≥ 500 requests, sane
  percentiles, **peak instances ≥ 2**), the Kubernetes rollout (2/2 ready, revision ≥ 2, ≥ 2
  distinct pods answering), and the destroy (0 resources left, URL dead).
- The **post-mortem** and the **demo** are assessed by the instructor.

## Free-tier & safety

- The Terraform service is capped at **3 instances × 1 GiB** and scales to zero; the load test
  is two minutes of cheap requests — thousands of the two million free invocations, a few
  hundred of the 360,000 free GiB-seconds. Alerting policies, log-based metrics and the
  Monitoring API cost nothing; the sink's log volume is megabytes against 50 GiB free.
- `kind` runs inside Cloud Shell, which is Always Free; the cluster is ephemeral and dies with
  the session anyway — `kind delete cluster` just makes it explicit.
- **`terraform destroy` is a graded step.** Nothing here costs money while idle, but the point
  of the phase is that infrastructure is disposable. Your data — bucket, Firestore, images —
  is untouched by design.

Step-by-step is in **[TASKS.md](TASKS.md)**.
