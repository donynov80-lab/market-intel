"""
maps_scanner.py
Scan lokasi/toko pakai Overpass API + Smart Classifier + Cache.
"""
import requests
from time import sleep
from math import radians, sin, cos, sqrt, atan2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


# =========================================================
# KOORDINAT FALLBACK (kalau DB tidak ada)
# =========================================================
KOORDINAT_KOTA = {
    "bandung": (-6.9175, 107.6191, "Kota Bandung, Jawa Barat"),
    "jakarta": (-6.2088, 106.8456, "DKI Jakarta"),
    "surabaya": (-7.2575, 112.7521, "Kota Surabaya, Jawa Timur"),
    "yogyakarta": (-7.7956, 110.3695, "DI Yogyakarta"),
    "jogja": (-7.7956, 110.3695, "DI Yogyakarta"),
    "semarang": (-6.9932, 110.4203, "Kota Semarang, Jawa Tengah"),
    "malang": (-7.9666, 112.6326, "Kota Malang, Jawa Timur"),
    "solo": (-7.5755, 110.8243, "Kota Surakarta"),
    "surakarta": (-7.5755, 110.8243, "Kota Surakarta"),
    "bekasi": (-6.2383, 106.9756, "Kota Bekasi"),
    "bogor": (-6.5971, 106.8060, "Kota Bogor"),
    "depok": (-6.4025, 106.7942, "Kota Depok"),
    "tangerang": (-6.1781, 106.6300, "Kota Tangerang"),
    "cimahi": (-6.8722, 107.5425, "Kota Cimahi"),
    "cirebon": (-6.7320, 108.5523, "Kota Cirebon"),
    "medan": (3.5952, 98.6722, "Kota Medan, Sumatera Utara"),
    "palembang": (-2.9761, 104.7754, "Kota Palembang"),
    "padang": (-0.9471, 100.4172, "Kota Padang"),
    "pekanbaru": (0.5071, 101.4478, "Kota Pekanbaru"),
    "balikpapan": (-1.2379, 116.8529, "Kota Balikpapan"),
    "samarinda": (-0.5022, 117.1536, "Kota Samarinda"),
    "banjarmasin": (-3.3186, 114.5944, "Kota Banjarmasin"),
    "pontianak": (-0.0263, 109.3425, "Kota Pontianak"),
    "makassar": (-5.1477, 119.4327, "Kota Makassar"),
    "manado": (1.4748, 124.8421, "Kota Manado"),
    "palu": (-0.8917, 119.8707, "Kota Palu"),
    "denpasar": (-8.6705, 115.2126, "Kota Denpasar, Bali"),
    "mataram": (-8.5833, 116.1167, "Kota Mataram"),
    "kupang": (-10.1772, 123.6070, "Kota Kupang"),
    "jayapura": (-2.5916, 140.6690, "Kota Jayapura"),
    "ambon": (-3.6954, 128.1814, "Kota Ambon"),
}


# =========================================================
# Mapping keyword → tag OSM
# =========================================================
KEYWORD_TO_OSM = {
    "kue": ["shop=bakery", "shop=confectionery", "shop=pastry"],
    "toko kue": ["shop=bakery", "shop=confectionery"],
    "camilan": ["shop=confectionery", "shop=convenience"],
    "restoran": ["amenity=restaurant"],
    "resto": ["amenity=restaurant"],
    "cafe": ["amenity=cafe"],
    "kafe": ["amenity=cafe"],
    "warung": ["amenity=fast_food", "shop=convenience"],
    "minuman": ["amenity=cafe", "amenity=bar"],
    "baju": ["shop=clothes", "shop=boutique"],
    "sepatu": ["shop=shoes"],
    "apotek": ["amenity=pharmacy"],
    "bengkel": ["shop=car_repair", "shop=motorcycle_repair"],
    "salon": ["shop=hairdresser", "shop=beauty"],
    "laundry": ["shop=laundry", "shop=dry_cleaning"],
    "buku": ["shop=books"],
    "mainan": ["shop=toys"],
    "buah": ["shop=greengrocer"],
    "sembako": ["shop=convenience", "shop=supermarket"],
    "frozen food": ["shop=frozen_food", "shop=convenience"],
    "hotel": ["tourism=hotel"],
    "masjid": ["amenity=place_of_worship"],
    "bank": ["amenity=bank"],
    "spbu": ["amenity=fuel"],
    "pasar": ["amenity=marketplace"],
    "toko": ["shop=*"],
    "toserba": ["shop=department_store"],
}


