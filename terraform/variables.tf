variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "The region to deploy resources to"
  type        = string
  default     = "us-central1"
}

variable "papers_bucket_name" {
  description = "Prefix for the GCS bucket name to store ArXiv papers data"
  type        = string
  default     = "arxiv-papers-"
}

variable "function_name" {
  description = "Name of the Cloud Function"
  type        = string
  default     = "arxiv-papers-scraper-func"
}

variable "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  type        = string
  default     = "arxiv-papers-weekly-job"
}

variable "service_account_id" {
  description = "ID for the service account"
  type        = string
  default     = "arxiv-papers-scheduler-sa"
}
