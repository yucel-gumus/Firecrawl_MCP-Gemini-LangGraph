#!/bin/bash
# Google Cloud Run Deployment Script
# Bu script, maliyet optimizasyonu ve Gunicorn yapılandırması ile projeyi deploy eder.

echo "🚀 Firecrawl & Gemini LangGraph Web Summarizer - Cloud Run Deploy"

SERVICE_NAME="firecrawl-ai-summarizer"
REGION="europe-west4"

echo "Servis Adı: $SERVICE_NAME"
echo "Bölge: $REGION"
echo "Deployment başlıyor. (Maksimum 2 instances, Minimum 0 instances, CPU Allocation aktif)"

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 180s \
  --update-env-vars="PORT=8080"

echo "✅ Deploy komutu tamamlandı."
echo ""
echo "⚠️  LÜTFEN DİKKAT: Uygulamanın çalışması için API anahtarlarınızı eklemeniz gerekiyor."
echo "Güvenliğiniz için terminalde düz metin (plain-text) yazmak istemezseniz, Google Cloud Console'dan ekleyebilirsiniz:"
echo "1. Cloud Console'a gidin -> Cloud Run -> $SERVICE_NAME"
echo "2. Edit & Deploy New Revision (Yeni Sürüm Düzenle) butonuna tıklayın."
echo "3. Variables & Secrets sekmesinde GEMINI_API_KEY ve FIRECRAWL_API_KEY değişkenlerini ekleyin ve deploy edin."
echo ""
echo "Veya gcloud CLI üzerinden şu komutla hemen ekleyebilirsiniz:"
echo "gcloud run services update $SERVICE_NAME --region=$REGION --update-env-vars=\"GEMINI_API_KEY=sizin_anahtar,FIRECRAWL_API_KEY=sizin_anahtar\""
