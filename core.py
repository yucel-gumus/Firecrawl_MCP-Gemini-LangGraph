"""
Core Module: Firecrawl Python SDK + Google Gemini + LangGraph State Pipeline
Gelişmiş & Kapsamlı AI İstihbarat ve Web Analiz Motoru.
Web sayfasını derinlemesine analiz eder; yönetici özeti, detaylı konu kırılımları,
bağlamsal istatistikler, aksiyon maddeleri ve bahsedilen teknolojileri çıkarır.

NOT: MCP/npx yerine Firecrawl Python SDK kullanılmaktadır.
     Node.js/npx gerektirmez — Cloud Run uyumlu.
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from firecrawl import FirecrawlApp
from langgraph.graph import StateGraph, START, END
from config import DEFAULT_MODEL, FALLBACK_MODELS, LLM_TIMEOUT_MS, PIPELINE_TIMEOUT_S

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


# --- 2. Yardımcı Fonksiyonlar ---

def validate_environment() -> None:
    """Gerekli API anahtarlarını doğrular. Uygulama başlangıcında bir kez çağrılır."""
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Hata: GEMINI_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")
    if not os.getenv("FIRECRAWL_API_KEY"):
        raise ValueError("Hata: FIRECRAWL_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")


# --- 3. Singleton API Client'ları ---
# Her istek için yeni client oluşturmak yerine modül seviyesinde bir kez oluşturulur.

_firecrawl_client: Optional[FirecrawlApp] = None
_gemini_client: Optional[genai.Client] = None


def get_firecrawl_client() -> FirecrawlApp:
    """Firecrawl SDK client'ını singleton olarak döndürür."""
    global _firecrawl_client
    if _firecrawl_client is None:
        _firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    return _firecrawl_client


def get_gemini_client() -> genai.Client:
    """Gemini API client'ını singleton olarak döndürür."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS)
        )
    return _gemini_client


# --- 4. Firecrawl Python SDK ile Kazıma ---

async def scrape_url_with_sdk(url: str) -> str:
    """
    Firecrawl Python SDK kullanarak URL'yi kazır ve Markdown döndürür.
    Node.js / npx gerektirmez.
    """
    def _scrape() -> str:
        client = get_firecrawl_client()
        result = client.scrape_url(url, formats=["markdown"])
        # SDK ScrapeResponse nesnesi — markdown alanını al
        if hasattr(result, "markdown") and result.markdown:
            return result.markdown
        # Fallback: dict ise
        if isinstance(result, dict):
            return result.get("markdown") or result.get("content") or ""
        return str(result)

    # Bloklayan I/O'yu thread pool'da çalıştır
    return await asyncio.to_thread(_scrape)


# --- 5. LLM: Google Gemini ile Yapılandırılmış Analiz ---

def extract_structured_summary(
    content: str,
    url: str,
    preferred_model: str = DEFAULT_MODEL
) -> WebSummary:
    """
    Google Gemini Chat API ile derinlemesine ve kapsamlı analiz yapar.
    Birincil modelde hata olursa yedek modellere geçer.
    """
    client = get_gemini_client()

    prompt = f"""
Sen dünya standartlarında kıdemli bir araştırma analisti, veri bilimci ve stratejistsin.
Sana verilen web sayfası içeriğini derinlemesine, ayrıntılı ve hiçbir kritik detayı atlamadan analiz edeceksin.

KAYNAK URL: {url}
---
KAZINAN WEB İÇERİĞİ:
{content[:2000000]}
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

    # Model isimleri config.py'den gelir — bu dosyada model adı YAZILMAZ
    models_to_try = [preferred_model] if preferred_model else []
    for m in FALLBACK_MODELS:
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


# --- 6. LangGraph İş Akışı (StateGraph) ---

def create_summarizer_graph():
    """LangGraph StateGraph iş akışını oluşturur."""

    async def scrape_node(state: PipelineState) -> PipelineState:
        url = state["url"]
        durations = state.get("durations", {})
        content_stats = state.get("content_stats", {})

        scrape_start = time.time()
        try:
            clean_md = await scrape_url_with_sdk(url)
        except Exception as exc:
            return {
                "raw_content": "",
                "error": f"Scraping hatası: {str(exc)}",
                "success": False,
            }

        durations["scraping_seconds"] = round(time.time() - scrape_start, 3)

        # Scrape sonrası boşluk kontrolü — boş içerik erken yakalanır
        if not clean_md or not clean_md.strip():
            return {
                "raw_content": "",
                "error": "Sayfa kazıma başarılı ancak içerik boş döndü. Sayfa dinamik (JS-render) olabilir.",
                "success": False,
            }

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
        preferred_model = state.get("preferred_model", DEFAULT_MODEL)

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


# Global olarak bir kez derlenen LangGraph iş akışı
_compiled_graph = create_summarizer_graph()

# --- 7. Üst Düzey Pipeline Runner ---

async def run_pipeline(
    url: str,
    model_name: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """Tam analiz iş akışını çalıştırır."""
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
        initial_state: PipelineState = {
            "url": url,
            "preferred_model": model_name,
            "durations": benchmark_data["durations"],
            "content_stats": {},
            "success": False,
            "error": None,
        }

        final_state = await asyncio.wait_for(
            _compiled_graph.ainvoke(initial_state),
            timeout=PIPELINE_TIMEOUT_S
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
