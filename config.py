"""
config.py — Merkezi Uygulama Ayarları
Tüm model isimleri, fallback zinciri ve sabitler buradan yönetilir.
Model değiştirmek için SADECE bu dosyayı düzenleyin.
"""

# ──────────────────────────────────────────────
# Gemini Model Yapılandırması
# ──────────────────────────────────────────────

# Birincil model: structured output (response_schema) destekleyen en güncel model
DEFAULT_MODEL = "gemini-3.6-flash"

# Fallback zinciri: birincil modelde hata alınırsa sırayla denenir
# NOT: DEFAULT_MODEL zaten 1. sıraya ekleniyor — buraya yazılmamalı
FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

# İzin verilen modellerin tam listesi (Güvenlik kontrolü için)
ALLOWED_MODELS = [DEFAULT_MODEL] + FALLBACK_MODELS

# ──────────────────────────────────────────────
# Zaman Aşımı Ayarları
# ──────────────────────────────────────────────

# Gemini API HTTP timeout (milisaniye) — LLM yanıtı için maksimum bekleme
LLM_TIMEOUT_MS = 120_000  # 120 saniye

# LangGraph pipeline toplam timeout (saniye)
PIPELINE_TIMEOUT_S = 120.0

# ──────────────────────────────────────────────
# Sunucu Ayarları
# ──────────────────────────────────────────────

DEFAULT_PORT = 8000
