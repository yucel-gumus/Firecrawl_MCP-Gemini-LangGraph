"""
Bu script, LangGraph, Gemini ve Firecrawl MCP kullanarak belirtilen bir web sayfasını özetleyen
bir AI agent oluşturur. Agent, Gemini modelini kullanarak web sayfasının içeriğini
analiz eder ve ana noktaları, istatistikleri ve önemli bulguları JSON formatında çıkarır.
Ayrıca, işlemin her adımının performansını ölçmek için kapsamlı benchmark (performans ölçümü)
özellikleri içerir.

Bu script, bir junior yazılımcının modern AI agent'larının nasıl çalıştığını anlaması için
detaylı açıklamalar ve yorum satırları ile donatılmıştır.

Ana İş Akışı:
1.  **Kurulum ve Kontroller:** Gerekli ortam değişkenleri (API anahtarları) ve bağımlılıklar (npx) kontrol edilir.
2.  **Argüman Ayrıştırma:** Kullanıcının komut satırından bir URL girmesi ve benchmark raporu isteyip istemediği alınır.
3.  **LLM ve Araçların Hazırlanması:** Gemini LLM (beyin) ve Firecrawl (veri toplama aracı) başlatılır.
4.  **Ham Veri Toplama:** Firecrawl aracı ile hedef URL'den web sayfasının metin içeriği kazınır.
5.  **Agent'ın Çalıştırılması:** LLM, verilen talimatlar (prompt) ve kazınan metin ile bir ReAct (Düşün ve Harekete Geç) döngüsüne girer.
6.  **Analiz ve Çıktı Üretme:** LLM, metni analiz eder ve istenen JSON formatında bir özet oluşturur.
7.  **Sonuçların Kaydedilmesi:** Hem ham veri, hem de LLM'in ürettiği özet ayrı dosyalara kaydedilir.
8.  **Performans Raporlama:** Tüm sürecin ne kadar sürdüğü ölçülür ve bir benchmark dosyasına kaydedilir.
"""

# --- 1. Gerekli Kütüphanelerin ve Modüllerin Yüklenmesi ---
# Bu bölümde, script'in çalışması için gereken tüm dış ve standart kütüphaneler içe aktarılır.

import os  # İşletim sistemiyle ilgili işlemler için (örn: environment değişkenlerini okuma).
import asyncio  # Asenkron (aynı anda birden çok iş yapabilen) kodları çalıştırmak için.
import json  # JSON verilerini işlemek (okumak/yazmak) için.
import argparse  # Komut satırından argüman (örn: URL) almayı kolaylaştırmak için.
import time  # Zamanla ilgili işlemler, özellikle performans ölçümleri için.
from datetime import datetime  # Tarih ve saat bilgisiyle çalışmak için.
from dotenv import load_dotenv  # .env dosyasından ortam değişkenlerini yüklemek için.
import subprocess  # Harici komutları (örn: npx) çalıştırmak için.

# LangChain kütüphaneleri: AI uygulamaları oluşturmayı sağlayan ana çatıdır.
from langchain_google_genai import ChatGoogleGenerativeAI  # Google'ın Gemini modelini kullanmak için.
from langchain_mcp_adapters.tools import load_mcp_tools  # MCP protokolü üzerinden araçları yüklemek için.
from langchain_core.messages import HumanMessage  # Agent'a gönderilecek insan mesajlarını formatlamak için.
from langgraph.prebuilt import create_react_agent  # ReAct (Reason+Act) tipi bir agent oluşturmak için.


# --- 2. Kurulum ve Ön Kontroller ---
# Bu bölümde, script'in çalışması için gerekli olan dış bağımlılıkların
# ve konfigürasyonların (API anahtarları) mevcut olup olmadığı kontrol edilir.

# Firecrawl'un çalışması için gerekli olan npx'in sistemde kurulu olup olmadığını kontrol et.
try:
    # `npx --version` komutunu çalıştırarak npx'in varlığını test ediyoruz.
    # `check=True` komut başarısız olursa bir hata fırlatmasını sağlar.
    # `capture_output=True` komutun çıktısını gizler.
    subprocess.run(["npx", "--version"], check=True, capture_output=True)
