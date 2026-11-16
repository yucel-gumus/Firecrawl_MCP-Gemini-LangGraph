#!/bin/bash
# Google Cloud Run Deployment Script - AUTO DEPLOY
# Runtime yapılandırma ve API anahtarları Firebase Firestore (aimunazara)
# `system_config/llm` + `system_config/firecrawl` üzerinden ADC ile okunur.

set -euo pipefail

echo "🚀 Firecrawl & Gemini LangGraph Web Summarizer - Cloud Run Deploy"

SERVICE_NAME="firecrawl-ai-summarizer"
REGION="europe-west4"
PROJECT_ID="agenticai-500618"

echo "Servis Adı: $SERVICE_NAME ($PROJECT_ID / $REGION)"

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 180s \
  --remove-env-vars="GEMINI_API_KEY,FIRECRAWL_API_KEY"

echo "✅ Canlı Deploy komutu tamamlandı."
