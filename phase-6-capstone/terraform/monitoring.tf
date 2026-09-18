# Observability as code: an alerting policy, a log-based metric and a log sink.
#
# Core Services M4 showed you these in the console. Here they are resources, created and
# destroyed with the service they watch — which is the only way a fleet of services stays
# monitored. You fill the two TODO blocks; the notification channel and the IAM plumbing
# that lets the sink write to BigQuery are provided.

# ---- Where alerts go ------------------------------------------------------------------- #
resource "google_monitoring_notification_channel" "email" {
  display_name = "EurecomGPT on-call (${var.alert_email})"
  type         = "email"
  labels       = { email_address = var.alert_email }
  depends_on   = [google_project_service.apis]
}

# ---- Alerting policy: the service is returning errors ----------------------------------- #
resource "google_monitoring_alert_policy" "chat_5xx" {
  display_name = "${var.service_name}: 5xx responses"
  combiner     = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]

  conditions {
    display_name = "5xx rate above threshold"
    condition_threshold {
      # TODO: watch metric.type run.googleapis.com/request_count for resource.type
      #       cloud_run_revision, filtered to resource.labels.service_name = var.service_name
      #       and metric.labels.response_code_class = "5xx"; ALIGN_RATE over 60s, fire when
      #       the rate is COMPARISON_GT 0.1 for a duration of "60s".
      #   filter          = "..."
      #   comparison      = "COMPARISON_GT"
      #   threshold_value = 0.1
      #   duration        = "60s"
      #   aggregations { alignment_period = "60s"  per_series_aligner = "ALIGN_RATE" }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "The ${var.service_name} Cloud Run service is returning 5xx. Check Logs Explorer for the revision, then `terraform apply` a fix."
    mime_type = "text/markdown"
  }
}

# ---- Log-based metric: count server errors in the application log ----------------------- #
resource "google_logging_metric" "chat_errors" {
  name   = "${var.service_name}_errors"
  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND severity >= ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# ---- Log sink: request logs to BigQuery, queryable with SQL ----------------------------- #
resource "google_logging_project_sink" "requests_to_bq" {
  name        = "${var.service_name}-requests-to-bq"
  destination = "bigquery.googleapis.com/projects/${var.project}/datasets/${google_bigquery_dataset.logs.dataset_id}"
  # TODO: filter to resource.type cloud_run_revision, resource.labels.service_name =
  #       var.service_name, and log_name projects/<project>/logs/run.googleapis.com%2Frequests
  #       (the request log only). Set unique_writer_identity = true so the sink gets its own
  #       service account — the binding below grants it write access to the dataset.
  #   filter                 = "..."
  #   unique_writer_identity = true

  bigquery_options {
    use_partitioned_tables = true
  }
}

# The sink writes as its own identity; without this binding every export silently fails.
resource "google_bigquery_dataset_iam_member" "sink_writer" {
  dataset_id = google_bigquery_dataset.logs.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.requests_to_bq.writer_identity
}