# =========================================================
# Cache kota (dari API EMSIFA)
# =========================================================
_KOTA_CACHE = None


def _load_semua_kota_online():
    global _KOTA_CACHE
    if _KOTA_CACHE is not None:
        return _KOTA_CACHE

    print("🌐 Loading kota dari EMSIFA...")
    try:
        r = requests.get(
            "https://www.emsifa.com/api-wilayah-indonesia/api/provinces.json",
            timeout=10
        )
        provinsi_list = r.json()

        semua_kota = []
        for prov in provinsi_list:
            try:
                r2 = requests.get(
                    f"https://www.emsifa.com/api-wilayah-indonesia/api/regencies/{prov['id']}.json",
                    timeout=5
                )
                for kota in r2.json():
                    semua_kota.append({
                        'id': kota['id'],
                        'provinsi': prov['name'],
                        'kota': kota['name'],
                        'display': f"{kota['name']}, {prov['name']}",
                        'lat': None, 'lon': None,
                    })
            except Exception:
                continue

        _KOTA_CACHE = semua_kota
        return semua_kota
    except Exception as e:
        print(f"⚠️ Gagal load API: {e}")
        _KOTA_CACHE = []
        return []


# =========================================================
# Cari kota — PRIORITAS: tabel wilayah_lengkap → KOORDINAT_KOTA → API
# =========================================================
def cari_kota_lengkap(keyword, limit=50):
    import sqlite3
    from pathlib import Path

    keyword_lower = str(keyword).lower().strip()
    hasil_raw = []
    db_path = Path(__file__).parent.parent.parent / "market_intel.db"

    # ===== PRIORITAS 1: tabel wilayah_lengkap =====
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()

            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wilayah_lengkap'")
            if c.fetchone():
                c.execute("""
                    SELECT kode, nama, provinsi_nama, lat, lng, luas, penduduk, level
                    FROM wilayah_lengkap
                    WHERE LOWER(nama) LIKE ? OR LOWER(provinsi_nama) LIKE ?
                    ORDER BY level DESC, penduduk DESC, nama ASC
                    LIMIT ?
                """, (f"%{keyword_lower}%", f"%{keyword_lower}%", limit))

                for row in c.fetchall():
                    kode, nama, prov, lat, lng, luas, penduduk, level = row
                    hasil_raw.append({
                        'id': kode, 'kota': nama, 'kota_nama': nama,
                        'provinsi': prov or '', 'provinsi_nama': prov or '',
                        'lat': lat, 'lon': lng,
                        'luas': luas, 'penduduk': penduduk,
                        'level': level,
                        'geocoded': lat is not None and lng is not None,
                        'display': f"{nama}, {prov}" if prov else nama,
                        'name': f"{nama}, {prov}" if prov else nama,
                    })

            conn.close()
            if hasil_raw:
                print(f"✅ {len(hasil_raw)} kota dari DB wilayah_lengkap")
                return hasil_raw[:limit]
        except Exception as e:
            print(f"⚠️ DB error: {e}")

    # ===== PRIORITAS 2: KOORDINAT_KOTA manual =====
    for kunci, (lat, lon, display) in KOORDINAT_KOTA.items():
        if keyword_lower in kunci or kunci in keyword_lower:
            hasil_raw.append({
                'id': kunci,
                'kota': display.split(',')[0].strip(),
                'kota_nama': display.split(',')[0].strip(),
                'provinsi': display.split(',')[-1].strip() if ',' in display else '',
                'provinsi_nama': display.split(',')[-1].strip() if ',' in display else '',
                'lat': lat, 'lon': lon,
                'luas': None, 'penduduk': None, 'level': 2,
                'geocoded': True,
                'display': display, 'name': display,
            })

    if hasil_raw:
        print(f"✅ {len(hasil_raw)} kota dari KOORDINAT_KOTA manual")
        return hasil_raw[:limit]

    # ===== PRIORITAS 3: API EMSIFA =====
    try:
        all_kota = _load_semua_kota_online()
        for k in all_kota:
            if keyword_lower in k['kota'].lower() or keyword_lower in k['provinsi'].lower():
                k['kota_nama'] = k['kota']
                k['provinsi_nama'] = k['provinsi']
                k['name'] = k['display']
                k['geocoded'] = False
                hasil_raw.append(k)
                if len(hasil_raw) >= limit:
                    break
    except Exception:
        pass

    return hasil_raw[:limit]


