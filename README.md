# Web İçeriği Analiz ve Özetleme Agent'ı

Bu proje, LangGraph, Gemini ve Firecrawl MCP (Model Context Protocol) teknolojilerini kullanarak web sayfalarından içerik çıkaran, analiz eden ve özetleyen bir AI agent'ıdır. Agent, belirtilen bir URL'deki metni kazır, ana fikirleri, istatistikleri ve önemli bulguları çıkarır ve bunları yapılandırılmış bir JSON formatında sunar. Ayrıca, işlem performansını ölçmek için dahili benchmark özelliklerine sahiptir.

## 🚀 Temel Özellikler

- **Akıllı İçerik Çıkarımı:** Web sayfalarındaki reklam, menü gibi gereksiz içerikleri atlayarak sadece ana metni hedefler.
- **Yapılandırılmış Veri Çıktısı:** Analiz edilen içerikten **ana noktaları**, **istatistikleri** ve **temel bulguları** ayırarak JSON formatında sunar.
- **Performans Ölçümü (Benchmark):** Agent'ın çalışma süresi, veri kazıma (scraping) hızı, LLM işlem süresi gibi kritik metrikleri ölçer ve raporlar.
- **Esnek Çalıştırma:** Komut satırından dinamik olarak herhangi bir web sayfasının URL'sini alabilir.

## 🛠️ Kullanılan Teknolojiler

- **Framework:** LangGraph
- **LLM:** Google Gemini 1.5 Flash
- **Veri Kazıma (Scraping):** Firecrawl (MCP üzerinden)
- **Dil:** Python 3.8+

## ⚙️ Kurulum

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### 1. Proje Dosyalarını İndirin

Bu repoyu klonlayın veya dosyaları ZIP olarak indirin.

### 2. Sanal Ortam (Virtual Environment) Oluşturun

Proje bağımlılıklarını sisteminizden izole etmek için bir sanal ortam oluşturmanız önerilir.

```bash
# Sanal ortamı oluştur
python3 -m venv venv

# Sanal ortamı aktive et (Linux/Mac)
source venv/bin/activate

# Sanal ortamı aktive et (Windows)
# venv\Scripts\activate
```

### 3. Bağımlılıkları Yükleyin

Gerekli Python kütüphanelerini `requirements.txt` dosyasını kullanarak yükleyin.

```bash
pip install -r requirements.txt
```
Ayrıca, Firecrawl MCP'nin çalışması için sisteminizde **Node.js** ve **npx**'in yüklü olması gerekmektedir.

### 4. API Anahtarlarını Ayarlayın

Proje kök dizininde `.env` adında bir dosya oluşturun ve içine Google Gemini ve Firecrawl API anahtarlarınızı ekleyin.

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
FIRECRAWL_API_KEY="YOUR_FIRECRAWL_API_KEY"
```

- **Gemini API Anahtarı:** [Google AI Studio](https://makersuite.google.com/app/apikey) üzerinden ücretsiz olarak alabilirsiniz.
- **Firecrawl API Anahtarı:** [Firecrawl.dev](https://firecrawl.dev) adresinden ücretsiz bir anahtar edinebilirsiniz.

## ⚡️ Çalıştırma

Agent'ı çalıştırmak için terminali kullanın. `app.py` script'ine argüman olarak analiz etmek istediğiniz web sayfasının tam URL'sini verin.

### Standart Çalıştırma

```bash
python app.py "https://ornek-web-sitesi.com/makale"
```

### Benchmark Raporu ile Çalıştırma

İşlem sonunda detaylı bir performans raporu görmek için `--benchmark` veya `-b` bayrağını ekleyin.

```bash
python app.py "https://ornek-web-sitesi.com/makale" --benchmark
```

## 📊 Çıktılar

Script başarıyla tamamlandığında proje dizininde aşağıdaki dosyalar oluşturulur:

1.  **`web_summary.json`**:
    Agent tarafından analiz edilen ve yapılandırılmış özet. İçeriği:
    - `main_points`: Makalenin ana fikirleri.
    - `statistics`: Metinde geçen somut veriler.
    - `key_findings`: Makalenin ulaştığı sonuçlar.

2.  **`raw_scraped_content.txt`**:
    Firecrawl tarafından kazınan ve LLM'e gönderilen ham metin içeriği. Bu dosya, agent'ın analizinin doğruluğunu kontrol etmek ve LLM'in hangi veri üzerinden çalıştığını görmek için kullanışlıdır.

3.  **`benchmark_results.json`**:
    Her çalıştırma için toplanan performans metriklerini içeren bir JSON dosyası. Bu dosya, zamanla agent'ın performansını izlemek için kullanılır. Örnek metrikler:
    - `total_seconds`: Toplam çalışma süresi.
    - `scraping_seconds`: Veri kazıma işleminin süresi.
    - `llm_processing_seconds`: Gemini modelinin analizi tamamlama süresi.
    - `scraped_content_length`: Kazınan metnin karakter sayısı.

## 🔧 Sorun Giderme

- **`npx not found` hatası:** Sisteminizde Node.js'in kurulu olduğundan ve `npx` komutunun PATH'e eklendiğinden emin olun.
- **`firecrawl_scrape aracı bulunamadı` hatası:** `npx firecrawl-mcp` komutunun düzgün çalışıp çalışmadığını ve `FIRECRAWL_API_KEY`'inizin doğru olduğunu kontrol edin.
- **API Anahtar Hataları:** `.env` dosyasının doğru formatta olduğundan ve API anahtarlarınızın geçerli olduğundan emin olun.