# Deploy AegisRoute to Google Cloud Run

## Prerequisites
1. A Google Cloud account (free tier available)
2. Google Cloud SDK (gcloud) installed on your machine
3. Docker installed (optional, but helpful for local testing)

## Step 1: Set up Google Cloud Project
1. Go to https://console.cloud.google.com/ and create a new project
2. Note your Project ID (e.g., `aegisroute-123456`)

## Step 2: Enable Required APIs
1. Go to https://console.cloud.google.com/apis/library
2. Enable the following APIs:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

## Step 3: Authenticate and Configure gcloud
Run these commands in your terminal:
```bash
# Log in to your Google Cloud account
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Set your region (choose one close to you, e.g., us-central1)
gcloud config set run/region us-central1
```

## Step 4: Deploy to Cloud Run
Run this command from the AegisRoute directory:
```bash
gcloud run deploy aegisroute-router \
  --source . \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

## Step 5: Get Your Deployment URL
After deployment completes, gcloud will give you a URL like:
`https://aegisroute-router-abcdef1234-uc.a.run.app`

## Step 6: Update Your Streamlit Dashboard
Update the `ROUTER_URL` in your Streamlit dashboard (or set it as an environment variable in your Streamlit deployment):
```python
ROUTER_URL = os.environ.get("ROUTER_URL", "https://your-cloud-run-url.a.run.app")
```

## Local Testing with Docker
To test locally before deploying:
```bash
# Build the Docker image
docker build -t aegisroute .

# Run the container
docker run -p 8000:8000 aegisroute
```

Then visit http://localhost:8000/docs to test the API!
