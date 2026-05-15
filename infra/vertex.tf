resource "google_vertex_ai_model" "classifier" {
    display_name = local.model.display_name
    description  = "XGBoost multi-class diabetes risk classifier — ${var.environment} v${var.model_version}"
    region       = var.region
    labels       = local.common_labels

    artifact_uri = local.model.artefact_dir

    container_spec {
        image_uri     = "us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.1-7:latest"
        predict_route = "/predict"
        health_route  = "/ping"
    }

    explanation_spec {
    metadata {
      inputs  = {}
      outputs = {}
    }

    parameters {
      sampled_shapley_attribution {
        path_count = 10
      }
    }
  }

  depends_on = [
    google_storage_bucket_object.prepared_model,
    google_storage_bucket_object.explanation_metadata,
    google_storage_bucket_object.explanation_parameters,
  ]
}

resource "google_vertex_ai_endpoint" "classifier" {
    name         = "${replace(local.model.name, "-", "_")}_endpoint"
    display_name = "${local.model.display_name} Endpoint"
    description  = "Online prediction endpoint for ${local.model.display_name}"
    location     = var.region
    labels       = local.common_labels
}

resource "google_vertex_ai_endpoint_deployed_model" "classifier" {
  endpoint = google_vertex_ai_endpoint.classifier.id
  location = var.region

  model      = google_vertex_ai_model.classifier.id
  model_version_id = google_vertex_ai_model.classifier.version_id

  display_name                   = local.model.display_name
  enable_access_logging          = true
  enable_container_logging       = true

  dedicated_resources {
    machine_spec {
      machine_type = var.vertex_machine_type   # e.g. "n1-standard-4"
    }

    # Autoscaling bounds — supplied per environment via tfvars
    min_replica_count = var.vertex_min_replicas
    max_replica_count = var.vertex_max_replicas

    autoscaling_metric_specs {
      metric_name = "aiplatform.googleapis.com/prediction/online/cpu/utilization"
      target      = 60
    }
  }

  depends_on = [
    google_vertex_ai_endpoint.classifier,
    google_vertex_ai_model.classifier,
  ]
}

output "vertex_endpoint_id" {
  description = "Vertex AI Endpoint resource ID"
  value       = google_vertex_ai_endpoint.classifier.id
}

output "vertex_endpoint_url" {
  description = "Public HTTPS URL for online predictions"
  value       = "https://${var.region}-aiplatform.googleapis.com/v1/${google_vertex_ai_endpoint.classifier.id}:predict"
}