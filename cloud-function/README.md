# Deploying the ArXiv Paper Scraper Cloud Function

This guide explains how to deploy the ArXiv paper scraper as a Google Cloud Function with a Cloud Scheduler.

## Prerequisites

1. Install Google Cloud SDK
2. Enable required APIs:

   ```bash
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

3. Create a Google Cloud Storage bucket:
   ```bash
   gsutil mb gs://YOUR_BUCKET_NAME
   ```

## Deployment Steps

1. Deploy the Cloud Function:

   ```bash
   gcloud functions deploy arxiv_scraper \
     --runtime python311 \
     --trigger-http \
     --allow-unauthenticated \
     --memory 512MB \
     --timeout 3600s \
     --set-env-vars BUCKET_NAME=YOUR_BUCKET_NAME
   ```

2. Create a Cloud Scheduler job (runs weekly on Saturday at 23:00 UTC):
   ```bash
   gcloud scheduler jobs create http arxiv-weekly-scraper \
     --schedule="0 23 * * 6" \
     --uri="YOUR_CLOUD_FUNCTION_URL" \
     --http-method=GET \
     --description="Runs every Saturday at 23:00 UTC to collect weekly arXiv papers"
   ```

## Environment Variables

- `BUCKET_NAME`: The name of the Google Cloud Storage bucket where the results will be stored

## Output

The function will create log files in the following format:

```
gs://YOUR_BUCKET_NAME/arxiv_papers/arxiv_DD_MM_YYYY_HH_MM.log
```

Each log file contains tab-separated entries with:

- Topic code
- Paper ID
- Paper title

## Monitoring

You can monitor the function's execution in the Google Cloud Console:

- Cloud Functions logs
- Cloud Storage for the output files
- Cloud Scheduler for the execution schedule
