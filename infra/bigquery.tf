resource "google_storage_bucket" "model_artefacts" {
    name          = var.model_bucket
    location      = var.model_region
    storage_class = "STANDARD"
    labels        = local.common_labels
    force_destory = false
    versioning {
        enabled = true
    }
    lifecycle_rule {
        condition {
            num_newer_versions = 5
        }
        action {
            type = "Delete"
        }
    }
}

resource "google_storage_bucket_object" "prepared_model" {
    name   = "models/${var.model_version}/prepaared_model.json"
    bucket = google_storage_bucket.model_artefacts.name
    source = "${var.local_artefact_dir}/prepaared_model.json"

    depends_on = [google_storage_bucket.model_artefacts]
}

resource "google_storage_bucket_object" "explanation_metadata" {
    name   = "models/${var.model_version}/explanation_metadata.json"
    bucket = google_storage_bucket.model_artefacts.name
    source = "${var.local_artefact_dir}/explanation_metadata.json"

    depends_on = [google_storage_bucket.model_artefacts]
}

resource "google_storage_bucket_object" "explanation_parameters" {
    name   = "models/${var.model_version}/explanation_parameters.json"
    bucket = google_storage_bucket.model_artefacts.name
    source = "${var.local_artefact_dir}/explanation_parameters.json"

    depends_on = [google_storage_bucket.model_artefacts]
}

resource "google_bigquery_dataset" "model_registry" {
    dataset_id                 = "model_registry"
    friendly_name              = "Sweet-Sense Model Registry"
    description                = "Tracks model versions, artefact paths, and deployment metadata."
    location                   = var.region
    delete_contents_on_destroy = false
    labels                     = local.common_labels
}

resource "google_bigquery_table" "model_version" {
    dataset_id          = google_bigquery_dataset.model_registry.dataset_id
    table_id            = "model_versions"
    deletion_protection = true
    labels              = local.common_labels

    schema = jsonencode([
        { name = "model_name",               type = "STRING",    mode = "REQUIRED" },
        { name = "version",                  type = "STRING",    mode = "REQUIRED" },
        { name = "environment",              type = "STRING",    mode = "REQUIRED" },
        { name = "prepared_model_uri",       type = "STRING",    mode = "REQUIRED" },
        { name = "explanation_metadata_uri", type = "STRING",    mode = "NULLABLE" },
        { name = "explanation_params_uri",   type = "STRING",    mode = "NULLABLE" },
        { name = "vertex_endpoint_id",       type = "STRING",    mode = "NULLABLE" },
        { name = "deployed_at",              type = "TIMESTAMP", mode = "REQUIRED" },
    ])

    depends_on = [google_bigquery_dataset.model_registry]
}