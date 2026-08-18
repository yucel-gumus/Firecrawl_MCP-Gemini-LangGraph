# 🕷️ Firecrawl MCP & LangGraph AI Web Scraper & Summarizer

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflow-FF9900?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Firecrawl](https://img.shields.io/badge/Firecrawl-MCP_Scraper-FF4F00?style=for-the-badge)](https://firecrawl.dev/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-Structured_Summary-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Portfolio](https://img.shields.io/badge/Portfolio-yucelgumus.dev-2563EB?style=for-the-badge&logo=google-chrome&logoColor=white)](https://www.yucelgumus.dev/)

> **Model Context Protocol (MCP)** ve **Firecrawl** entegrasyonu ile web sayfalarını temiz Markdown formatında kazıyan, **LangGraph** tabanlı akıllı ajan döngüsüyle içeriği analiz edip yapılandırılmış JSON özetleri ve anahtar çıkarımlar üreten Agentic AI platformu.

---

## 🌟 Öne Çıkan Özellikler

- 🕸️ **Firecrawl MCP Entegrasyonu:** JavaScript ile dinamik yüklenen modern web sitelerini dahi DOM gürültüsünden arındırarak saf Markdown ve metin olarak kazıma.
- 🔄 **LangGraph Döngüsel Ajan Mimarisi:** Kazıma (Scrape) ➔ Temizleme (Clean) ➔ Analiz (Analyze) ➔ Yapılandırılmış Çıkarım (Structured Extraction) aşamalarından oluşan otonom iş akışı.
- 📊 **Yapılandırılmış JSON & Rapor Üretimi:** Web sayfasının ana fikrini, temel istatistiklerini, hedef kitlesini ve eylem maddelerini standart JSON formatında dışa aktarma (`web_summary.json`).
- 🖥️ **Çift Kullanım Modu (CLI & Web UI):** İster terminal üzerinden hızlı komut satırı aracı (`main.py`), ister FastAPI & Jinja2 tabanlı modern web arayüzü (`app.py`).
- ⚡ **Benchmark & Performans İzleme:** Kazıma sürelerini ve token verimliliğini ölçen yerleşik kıyaslama sistemi (`benchmark_results.json`).

---

## 🏗️ Mimari & LangGraph Ajan Akışı

```mermaid
graph TD
    InputURL[Hedef URL Girdisi] --> FirecrawlMCP[Firecrawl MCP Client]
    FirecrawlMCP -->|Ham / Temiz Markdown| StateGraph[LangGraph State Workflow]
    StateGraph --> NodeParse[1. İçerik ve Başlık Analizi]
    NodeParse --> NodeSummarize[2. Gemini 1.5 Özümseme]
    NodeSummarize --> NodeExtract[3. JSON Şema Çıkarımı]
    NodeExtract --> OutputJSON[(web_summary.json)]
    NodeExtract --> WebUI[Web Arayüzü & CLI Görüntüleyici]
```

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- **Python**: 3.10 veya üstü
- **Firecrawl API Key** & **Google Gemini API Key**

### Kurulum

```bash
git clone https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph.git
cd Firecrawl_MCP-Gemini-LangGraph

# Sanal ortam
python3 -m venv .venv
source .venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt
```

### Ortam Değişkenleri (`.env`)

```env
FIRECRAWL_API_KEY=your_firecrawl_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Çalıştırma

**Komut Satırı (CLI) Modu:**
```bash
python main.py --url https://example.com
```

**Web Arayüzü (FastAPI) Modu:**
```bash
python app.py
```
Arayüze `http://localhost:8000` adresinden erişebilirsiniz.

---

## 📂 Proje Dizin Yapısı

```
Firecrawl_MCP-Gemini-LangGraph/
├── requirements.txt
├── app.py                          # FastAPI Web sunucusu
├── main.py                         # CLI ve LangGraph motoru
├── benchmark_results.json          # Performans analiz verileri
├── web_summary.json                # Üretilen son yapısal özet
└── templates/
    └── index.html                  # Web arayüzü şablonu
```

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

## 👨‍💻 Geliştirici & İletişim

**Yücel Gümüş** - Full Stack Developer

- 🌐 **Web Sitesi / Portfolyo:** [yucelgumus.dev](https://www.yucelgumus.dev/)
- 💼 **LinkedIn:** [linkedin.com/in/yucel-gumus](https://www.linkedin.com/in/yucel-gumus/)
- 🐙 **GitHub:** [@yucel-gumus](https://github.com/yucel-gumus)

<p align="left">
  <a href="https://www.yucelgumus.dev/" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/Developed%20by-Yücel%20Gümüş-blue?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Yücel Gümüş Portfolio" />
  </a>
</p>