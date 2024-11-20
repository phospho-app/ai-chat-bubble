
# This file use GCP cloud build to build the image and deploy it to GCP Cloud Run
# For it to work with your GCP project, replace the project id, region, and other variables with your own

# You will need 
# - Qdrant cloud to host your vectors: https://qdrant.tech 
# - gcloud CLI installed and authenticated with your GCP account: https://cloud.google.com/sdk/docs/install
# - environment variables in app/.env file (look at app/.env.example for reference)

# EXAMPLE USAGE: 
#      gcloud init
#      sudo bash app/gcloud_deploy.sh

echo "Deploying ai-chat-bubble to GCP"

# GCP builds the image and pushes it to the container registry
gcloud builds submit --region=europe-west1 --tag europe-west1-docker.pkg.dev/portal-385519/phospho-backend/ai-chat-bubble:latest

# Read the .env file and export the variables
set -a && source .env && set +a

# Deploy the image to GCP Cloud Run
gcloud run deploy ai-chat-bubble \
 --image=europe-west1-docker.pkg.dev/portal-385519/phospho-backend/ai-chat-bubble:latest \
 --region=europe-west1 \
 --allow-unauthenticated \
 --set-env-vars URL=$URL,PHOSPHO_API_KEY=$PHOSPHO_API_KEY,PHOSPHO_PROJECT_ID=$PHOSPHO_PROJECT_ID \
 --set-env-vars QDRANT_API_KEY=$QDRANT_API_KEY,QDRANT_LOCATION=$QDRANT_LOCATION,ORIGIN=$ORIGIN,MISTRAL_API_KEY=$MISTRAL_API_KEY \
 --memory=1Gi