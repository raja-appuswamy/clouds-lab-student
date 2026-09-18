# The EurecomGPT serving stack, from zero, as code.
#
# Everything the chat app needs to run — APIs, identity, the Cloud Run service, its data
# plane (bigquery.tf) and its observability (monitoring.tf) — declared here, so that
# `terraform apply` on an empty project produces a working, monitored service and
# `terraform destroy` removes every trace. What is NOT managed here, deliberately:
#   * the bucket and the artifacts in it (model.safetensors, tfidf.parquet) — data outlives
#     infrastructure, so it is read as a data source and never destroyed;
#   * the Firestore database — one per project, permanent, created in Phase 5;
#   * the container image — built in Phase 5, referenced by var.image.
#
# You fill the blocks marked TODO. Everything else is provided.

# ---- APIs ---------------------------------------------------------------------------- #
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "firestore.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "iam.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false   # destroying the stack must not switch off APIs other phases use
}

# ---- Data that outlives this stack (read-only) ---------------------------------------- #
data "google_storage_bucket" "artifacts" {
  name = local.bucket
}

# ---- Identity: the service runs as its own least-privilege account ------------------- #
resource "google_service_account" "chat" {
  account_id   = "${var.service_name}-runner"
  display_name = "EurecomGPT chat service (Terraform-managed)"
}

# The custom role from Phase 4, now as code: exactly what the server needs to read the
# TF-IDF table and nothing more.
resource "google_project_iam_custom_role" "chat_bq_reader" {
  role_id = "${replace(var.service_name, "-", "")}BigQueryReader"
  title   = "Chat BigQuery Reader (Terraform)"
  # TODO: the two permissions the chat server needs to read a table (Phase 4 Task 5).
  # permissions = [...]
}

resource "google_project_iam_member" "chat_roles" {
  for_each = toset([
    "roles/bigquery.jobUser",   # run the retrieval query
    "roles/datastore.user",     # read/write Firestore sessions (Phase 5 store)
  ])
  project = var.project
  role    = each.key
  member  = "serviceAccount:${google_service_account.chat.email}"
}

resource "google_project_iam_member" "chat_custom_role" {
  project = var.project
  role    = google_project_iam_custom_role.chat_bq_reader.id
  member  = "serviceAccount:${google_service_account.chat.email}"
}

# ---- The service ----------------------------------------------------------------------- #
resource "google_cloud_run_v2_service" "chat" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false                        # this stack is meant to be destroyed

  template {
    service_account = google_service_account.chat.email

    # TODO: declare the service the way you deployed it by hand in Phases 4-5, as code:
    #   scaling { min_instance_count = 0  max_instance_count = 3 }
    #   max_instance_request_concurrency = 5    # small on purpose: forces scale-OUT under load
    #   containers {
    #     image = var.image
    #     resources { limits = { memory = "1Gi", cpu = "1" } }
    #     env { name = "MODEL_URL"     value = local.model_url }
    #     env { name = "BQ_TABLE"      value = local.bq_table }
    #     env { name = "STORE_BACKEND" value = "firestore" }
    #   }
  }

  depends_on = [google_project_service.apis, google_bigquery_job.load_tfidf]
}

# Public, like Phases 4-5: anyone may invoke.
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.chat.name
  location = google_cloud_run_v2_service.chat.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
