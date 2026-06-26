# Web İçeriği Analiz ve Özetleme Agent'ı

**Firecrawl MCP + LangGraph + Gemini** ile herhangi bir URL'den metin kazıyan, yapılandırılmış özet (ana noktalar, istatistikler, bulgular) üreten ve performans metriklerini kaydeden AI agent.

**GitHub:** [yucel-gumus/Firecrawl_MCP-Gemini-LangGraph](https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph)

---

## Ne yapar?

1. **Firecrawl (MCP)** ile hedef sayfanın temiz metnini çıkarır
2. **Gemini** (LangGraph ReAct agent) içeriği analiz eder
3. Çıktıyı **JSON** olarak kaydeder (`web_summary.json`)
4. İsteğe bağlı **benchmark** raporu (`benchmark_results.json`, ham metin `raw_scraped_content.txt`)

Hem **CLI** (`main.py`) hem **web arayüzü** (`app.py` + FastAPI + Jinja2 templates) desteklenir.

---

## Mimari

```
URL ──► Firecrawl MCP (npx) ──► ham metin
                    │
                    ▼
         LangGraph create_react_agent
                    │
                    ▼
              Gemini 1.5 Flash
                    │
                    ▼
    JSON özet + benchmark zamanları
```

---

## Gereksinimler

- Python 3.8+
- **Node.js + npx** (Firecrawl MCP sunucusu için)
- `GOOGLE_API_KEY` veya `GEMINI_API_KEY` (`.env`)
- `FIRECRAWL_API_KEY` (Firecrawl kullanımı için)

```bash
pip install -r requirements.txt
```

---

## Komut satırı

```bash
python main.py "https://example.com/article"
python main.py "https://example.com" --benchmark
```

---

## Web arayüzü

```bash
uvicorn app:app --reload
# http://127.0.0.1:8000 — formdan URL girin
```

`app.py` aynı agent mantığını HTTP POST ile çalıştırır; sonuçları template üzerinde gösterir.

---

## Çıktı dosyaları

| Dosya | İçerik |
|-------|--------|
| `raw_scraped_content.txt` | Kazınan ham metin |
| `web_summary.json` | LLM yapılandırılmış özeti |
| `benchmark_results.json` | Scraping / LLM süreleri |

---

## Teknolojiler

| Bileşen | Kütüphane |
|---------|-----------|
| Agent | LangGraph, LangChain |
| LLM | `langchain_google_genai` |
| MCP | `langchain_mcp_adapters` |
| Web | FastAPI, Jinja2 |
| Scraping | Firecrawl via MCP |

---

## Sorun giderme

| Hata | Çözüm |
|------|--------|
| `npx` bulunamadı | Node.js LTS kurun |
| MCP bağlantı hatası | Firecrawl API key ve ağ erişimi |
| Gemini 429 | Rate limit — tekrar deneyin veya model kotası |

---

## Lisans

MIT veya repo ile belirtilen lisans.