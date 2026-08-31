# Terraform Outputs for PCA Study Agent Infrastructure

output "cloud_run_service_uri" {
  description = "The public URL endpoint of the deployed PCA Study Agent FastAPI service."
  value       = google_cloud_run_v2_service.study_agent_service.uri
}

output "service_account_email" {
  description = "The email address of the dedicated Cloud Run runtime service account."
  value       = google_service_account.agent_runner_sa.email
}

output "storage_bucket_name" {
  description = "The name of the GCS bucket for study materials."
  value       = google_storage_bucket.study_materials_bucket.name
}

output "secret_manager_secret_id" {
  description = "The ID of the Secret Manager secret for API keys."
  value       = google_secret_manager_secret.gemini_api_key.secret_id
}
