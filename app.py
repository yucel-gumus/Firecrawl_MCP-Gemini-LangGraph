"""
FastAPI Web Application: Firecrawl MCP & Gemini LangGraph Summarizer
Modern web arayüzü ve REST API sunucusu.
"""

import os
import json
import uvicorn
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from core import run_pipeline, validate_environment

# FastAPI uygulamasını başlat
app = FastAPI(
    title="Firecrawl MCP & Gemini LangGraph Web Summarizer",
    description="Model Context Protocol (MCP) ve LangGraph ile Otonom Web Kazıma ve Yapılandırılmış Özetleme API",
    version="2.0.0"
)

# HTML Şablonları dizini
templates = Jinja2Templates(directory="templates")


# --- Pydantic İstek ve Yanıt Modelleri ---

class SummarizeRequest(BaseModel):
    url: str = Field(..., description="Kazınacak ve özetlenecek tam web sayfası URL'si")
    model: Optional[str] = Field(default="gemini-3.7-flash", description="Kullanılacak Gemini modeli")
    save_files: Optional[bool] = Field(default=True, description="Sonuçların diske yazılıp yazılmayacağı")


# --- Endpointler ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Ana dashboard sayfasını sunar."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/summarize", response_class=JSONResponse)
async def summarize_endpoint(req: SummarizeRequest):
    """
    Gönderilen URL'yi LangGraph + Firecrawl MCP + Gemini hattında işler
    ve yapılandırılmış özet + performans metriklerini döndürür.
    """
    url_str = req.url.strip()
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        raise HTTPException(status_code=400, detail="Geçerli bir URL girmelisiniz (http:// veya https:// ile başlamalıdır).")

    try:
        result = await run_pipeline(
            url=url_str,
            save_files=req.save_files if req.save_files is not None else True,
            model_name=req.model or "gemini-3.7-flash"
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


@app.get("/api/benchmark-history", response_class=JSONResponse)
async def get_benchmark_history():
    """benchmark_results.json dosyasındaki geçmiş performans kayıtlarını döner."""
    benchmark_file = "benchmark_results.json"
    if os.path.exists(benchmark_file):
        try:
            with open(benchmark_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return JSONResponse(content=data[-20:])  # Son 20 kayıt
                return JSONResponse(content=[data])
        except Exception:
            return JSONResponse(content=[])
    return JSONResponse(content=[])


# --- Sunucuyu Başlatma ---

if __name__ == "__main__":
    # python app.py komutuyla doğrudan FastAPI & Uvicorn sunucusunu başlatır
    print("🌐 FastAPI Sunucusu Başlatılıyor: http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
