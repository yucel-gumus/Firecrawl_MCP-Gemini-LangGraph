"""
CLI Runner: Firecrawl MCP & Gemini LangGraph Summarizer
Kapsamlı Web İstihbarat ve Analiz Terminal Arayüzü.
"""

import sys
import asyncio
import argparse
import json
from core import run_pipeline, validate_environment
from config import DEFAULT_MODEL


def parse_arguments():
    """Komut satırı argümanlarını ayrıştırır."""
    parser = argparse.ArgumentParser(
        description="🕷️ Firecrawl MCP & Gemini 3.7 Flash LangGraph AI Web Scraper & Intelligence Agent"
    )
    parser.add_argument(
        "url",
        type=str,
        help="Kazınacak ve derinlemesine özetlenecek web sayfasının tam URL'si"
    )
    parser.add_argument(
        "--benchmark",
        "-b",
        action="store_true",
        help="İşlem sonunda detaylı performans ve süre metriklerini gösterir."
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Kullanılacak Gemini modeli (Varsayılan: {DEFAULT_MODEL})"
    )
    return parser.parse_args()


def print_summary_report(result: dict):
    """Yapılandırılmış ve zenginleştirilmiş özet verisini terminalde okunaklı şekilde yazdırır."""
    summary = result.get("summary")
    if not summary:
        print("\n❌ Özet çıkarılamadı veya bir hata oluştu.")
        if result.get("error"):
            print(f"Hata detayı: {result['error']}")
        return

    print("\n" + "=" * 70)
    print("🌟 KAPSAMLI WEB SAYFASI İSTİHBARAT VE ANALİZ RAPORU")
    print("=" * 70)

    # 1. Yönetici Özeti
    if summary.get("executive_summary"):
        print("\n📖 YÖNETİCİ ÖZETİ (EXECUTIVE SUMMARY):")
        print("-" * 70)
        print(summary["executive_summary"])

    # 2. Detaylı Konu Kırılımları
    topics = summary.get("topics", [])
    if topics:
        print(f"\n📑 DETAYLI KONU ANALİZİ ({len(topics)} Ana Başlık):")
        print("-" * 70)
        for i, t in enumerate(topics, 1):
            print(f"\n  [{i}] 📌 {t.get('topic', 'Konu')}")
            if t.get("details"):
                print(f"      Açıklama: {t['details']}")
            for point in t.get("key_points", []):
                print(f"      • {point}")

    # 3. İstatistikler ve Metrikler
    stats = summary.get("statistics", [])
    print(f"\n📈 SOMUT VERİLER, İSTATİSTİKLER & TARİHLER ({len(stats)} adet):")
    print("-" * 70)
    if stats:
        for s in stats:
            if isinstance(s, dict):
                print(f"  📊 {s.get('metric', '')}: {s.get('value', '')} (Bağlam: {s.get('context', '')})")
            else:
                print(f"  📊 {s}")
    else:
        print("  (Metinde somut sayısal veya istatistiki veri tespit edilmedi)")

    # 4. Önemli Bulgular
    findings = summary.get("key_findings", [])
    if findings:
        print(f"\n💡 STRATEJİK ÇIKARIMLAR & ÖNEMLİ BULGULAR ({len(findings)} adet):")
        print("-" * 70)
        for f in findings:
            print(f"  ✓ {f}")

    # 5. Aksiyon Maddeleri
    takeaways = summary.get("actionable_takeaways", [])
    if takeaways:
        print(f"\n🎯 UYGULANABİLİR EYLEM MADDELERİ & TAVSİYELER ({len(takeaways)} adet):")
        print("-" * 70)
        for t in takeaways:
            print(f"  👉 {t}")

    # 6. Bahsedilen Teknolojiler & Şirketler
    entities = summary.get("entities_and_technologies", [])
    if entities:
        print(f"\n🏷️ TESPİT EDİLEN TEKNOLOJİLER, KURUMLAR & VARLIKLAR:")
        print("-" * 70)
        print("  " + " | ".join(entities))

    print("\n" + "=" * 70)


def print_benchmark_report(result: dict):
    """Detaylı benchmark ve performans metriklerini ekrana basar."""
    print("\n" + "=" * 70)
    print("⚡ DETAYLI PERFORMANS RAPORU (BENCHMARK)")
    print("=" * 70)
    print(f"Hedef URL     : {result.get('url')}")
    print(f"Zaman Damgası : {result.get('timestamp')}")
    print(f"Başarı Durumu : {'✅ Başarılı' if result.get('success') else '❌ Başarısız'}")

    durations = result.get("durations", {})
    print("\n⏱️ SÜRE DAĞILIMI (Saniye):")
    print(f"  • MCP Araç Yükleme    : {durations.get('tools_load_seconds', 0):.3f}s")
    print(f"  • Firecrawl Kazıma    : {durations.get('scraping_seconds', 0):.3f}s")
    print(f"  • Gemini Analiz Süresi: {durations.get('llm_processing_seconds', 0):.3f}s")
    print(f"  ---------------------------------")
    print(f"  ⭐ TOPLAM İŞLEM SÜRESİ : {durations.get('total_seconds', 0):.3f}s")

    stats = result.get("content_stats", {})
    if stats:
        print("\n📝 İÇERİK METRİKLERİ:")
        print(f"  • Kazınan İçerik Boyutu: {stats.get('scraped_content_length', 0):,} karakter")
        print(f"  • JSON Çıktı Boyutu    : {stats.get('summary_length', 0):,} karakter")

    if result.get("error"):
        print(f"\n⚠️ HATA: {result['error']}")
    print("=" * 70 + "\n")


async def main():
    args = parse_arguments()

    print(f"🚀 İşlem başlatılıyor: {args.url}")
    print(f"🧠 Model: {args.model} | LangGraph StateGraph Akışı Aktif...")

    result = await run_pipeline(
        url=args.url,
        model_name=args.model
    )

    if result.get("success"):
        print_summary_report(result)
    else:
        print(f"\n❌ İşlem başarısız: {result.get('error')}")

    if args.benchmark:
        print_benchmark_report(result)
    else:
        dur = result.get("durations", {}).get("total_seconds", 0)
        print(f"\n⚡ Toplam süre: {dur:.3f}s | Başarı: {'Evet' if result.get('success') else 'Hayır'}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nİşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"\nKritik Hata: {e}", file=sys.stderr)
        sys.exit(1)