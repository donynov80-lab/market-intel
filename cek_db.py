"""
cek_db.py
Script untuk melihat isi database trending.
"""
import sys
from pathlib import Path

# Biar bisa import dari backend/
sys.path.insert(0, str(Path(__file__).parent))

from backend.db.trending_db import ambil_trending, hitung_total, list_region


def main():
    print("=" * 55)
    print("📊 CEK DATABASE TRENDING")
    print("=" * 55)

    total = hitung_total()
    regions = list_region()

    print(f"\nTotal baris : {total}")
    print(f"Region      : {regions if regions else '(kosong)'}\n")

    if total == 0:
        print("⚠️  Database masih kosong.")
        print("Jalankan dulu: python backend/modules/trending_collector.py")
        return

    for region in regions:
        print("=" * 55)
        print(f"🌏 Region: {region}")
        print("=" * 55)
        rows = ambil_trending(region=region, limit=20)
        for rank, kw, collected_at in rows:
            print(f"{rank:2}. {kw}")
        print()


if __name__ == "__main__":
    main()