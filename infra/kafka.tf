resource "confluent_environment" "sweet_sense" {
  display_name = "sweet-sense-${var.environment}"

  stream_governance {
    package = "ESSENTIALS"
  }
}

resource "confluent_kafka_cluster" "main" {
  display_name = "sweet-sense-${var.environment}-cluster"
  availability = "SINGLE_ZONE"
  cloud        = "GCP"
  region       = var.region

  basic {}

  environment {
    id = confluent_environment.sweet_sense.id
  }
}

resource "confluent_service_account" "app" {
  display_name = "sweet-sense-${var.environment}-sa"
  description  = "Service account for Sweet-Sense producers and consumers"
}

resource "confluent_role_binding" "app_producer" {
  principal   = "User:${confluent_service_account.app.id}"
  role_name   = "DeveloperWrite"
  crn_pattern = "${confluent_kafka_cluster.main.rbac_crn}/kafka=${confluent_kafka_cluster.main.id}/topic=vitals-input"
}

resource "confluent_role_binding" "app_consumer" {
  principal   = "User:${confluent_service_account.app.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${confluent_kafka_cluster.main.rbac_crn}/kafka=${confluent_kafka_cluster.main.id}/topic=diagnostics-output"
}

resource "confluent_api_key" "app_kafka" {
  display_name = "sweet-sense-${var.environment}-kafka-key"
  description  = "Kafka API key for Sweet-Sense application service account"

  owner {
    id          = confluent_service_account.app.id
    api_version = confluent_service_account.app.api_version
    kind        = confluent_service_account.app.kind
  }

  managed_resource {
    id          = confluent_kafka_cluster.main.id
    api_version = confluent_kafka_cluster.main.api_version
    kind        = confluent_kafka_cluster.main.kind

    environment {
      id = confluent_environment.sweet_sense.id
    }
  }

  depends_on = [
    confluent_role_binding.app_producer,
    confluent_role_binding.app_consumer,
  ]
}

resource "confluent_kafka_topic" "vitals_input" {
  topic_name       = "vitals-input"
  partitions_count = var.kafka_partitions
  rest_endpoint    = confluent_kafka_cluster.main.rest_endpoint

  config = {
    "cleanup.policy"  = "delete"
    "retention.ms"    = tostring(var.kafka_retention_ms)
    "compression.type" = "lz4"
  }

  credentials {
    key    = confluent_api_key.app_kafka.id
    secret = confluent_api_key.app_kafka.secret
  }

  kafka_cluster {
    id = confluent_kafka_cluster.main.id
  }

  environment {
    id = confluent_environment.sweet_sense.id
  }

  depends_on = [confluent_api_key.app_kafka]
}

resource "confluent_kafka_topic" "diagnostics_output" {
  topic_name       = "diagnostics-output"
  partitions_count = var.kafka_partitions
  rest_endpoint    = confluent_kafka_cluster.main.rest_endpoint

  config = {
    "cleanup.policy"   = "delete"
    "retention.ms"     = tostring(var.kafka_retention_ms)
    "compression.type" = "lz4"
  }

  credentials {
    key    = confluent_api_key.app_kafka.id
    secret = confluent_api_key.app_kafka.secret
  }

  kafka_cluster {
    id = confluent_kafka_cluster.main.id
  }

  environment {
    id = confluent_environment.sweet_sense.id
  }

  depends_on = [confluent_api_key.app_kafka]
}

output "kafka_bootstrap_endpoint" {
  description = "Kafka cluster bootstrap endpoint"
  value       = confluent_kafka_cluster.main.bootstrap_endpoint
}

output "kafka_api_key_id" {
  description = "Kafka API key ID (username)"
  value       = confluent_api_key.app_kafka.id
  sensitive   = true
}

output "kafka_api_key_secret" {
  description = "Kafka API key secret (password)"
  value       = confluent_api_key.app_kafka.secret
  sensitive   = true
}