except (subprocess.SubprocessError, FileNotFoundError):
    # Eğer komut çalışmazsa veya npx bulunamazsa, kullanıcıyı uyar.
    print("Uyarı: 'npx' komutu bulunamadı. Firecrawl MCP'nin çalışması için Node.js ve npx'in yüklü olması gerekmektedir.")

# `.env` dosyasını yükleyerek içindeki değişkenleri ortam değişkeni olarak ayarla.
# Bu, API anahtarları gibi hassas bilgileri kodun dışında tutmamızı sağlar.
load_dotenv()

# Gemini API anahtarının ortam değişkenlerinde ayarlı olup olmadığını kontrol et.
if not os.getenv("GEMINI_API_KEY"):
    # Eğer ayarlı değilse, bir hata fırlatarak programı durdur.
    # Bu, programın API anahtarı olmadan boşuna çalışmasını engeller.
    raise ValueError("Hata: GEMINI_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")

# Firecrawl API anahtarının ortam değişkenlerinde ayarlı olup olmadığını kontrol et.
if not os.getenv("FIRECRAWL_API_KEY"):
    raise ValueError("Hata: FIRECRAWL_API_KEY ortam değişkeni ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")


# --- 3. Ana Fonksiyon (main) ---
# Script'in ana iş mantığının bulunduğu asenkron fonksiyondur.
# `async def` tanımı, bu fonksiyon içinde `await` anahtar kelimesinin kullanılmasına
# ve asenkron operasyonların (örn: ağ istekleri) beklenmesine olanak tanır.

