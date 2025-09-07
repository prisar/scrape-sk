# Terraform Deployment for ArXiv Scraper

This directory contains Terraform configurations to deploy the ArXiv scraper as a Google Cloud Function with associated resources.

## Prerequisites

1. Install Terraform
2. Install Google Cloud SDK
3. Enable required APIs:
   ```bash
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable iam.googleapis.com
   ```

## Configuration

There are two ways to configure the deployment:

1. Using environment variables:
   ```bash
   export TF_VAR_project_id="your-project-id"
   export TF_VAR_papers_bucket_name="your-bucket-name"
   ```

2. Using a local tfvars file (recommended for development):
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   Then edit `terraform.tfvars` with your specific values. This file is git-ignored for security.

Note: Never commit `terraform.tfvars` or any files containing sensitive information to version control.

## Deployment

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Preview the changes:
   ```bash
   terraform plan
   ```

3. Apply the configuration:
   ```bash
   terraform apply
   ```

## Resources Created

- Cloud Storage bucket for function source code
- Cloud Storage bucket for ArXiv papers data
- Cloud Function with HTTP trigger
- Cloud Scheduler job (runs weekly on Saturday at 23:00 UTC)
- Service Account for Cloud Scheduler
- IAM bindings

## Outputs

After deployment, Terraform will output:
- The Cloud Function URL
- The name of the GCS bucket storing ArXiv papers
- The name of the Cloud Scheduler job

## Cleanup

To remove all created resources:
```bash
terraform destroy
```
