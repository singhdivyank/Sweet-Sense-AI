variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_service_account_path" {
  description = "Local path to the GCP service account JSON key"
  type        = string
  sensitive   = true
}

variable "model_version" {
  description = "Semantic version of the model being deployed (e.g. 1.0.0)"
  type        = string
}

variable "model_bucket" {
  description = "GCS bucket name that stores model artefacts"
  type        = string
}

variable "local_artefact_dir" {
  description = "Local directory containing the three model JSON files"
  type        = string
  default     = "./model/jsons"
}

variable "vertex_machine_type" {
  description = "Machine type for Vertex AI dedicated resources"
  type        = string
  default     = "n1-standard-4"
}

variable "vertex_min_replicas" {
  description = "Minimum number of Vertex AI replicas (autoscaling lower bound)"
  type        = number
  default     = 1
}

variable "vertex_max_replicas" {
  description = "Maximum number of Vertex AI replicas (autoscaling upper bound)"
  type        = number
  default     = 3
}

variable "confluent_api_key" {
  description = "Confluent Cloud API key (from Confluent Cloud Console)"
  type        = string
  sensitive   = true
}

variable "confluent_api_secret" {
  description = "Confluent Cloud API secret"
  type        = string
  sensitive   = true
}

variable "kafka_partitions" {
  description = "Number of partitions for each Kafka topic"
  type        = number
  default     = 3
}

variable "kafka_retention_ms" {
  description = "Kafka topic retention in milliseconds (default: 7 days)"
  type        = number
  default     = 604800000
}