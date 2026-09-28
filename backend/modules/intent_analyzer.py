"""
intent_analyzer.py
Analisis otomatis: kategori apa yang terkandung di keyword.
Berguna untuk klasifikasi produk & rekomendasi konten UMKM.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.trending_db import (
    simpan_autocomplete, ambil_autocomplete_db, hitung_total_autocomplete
)
from autocomplete_analyzer import ambil_autocomplete_bertingkat


# =========================================================
# KAMUS KATEGORI
# =========================================================
KATEGORI = {
    "LOKAL": [
        "terdekat", "dekat sini", "sekitar", "daerah", "kota", "kabupaten",
        "bandung", "jakarta", "bogor", "surabaya", "medan", "semarang",
        "yogyakarta", "jogja", "malang", "bekasi", "tangerang", "depok",
        "dari lokasi saya", "buka sekarang",
    ],
    "HARGA": [
        "murah", "harga", "gratis", "diskon", "promo", "termurah",
        "premium", "mahal", "budget", "kiloan",
    ],
    "MOMEN": [
        "lebaran", "natal", "ultah", "ulang tahun", "tahun baru",
        "valentine", "anniversary", "wisuda", "khitanan", "pernikahan",
    ],
    "CUSTOM": [
        "custom", "aesthetic", "karakter", "kuromi", "hello kitty",
        "unicorn", "foto", "edible", "tema",
    ],
    "RESEP": [
        "resep", "cara buat", "cara membuat", "bahan", "asal", "khas",
        "tradisional", "jadul", "berasal dari",
    ],
    "JUAL_BELI": [
        "jual", "beli", "toko", "order", "pesan", "ready",
    ],
}


def deteksi_kategori(keyword):
    """
    Deteksi kategori dari keyword.
    Return: list kategori yang cocok (bisa lebih dari 1).
    """
    keyword_lower = keyword.lower()
    hasil = []
    for kategori, kata_kunci in KATEGORI.items():
        for kk in kata_kunci:
            if kk in keyword_lower:
                hasil.append(kategori)
                break
    return hasil if hasil else ["UMUM"]


def analisis_ekspansi(seed, kedalaman=2):
    """
    Ekspansi keyword + kategori + simpan ke DB.
    """
    print(f"\n🔍 Menganalisis '{seed}' (kedalaman {kedalaman})...")
    hasil = ambil_autocomplete_bertingkat(seed, kedalaman=kedalaman)

    semua = hasil["semua"]

    # Kategorikan
    kategori_map = {}
    for kw in semua:
        kategori_map[kw] = deteksi_kategori(kw)

    # Simpan ke DB
    tersimpan = simpan_autocomplete(seed, semua, level=kedalaman)

    return {
        "seed": seed,
        "total": len(semua),
        "tersimpan": tersimpan,
        "kategori_map": kategori_map,
        "semua": semua,
    }


def tampilkan_laporan(hasil):
    """Tampilkan laporan analisis rapi."""
    print("\n" + "=" * 60)
    print(f"📊 LAPORAN: '{hasil['seed']}'")
    print("=" * 60)
    print(f"Total keyword : {hasil['total']}")
    print(f"Tersimpan DB  : {hasil['tersimpan']}")

    # Group per kategori
    kategori_count = {}
    for kw, kats in hasil["kategori_map"].items():
        for kat in kats:
            kategori_count.setdefault(kat, []).append(kw)

    print("\n📂 Distribusi Kategori:")
    print("-" * 60)
    for kat, kws in sorted(kategori_count.items(), key=lambda x: -len(x[1])):
        print(f"  {kat:12} : {len(kws):3} keyword")
        for kw in kws[:3]:
            print(f"      • {kw}")


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 INTENT ANALYZER — Kategorisasi Keyword UMKM")
    print("=" * 60)

    # Analisis beberapa seed
    seeds = ["kue ulang tahun", "kue kering", "jual kue"]

    for seed in seeds:
        hasil = analisis_ekspansi(seed, kedalaman=1)
        tampilkan_laporan(hasil)

    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY DATABASE")
    print("=" * 60)
    print(f"Total keyword autocomplete di DB: {hitung_total_autocomplete()}")