terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a zip of the Cloud Function code
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../cloud-function"
  output_path = "${path.root}/function.zip"
  excludes    = ["README.md", "__pycache__"]
}

# Create Cloud Storage bucket for function code
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "google_storage_bucket" "function_bucket" {
  name     = "function-source-${random_id.bucket_suffix.hex}"
  location = var.region
  uniform_bucket_level_access = true
}

# Upload function code to bucket
resource "google_storage_bucket_object" "function_code" {
  name   = "function-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_zip.output_path
}

# Create bucket for ArXiv papers
resource "random_id" "papers_bucket_suffix" {
  byte_length = 4
}

resource "google_storage_bucket" "arxiv_papers" {
  name     = "${var.papers_bucket_name}${random_id.papers_bucket_suffix.hex}"
  location = var.region
  uniform_bucket_level_access = true
}

# Create Cloud Function
resource "google_cloudfunctions_function" "arxiv_scraper" {
  name                  = var.function_name
  description           = "Function to scrape ArXiv papers weekly"
  runtime               = "python39"
  available_memory_mb   = 512
  timeout               = 540
  entry_point          = "arxiv_scraper"
  
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_code.name
  
  trigger_http = true

  environment_variables = {
    BUCKET_NAME = google_storage_bucket.arxiv_papers.name
  }
}

# Create Cloud Scheduler job
resource "google_cloud_scheduler_job" "arxiv_scheduler" {
  name        = var.scheduler_job_name
  description = "Runs every Saturday at 23:00 UTC to collect weekly arXiv papers"
  schedule    = "0 23 * * 6"
  time_zone   = "UTC"

  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions_function.arxiv_scraper.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }
}

# Create service account for Cloud Scheduler
resource "google_service_account" "scheduler_invoker" {
  account_id   = var.service_account_id
  display_name = "Service Account for Cloud Scheduler to invoke Cloud Function"
}

# Grant invoker role to service account
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.arxiv_scraper.project
  region         = google_cloudfunctions_function.arxiv_scraper.region
  cloud_function = google_cloudfunctions_function.arxiv_scraper.name
  role          = "roles/cloudfunctions.invoker"
  member        = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}
