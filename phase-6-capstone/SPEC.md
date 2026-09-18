# EurecomGPT serving stack — specification

This is the brief. In Phases 4–5 you built this stack by hand; in Phase 6 an AI agent builds
it for you from this document, under your supervision. Give the agent this file (the
`agent/` folder wires it in) and hold it to every line. Anything not stated here is the agent's
choice — and yours to review.

## Goal

A `terraform apply` on the project, starting from nothing but the artifacts below, produces a
working, monitored chat service. A `terraform destroy` removes every resource it created and
nothing else.

## Inputs that already exist (read, never create, never destroy)

| Artifact | Where | Made in |
|---|---|---|
| `model.safetensors` (public) | bucket `<project>-eurecomgpt` | Phase 2 |
| `tfidf.parquet` (public) | bucket `<project>-eurecomgpt` | Phase 3 |
| Firestore database (Native mode) | the project | Phase 5 |
| Container image `chat:v2` (Firestore-backed server) | Artifact Registry `eurecomgpt` | Phase 5 |

The bucket is referenced as a **data source**. The Firestore database and the image are not
referenced by Terraform at all. `delete_contents_on_destroy` may be set only on datasets this
stack creates.

## Resources the stack must create

1. **APIs**: run, artifactregistry, bigquery, firestore, monitoring, logging, iam — with
   `disable_on_destroy = false` (other phases use them).
2. **Identity**: a service account for the service; project roles `bigquery.jobUser` and
   `datastore.user`; and a **custom role** granting exactly `bigquery.tables.get` and
   `bigquery.tables.getData`, bound in place of any broad BigQuery viewer role.
3. **Data plane**: a BigQuery dataset `eurecomgpt_tf` whose `tfidf` table is **loaded from the
   Parquet in the bucket by a `google_bigquery_job`** (source format PARQUET, write truncate),
   so the data plane is rebuilt from the durable artifact on every apply. A second dataset
   `eurecomgpt_logs` for the log sink.
4. **Service**: Cloud Run v2, name from `var.service_name` (default `chat-tf`), region from
   `var.region`, image from `var.image`, publicly invokable (`allUsers` → `roles/run.invoker`),
   running as the service account above. Environment: `MODEL_URL` (the public model URL),
   `BQ_TABLE` (`<project>.eurecomgpt_tf.tfidf`), `STORE_BACKEND=firestore`. Memory 1 GiB,
   1 CPU. Scaling **min 0, max 3**, `max_instance_request_concurrency` **≤ 10** (the load test
   must be able to make it scale out). `deletion_protection = false`.
5. **Observability**: an e-mail notification channel (`var.alert_email`); an **alerting policy**
   on `run.googleapis.com/request_count` restricted to this service and to
   `response_code_class = "5xx"`, aligned as a rate (`ALIGN_RATE`, 60 s), threshold `> 0.1`
   for 60 s; a **log-based metric** counting `severity >= ERROR` for this service; a **log
   sink** exporting only this service's request log (`run.googleapis.com%2Frequests`) to the
   `eurecomgpt_logs` dataset, with `unique_writer_identity = true` **and** a
   `roles/bigquery.dataEditor` binding for the sink's writer identity on that dataset.
6. **Outputs**: `chat_url`, `service_name`, `service_account`, `bq_table`, `logs_dataset`,
   `sink_writer_identity`, `alert_policy`.

## Constraints the agent must respect

- **Cost**: nothing may run while idle. `min_instance_count` is 0. No VMs, no GKE, no
  Dataproc, no reserved anything. Max 3 instances × 1 GiB.
- **Scope**: only the project in `var.project`; never touch other projects, the bucket's
  contents, or Firestore data.
- **No secrets in code**: no key files, no tokens. Identity comes from the environment.
- **Providers**: `hashicorp/google ~> 6.0`, `hashicorp/random ~> 3.5`. The provider block may
  set `impersonate_service_account = var.impersonate` (null by default).
- **Never** run `terraform destroy`, delete any resource, or run `rm -rf`. The engineer does
  that, by hand, at the end.

## Definition of done

`terraform validate` passes; `terraform plan` on an empty project proposes only additions;
after `apply`, `curl <chat_url>/health` returns `{"status":"ok","store":"firestore",…}` and
`POST <chat_url>/chat` returns a reply with retrieved document ids; the offline static tests
in `tests/test_units.py` pass against `terraform/*.tf`.
