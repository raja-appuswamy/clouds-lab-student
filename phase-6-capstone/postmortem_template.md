# Phase 6 — Capstone Post-mortem

Copy this file to `submission/phase6_postmortem.md`, fill in every answer slot, and commit it:

```bash
cp phase-6-capstone/postmortem_template.md submission/phase6_postmortem.md
```

**How to fill it in.** Each answer sits between a pair of `<!--answer:...-->` markers. Replace
the `TODO` line with your answer — **leave the markers themselves untouched**, they are how the
grader finds your answers. Anything you write outside the markers is ignored, so add extra
prose, tables or screenshots freely.

Numbers in section 1 must **match `submission/phase6_report.json`** — copy them across, do not
retype from memory; they are checked against it.

---

## 1. Facts from your runs

Numbers only.

| | Value |
|---|---|
| Resources Terraform created (`terraform.resource_count`) | <!--answer:tf_resource_count-->TODO<!--/answer--> |
| Load test: requests sent (`loadtest.requests`) | <!--answer:load_requests-->TODO<!--/answer--> |
| Load test: p50 latency, ms (`loadtest.latency_ms.p50`) | <!--answer:load_p50_ms-->TODO<!--/answer--> |
| Load test: p99 latency, ms (`loadtest.latency_ms.p99`) | <!--answer:load_p99_ms-->TODO<!--/answer--> |
| Peak Cloud Run instances during the test (`loadtest.max_instances`) | <!--answer:load_max_instances-->TODO<!--/answer--> |
| Resources left in state after destroy (`destroyed.resources_remaining`) | <!--answer:tf_remaining-->TODO<!--/answer--> |

---

## 2. Infrastructure as code

**From zero, and back.** What did `terraform apply` create that you had built by hand across
Phases 4 and 5, and what did it *not* create (and why not)? After `terraform destroy`, what
still exists in your project, and why is that the right split? (~80 words)

<!--answer:iac_scope-->
TODO
<!--/answer-->

**Something broke.** Every capstone hits at least one apply or destroy error — a missing API, a
permission the sink needed, a name already taken, an ordering problem. Describe one you hit,
what the error said, how you diagnosed it, and what the fix was. (~70 words)

<!--answer:what_broke-->
TODO
<!--/answer-->

---

## 3. Elasticity, measured

**Explain the scale-out.** Using your numbers from section 1: why did Cloud Run reach the peak
instance count it did — which setting in `main.tf` decided that, and what would have happened
with Cloud Run's default concurrency of 80? Where does the p99 latency come from? (~90 words)

<!--answer:elasticity_explanation-->
TODO
<!--/answer-->

**Your alert.** What does the alerting policy watch, why that metric and threshold, and did it
fire during the load test? If it did not, what would have to happen for it to fire — and is
that the right trigger for an on-call engineer? (~60 words)

<!--answer:alert_design-->
TODO
<!--/answer-->

**The log sink.** Paste one SQL query you ran against the request-log table in BigQuery and one
line of its result (e.g. requests per status code, or p99 by endpoint). (verbatim)

<!--answer:log_sink_query-->
TODO
<!--/answer-->

---

## 4. At 1,000× scale

**What breaks first.** If a thousand times more users arrived tomorrow, which component of the
stack you built — the Cloud Run service, Firestore, the BigQuery retrieval query, the model
download at startup, the single region — fails first, how would you know (which metric or alert),
and what is the first change you would make? (~100 words)

<!--answer:scale_1000x-->
TODO
<!--/answer-->
