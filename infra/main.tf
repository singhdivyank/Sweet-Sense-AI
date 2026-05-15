terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 1.83"
    }
  }
  
  backend "gcs" {
    bucket = "sweet-sense-ai-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project     = var.gcp_project
  region      = var.region
  credentials = file(var.gcp_service_account_path)
}

provider "confluent" {
  cloud_api_key    = var.confluent_api_key
  cloud_api_secret = var.confluent_api_secret
}

locals {
  model = {
    name                      = "sweet-sense-diabetes-classifier"
    version                   = var.model_version
    display_name              = "Sweet-Sense Diabetes Classifier v${var.model_version}"

    artefact_dir              = "gs://${var.model_bucket}/models/${var.model_version}"
    prepared_model_path       = "gs://${var.model_bucket}/models/${var.model_version}/prepared_model.json"
    explanation_metadata_path = "gs://${var.model_bucket}/models/${var.model_version}/explanation_metadata.json"
    explanation_params_path   = "gs://${var.model_bucket}/models/${var.model_version}/explanation_parameters.json"
  }

  common_labels = {
    project     = "sweet-sense-ai"
    environment = var.environment
    version     = replace(var.model_version, ".", "-")
    managed_by  = "terraform"
  }
}
