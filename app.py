"""
FastAPI Web Application: Firecrawl & Gemini LangGraph Summarizer
Modern web arayüzü ve REST API sunucusu.
"""

import logging
import os
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn
from pydantic import BaseModel, Field, HttpUrl
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from core import run_pipeline, validate_environment
from config import DEFAULT_MODEL, DEFAULT_PORT, get_runtime_config

logger = logging.getLogger(__name__)


# --- Basit Sliding-Window IP Rate Limiter ---
_rate_lock = threading.Lock()
_ip_hits: dict[str, deque[float]] = {}
_RATE_WINDOW_SECONDS = 60.0


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        # Cloud Run arkasında son proxy'den önceki veya sağdan güvenilen IP
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return request.client.host if request.client else "unknown"


def _is_rate_limited(ip: str, limit: int) -> bool:
    if limit <= 0:
        return False
    now = time.monotonic()
    with _rate_lock:
        if len(_ip_hits) > 5000:
            stale = [k for k, q in _ip_hits.items() if not q or now - q[-1] >= _RATE_WINDOW_SECONDS]
            for k in stale:
                del _ip_hits[k]
        hits = _ip_hits.setdefault(ip, deque())
        while hits and now - hits[0] >= _RATE_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= limit:
            return True
        hits.append(now)
        return False


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """Firestore `system_config/firecrawl.allowed_origins` listesine göre dinamik CORS."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        cfg = get_runtime_config()
        allowed = set(cfg.get("allowed_origins") or [])
        request_origin = f"{request.url.scheme}://{request.url.netloc}"
        is_allowed = bool(origin and (origin in allowed or origin == request_origin))

        if request.method == "OPTIONS":
            headers = {"Vary": "Origin"}
            if is_allowed:
                headers.update({
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                })
            return Response(status_code=204 if is_allowed else 403, headers=headers)

        response = await call_next(request)
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response


# --- Uygulama Yaşam Döngüsü ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlarken yapılandırmayı yükler."""
    try:
        validate_environment()
    except Exception as exc:
        logger.warning("Başlangıç doğrulama uyarısı (istekte yeniden denenecek): %s", exc)
    yield


# FastAPI uygulamasını başlat
app = FastAPI(
    title="Firecrawl & Gemini LangGraph Web Summarizer",
    description="Firecrawl Python SDK ve LangGraph ile Otonom Web Kazıma ve Yapılandırılmış Özetleme API",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(DynamicCORSMiddleware)

# HTML Şablonları dizini
templates = Jinja2Templates(directory="templates")

# Statik dosyaları servis et (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic İstek ve Yanıt Modelleri ---

class SummarizeRequest(BaseModel):
    url: HttpUrl = Field(..., description="Kazınacak ve özetlenecek tam web sayfası URL'si")
    model: Optional[str] = Field(
        default=None,
        description=f"Kullanılacak Gemini modeli (boş bırakılırsa Firestore / varsayılan: {DEFAULT_MODEL})"
    )


# --- Endpointler ---

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Cloud Run sağlık kontrolü ve aktif model durumu."""
    cfg = get_runtime_config()
    return {
        "status": "ok",
        "active_model": cfg.get("active_model", DEFAULT_MODEL),
        "thinking_level": cfg.get("thinking_level", "high"),
    }


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Ana dashboard sayfasını sunar."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/summarize", response_class=JSONResponse)
async def summarize_endpoint(req: SummarizeRequest, request: Request):
    """
    Gönderilen URL'yi LangGraph + Firecrawl SDK + Gemini hattında işler
    ve yapılandırılmış özet + performans metriklerini döndürür.
    """
    cfg = get_runtime_config()
    limit = int(cfg.get("rate_limit_per_minute", 10))
    if _is_rate_limited(_client_ip(request), limit):
        raise HTTPException(
            status_code=429,
            detail="Çok fazla istek gönderildi. Lütfen bir dakika sonra yeniden deneyin.",
        )

    url_str = str(req.url)
    allowed_models = cfg.get("allowed_models") or [DEFAULT_MODEL]
    model_name = req.model or cfg.get("active_model") or DEFAULT_MODEL

    if model_name not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz model: '{model_name}'. İzin verilen modeller: {', '.join(allowed_models)}"
        )

    try:
        result = await run_pipeline(
            url=url_str,
            model_name=model_name
        )
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "summary": None,
                "durations": {}
            }
        )


# --- Sunucuyu Başlatma ---

if __name__ == "__main__":
    port = int(os.getenv("PORT", DEFAULT_PORT))
    print(f"🌐 FastAPI Sunucusu Başlatılıyor: http://127.0.0.1:{port}")
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