# =========================================================
# Parse hasil Overpass
# =========================================================
def _parse_overpass_result(data, lat, lon, maks):
    hasil = []
    for el in data.get('elements', []):
        t = el.get('tags', {})
        if el['type'] == 'node':
            plat, plon = el.get('lat'), el.get('lon')
        else:
            center = el.get('center', {})
            plat, plon = center.get('lat'), center.get('lon')

        if not plat or not plon:
            continue

        nama = t.get('name', 'Tanpa nama')
        kategori_list = []
        for key in ['shop', 'amenity', 'craft', 'office', 'tourism']:
            if t.get(key):
                kategori_list.append(f"{key}={t[key]}")

        alamat_parts = [
            t.get('addr:street', ''),
            t.get('addr:city', ''),
        ]
        alamat = ", ".join([p for p in alamat_parts if p])

        R = 6371
        dlat = radians(plat - lat)
        dlon = radians(plon - lon)
        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(plat))*sin(dlon/2)**2
        jarak = 2 * R * atan2(sqrt(a), sqrt(1-a))

        hasil.append({
            'nama': nama,
            'kategori': ", ".join(kategori_list) if kategori_list else '-',
            'alamat': alamat if alamat else '-',
            'lat': plat, 'lon': plon,
            'jarak_km': round(jarak, 2),
            'kontak': t.get('phone', t.get('contact:phone', '-')),
            'jam_buka': t.get('opening_hours', '-'),
        })

    hasil.sort(key=lambda x: x['jarak_km'])
    return hasil[:maks]


