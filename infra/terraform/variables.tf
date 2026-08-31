# Terraform Variables for PCA Study Agent Infrastructure

variable "project_id" {
  type        = string
  description = "The Google Cloud project ID to deploy resources into."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "The Google Cloud region for compute and storage resources."
}

variable "container_image" {
  type        = string
  default     = "gcr.io/google-cloud-pca/study-agent:latest"
  description = "The Artifact Registry / GCR container image URI."
}

variable "secret_manager_key_name" {
  type        = string
  default     = "pca-study-agent-gemini-key"
  description = "Name of the Secret Manager secret containing the Gemini API key."
}

variable "allow_unauthenticated" {
  type        = bool
  default     = true
  description = "Whether to allow unauthenticated public invocations on the Cloud Run endpoint."
}
