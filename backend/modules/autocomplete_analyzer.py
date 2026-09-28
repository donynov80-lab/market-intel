"""
autocomplete_analyzer.py
Ambil saran pencarian Google (autocomplete) — REAL query orang Indonesia.

Ini sumber data TERBAIK untuk riset kata kunci UMKM:
- Gratis, tanpa API key
- Real-time dari Google
- Benar-benar apa yang orang ketik
"""
import requests
import json
from time import sleep


def ambil_autocomplete(keyword, bahasa='id', negara='id'):
    """
    Ambil saran pencarian Google untuk keyword tertentu.
    
    Args:
        keyword (str): kata kunci awal, contoh "kue"
        bahasa (str): kode bahasa, 'id' = Indonesia
        negara (str): kode negara, 'id' = Indonesia
    
    Returns:
        list of str: saran pencarian
    """
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",  # format output: JSON array
        "q": keyword,
        "hl": bahasa,
        "gl": negara,
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = json.loads(r.text)
        # Format: [query_asli, [list_saran], ...]
        return data[1] if len(data) > 1 else []
    except Exception as e:
        return [f"⚠️ Error: {e}"]


def ambil_autocomplete_bertingkat(keyword, kedalaman=1):
    """
    Ambil autocomplete bertingkat (ekspansi).
    
    kedalaman=1: keyword → 10 saran
    kedalaman=2: keyword → 10 saran → tiap saran → 10 saran (100 saran)
    
    Args:
        keyword (str): seed keyword
        kedalaman (int): 1 atau 2
    
    Returns:
        dict: {
            'seed': keyword,
            'level_1': [...],
            'level_2': {saran: [sub_saran]},
            'total_unik': int
        }
    """
    hasil = {
        "seed": keyword,
        "level_1": [],
        "level_2": {},
        "total_unik": 0,
    }

    semua = set()

    # Level 1
    level_1 = ambil_autocomplete(keyword)
    if level_1 and not level_1[0].startswith("⚠️"):
        hasil["level_1"] = level_1
        semua.update(level_1)

    # Level 2
    if kedalaman >= 2:
        for saran in hasil["level_1"]:
            sleep(0.5)  # hindari rate limit
            sub = ambil_autocomplete(saran)
            if sub and not sub[0].startswith("⚠️"):
                hasil["level_2"][saran] = sub
                semua.update(sub)

    hasil["total_unik"] = len(semua)
    hasil["semua"] = sorted(semua)
    return hasil


def analisis_beberapa_keyword(daftar_keyword):
    """
    Analisis beberapa seed keyword sekaligus (untuk perbandingan).
    
    Returns:
        dict: {keyword: [saran, ...], ...}
    """
    hasil = {}
    for kw in daftar_keyword:
        print(f"🔍 Menganalisis: {kw}")
        hasil[kw] = ambil_autocomplete(kw)
        sleep(1)
    return hasil


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 GOOGLE AUTOCOMPLETE — Real Query Orang Indonesia")
    print("=" * 60)

    # Test 1: Autocomplete dasar
    print("\n📌 TEST 1 — Autocomplete untuk 'kue'")
    print("-" * 60)
    saran = ambil_autocomplete("kue")
    for i, s in enumerate(saran, 1):
        print(f"{i:2}. {s}")

    sleep(1.5)

    # Test 2: Bandingkan beberapa keyword
    print("\n📌 TEST 2 — Bandingkan beberapa keyword terkait")
    print("-" * 60)
    hasil = analisis_beberapa_keyword([
        "kue ulang tahun",
        "kue kering",
        "kue basah",
        "jual kue",
    ])
    for kw, daftar in hasil.items():
        print(f"\n🔸 '{kw}':")
        for i, s in enumerate(daftar[:8], 1):
            print(f"   {i}. {s}")

    sleep(1.5)

    # Test 3: Ekspansi bertingkat
    print("\n📌 TEST 3 — Ekspansi bertingkat 'kue' (kedalaman 2)")
    print("-" * 60)
    ekspansi = ambil_autocomplete_bertingkat("kue", kedalaman=2)
    print(f"Total keyword unik: {ekspansi['total_unik']}")
    print(f"\nContoh 20 pertama:")
    for i, s in enumerate(ekspansi['semua'][:20], 1):
        print(f"{i:2}. {s}")