# =========================================================
# SCAN — Multi-query fallback
# =========================================================
def scan_sekitar(lat, lon, radius_m=5000, keyword="kue", maks=50, retry=2, smart=True):
    """Scan POI + SMART FALLBACK (coba multi query)."""
    keyword_lower = keyword.lower()
    radius_km = radius_m / 1000

    # === 1. CACHE ===
    from backend.db.cache_db import get_cached, save_cache
    cached = get_cached(lat, lon, radius_km, keyword_lower)
    if cached:
        print(f"♻️ Cache hit: {cached['jumlah']} toko")
        return {'success': True, 'data': cached['data'][:maks],
                'error': '', 'from_cache': True, 'query_used': 'cache'}

    # === 2. BUILD QUERIES (dari simpel ke kompleks) ===
    queries = []

    # Query 1: SANGAT SIMPLE — semua shop/amenity di radius
    queries.append({
        'name': 'raw-all',
        'query': f"""[out:json][timeout:25];
(
  node["shop"](around:{radius_m},{lat},{lon});
  way["shop"](around:{radius_m},{lat},{lon});
  node["amenity"](around:{radius_m},{lat},{lon});
  way["amenity"](around:{radius_m},{lat},{lon});
);
out center {maks};"""
    })

    # Query 2: MEDIUM — pakai tag dari keyword
    if smart:
        try:
            from backend.modules.business_classifier import cari_konfigurasi_keyword
            config = cari_konfigurasi_keyword(keyword)
            tags = config.get('osm_tags', [])
        except Exception:
            tags = KEYWORD_TO_OSM.get(keyword_lower, [])
    else:
        tags = KEYWORD_TO_OSM.get(keyword_lower, [])

    if tags:
        tq = []
        for tag in tags:
            if '=' in tag:
                k, v = tag.split('=')
                tq.append(f'node["{k}"="{v}"](around:{radius_m},{lat},{lon});')
                tq.append(f'way["{k}"="{v}"](around:{radius_m},{lat},{lon});')
        if tq:
            queries.append({
                'name': f'tag-{keyword}',
                'query': f"""[out:json][timeout:25];
(
  {chr(10).join(tq)}
);
out center {maks};"""
            })

    # Query 3: BY NAME
    queries.append({
        'name': f'name-{keyword}',
        'query': f"""[out:json][timeout:25];
(
  node["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
  way["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
);
out center {maks};"""
    })

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass.osm.ch/api/interpreter",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # === 3. LOOP ===
    for q in queries:
        print(f"🔍 Query: {q['name']}")
        for attempt in range(retry):
            for endpoint in endpoints:
                try:
                    print(f"   → {endpoint.split('/')[2]}")
                    r = requests.post(endpoint, data={"data": q['query']},
                                       headers=headers, timeout=60)

                    if r.status_code == 200:
                        data = r.json()
                        raw = _parse_overpass_result(data, lat, lon, maks)
                        print(f"   ✅ {len(raw)} hasil")

                        # Smart filter
                        if smart and raw and q['name'] != 'raw-all':
                            try:
                                from backend.modules.business_classifier import filter_bisnis_smart
                                filtered = filter_bisnis_smart(raw, keyword, threshold=8)
                                final = filtered if filtered else raw
                            except Exception:
                                final = raw
                        else:
                            final = raw

                        if final:
                            save_cache(lat, lon, radius_km, keyword_lower, final)
                            return {'success': True, 'data': final,
                                    'error': '', 'from_cache': False,
                                    'query_used': q['name']}
                        break
                    elif r.status_code in [429, 504]:
                        sleep(3)
                        continue
                    else:
                        print(f"   ⚠️ Status {r.status_code}")
                        continue
                except Exception as e:
                    print(f"   ⚠️ {str(e)[:60]}")
                    continue

            if attempt < retry - 1:
                sleep(2)

    # === 4. FALLBACK KE CACHE LAMA ===
    old = get_cached(lat, lon, radius_km, keyword_lower, max_age_hours=8760)
    if old:
        return {'success': True, 'data': old['data'][:maks], 'error': '',
                'from_cache': True, 'query_used': 'old-cache'}

    return {
        'success': False, 'data': [],
        'error': 'Semua server Overpass tidak merespons atau tidak ada hasil.',
    }


