# --- Sadece Python — Node.js/npx gerektirmez ---
FROM python:3.11-slim

# Temel sistem araçları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Önce bağımlılıkları kur (Docker layer cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Cloud Run PORT env değişkenini kullanır (varsayılan 8080)
ENV PORT=8080

# Uvicorn — production modu (reload yok, tek worker)
CMD uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1
