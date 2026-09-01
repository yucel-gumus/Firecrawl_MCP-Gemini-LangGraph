"""
FastAPI Web Application: Firecrawl & Gemini LangGraph Summarizer
Modern web arayüzü ve REST API sunucusu.
"""

import os
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core import run_pipeline, validate_environment
from config import DEFAULT_MODEL, ALLOWED_MODELS, DEFAULT_PORT
from fastapi.middleware.cors import CORSMiddleware


# --- Uygulama Yaşam Döngüsü ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlarken env değişkenlerini bir kez doğrular."""
    validate_environment()
    yield


# FastAPI uygulamasını başlat
app = FastAPI(
    title="Firecrawl & Gemini LangGraph Web Summarizer",
    description="Firecrawl Python SDK ve LangGraph ile Otonom Web Kazıma ve Yapılandırılmış Özetleme API",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Middleware Ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Şablonları dizini
templates = Jinja2Templates(directory="templates")

# Statik dosyaları servis et (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic İstek ve Yanıt Modelleri ---

class SummarizeRequest(BaseModel):
    url: HttpUrl = Field(..., description="Kazınacak ve özetlenecek tam web sayfası URL'si")
    model: Optional[str] = Field(
        default=None,
        description=f"Kullanılacak Gemini modeli (boş bırakılırsa varsayılan: {DEFAULT_MODEL})"
    )


# --- Endpointler ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Ana dashboard sayfasını sunar."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/summarize", response_class=JSONResponse)
async def summarize_endpoint(req: SummarizeRequest):
    """
    Gönderilen URL'yi LangGraph + Firecrawl SDK + Gemini hattında işler
    ve yapılandırılmış özet + performans metriklerini döndürür.
    """
    url_str = str(req.url)
    model_name = req.model or DEFAULT_MODEL

    if model_name not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz model: '{model_name}'. İzin verilen modeller: {', '.join(ALLOWED_MODELS)}"
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
