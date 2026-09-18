# What make_report.py and you need after `terraform apply` (provided).
output "chat_url" {
  description = "Public URL of the Terraform-managed chat service."
  value       = google_cloud_run_v2_service.chat.uri
}

output "service_name" {
  value = google_cloud_run_v2_service.chat.name
}

output "service_account" {
  value = google_service_account.chat.email
}

output "bq_table" {
  description = "The TF-IDF table this stack rebuilt from the Phase-3 Parquet."
  value       = local.bq_table
}

output "logs_dataset" {
  description = "Where the request-log sink lands rows: query it with SQL after the load test."
  value       = "${var.project}.${google_bigquery_dataset.logs.dataset_id}"
}

output "sink_writer_identity" {
  value = google_logging_project_sink.requests_to_bq.writer_identity
}

output "alert_policy" {
  value = google_monitoring_alert_policy.chat_5xx.display_name
}
