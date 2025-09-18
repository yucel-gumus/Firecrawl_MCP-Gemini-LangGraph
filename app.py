"""
Bu script, LangGraph, Gemini ve Firecrawl MCP kullanarak belirtilen bir web sayfasını özetleyen
bir AI agent oluşturur. Agent, Gemini modelini kullanarak web sayfasının içeriğini
analiz eder ve ana noktaları, istatistikleri ve önemli bulguları JSON formatında çıkarır.
Ayrıca, işlemin her adımının performansını ölçmek için kapsamlı benchmark (performans ölçümü)
özellikleri içerir.

Bu script, hem komut satırından hem de bir web arayüzü üzerinden çalıştırılabilir.

Komut Satırı Kullanımı:
    python app.py "https://example.com" --benchmark

Web Arayüzü Kullanımı:
    1. `uvicorn app:app --reload` komutu ile sunucuyu başlatın.
    2. Tarayıcınızda `http://127.0.0.1:8000` adresini açın.
"""

# --- 1. Gerekli Kütüphanelerin ve Modüllerin Yüklenmesi ---
import os
import asyncio
import json
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
import subprocess
from typing import Optional

# LangChain ve LangGraph kütüphaneleri
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# FastAPI ve web sunucusu için kütüphaneler
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# --- 2. Kurulum ve Ön Kontroller ---

# .env dosyasını yükle
load_dotenv()

# Gerekli API anahtarlarını kontrol et
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Hata: GEMINI_API_KEY ortam değişkeni ayarlanmamış.")
if not os.getenv("FIRECRAWL_API_KEY"):
    raise ValueError("Hata: FIRECRAWL_API_KEY ortam değişkeni ayarlanmamış.")

# npx kontrolü
try:
    subprocess.run(["npx", "--version"], check=True, capture_output=True)
except (subprocess.SubprocessError, FileNotFoundError):
    print(
        "Uyarı: 'npx' komutu bulunamadı. Firecrawl MCP'nin çalışması için Node.js ve npx'in yüklü olması gerekmektedir."
    )

# --- 3. FastAPI Uygulamasını ve Şablonları Ayarlama ---

# FastAPI uygulamasını oluştur
app = FastAPI()

# HTML şablonlarının bulunduğu dizini ayarla
templates = Jinja2Templates(directory="templates")


# İstek gövdesi için Pydantic modeli
class URLRequest(BaseModel):
    url: str


# --- 4. Ana Agent Mantığı ---


