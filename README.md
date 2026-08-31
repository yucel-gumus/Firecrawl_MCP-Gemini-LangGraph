# 🕷️ Firecrawl MCP + Gemini 3.7 Flash + LangGraph Web Intelligence Agent

**Firecrawl MCP**, **Google Gemini 3.7 Flash** ve **LangGraph StateGraph** mimarisini bir araya getiren yeni nesil yapay zeka destekli web istihbarat, içerik kazıma ve derinlemesine analiz platformu.

Bu proje; web sayfalarını karmaşık HTML/DOM etiketlerinden ve reklam gürültüsünden arındırarak saf Markdown formatında çeker, ardından **LangGraph** durumu üzerinde **Google Gemini 3.7 Flash** ile yapılandırılmış kurumsal analiz raporlarına (Yönetici Özeti, Tematik Konular, İstatistik Tablosu, Stratejik Bulgular, Eylem Planı, Tespit Edilen Şirket/Teknoloji Matrisi) dönüştürür.

---

## 🌟 Temel Özellikler

- **⚡ Tek Adımlı Akıllı Kazıma (Single-Pass Scraping):** Firecrawl MCP stdio protokolü ile entegre edilerek çift istek (double scraping) maliyeti ve gecikmesi ortadan kaldırılmıştır.
- **🧠 Google Gemini 3.7 Flash & Akıllı Yedekleme (Fallback):** Birincil model olarak en güncel `gemini-3.7-flash` kullanılır. 10 saniyelik deadline süresiyle olası 503/gecikme durumlarında sistem duraksamadan anında optimize edilmiş yedek modellere (`gemini-flash-lite-latest` / `gemini-3.5-flash-lite`) geçer.
- **🔄 LangGraph StateGraph Pipeline:** `scrape_node` ve `summarize_node` düğümleri arasında Pydantic şeması ile tip güvenli ve izlenebilir durum yönetimi.
- **📊 Kapsamlı İstihbarat Şeması:**
  - **Yönetici Özeti (Executive Summary):** 2-3 paragraflık derinlemesine genel bakış.
  - **Detaylı Konu Kırılımları:** Sayfadaki her ana temanın detaylı açıklaması ve alt maddeleri.
  - **Doğrulanmış İstatistik ve Veri Tablosu:** Metrik, Sayısal Değer ve Bağlam sütunları.
  - **Stratejik Bulgular ve Aksiyon Planı:** Somut çıkarımlar ve uygulanabilir öneriler.
  - **Varlık & Teknoloji Matrisi:** Bahsedilen modeller, kurumlar, protokoller ve kişiler.
- **🗂️ Sekmeli Çalışma Alanı (Tabbed Workspace Web UI):** FastAPI & Jinja2 tabanlı, gereksiz süslemelerden arındırılmış, modern ve odaklı araştırma arayüzü.
- **📄 Vektörel Kurumsal PDF Raporu:** `html2pdf.js` ile tek tıkla resmi, antetli ve temiz A4 formatında PDF rapor indirme imkânı.
- **💻 CLI & Benchmark Desteği:** Komut satırından `--benchmark` bayrağı ile anlık süre dağılımı (MCP, Kazıma, LLM süresi) ve içerik boyutu metrikleri.

---

## 🏗️ Mimari Şema

```
                           ┌────────────────────────┐
                           │      Hedef Web URL     │
                           └───────────┬────────────┘
                                       │
                                       ▼
                     ┌────────────────────────────────────┐
                     │         LangGraph StateGraph       │
                     └─────────────────┬──────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     ┌─────────────────────┐                       ┌─────────────────────┐
     │     Scrape Node     │                       │   Summarize Node    │
     │  (Firecrawl MCP)    │                       │  (Gemini 3.7 Flash) │
     │  Saf Markdown Çekimi│ ────── State ───────► │  Yapılandırılmış    │
     │  & JSON Temizleme   │                       │  Pydantic Çıkarımı  │
     └─────────────────────┘                       └──────────┬──────────┘
                                                              │
                                       ┌──────────────────────┴──────────────────────┐
                                       ▼                                             ▼
                            ┌─────────────────────┐                       ┌─────────────────────┐
                            │   Modern Web UI     │                       │    CLI & Benchmark  │
                            │  Sekmeli Çalışma    │                       │   (main.py terminal │
                            │  Alanı & A4 PDF     │                       │    raporlama)       │
                            └─────────────────────┘                       └─────────────────────┘
```

