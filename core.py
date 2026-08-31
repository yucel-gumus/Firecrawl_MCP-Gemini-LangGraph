"""
Core Module: Firecrawl MCP + Google Gemini + LangGraph State Pipeline
Gelişmiş & Kapsamlı AI İstihbarat ve Web Analiz Motoru.
Web sayfasını derinlemesine analiz eder; yönetici özeti, detaylı konu kırılımları,
bağlamsal istatistikler, aksiyon maddeleri ve bahsedilen teknolojileri çıkarır.
"""

import os
import sys
import time
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph import StateGraph, START, END

# Ortam değişkenlerini yükle
load_dotenv()


# --- 1. Gelişmiş Pydantic Şemaları & Kapsamlı İstihbarat Modeli ---

class MetricItem(BaseModel):
    """Metinde geçen somut sayısal veri veya istatistik."""
    metric: str = Field(description="İstatistiğin veya ölçümün konusu/başlığı")
    value: str = Field(description="Sayısal değer, yüzde, para birimi, tarih veya miktar")
    context: str = Field(description="Bu verinin ne anlama geldiği ve bağlamı")


class TopicBreakdown(BaseModel):
    """Sayfadaki ana temalara ait detaylı konu kırılımı."""
    topic: str = Field(description="Ana konu başlığı")
    details: str = Field(description="Konunun derinlemesine analizi ve açıklaması")
    key_points: List[str] = Field(default_factory=list, description="Bu konuya ait önemli alt maddeler")


class WebSummary(BaseModel):
    """Web sayfasından çıkarılan zenginleştirilmiş ve kapsamlı veri modeli."""
    executive_summary: str = Field(
        description="Sayfanın amacını, çözülen problemi ve ana fikrini aktaran 2-3 paragraflık akıcı ve kapsamlı yönetici özeti"
    )
    topics: List[TopicBreakdown] = Field(
        default_factory=list,
        description="Sayfada ele alınan ana konuların ve argümanların detaylı analizi"
    )
    statistics: List[MetricItem] = Field(
        default_factory=list,
        description="Metinde tespit edilen tüm somut veriler, oranlar, tarihler, finansal rakamlar ve metrikler"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="Stratejik çıkarımlar, varılan nihai sonuçlar ve kritik bulgular"
    )
    actionable_takeaways: List[str] = Field(
        default_factory=list,
        description="Okuyucu, araştırmacı veya işletmeler için uygulanabilir eylem maddeleri ve tavsiyeler"
    )
    entities_and_technologies: List[str] = Field(
        default_factory=list,
        description="Metinde adı geçen önemli şirketler, teknolojiler, modeller, protokoller veya kişiler"
    )


class PipelineState(TypedDict, total=False):
    """LangGraph iş akışında düğümler arasında taşınan durum nesnesi."""
    url: str
    preferred_model: str
    raw_content: str
    summary: Dict[str, Any]
    durations: Dict[str, float]
    content_stats: Dict[str, int]
    success: bool
    error: Optional[str]


# --- 2. Yardımcı Fonksiyonlar & Temizleme ---

