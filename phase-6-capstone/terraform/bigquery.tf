# The data plane, rebuilt from the durable artifact (provided).
#
# The chat server needs the TF-IDF table. Phase 3 loaded it by hand from the Parquet in the
# bucket; here the same load is a resource, so "from zero" includes the data: destroy the
# stack, apply again, and the table is back — from the Parquet, which is never destroyed.

resource "google_bigquery_dataset" "tf" {
  dataset_id                 = "eurecomgpt_tf"
  location                   = "US"
  delete_contents_on_destroy = true
  depends_on                 = [google_project_service.apis]
}

# A load job needs a unique id per run; random_id gives one per apply.
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

# Where the log sink (monitoring.tf) lands request logs. Separate dataset so a destroy of
# the logs never touches the retrieval table and vice versa.
resource "google_bigquery_dataset" "logs" {
  dataset_id                 = "eurecomgpt_logs"
  location                   = "US"
  delete_contents_on_destroy = true
  depends_on                 = [google_project_service.apis]
}