---

## 🔑 Gereksinimler & API Anahtarları

Projeyi çalıştırmak için aşağıdaki iki API anahtarı gereklidir:

1. **Google Gemini API Key:** [Google AI Studio](https://aistudio.google.com/) üzerinden ücretsiz temin edilebilir.
2. **Firecrawl API Key:** [Firecrawl.dev](https://www.firecrawl.dev/) üzerinden ücretsiz temin edilebilir.
3. **Node.js & npx:** Firecrawl MCP aracını arka planda çalıştırmak için sisteminizde Node.js (v18+) kurulu olmalıdır.

---

## 🚀 Kurulum ve Başlangıç

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/yucel-gumus/Firecrawl_MCP-Gemini-LangGraph.git
cd Firecrawl_MCP-Gemini-LangGraph
```

### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
# Sanal ortam oluşturma (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# veya: .venv\Scripts\activate  # Windows

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Tanımlayın
`.env.example` dosyasını kopyalayarak `.env` oluşturun ve API anahtarlarınızı ekleyin:
```bash
cp .env.example .env
```
`.env` dosya içeriği:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

---

## 🖥️ Kullanım Yöntemleri

### A) Web Arayüzünü Başlatma (FastAPI)
```bash
python app.py
```
Tarayıcınızda `http://127.0.0.1:8000` adresini açın. Analiz etmek istediğiniz URL'yi girip **"Analiz Başlat"** butonuna basarak sekmeli analiz paneline ve PDF raporunuza erişin.

---

### B) Komut Satırından (CLI) Çalıştırma
Herhangi bir URL'yi doğrudan terminal üzerinden analiz etmek için:
```bash
# Temel çalıştırma
python main.py https://openai.com/tr-TR/index/openai-api/

# Detaylı benchmark ve süre dağılımı ile çalıştırma
python main.py https://openai.com/tr-TR/index/openai-api/ --benchmark

# Özel bir model belirterek çalıştırma
python main.py https://openai.com/tr-TR/index/openai-api/ --model gemini-3.7-flash
```

---

## 📁 Proje Dosya Yapısı

```
Firecrawl_MCP-Gemini-LangGraph/
├── app.py                   # FastAPI web sunucusu ve API uç noktaları
├── core.py                  # LangGraph StateGraph, MCP ve Gemini analiz çekirdeği
├── main.py                  # CLI runner ve benchmark terminal raporlayıcısı
├── requirements.txt         # Sadeleştirilmiş ve test edilmiş bağımlılıklar listesi
├── templates/
│   └── index.html           # Sekmeli araştırma paneli ve kurumsal A4 PDF şablonu
├── .env.example             # Çevre değişkenleri şablonu
├── .gitignore               # Hassas verileri ve çıktıları koruyan git kuralları
└── README.md                # Kapsamlı proje dokümantasyonu
```

---

## 🛡️ Güvenlik

* `.env` dosyası ve tüm API anahtarları `.gitignore` kapsamındadır ve depoya dahil edilmez.
* Girdi URL'leri ve Pydantic şema doğrulamaları tip güvenliği standartlarına uygundur.

---

## 👨‍💻 Geliştirici

**Yücel Gümüş**  
* Website: [yucelgumus.dev](https://www.yucelgumus.dev/)  
* GitHub: [@yucel-gumus](https://github.com/yucel-gumus)