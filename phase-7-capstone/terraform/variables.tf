# Inputs (provided). Copy terraform.tfvars.example to terraform.tfvars and fill it in.
variable "project" {
  description = "Your GCP project id (Phase 0)."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run — same as every earlier phase."
  type        = string
  default     = "us-central1"
}

variable "image" {
  description = "The Firestore-backed chat image you built in Phase 5, e.g. us-central1-docker.pkg.dev/<project>/eurecomgpt/chat:v2"
  type        = string
}

variable "alert_email" {
  description = "Where the alerting policy sends notifications."
  type        = string
}

variable "impersonate" {
  description = "Service account e-mail Terraform should impersonate (Task 1's agent-operator), or null."
  type        = string
  default     = null
}

variable "service_name" {
  description = "Name of the Cloud Run service Terraform manages. Distinct from Phase 4/5's `chat` so both can coexist."
  type        = string
  default     = "chat-tf"
}

locals {
  bucket    = "${var.project}-eurecomgpt"                                          # the Phase-2/3 bucket (data, not managed here)
  model_url = "https://storage.googleapis.com/${local.bucket}/model.safetensors"   # Phase 2 artifact
  bq_table  = "${var.project}.${google_bigquery_dataset.tf.dataset_id}.tfidf"      # rebuilt from the Phase-3 Parquet below
}
