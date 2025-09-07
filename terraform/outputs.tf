output "function_url" {
  description = "The URL of the deployed Cloud Function"
  value       = google_cloudfunctions_function.arxiv_scraper.https_trigger_url
}

output "papers_bucket" {
  description = "The name of the GCS bucket storing ArXiv papers data"
  value       = google_storage_bucket.arxiv_papers.name
  sensitive   = true
}

output "scheduler_job" {
  description = "The name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.arxiv_scheduler.name
}