async def main():
    """
    Agent'ı çalıştıran ana asenkron fonksiyon.
    URL'yi komut satırından alır, web sayfasını kazır, özetler ve sonucu dosyaya yazar.
    Ayrıca tüm adımların performansını ölçer ve kaydeder.
    """
    # --- 3.1. Benchmark Veri Yapısını ve Başlangıç Zamanını Ayarlama ---
    # `total_start_time`, tüm işlemin başlangıç anını kaydeder.
    total_start_time = time.time()
    # `benchmark_data`, bu çalıştırmaya ait tüm performans metriklerini ve
    # diğer bilgileri saklayacağımız bir sözlük (dictionary) yapısıdır.
    benchmark_data = {
        "timestamp": datetime.now().isoformat(),  # İşlemin ne zaman yapıldığı.
        "url": "",  # Hangi URL'nin işlendiği.
        "durations": {},  # Süre ölçümlerinin (saniye cinsinden) saklanacağı yer.
        "content_stats": {},  # İçerik ile ilgili istatistiklerin (örn: uzunluk) saklanacağı yer.
        "success": False,  # İşlemin başarılı olup olmadığı.
        "error": None,  # Eğer bir hata oluşursa, hata mesajının saklanacağı yer.
    }

    # --- 3.2. Komut Satırı Argümanlarını Ayarlama ve Ayrıştırma ---
    # `argparse` modülü, kullanıcıların komut satırından programa veri (argüman)
    # göndermesini sağlayan standart bir yol sunar.
    try:
        # `ArgumentParser`, argümanları nasıl işleyeceğimizi tanımlayan bir nesne oluşturur.
        parser = argparse.ArgumentParser(
            description="Bir web sayfasını kazıyıp özetleyen ve performansını ölçen AI Agent."
        )
        # `add_argument` ile beklediğimiz argümanları tanımlarız.
        # "url": Zorunlu bir argümandır, analiz edilecek web sayfasını belirtir.
        parser.add_argument(
            "url", type=str, help="Kazınacak ve özetlenecek web sayfasının tam URL'si."
        )
        # "--benchmark" veya "-b": İsteğe bağlı bir bayraktır. Kullanıcı bu bayrağı eklerse,
        # `action="store_true"` sayesinde `args.benchmark` değeri `True` olur.
        parser.add_argument(
            "--benchmark",
            "-b",
            action="store_true",
            help="İşlem sonunda detaylı bir benchmarking raporu gösterir.",
        )
        # `parse_args()`, komut satırından girilen değerleri okur ve ayrıştırır.
        args = parser.parse_args()
        url = args.url
        benchmark_data["url"] = url

        # --- 3.3. Agent'ın Bileşenlerini Başlatma ---

        # a) Gemini LLM'i Başlatma
        # LLM (Large Language Model), agent'ımızın "beyni" olarak görev yapar.
        # `ChatGoogleGenerativeAI` sınıfı ile Gemini modeline bağlanıyoruz.
        llm_init_start_time = time.time()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Hızlı ve maliyet etkin bir model.
            temperature=0,  # Yaratıcılık seviyesi. 0, en tutarlı ve tekrarlanabilir cevapları verir.
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        benchmark_data["durations"]["llm_init_seconds"] = round(time.time() - llm_init_start_time, 3)

        # b) Firecrawl MCP Bağlantısını Ayarlama
        # MCP (Model Context Protocol), LLM'lerin dış araçlarla (bu örnekte Firecrawl)
        # güvenli ve standart bir şekilde iletişim kurmasını sağlayan bir protokoldür.
        # `connection` sözlüğü, LangChain'e bu araca nasıl bağlanacağını söyler.
        #detaylı bilgi için https://docs.firecrawl.dev/mcp-server web sitesinden bilgi edinebilirsiniz.
        connection = {
            "transport": "stdio",  # İletişim kanalı: Standart Giriş/Çıkış (klavye/ekran gibi).
            "command": "npx",  # Çalıştırılacak ana komut.
            "args": ["firecrawl-mcp"],  # Komutun argümanları.
            "env": {"FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")},  # Alt sürece gönderilecek ortam değişkeni.
        }

        # c) MCP Araçlarını Yükleme
        # `load_mcp_tools`, yukarıda tanımlanan bağlantıyı kullanarak Firecrawl'un
        # sunduğu araçları (örn: 'scrape', 'search') keşfeder ve yükler.
        tools_load_start_time = time.time()
        print("Firecrawl MCP araçları yükleniyor...")
        tools = await load_mcp_tools(None, connection=connection)
        # Yüklenen araçlar listesinden sadece `firecrawl_scrape` aracını seçiyoruz.
        scrape_tool = next((t for t in tools if t.name == "firecrawl_scrape"), None)
        benchmark_data["durations"]["tools_load_seconds"] = round(time.time() - tools_load_start_time, 3)

        # `scrape_tool`'un bulunup bulunmadığını kontrol et.
        if not scrape_tool:
            raise RuntimeError("Hata: 'firecrawl_scrape' aracı bulunamadı. Lütfen npx ve Firecrawl kurulumunu kontrol edin.")

        # d) LangGraph Agent'ını Oluşturma
        # `create_react_agent`, bir "ReAct" (Reasoning and Acting - Düşünme ve Harekete Geçme)
        # mantığıyla çalışan bir agent oluşturur. Bu agent, bir hedefi başarmak için
        # düşünür (LLM'i kullanır) ve gerekli araçları kullanma kararı alır.
        agent_init_start_time = time.time()
        agent = create_react_agent(
            llm,  # Agent'ın "beyni".
            tools=[scrape_tool]  # Agent'ın kullanabileceği araçların listesi.
        )
        benchmark_data["durations"]["agent_init_seconds"] = round(time.time() - agent_init_start_time, 3)

        # --- 3.4. Agent İçin Talimat (Prompt) Hazırlama ---
        # `user_prompt`, agent'a ne yapması gerektiğini adım adım anlatan talimat metnidir.
        # İyi bir prompt, başarılı bir sonuç için en kritik unsurlardan biridir.
        user_prompt = f"""
        Senin görevin bir web sayfasının içeriğini analiz edip özetlemek. Süreci şu adımlarla izle:
        1.  **Veriyi Topla:** `firecrawl_scrape` aracını kullanarak `{url}` adresindeki web sayfasının tam metin içeriğini al.
        2.  **İçeriği Analiz Et:** Araçtan elde ettiğin metni dikkatlice oku. Bu metinden aşağıdaki bilgileri çıkar:
            - Makalenin ana fikirleri ve en önemli noktaları.
            - Metinde geçen tüm somut istatistikler (yüzdeler, sayılar, finansal veriler vb.).
            - Makalenin ulaştığı anahtar bulgular veya sonuçlar.
        3.  **JSON Olarak Formatla:** Çıkardığın bu bilgileri 'main_points', 'statistics', ve 'key_findings' anahtarlarını içeren geçerli bir JSON nesnesi olarak sun. Yanıtında sadece bu JSON nesnesi bulunsun, başka hiçbir açıklama veya giriş metni ekleme.
        """

        # --- 3.5. Veri Kazıma (Scraping) İşlemi ---
        # Agent'ı çalıştırmadan önce, web sayfasından ham veriyi manuel olarak çekiyoruz.
        # Bu, LLM'in hangi veriyle çalıştığını tam olarak bilmemizi ve
        # scraping işleminin süresini ayrıca ölçmemizi sağlar.
        print(f"'{url}' adresinden ham veri kazınıyor...")
        scrape_start_time = time.time()
        # `scrape_tool.ainvoke`, aracı asenkron olarak çalıştırır.
        scrape_result = await scrape_tool.ainvoke({"url": url})
        benchmark_data["durations"]["scraping_seconds"] = round(time.time() - scrape_start_time, 3)

        # Kazınan içeriği bir değişkene al.
        raw_scraped_content = scrape_result.content if hasattr(scrape_result, "content") else str(scrape_result)
        benchmark_data["content_stats"]["scraped_content_length"] = len(raw_scraped_content)

        # Ham veriyi daha sonra incelemek üzere bir dosyaya kaydet.
        raw_file = "raw_scraped_content.txt"
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(raw_scraped_content)
        print(f"Ham veri '{raw_file}' dosyasına kaydedildi.")

        # --- 3.6. Agent'ı Çalıştırma ve Analizi Gerçekleştirme ---
        print("Agent, kazınan veriyi analiz ediyor...")
        llm_processing_start_time = time.time()
        # `agent.ainvoke`, hazırlanan talimat (prompt) ile agent'ı çalıştırır.
        # Agent, prompt'u okur, `firecrawl_scrape` aracını kullanması gerektiğini anlar,
        # aracı çalıştırır (aslında veri zaten hazır ama ReAct döngüsü bunu gerektirir),
        # ve dönen sonuçları analiz ederek nihai JSON çıktısını üretir.
        response = await asyncio.wait_for(
            agent.ainvoke({"messages": [HumanMessage(content=user_prompt)]}),
            timeout=90.0,  # Agent'ın cevabı için maksimum 90 saniye bekle.
        )
        benchmark_data["durations"]["llm_processing_seconds"] = round(time.time() - llm_processing_start_time, 3)

        # --- 3.7. Sonucu İşleme ve Kaydetme ---
        # Agent'ın cevabı, mesaj listesinin son elemanında bulunur.
        agent_response_content = response["messages"][-1].content

        output_file = "web_summary.json"
        summary_json = None

        # LLM'in cevabını temizle. LLM'ler bazen JSON'ı ```json ... ``` gibi
        # Markdown kod blokları içinde döndürebilir. Bu blokları temizliyoruz.
        cleaned_content = agent_response_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:-3].strip()
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:-3].strip()

        # Temizlenmiş metni JSON'a çevirmeyi dene.
        try:
            summary_json = json.loads(cleaned_content)
            benchmark_data["success"] = True  # JSON ayrıştırma başarılı.
            print("JSON çıktısı başarıyla oluşturuldu ve doğrulandı.")
        except json.JSONDecodeError:
            # Eğer LLM geçerli bir JSON döndürmediyse, bu durumu ele al.
            error_msg = "Uyarı: LLM çıktısı geçerli bir JSON formatında değil. Ham metin kaydediliyor."
            benchmark_data["error"] = error_msg
            print(error_msg)
            # Özeti, ham metin olarak kaydet.
            summary_json = {"error": error_msg, "raw_text": agent_response_content}

        # Sonuçları (başarılı JSON veya hata mesajı) dosyaya yaz.
        with open(output_file, "w", encoding="utf-8") as f:
            # `ensure_ascii=False` Türkçe karakterlerin doğru yazılmasını sağlar.
            # `indent=2` JSON'un okunaklı olmasını sağlar.
            json.dump(summary_json, f, ensure_ascii=False, indent=2)
        print(f"Yapılandırılmış özet '{output_file}' dosyasına kaydedildi.")
        benchmark_data["content_stats"]["summary_length"] = len(json.dumps(summary_json))

    except Exception as e:
        # `try` bloğu içinde herhangi bir beklenmedik hata olursa, bu blok çalışır.
        error_msg = f"Ana işlem sırasında beklenmeyen bir hata oluştu: {e}"
        benchmark_data["error"] = error_msg
        print(error_msg)

    finally:
        # --- 3.8. Benchmark Sonuçlarını Hesaplama ve Raporlama ---
        # `finally` bloğu, `try` bloğunda bir hata olsa bile her zaman çalışır.
        # Bu, performans verilerinin her durumda kaydedilmesini garanti eder.
        total_end_time = time.time()
        benchmark_data["durations"]["total_seconds"] = round(total_end_time - total_start_time, 3)

        benchmark_file = "benchmark_results.json"
        try:
            # Önceki benchmark kayıtlarını oku (varsa).
            existing_data = []
            if os.path.exists(benchmark_file):
                with open(benchmark_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            # Yeni sonucu mevcut listeye ekle.
            existing_data.append(benchmark_data)

            # Tüm veriyi tekrar dosyaya yaz.
            with open(benchmark_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"Performans metrikleri '{benchmark_file}' dosyasına eklendi.")

            # Eğer kullanıcı `--benchmark` bayrağını kullandıysa, detaylı raporu ekrana yazdır.
            if args.benchmark:
                print("\n" + "=" * 50)
                print("DETAYLI PERFORMANS RAPORU")
                print("=" * 50)
                print(f"URL: {benchmark_data['url']}")
                print(f"Zaman: {benchmark_data['timestamp']}")
                print(f"Durum: {"Başarılı" if benchmark_data['success'] else "Başarısız"}")

                print("\nSÜRE ÖLÇÜMLERİ (saniye):")
                for key, value in benchmark_data["durations"].items():
                    print(f"  - {key.replace('_', ' ').capitalize()}: {value}")

                print("\nİÇERİK İSTATİSTİKLERİ:")
                for key, value in benchmark_data["content_stats"].items():
                    print(f"  - {key.replace('_', ' ').capitalize()}: {value}")

                if benchmark_data["error"]:
                    print(f"\nHATA: {benchmark_data['error']}")
                print("=" * 50)
            else:
                # Standart çalıştırmada kısa bir özet göster.
                print("\nPERFORMANS ÖZETİ:")
                print(f"  - Toplam süre: {benchmark_data['durations'].get('total_seconds', 'N/A')}s")
                print(f"  - Başarı durumu: {"Evet" if benchmark_data['success'] else "Hayır"}")

        except Exception as e:
            print(f"Benchmark sonuçları kaydedilirken bir hata oluştu: {e}")


# --- 4. Script'in Başlatılması ---
# Bu standart Python yapısı, script'in doğrudan `python app.py` komutuyla
# çalıştırıldığında `main()` fonksiyonunu çağırmasını sağlar.
# Eğer bu dosya başka bir Python dosyası tarafından `import` edilirse,
# bu blok çalışmaz.
if __name__ == "__main__":
    # Asenkron `main` fonksiyonunu çalıştır.
    asyncio.run(main())