async def process_url(url: str, benchmark: bool = False):
    """
    Belirtilen URL'yi işleyen, özetleyen ve sonucu JSON olarak döndüren ana fonksiyon.
    """
    total_start_time = time.time()
    benchmark_data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "durations": {},
        "content_stats": {},
        "success": False,
        "error": None,
    }

    try:
        # --- Agent'ın Bileşenlerini Başlatma ---
        llm_init_start_time = time.time()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        benchmark_data["durations"]["llm_init_seconds"] = round(
            time.time() - llm_init_start_time, 3
        )

        connection = {
            "transport": "stdio",
            "command": "npx",
            "args": ["firecrawl-mcp"],
            "env": {"FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")},
        }

        tools_load_start_time = time.time()
        tools = await load_mcp_tools(None, connection=connection)
        scrape_tool = next((t for t in tools if t.name == "firecrawl_scrape"), None)
        benchmark_data["durations"]["tools_load_seconds"] = round(
            time.time() - tools_load_start_time, 3
        )

        if not scrape_tool:
            raise RuntimeError("Hata: 'firecrawl_scrape' aracı bulunamadı.")

        agent_init_start_time = time.time()
        agent = create_react_agent(llm, tools=[scrape_tool])
        benchmark_data["durations"]["agent_init_seconds"] = round(
            time.time() - agent_init_start_time, 3
        )

        # --- Agent İçin Talimat (Prompt) Hazırlama ---
        user_prompt = f"""
GÖREV: Aşağıdaki web sayfası içeriğini analiz et ve yapılandırılmış veri çıkar.

ADıM 1: firecrawl_scrape aracını kullanarak {url} adresinden içeriği çek.

ADIM 2: Çekilen içeriği dikkatlice analiz et ve şu bilgileri çıkar:

**ÖNEMLI**: İstatistikler için özellikle şunları ara:
- Yüzdeler: %25, 50%, "yüzde 75" gibi ifadeler
- Sayılar: 1,000; 5 milyon; 10.5 milyar gibi rakamlar
- Para birimleri: $100, €50, ₺1000, "100 dolar" gibi
- Tarihler: 2023, 2024 yılında, Ocak 2025 gibi
- Ölçümler: 50 km, 100 metre, 5 kg gibi
- Büyüme/düşüş oranları: "2 kat artış", "30% azalma" gibi
- Kullanıcı/kişi sayıları: "10,000 kullanıcı", "5 milyon kişi" gibi
- Zaman dilimleri: "3 yıl", "6 ay" gibi

**ÖNEMLİ UYARI**: Eğer metinde HİÇBİR sayısal veri bulamazsan, statistics alanını boş dizi [] olarak bırak. Ancak varsa MUTLAKA bul ve dahil et.

Sonucu bu JSON formatında ver:
{{
  "main_points": ["ana nokta 1", "ana nokta 2", "ana nokta 3"],
  "statistics": ["istatistik 1", "istatistik 2", "istatistik 3"],
  "key_findings": ["bulgu 1", "bulgu 2", "bulgu 3"]
}}

SADECE JSON döndür, başka hiçbir açıklama yazma.
        """

        # --- Veri Kazıma (Scraping) İşlemi ---
        print(f"'{url}' adresinden ham veri kazınıyor...")
        scrape_start_time = time.time()
        scrape_result = await scrape_tool.ainvoke({"url": url})
        benchmark_data["durations"]["scraping_seconds"] = round(
            time.time() - scrape_start_time, 3
        )

        raw_scraped_content = (
            scrape_result.content
            if hasattr(scrape_result, "content")
            else str(scrape_result)
        )
        benchmark_data["content_stats"]["scraped_content_length"] = len(
            raw_scraped_content
        )

        with open("raw_scraped_content.txt", "w", encoding="utf-8") as f:
            f.write(raw_scraped_content)
        print(f"Ham veri 'raw_scraped_content.txt' dosyasına kaydedildi.")

        # --- Agent'ı Çalıştırma ve Analizi Gerçekleştirme ---
        print("Agent, kazınan veriyi analiz ediyor...")
        llm_processing_start_time = time.time()
        response = await asyncio.wait_for(
            agent.ainvoke({"messages": [HumanMessage(content=user_prompt)]}),
            timeout=90.0,
        )
        benchmark_data["durations"]["llm_processing_seconds"] = round(
            time.time() - llm_processing_start_time, 3
        )

        # --- Sonucu İşleme ve Kaydetme ---
        agent_response_content = response["messages"][-1].content
        summary_json = None

        cleaned_content = agent_response_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:-3].strip()
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:-3].strip()

        try:
            summary_json = json.loads(cleaned_content)
            benchmark_data["success"] = True
            print("JSON çıktısı başarıyla oluşturuldu ve doğrulandı.")
        except json.JSONDecodeError:
            error_msg = "Uyarı: LLM çıktısı geçerli bir JSON formatında değil."
            benchmark_data["error"] = error_msg
            print(error_msg)
            summary_json = {"error": error_msg, "raw_text": agent_response_content}

        with open("web_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary_json, f, ensure_ascii=False, indent=2)
        print(f"Yapılandırılmış özet 'web_summary.json' dosyasına kaydedildi.")
        benchmark_data["content_stats"]["summary_length"] = len(
            json.dumps(summary_json)
        )

        return summary_json

    except Exception as e:
        error_msg = f"İşlem sırasında beklenmeyen bir hata oluştu: {e}"
        benchmark_data["error"] = error_msg
        print(error_msg)
        return {"error": error_msg}

    finally:
        # --- Benchmark Sonuçlarını Hesaplama ve Raporlama ---
        total_end_time = time.time()
        benchmark_data["durations"]["total_seconds"] = round(
            total_end_time - total_start_time, 3
        )

        benchmark_file = "benchmark_results.json"
        try:
            existing_data = []
            if os.path.exists(benchmark_file):
                with open(benchmark_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            existing_data.append(benchmark_data)
            with open(benchmark_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"Performans metrikleri '{benchmark_file}' dosyasına eklendi.")

            if benchmark:
                print("\n" + "=" * 50 + "\nDETAYLI PERFORMANS RAPORU\n" + "=" * 50)
                # ... (benchmark raporlama kodu buraya eklenebilir) ...
                print(json.dumps(benchmark_data, indent=2))

        except Exception as e:
            print(f"Benchmark sonuçları kaydedilirken bir hata oluştu: {e}")


# --- 5. FastAPI Endpoints ---


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Ana sayfayı (index.html) sunar.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/summarize", response_class=JSONResponse)
async def summarize_url(request: URLRequest):
    """
    Kullanıcıdan gelen URL'yi alır, `process_url` fonksiyonunu çalıştırır
    ve sonucu JSON olarak döndürür.
    """
    try:
        summary = await process_url(request.url)
        return JSONResponse(content=summary)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- 6. Komut Satırı Çalıştırıcısı ---


async def cli_main():
    """
    Komut satırı argümanlarını işleyen ve `process_url`'i çağıran fonksiyon.
    """
    parser = argparse.ArgumentParser(
        description="Bir web sayfasını kazıyıp özetleyen ve performansını ölçen AI Agent."
    )
    parser.add_argument(
        "url", type=str, help="Kazınacak ve özetlenecek web sayfasının tam URL'si."
    )
    parser.add_argument(
        "--benchmark",
        "-b",
        action="store_true",
        help="İşlem sonunda detaylı bir benchmarking raporu gösterir.",
    )
    args = parser.parse_args()
    await process_url(args.url, benchmark=args.benchmark)


if __name__ == "__main__":
    # Script'in doğrudan mı yoksa uvicorn tarafından mı çalıştırıldığını kontrol et
    if "uvicorn" in os.sys.argv[0]:
        # Web sunucusu olarak çalışıyorsa bir şey yapma, FastAPI devralır
        pass
    else:
        # Komut satırından çalıştırılıyorsa
        asyncio.run(cli_main())
