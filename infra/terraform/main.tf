# Google Cloud PCA Study Agent - Terraform Infrastructure as Code
# Provisions Secret Manager, Cloud Storage, Service Account IAM, and Cloud Run Service

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Google Cloud Storage Bucket for Seed Study Materials & Backups
resource "google_storage_bucket" "study_materials_bucket" {
  name                        = "${var.project_id}-pca-study-materials"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# 2. Secret Manager Secret for Gemini API Credentials
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = var.secret_manager_key_name

  replication {
    auto {}
  }
}

# 3. Dedicated Service Account with Least Privilege
resource "google_service_account" "agent_runner_sa" {
  account_id   = "pca-study-agent-runner"
  display_name = "PCA Study Agent Runtime Service Account"
  description  = "Service account for PCA Study Agent running on Cloud Run with minimal Secret Manager access."
}

# Grant Secret Accessor to the Agent Service Account
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runner_sa.email}"
}

# Grant Storage Object Viewer to access study materials
resource "google_storage_bucket_iam_member" "bucket_viewer" {
  bucket = google_storage_bucket.study_materials_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.agent_runner_sa.email}"
}

# 4. Cloud Run Service Deployment
resource "google_cloud_run_v2_service" "study_agent_service" {
  name     = "pca-study-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.agent_runner_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "USE_GCP_SECRET_MANAGER"
        value = "true"
      }
      env {
        name  = "SECRET_MANAGER_KEY_NAME"
        value = var.secret_manager_key_name
      }
      env {
        name  = "ENABLE_OTEL_TRACING"
        value = "true"
      }

      ports {
        container_port = 8000
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated public access for testing (optional / can be restricted)
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  service  = google_cloud_run_v2_service.study_agent_service.name
  location = google_cloud_run_v2_service.study_agent_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
