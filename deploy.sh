#!/bin/bash
# Google Cloud Run Deployment Script - AUTO DEPLOY
# Bu script API keyleri gizlice okur ve Cloud Run'a atar.

echo "🚀 Firecrawl & Gemini LangGraph Web Summarizer - Secure Cloud Run Deploy"

SERVICE_NAME="firecrawl-ai-summarizer"
REGION="europe-west4"

echo "Servis Adı: $SERVICE_NAME"
echo "Bölge: $REGION"
echo "Güvenlik: API keyler .env'den alınıyor..."

# .env dosyasından okuma (başında # olmayan satırları export eder)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "HATA: .env dosyası bulunamadı. Lütfen API keyleri kontrol edin."
  exit 1
fi

echo "Deployment başlıyor. (Maksimum 2 instances, Minimum 0 instances, CPU Allocation aktif)"

# Secret değişkenleri terminale yazdırmadan (--quiet vb) çalıştırıyoruz.
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 180s \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}"

echo "✅ Canlı Deploy komutu tamamlandı."