# =========================================================
# ANALISIS PELUANG
# =========================================================
def _analisis_peluang_single(lat, lon, keyword, radius_km=5, kompetitor_list=None):
    hasil = {
        'lat': lat, 'lon': lon, 'keyword': keyword, 'radius_km': radius_km,
        'jumlah_kompetitor': 0, 'skor_peluang': None,
        'kompetitor': [], 'rekomendasi': '', 'status_data': '',
    }

    if kompetitor_list is not None:
        kompetitor = kompetitor_list
        hasil['status_data'] = f'♻️ Reuse {len(kompetitor)} toko'
    else:
        scan_result = scan_sekitar(lat, lon, radius_m=radius_km * 1000,
                                    keyword=keyword, maks=100)
        if not scan_result['success']:
            hasil['status_data'] = f'❌ GAGAL SCAN'
            hasil['skor_peluang'] = None
            hasil['rekomendasi'] = (
                '⚠️ **Data tidak tersedia** — Server Overpass API sedang rate limit.\n\n'
                '**Coba:**\n'
                '1. Tunggu 30-60 detik, klik lagi\n'
                '2. Ganti kota: pilih **KOTA** bukan **KABUPATEN**\n'
                '3. Ganti keyword ke: `restoran`, `cafe`, `toko`'
            )
            hasil['kategori'] = 'DATA TIDAK TERSEDIA'
            hasil['opportunity_score'] = None
            hasil['total_pesaing'] = 0
            hasil['competitors'] = []
            hasil['recommendation'] = hasil['rekomendasi']
            return hasil
        kompetitor = scan_result['data']
        hasil['status_data'] = f'🔍 Scan: {len(kompetitor)} toko'

    hasil['jumlah_kompetitor'] = len(kompetitor)
    hasil['kompetitor'] = kompetitor[:20]

    n = hasil['jumlah_kompetitor']
    if n == 0:
        hasil['skor_peluang'] = None
        hasil['rekomendasi'] = (
            '⚠️ **0 pesaing terdeteksi** — mungkin:\n'
            '- Data OpenStreetMap kurang lengkap\n'
            '- Rate limit server\n\n'
            '**Coba:** Klik "Scan Sekarang" dulu untuk verifikasi.'
        )
        hasil['kategori'] = 'PERLU VERIFIKASI'
    elif n <= 2:
        hasil['skor_peluang'] = 9
        hasil['rekomendasi'] = '🟢 BAIK — pesaing sedikit.'
        hasil['kategori'] = 'PELUANG BESAR'
    elif n <= 5:
        hasil['skor_peluang'] = 7
        hasil['rekomendasi'] = '🟡 CUKUP — masih bisa bersaing.'
        hasil['kategori'] = 'PELUANG SEDANG'
    elif n <= 10:
        hasil['skor_peluang'] = 5
        hasil['rekomendasi'] = '🟠 SEDANG — perlu diferensiasi.'
        hasil['kategori'] = 'PELUANG SEDANG'
    elif n <= 20:
        hasil['skor_peluang'] = 3
        hasil['rekomendasi'] = '🔴 SULIT — banyak pesaing.'
        hasil['kategori'] = 'PELUANG KECIL'
    else:
        hasil['skor_peluang'] = 1
        hasil['rekomendasi'] = '🔴 JENUH — pasar padat.'
        hasil['kategori'] = 'PELUANG KECIL'

    # Alias
    hasil['opportunity_score'] = hasil['skor_peluang']
    hasil['total_kompetitor'] = hasil['jumlah_kompetitor']
    hasil['total_pesaing'] = hasil['jumlah_kompetitor']
    hasil['total_competitors'] = hasil['jumlah_kompetitor']
    hasil['competitors'] = hasil['kompetitor']
    hasil['daftar_kompetitor'] = hasil['kompetitor']
    hasil['recommendation'] = hasil['rekomendasi']

    return hasil


def analisis_peluang(*args, **kwargs):
    """Analisis peluang — support 2 format."""
    if len(args) >= 3 and isinstance(args[0], (int, float)):
        return _analisis_peluang_single(
            float(args[0]), float(args[1]), str(args[2]),
            kwargs.get('radius_km', 5),
            kwargs.get('kompetitor_list', None)
        )
    elif len(args) >= 3 and isinstance(args[0], str):
        keyword = args[0]
        daftar_kota = args[1] if len(args) > 1 else []
        hasil = []
        for kota in daftar_kota[:kwargs.get('max_kota', 5)]:
            lat, lon = kota.get('lat'), kota.get('lon')
            if not lat or not lon:
                continue
            single = _analisis_peluang_single(lat, lon, keyword,
                                               kwargs.get('radius_km', 5))
            single['kota'] = kota.get('kota', '-')
            single['provinsi'] = kota.get('provinsi', '-')
            single['display'] = kota.get('display', '-')
            hasil.append(single)
        hasil.sort(key=lambda x: (-(x['skor_peluang'] or 0), x['jumlah_kompetitor']))
        return hasil
    else:
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            return _analisis_peluang_single(
                float(lat), float(lon), kwargs.get('keyword', 'kue'),
                kwargs.get('radius_km', 5),
                kwargs.get('kompetitor_list', None)
            )
        return []


# =========================================================
# MAIN — Test
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🗺️ TEST SCAN KOTA BANDUNG")
    print("=" * 60)

    lok = KOORDINAT_KOTA.get("bandung")
    if lok:
        print(f"📍 {lok[2]} — {lok[0]}, {lok[1]}")
        result = scan_sekitar(lok[0], lok[1], radius_m=5000, keyword="kue")
        print(f"\nSuccess: {result['success']}")
        print(f"Jumlah: {len(result.get('data', []))}")
        for i, t in enumerate(result.get('data', [])[:10], 1):
            print(f"{i}. {t['nama']} ({t['kategori']}) — {t['jarak_km']} km")