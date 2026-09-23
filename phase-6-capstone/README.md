# Phase 6 — Capstone: supervise an agent operating your stack

> New to the lab, or unsure how this phase fits? Read the **[project map](../README.md)** first — it shows what every phase builds and which later phases depend on it.

**Goal:** operate what you built — with an **AI agent as your operator** and you as the
engineer accountable for it. The agent writes the Terraform from a spec, runs the plan/apply
loop, reads errors and retries. You give it a bounded identity, decide what
it may do without asking, watch it work, catch what it gets wrong, review another agent's
pull request for planted faults, and destroy everything yourself. The stack it builds
is graded exactly as a hand-built one would be; how you supervised is graded as well.

**Environment: Google Cloud Shell**, with an agent that
executes commands under approval — Gemini CLI has a free tier and runs there; any equivalent is
fine, and the phase can be done without one. **Prerequisites:** Phases 2–5 artifacts still in
place — `model.safetensors` and `tfidf.parquet` in your bucket, the Firestore database, the
Phase-5 image `chat:v2` in Artifact Registry.

### Why the rules change here

Phases 0–5 withhold commands and code because you were learning the primitives — there is no
substitute for having typed `gcloud run deploy` and read its errors yourself. By now that is
done. The skill this phase teaches is the one that comes *after* the primitives: specifying
precisely, delegating the toil, and reviewing what comes back for cost, security and
correctness while remaining accountable for it. That is what operating cloud systems looks
like now, and it is only teachable to someone who already has Phases 1–5 in their hands.

---

## What you build

0. **An identity and a boundary for the agent** ([agent/](agent/)). A service account
   `agent-operator` with only the roles the stack needs — deliberately not project-IAM admin —
   that your shell impersonates without a key file; and `policy.json`, your written decision of
   what the agent may run unasked, what needs your approval, and what is forbidden (destroy,
   delete). The autograder reads the policy. [agent/PROMPT.md](agent/PROMPT.md) is the kickoff
   prompt: it makes the agent explain each resource — spec line, the attribute that would
   silently break it, the cost — and stop for you, rather than emitting a wall of HCL.
1. **The stack, as code — written by the agent** ([SPEC.md](SPEC.md) → [terraform/](terraform/)).
   Twenty-odd resources: the APIs, a least-privilege service account with the custom role from
   Phase 4, the Cloud Run service with its scaling and environment, a BigQuery dataset whose
   TF-IDF table is **loaded from your Phase-3 Parquet by a Terraform resource**, and the
   observability — alerting policy, log-based metric, log sink to BigQuery with its IAM binding.
   The agent completes the scaffolding from the spec; you read the plan and approve the apply.
   Mid-apply it hits a `403` — a role you withheld on purpose — and *you* decide what to do.
   `terraform destroy`, which the agent may never run, leaves only the data.
2. **Elasticity, measured** ([loadtest.py](loadtest.py)). Twenty concurrent clients for two
   minutes, then a query to the Cloud Monitoring API for the peak instance count. With
   `max_instance_request_concurrency = 5`, Cloud Run must scale out — and you have the number.
3. **A review of another agent's pull request** ([review/main.tf](review/main.tf)): a
   complete, valid Terraform for the same stack with **three planted faults** — one costs money,
   one over-grants, one fails silently. You find them before they reach a project.
4. **A supervision log** ([supervision_template.md](supervision_template.md)): every approval
   the agent asked for and what you decided, the 403 moment, what it got wrong, what you did by
   hand, and where you would now draw the line.
5. **A post-mortem** ([postmortem_template.md](postmortem_template.md)): what Terraform managed
   and what it deliberately did not, what broke, why the service scaled the way it did, and what
   breaks first at 1,000× the load.
6. **Teardown by hand, proven** — `terraform destroy` is yours, not the agent's, and the
   report records that nothing is left.

```
 you ──► policy.json (auto / confirm / forbidden) ──► agent, running as agent-operator (no IAM admin)
                                                        │
   SPEC.md ─────────────────────────────────────────────┤ writes terraform/, runs plan  (auto)
                                                        │ asks: apply?                (you: yes)
                                                        │ 403 on IAM binding ── asks  (you decide)
                                                        ▼
terraform apply ──► APIs · SA + roles · Cloud Run "chat-tf" · BigQuery (tfidf ← Parquet) · alert · log metric · log sink
      │                                          ▲
      │        loadtest.py ─── 20 clients ───────┘ ───► Monitoring: instance_count peaks at 3
      │
      └── NOT managed: bucket + artifacts, Firestore DB, the image      (data outlives infrastructure)

review/main.tf (PR #12, by another agent) ──► you find: min_instances=1 · dataViewer · silent sink
terraform destroy ──► by you, never the agent
```

---

## Background reading (study before the tasks)

- **Gemini CLI** — running an agent in Cloud Shell, approval prompts, settings:
  <https://github.com/google-gemini/gemini-cli>
- **Service account impersonation** (no key files):
  <https://cloud.google.com/docs/authentication/use-service-account-impersonation>
- **Terraform on Google Cloud** — the google provider, `google_cloud_run_v2_service`,
  `google_bigquery_job`, `google_logging_project_sink`:
  <https://registry.terraform.io/providers/hashicorp/google/latest/docs>
- **Cloud Run scaling** — instance count, concurrency, and why they trade against latency:
  <https://cloud.google.com/run/docs/about-instance-autoscaling>
- **Cloud Monitoring** — alerting policies, log-based metrics, sinks to BigQuery:
  <https://cloud.google.com/monitoring/alerts>, <https://cloud.google.com/logging/docs/export/configure_export_v2>
- **Cloud Run pricing** — what the service would cost under real load:
  <https://cloud.google.com/run/pricing>

---

## How it's graded

- **Offline static checks** parse your `terraform/*.tf` — whoever wrote them, they must
  declare what `SPEC.md` requires (env, scaling, custom role, alert filter, sink filter) — and
  `agent/policy.json` (destroy and delete forbidden, apply needs approval, plan automatic).
- **Live checks** curl the Terraform-managed service while it exists (they skip once your report
  records the destroy — so push once *before* destroying).
- **Report checks** read `submission/phase6_report.json`, built in three stages by
  `make_report.py`: the apply (resource types, health), the load test (≥ 500 requests, sane
  percentiles, **peak instances ≥ 2**), and the destroy (0 resources left, URL dead).
- **Writeup structure checks**: the supervision log has every slot filled and ≥ 4 approval
  rows including a refusal; the review names three faults with a fix each. A hidden test checks
  the three faults are the *right* three.
- The **review**, the **supervision log** and the **post-mortem** are assessed by the
  instructor — that is where the understanding lives in this phase.

## Free-tier & safety

- The Terraform service is capped at **3 instances × 1 GiB** and scales to zero; the load test
  is two minutes of cheap requests — thousands of the two million free invocations, a few
  hundred of the 360,000 free GiB-seconds. Alerting policies, log-based metrics and the
  Monitoring API cost nothing; the sink's log volume is megabytes against 50 GiB free.
- **`terraform destroy` is a graded step.** Nothing here costs money while idle, but the point
  of the phase is that infrastructure is disposable. Your data — bucket, Firestore, images —
  is untouched by design.

The tasks, what each one must achieve and how it is checked are in **[TASKS.md](TASKS.md)**.
In this phase the commands *are* given wherever the step is yours rather than the agent's —
agent tooling is not part of the Google Cloud track.
