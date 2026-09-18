# ---------------------------------------------------------------------------------------
# Pull request #12 — "EurecomGPT serving stack as Terraform"   (opened by: an AI agent)
#
#   Implements SPEC.md end to end in a single file. `terraform validate` passes and
#   `terraform plan` shows 19 resources to add. Ready for review.
#
# ---------------------------------------------------------------------------------------
# YOUR JOB (Task 10): review it as if it were about to be applied to your project. It is
# plausible, it validates, and it would apply cleanly. It also contains THREE faults that a
# careless reviewer would approve — one that costs money, one that grants more than it should,
# one that fails silently. Find them and fill review_template.md. Do not apply this file.
# ---------------------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
    random = { source = "hashicorp/random", version = "~> 3.5" }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

variable "project" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "image" { type = string }
variable "alert_email" { type = string }
variable "service_name" {
  type    = string
  default = "chat-tf"
}

locals {
  bucket    = "${var.project}-eurecomgpt"
  model_url = "https://storage.googleapis.com/${local.bucket}/model.safetensors"
  bq_table  = "${var.project}.${google_bigquery_dataset.tf.dataset_id}.tfidf"
}

# ---- APIs ------------------------------------------------------------------------------ #
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com", "artifactregistry.googleapis.com", "bigquery.googleapis.com",
    "firestore.googleapis.com", "monitoring.googleapis.com", "logging.googleapis.com",
    "iam.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

data "google_storage_bucket" "artifacts" {
  name = local.bucket
}

# ---- Identity -------------------------------------------------------------------------- #
resource "google_service_account" "chat" {
  account_id   = "${var.service_name}-runner"
  display_name = "EurecomGPT chat service"
}

resource "google_project_iam_member" "chat_roles" {
  for_each = toset([
    "roles/bigquery.jobUser",
    "roles/bigquery.dataViewer",
    "roles/datastore.user",
  ])
  project = var.project
  role    = each.key
  member  = "serviceAccount:${google_service_account.chat.email}"
}

# ---- Data plane ------------------------------------------------------------------------- #
resource "google_bigquery_dataset" "tf" {
  dataset_id                 = "eurecomgpt_tf"
  location                   = "US"
  delete_contents_on_destroy = true
  depends_on                 = [google_project_service.apis]
}

resource "random_id" "load" {
  byte_length = 4
  keepers     = { dataset = google_bigquery_dataset.tf.dataset_id }
}

resource "google_bigquery_job" "load_tfidf" {
  job_id   = "load-tfidf-${random_id.load.hex}"
  location = "US"
  load {
    source_uris       = ["gs://${data.google_storage_bucket.artifacts.name}/tfidf.parquet"]
    source_format     = "PARQUET"
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    destination_table {
      project_id = var.project
      dataset_id = google_bigquery_dataset.tf.dataset_id
      table_id   = "tfidf"
    }
  }
}

resource "google_bigquery_dataset" "logs" {
  dataset_id                 = "eurecomgpt_logs"
  location                   = "US"
  delete_contents_on_destroy = true
  depends_on                 = [google_project_service.apis]
}

# ---- Service ---------------------------------------------------------------------------- #
resource "google_cloud_run_v2_service" "chat" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.chat.email

    # Keep one instance warm so the first user never waits for a cold start.
    scaling {
      min_instance_count = 1
      max_instance_count = 3
    }
    max_instance_request_concurrency = 5

    containers {
      image = var.image
      resources {
        limits = { memory = "1Gi", cpu = "1" }
      }
      env {
        name  = "MODEL_URL"
        value = local.model_url
      }
      env {
        name  = "BQ_TABLE"
        value = local.bq_table
      }
      env {
        name  = "STORE_BACKEND"
        value = "firestore"
      }
    }
  }
  depends_on = [google_project_service.apis, google_bigquery_job.load_tfidf]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.chat.name
  location = google_cloud_run_v2_service.chat.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---- Observability ---------------------------------------------------------------------- #
resource "google_monitoring_notification_channel" "email" {
  display_name = "EurecomGPT on-call"
  type         = "email"
  labels       = { email_address = var.alert_email }
  depends_on   = [google_project_service.apis]
}

resource "google_monitoring_alert_policy" "chat_5xx" {
  display_name          = "${var.service_name}: 5xx responses"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]
  conditions {
    display_name = "5xx rate above threshold"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1
      duration        = "60s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      trigger { count = 1 }
    }
  }
}

resource "google_logging_metric" "chat_errors" {
  name   = "${var.service_name}_errors"
  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND severity >= ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_project_sink" "requests_to_bq" {
  name        = "${var.service_name}-requests-to-bq"
  destination = "bigquery.googleapis.com/projects/${var.project}/datasets/${google_bigquery_dataset.logs.dataset_id}"
  filter      = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND log_name = \"projects/${var.project}/logs/run.googleapis.com%2Frequests\""
  bigquery_options {
    use_partitioned_tables = true
  }
}

# ---- Outputs ---------------------------------------------------------------------------- #
output "chat_url" { value = google_cloud_run_v2_service.chat.uri }
output "service_name" { value = google_cloud_run_v2_service.chat.name }
output "service_account" { value = google_service_account.chat.email }
output "bq_table" { value = local.bq_table }
output "logs_dataset" { value = "${var.project}.${google_bigquery_dataset.logs.dataset_id}" }
output "alert_policy" { value = google_monitoring_alert_policy.chat_5xx.display_name }
