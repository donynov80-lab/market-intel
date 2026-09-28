"""
trending_collector.py
Ambil trending dari Google Trends RSS → simpan ke SQLite.
Support multi-region.
"""
import requests
from xml.etree import ElementTree as ET
from time import sleep
import sys
from pathlib import Path

# Biar bisa import dari db/
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.trending_db import (
    simpan_trending, ambil_trending, hitung_total, list_region
)


def fetch_trending_rss(region='ID', max_items=50):
    """
    Ambil trending dari Google Trends RSS.
    
    Returns:
        list of dict: [{'rank': 1, 'keyword': 'xxx'}, ...]
    """
    # Coba dua varian: geo=ID dan geo=id
    for geo_code in [region, region.lower()]:
        url = f"https://trends.google.com/trending/rss?geo={geo_code}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8"
        }

        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()

            root = ET.fromstring(r.content)
            results = []
            rank = 1

            for item in root.iter():
                if item.tag.endswith("item"):
                    title_el = None
                    for child in item:
                        if child.tag.endswith("title"):
                            title_el = child
                            break
                    if title_el is not None and title_el.text:
                        results.append({
                            "rank": rank,
                            "keyword": title_el.text.strip()
                        })
                        rank += 1
                        if len(results) >= max_items:
                            break

            if results:
                print(f"✅ [{geo_code}] {len(results)} trending diambil")
                return results
            else:
                print(f"⚠️ [{geo_code}] Kosong, coba varian lain")

        except Exception as e:
            print(f"⚠️ [{geo_code}] Gagal: {e}")
            continue

    return []


def collect_all_regions(regions=None, max_items=50):
    """
    Ambil trending untuk beberapa region dan simpan ke DB.
    
    Args:
        regions (list): list kode region. Default: ['ID', 'US', 'SG', 'MY']
        max_items (int): jumlah maksimal per region
    """
    if regions is None:
        regions = ['ID', 'US', 'SG', 'MY']

    total = 0
    for region in regions:
        print(f"\n🌏 Mengambil trending untuk {region}...")
        keywords = fetch_trending_rss(region, max_items=max_items)

        if keywords:
            saved = simpan_trending(region, keywords)
            print(f"💾 Tersimpan: {saved} baris")
            total += saved
        else:
            print(f"❌ Tidak ada data untuk {region}")

        sleep(3)  # jeda biar tidak kena rate limit

    print(f"\n✅ Total {total} baris tersimpan di database.")
    return total


if __name__ == "__main__":
    print("=" * 55)
    print("🔥 TRENDING COLLECTOR — Google Trends RSS")
    print("=" * 55)

    # Kumpulkan dari beberapa region
    collect_all_regions(
        regions=['ID', 'US', 'SG', 'MY'],
        max_items=50
    )

    # Tampilkan summary
    print("\n" + "=" * 55)
    print("📊 SUMMARY DATABASE")
    print("=" * 55)
    print(f"Total baris: {hitung_total()}")
    print(f"Region: {list_region()}")

    # Tampilkan top 10 ID
    print("\n🇮🇩 Top 10 trending Indonesia (dari DB):")
    print("-" * 55)
    rows = ambil_trending(region='ID', limit=10)
    if rows:
        for rank, keyword, collected_at in rows:
            print(f"{rank:2}. {keyword}")
    else:
        print("(kosong)")