def check_npx_available() -> bool:
    """Sistemde npx komutunun bulunup bulunmadığını kontrol eder."""
    try:
        subprocess.run(["npx", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def validate_environment() -> None:
    """Gerekli API anahtarlarını ve sistem gereksinimlerini doğrular."""
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Hata: GEMINI_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")
    if not os.getenv("FIRECRAWL_API_KEY"):
        raise ValueError("Hata: FIRECRAWL_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")
    if not check_npx_available():
        print("Uyarı: 'npx' komutu bulunamadı. Firecrawl MCP için Node.js ve npx yüklü olmalıdır.", file=sys.stderr)


def extract_clean_markdown(raw_content: str) -> str:
    """Firecrawl MCP çıktısından saf Markdown metnini ayıklar."""
    if not raw_content:
        return ""
    try:
        parsed = json.loads(raw_content)
        if isinstance(parsed, list) and len(parsed) > 0:
            first_item = parsed[0]
            if isinstance(first_item, dict) and "text" in first_item:
                inner_json = json.loads(first_item["text"])
                if isinstance(inner_json, dict) and "markdown" in inner_json:
                    return inner_json["markdown"]
        elif isinstance(parsed, dict) and "markdown" in parsed:
            return parsed["markdown"]
    except Exception:
        pass
    return raw_content


# --- 3. MCP ve LLM İstemcileri ---

async def get_firecrawl_scrape_tool():
    """Firecrawl MCP aracını stdio transport üzerinden başlatır."""
    connection = {
        "transport": "stdio",
        "command": "npx",
        "args": ["firecrawl-mcp"],
        "env": {"FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")},
    }
    tools = await load_mcp_tools(None, connection=connection)
    scrape_tool = next((t for t in tools if t.name == "firecrawl_scrape"), None)
    if not scrape_tool:
        raise RuntimeError("Hata: 'firecrawl_scrape' MCP aracı yüklenemedi. Firecrawl API anahtarınızı kontrol edin.")
    return scrape_tool


def extract_structured_summary(
    content: str,
    url: str,
    preferred_model: str = "gemini-3.7-flash"
) -> WebSummary:
    """
    Google Gemini ile derinlemesine ve kapsamlı analiz yapar.
    10 saniyelik deadline ile birincil modeli dener; 503/gecikme durumunda
    anında optimize edilmiş yedek modellere geçerek yanıt üretir.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=120000)  # 120 saniye
    )

    prompt = f"""
Sen dünya standartlarında kıdemli bir araştırma analisti, veri bilimci ve stratejistsin.
Sana verilen web sayfası içeriğini derinlemesine, ayrıntılı ve hiçbir kritik detayı atlamadan analiz edeceksin.

KAYNAK URL: {url}
---
KAZINAN WEB İÇERİĞİ:
{content[:45000]}
---

GÖREV TALİMATLARI:
1. **executive_summary**: Sayfanın tamamını kapsayan, neyi amaçladığını, arka planını, çözülen problemi ve sunulan çözümleri anlatan en az 2-3 zengin ve akıcı Türkçe paragraf yaz.
2. **topics**: İçerikteki her bir ana konuyu/bölümü ayrı ayrı ele al. Başlığını, derinlemesine açıklamasını ('details') ve o konuya ait somut alt maddeleri ('key_points') detaylıca çıkar.
3. **statistics**: Metindeki TÜM somut sayısal verileri (% oranlar, maliyetler, kişi sayıları, tarihler, hız/performans ölçümleri, büyüme oranları vb.) konusu ('metric'), değeri ('value') ve bağlamıyla ('context') birlikte listele.
4. **key_findings**: Sayfadan çıkarılan en kritik stratejik bulguları, avantajları, dezavantajları ve nihai sonuçları geniş maddeler halinde yaz.
5. **actionable_takeaways**: Bu bilgileri okuyan bir uzman, yazılımcı veya yönetici hangi somut adımları atabilir? Uygulanabilir tavsiyeler üret.
6. **entities_and_technologies**: Metinde adı geçen şirketler, algoritmalar, yapay zeka modelleri, yazılım dilleri, framework'ler ve kişileri listele.

Lütfen yüzeysel veya kısa maddeler yerine, okuyucuya tam kapsamlı istihbarat sunacak zenginlikte yanıt ver.
"""

    # Geçerli ve aktif Gemini model isimleri
    fallback_models = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
    models_to_try = [preferred_model] if preferred_model else []
    for m in fallback_models:
        if m not in models_to_try:
            models_to_try.append(m)

    last_err = None
    for model_name in models_to_try:
        try:
            # Chat API kullanımı: SDK'nın önerdiği yöntem (AFC uyarısını önler)
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=WebSummary,
                    temperature=0.1
                )
            )
            resp = chat.send_message(prompt)
            return WebSummary.model_validate_json(resp.text)
        except BrokenPipeError as exc:
            last_err = exc
            print(f"Bilgi: '{model_name}' bağlantı hatası (Broken Pipe), sonraki modele geçiliyor...", file=sys.stderr)
        except Exception as exc:
            last_err = exc
            print(f"Bilgi: '{model_name}' geçici yanıt vermedi, sonraki modele geçiliyor... ({type(exc).__name__})", file=sys.stderr)

    raise RuntimeError(f"Tüm modeller denendi fakat yanıt alınamadı. Son hata: {last_err}")


# --- 4. LangGraph İş Akışı (StateGraph) ---

def create_summarizer_graph(scrape_tool):
    """LangGraph StateGraph iş akışını oluşturur."""
    async def scrape_node(state: PipelineState) -> PipelineState:
        url = state["url"]
        durations = state.get("durations", {})
        content_stats = state.get("content_stats", {})

        scrape_start = time.time()
        try:
            scrape_result = await scrape_tool.ainvoke({"url": url})
            raw_text = scrape_result.content if hasattr(scrape_result, "content") else str(scrape_result)
            clean_md = extract_clean_markdown(raw_text)
        except Exception as exc:
            return {
                "raw_content": "",
                "error": f"Scraping hatası: {str(exc)}",
                "success": False,
            }

        durations["scraping_seconds"] = round(time.time() - scrape_start, 3)
        content_stats["scraped_content_length"] = len(clean_md)

        return {
            "raw_content": clean_md,
            "durations": durations,
            "content_stats": content_stats,
        }

    async def summarize_node(state: PipelineState) -> PipelineState:
        if state.get("error"):
            return state

        raw_content = state.get("raw_content", "")
        if not raw_content or not raw_content.strip():
            return {
                "error": "Web sayfasından içerik alınamadı veya sayfa boş.",
                "success": False,
            }

        durations = state.get("durations", {})
        content_stats = state.get("content_stats", {})
        preferred_model = state.get("preferred_model", "gemini-3.7-flash")

        llm_start = time.time()
        try:
            summary_obj = await asyncio.to_thread(
                extract_structured_summary,
                raw_content,
                state.get("url", ""),
                preferred_model
            )
            summary_dict = summary_obj.model_dump()
            durations["llm_processing_seconds"] = round(time.time() - llm_start, 3)
            content_stats["summary_length"] = len(json.dumps(summary_dict, ensure_ascii=False))

            return {
                "summary": summary_dict,
                "durations": durations,
                "content_stats": content_stats,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            return {
                "error": f"LLM analiz hatası: {str(exc)}",
                "success": False,
            }

    workflow = StateGraph(PipelineState)
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("summarize", summarize_node)

    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()


# --- 5. Üst Düzey Pipeline Runner ---

async def run_pipeline(
    url: str,
    save_files: bool = True,
    model_name: str = "gemini-3.7-flash"
) -> Dict[str, Any]:
    """Tam analiz iş akışını çalıştırır."""
    validate_environment()
    total_start_time = time.time()

    benchmark_data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "durations": {},
        "content_stats": {},
        "success": False,
        "error": None,
        "summary": None,
    }

    try:
        tool_init_start = time.time()
        scrape_tool = await get_firecrawl_scrape_tool()
        benchmark_data["durations"]["tools_load_seconds"] = round(time.time() - tool_init_start, 3)

        graph = create_summarizer_graph(scrape_tool)

        initial_state: PipelineState = {
            "url": url,
            "preferred_model": model_name,
            "durations": benchmark_data["durations"],
            "content_stats": {},
            "success": False,
            "error": None,
        }

        final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=90.0
        )

        benchmark_data["durations"] = final_state.get("durations", benchmark_data["durations"])
        benchmark_data["content_stats"] = final_state.get("content_stats", {})
        benchmark_data["success"] = final_state.get("success", False)
        benchmark_data["error"] = final_state.get("error")
        benchmark_data["summary"] = final_state.get("summary")

    except asyncio.TimeoutError:
        benchmark_data["error"] = "Pipeline zaman aşımına uğradı (Timeout)."
        benchmark_data["success"] = False
    except Exception as e:
        benchmark_data["error"] = f"Pipeline çalışma hatası: {type(e).__name__} - {str(e)}"
        benchmark_data["success"] = False
    finally:
        total_end_time = time.time()
        benchmark_data["durations"]["total_seconds"] = round(total_end_time - total_start_time, 3)

    return benchmark_data
