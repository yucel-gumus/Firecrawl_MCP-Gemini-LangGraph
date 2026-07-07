# 🕷️ Web Analiz & Özetleme Ajanı (LangGraph & Firecrawl MCP Agent)

Bu proje; Model Context Protocol (MCP) kullanarak harici web kazıma (scraping) servislerine bağlanan, **LangGraph** tabanlı bir akıllı ReAct (Reasoning + Acting) döngüsüyle hedef web sayfalarının temiz metin içeriklerini çıkartıp analiz eden ve yapılandırılmış özetler (JSON) üreten **Python & FastAPI** tabanlı bir Agentic AI uygulamasıdır.

Uygulama, hem komut satırı (CLI) hem de kullanıcı dostu bir web arayüzü (FastAPI + Jinja2) üzerinden çalıştırılabilir.

---

## 🌟 Öne Çıkan Özellikler

* 🤖 **LangGraph ReAct Ajan Mimarisi:** Karar ve eylem döngülerini (ReAct) yönetmek için LangGraph (`StateGraph`) kullanılmıştır. Ajan, hedeflenen URL'i analiz etmek için ne zaman ve nasıl arama yapması gerektiğine kendisi karar verir.
* 🔌 **Model Context Protocol (MCP) Entegrasyonu:** `langchain-mcp-adapters` aracılığıyla, standartlaştırılmış MCP arayüzü üzerinden **npx Firecrawl MCP** sunucusuna bağlanır. Model, web kazıma işlemini yerel/harici bir araç çağrısı (Tool Calling) olarak yürütür.
* 🕸️ **Firecrawl ile Temiz Metin Kazıma:** Hedef web sayfasının HTML kodları, reklamları ve CSS dosyaları elenerek temizlenmiş Markdown/düz metin formatında okunur.
* 📊 **Zamanlı Benchmark Ölçümü:** Web kazıma ve yapay zeka modelinin (Gemini) yanıt sürelerini ölçüp karşılaştırarak `benchmark_results.json` dosyasına performans analizlerini kaydeder.
* 💻 **Çift Arayüz Desteği:**
  * **CLI:** `python main.py <url>` komutuyla hızlı analiz.
  * **Web UI:** FastAPI ve Jinja2 şablonları (`app.py`) ile görsel sonuç paneli.

---

## 🏗️ Mimarî İş Akışı (LangGraph Graph)

```
[ Arama Talebi (URL) ] 
          │
          ▼
[ LangGraph StateGraph (Start) ]
          │
          ▼
[ Agent Decision Node ] ──► (Gerektiğinde Firecrawl MCP Aracını Tetikler)
          │
          ▼
[ Tool Node (Firecrawl) ] ──► (Ham HTML -> Temiz Markdown Metni Dönüştürür)
          │
          ▼
[ Agent Analysis Node ] ──► (İçeriği Okur, Ana Bulguları & İstatistikleri Çıkarır)
          │
          ▼
[ JSON Output Generation ] ──► (Özeti `web_summary.json` Olarak Yazar)
```

---

## 🛠️ Teknoloji Stack

* **Ajan & LLM Framework:** LangGraph, LangChain, `langchain-google-genai`.
* **Protokol:** MCP (Model Context Protocol) via `mcp` & `langchain-mcp-adapters`.
* **Web Framework:** FastAPI, Uvicorn, Jinja2 Templates.
* **Veri Yönetimi:** Pydantic (veri şeması doğrulama), `orjson`.

---

## 📂 Proje Klasör Yapısı

```
Firecrawl_MCP-Gemini-LangGraph/
├── templates/
│   └── index.html            # FastAPI web arayüzü Jinja2 şablonu
├── app.py                    # Web sunucu arayüzü (FastAPI)
├── main.py                   # Ajan mantığının kurulduğu ve CLI giriş noktası
├── requirements.txt          # LangGraph, LangChain ve MCP bağımlılıkları
├── web_summary.json          # En son üretilen yapılandırılmış JSON özeti
└── benchmark_results.json    # Kazıma ve analiz işlem süreleri performans raporu
```

---

## 🚀 Kurulum ve Yerel Çalıştırma

### 1. Bağımlılıkları Yükleyin
```bash
git clone https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph.git
cd Firecrawl_MCP-Gemini-LangGraph
pip install -r requirements.txt
```

### 2. Ortam Değişkenleri (`.env`)
Kök dizinde `.env` dosyası oluşturun ve anahtarlarınızı girin:

```env
# Google Gemini API Anahtarı
GOOGLE_API_KEY=your_gemini_api_key

# Firecrawl API Anahtarı
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### 3. Komut Satırı Üzerinden Çalıştırma (CLI)
```bash
# Sadece analiz yapma
python main.py "https://example.com/article"

# Performans sürelerini ölçerek benchmark modunda çalıştırma
python main.py "https://example.com/article" --benchmark
```

### 4. Web Arayüzünü Başlatma
```bash
uvicorn app:app --reload
```
Uygulama `http://127.0.0.1:8000` adresinde başlayacaktır.

---

## 🔗 Bağlantılar
* **GitHub Repository:** [https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph](https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph)
* **Geliştirici LinkedIn:** [https://linkedin.com/in/yucel-gumus](https://linkedin.com/in/yucel-gumus)