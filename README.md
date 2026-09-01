# 🕷️ Firecrawl + Gemini 3.7 Flash + LangGraph Web Intelligence Agent

**Firecrawl Python SDK**, **Google Gemini 3.7 Flash** ve **LangGraph StateGraph** mimarisini bir araya getiren yeni nesil yapay zeka destekli web istihbarat, içerik kazıma ve derinlemesine analiz platformu.

> 🚀 **Canlı Uygulama / Demo:** [https://firecrawl-mcp.web.app](https://firecrawl-mcp.web.app)

Bu proje; web sayfalarını karmaşık HTML/DOM etiketlerinden ve reklam gürültüsünden arındırarak saf Markdown formatında çeker, ardından **LangGraph** durumu üzerinde **Google Gemini 3.7 Flash** ile yapılandırılmış kurumsal analiz raporlarına (Yönetici Özeti, Tematik Konular, İstatistik Tablosu, Stratejik Bulgular, Eylem Planı, Tespit Edilen Şirket/Teknoloji Matrisi) dönüştürür.

---

## 🌟 Temel Özellikler

- **⚡ Tek Adımlı Akıllı Kazıma (Single-Pass Scraping):** Firecrawl Python SDK ile entegre edilerek Node.js/npx bağımlılığı tamamen ortadan kaldırılmıştır. Saf Python mimarisi.
- **🧠 Google Gemini 3.7 Flash & Akıllı Yedekleme (Fallback):** Birincil model olarak `gemini-3.7-flash` kullanılır. Hata durumunda `gemini-3.5-flash` ve `gemini-3.5-flash-lite` yedek modellerine otomatik geçiş yapılır.
- **🔄 LangGraph StateGraph Pipeline:** `scrape_node` ve `summarize_node` düğümleri arasında Pydantic şeması ile tip güvenli ve izlenebilir durum yönetimi.
- **📊 Kapsamlı İstihbarat Şeması:**
  - **Yönetici Özeti (Executive Summary):** 2-3 paragraflık derinlemesine genel bakış.
  - **Detaylı Konu Kırılımları:** Sayfadaki her ana temanın detaylı açıklaması ve alt maddeleri.
  - **Doğrulanmış İstatistik ve Veri Tablosu:** Metrik, Sayısal Değer ve Bağlam sütunları.
  - **Stratejik Bulgular ve Aksiyon Planı:** Somut çıkarımlar ve uygulanabilir öneriler.
  - **Varlık & Teknoloji Matrisi:** Bahsedilen modeller, kurumlar, protokoller ve kişiler.
- **🗂️ Sekmeli Çalışma Alanı (Tabbed Workspace Web UI):** FastAPI & Jinja2 tabanlı modern araştırma arayüzü.
- **📄 Tarayıcı Native PDF Raporu:** CSS overflow ve height optimizasyonları ile sayfa kesintisi yaşamadan kusursuz A4 PDF indirme.
- **☁️ Cloud Run & Firebase Hosting:** `Gunicorn` entegrasyonu ile production-ready. Firebase Hosting (Rewrite) desteğiyle şık URL, $0 idle cost (`min-instances: 0`).
- **💻 CLI & Benchmark Desteği:** `--benchmark` bayrağı ile süre dağılımı ve içerik metrikleri.

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
     │  (Firecrawl Python  │                       │  (Gemini 3.7 Flash) │
     │   SDK — npx yok!)   │ ────── State ───────► │  Yapılandırılmış    │
     │  Saf Markdown Çekimi│                       │  Pydantic Çıkarımı  │
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

> **Not:** Node.js veya npx kurulumu **gerekmemektedir.** Firecrawl artık Python SDK üzerinden çalışmaktadır.

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

## ☁️ Google Cloud Run & Firebase Hosting (Production)

Proje, production için **Gunicorn** ve **UvicornWorker** destekli Dockerfile barındırır.
Mevcut yapılandırma ile Cloud Run uygulamanız `min-instances: 0` olarak ayağa kalkar, böylece trafik yokken 0$ maliyet yaratır.

### Deploy İşlemi

`.env` şifrelerinizi sızdırmamak ve güvenli deployment yapmak için `deploy.sh` dosyasını kullanın:

```bash
# 1. Projeyi Güvenle Deploy Edin (Otomatik Cloud Run Deploy)
chmod +x deploy.sh
./deploy.sh

# 2. Firebase Hosting'e Bağlayın (Temiz URL için)
npx -y firebase-tools@latest deploy --only hosting
```

> **Nasıl Çalışır?** `firebase.json` içerisindeki `rewrites` kuralı, Firebase Hosting'e gelen trafiği bir köprü (proxy) mantığıyla arka plandaki Cloud Run sunucusuna iletir. Böylece `firecrawl-mcp.web.app` gibi çok daha profesyonel bir canlı URL elde edilir.

---

## 📁 Proje Dosya Yapısı

```
Firecrawl_MCP-Gemini-LangGraph/
├── app.py                   # FastAPI web sunucusu ve API uç noktaları
├── core.py                  # LangGraph StateGraph, Firecrawl SDK ve Gemini analiz çekirdeği
├── main.py                  # CLI runner ve benchmark terminal raporlayıcısı
├── requirements.txt         # Python bağımlılıkları (Node.js yok)
├── Dockerfile               # Cloud Run hazır container tanımı
├── .dockerignore            # Docker build optimizasyonu
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
* Cloud Run deploy'da API anahtarları `--set-env-vars` veya Secret Manager üzerinden yönetilmelidir.

---

## 👨‍💻 Geliştirici

**Yücel Gümüş**  
* Website: [yucelgumus.dev](https://www.yucelgumus.dev/)  
* GitHub: [@yucel-gumus](https://github.com/yucel-gumus)