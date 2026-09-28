"""
maps_scanner.py
Scan lokasi/toko pakai Overpass API + cari kota.
"""
import requests
from time import sleep
from math import radians, sin, cos, sqrt, atan2
import sys
from pathlib import Path

from backend.db.cache_db import get_cached, save_cache
from backend.modules.business_classifier import (
    filter_bisnis_smart, expand_keyword, cari_konfigurasi_keyword
)

sys.path.insert(0, str(Path(__file__).parent))


# =========================================================
# KOORDINAT FALLBACK (48 KOTA BESAR)
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
    "sidoarjo": (-7.4478, 112.7183, "Kabupaten Sidoarjo"),
    "serang": (-6.1104, 106.1500, "Kota Serang"),
    "sukabumi": (-6.9277, 106.9300, "Kota Sukabumi"),
    "medan": (3.5952, 98.6722, "Kota Medan, Sumatera Utara"),
    "palembang": (-2.9761, 104.7754, "Kota Palembang"),
    "padang": (-0.9471, 100.4172, "Kota Padang"),
    "pekanbaru": (0.5071, 101.4478, "Kota Pekanbaru"),
    "banda aceh": (5.5483, 95.3238, "Kota Banda Aceh"),
    "batam": (1.0456, 104.0305, "Kota Batam"),
    "jambi": (-1.6101, 103.6131, "Kota Jambi"),
    "bengkulu": (-3.7928, 102.2608, "Kota Bengkulu"),
    "bandar lampung": (-5.3971, 105.2668, "Bandar Lampung"),
    "balikpapan": (-1.2379, 116.8529, "Kota Balikpapan"),
    "samarinda": (-0.5022, 117.1536, "Kota Samarinda"),
    "banjarmasin": (-3.3186, 114.5944, "Kota Banjarmasin"),
    "pontianak": (-0.0263, 109.3425, "Kota Pontianak"),
    "palangkaraya": (-2.2080, 113.9165, "Kota Palangka Raya"),
    "makassar": (-5.1477, 119.4327, "Kota Makassar"),
    "manado": (1.4748, 124.8421, "Kota Manado"),
    "palu": (-0.8917, 119.8707, "Kota Palu"),
    "kendari": (-3.9450, 122.4989, "Kota Kendari"),
    "gorontalo": (0.5435, 123.0568, "Kota Gorontalo"),
    "denpasar": (-8.6705, 115.2126, "Kota Denpasar, Bali"),
    "mataram": (-8.5833, 116.1167, "Kota Mataram"),
    "kupang": (-10.1772, 123.6070, "Kota Kupang"),
    "jayapura": (-2.5916, 140.6690, "Kota Jayapura"),
    "ambon": (-3.6954, 128.1814, "Kota Ambon"),
    "ternate": (0.7900, 127.3800, "Kota Ternate"),
    "sorong": (-0.8762, 131.2558, "Kota Sorong"),
    "cibadak": (-6.8846, 106.7894, "Cibadak, Kabupaten Sukabumi"),
    "cianjur": (-6.8168, 107.1425, "Kabupaten Cianjur"),
    "garut": (-7.2144, 107.9030, "Kabupaten Garut"),
    "tasikmalaya": (-7.3274, 108.2207, "Kota Tasikmalaya"),
    "purwokerto": (-7.4228, 109.2342, "Kabupaten Banyumas"),
        # Tambahan kota kecil/potensial
    "cibadak": (-6.8846, 106.7894, "Cibadak, Kabupaten Sukabumi"),
    "cianjur": (-6.8168, 107.1425, "Kabupaten Cianjur"),
    "garut": (-7.2144, 107.9030, "Kabupaten Garut"),
    "tasikmalaya": (-7.3274, 108.2207, "Kota Tasikmalaya"),
    "purwokerto": (-7.4228, 109.2342, "Kabupaten Banyumas"),
    "tegal": (-6.8694, 109.1402, "Kota Tegal"),
    "pekalongan": (-6.8886, 109.6753, "Kota Pekalongan"),
    "kudus": (-6.8048, 110.8405, "Kabupaten Kudus"),
    "jepara": (-6.5896, 110.6682, "Kabupaten Jepara"),
    "magelang": (-7.4797, 110.2177, "Kota Magelang"),
    "blitar": (-8.0955, 112.1610, "Kota Blitar"),
    "madiun": (-7.6298, 111.5239, "Kota Madiun"),
    "kediri": (-7.8480, 112.0178, "Kota Kediri"),
    "jember": (-8.1689, 113.7020, "Kabupaten Jember"),
    "banyuwangi": (-8.2192, 114.3691, "Kabupaten Banyuwangi"),
    "gresik": (-7.1560, 112.6553, "Kabupaten Gresik"),
    "mojokerto": (-7.4726, 112.4381, "Kota Mojokerto"),
    "pasuruan": (-7.6469, 112.9075, "Kota Pasuruan"),
    "probolinggo": (-7.7543, 113.2159, "Kota Probolinggo"),
    "bogor": (-6.5971, 106.8060, "Kota Bogor"),
    "sukabumi": (-6.9277, 106.9300, "Kota Sukabumi"),
    "bandung barat": (-6.8326, 107.4917, "Kabupaten Bandung Barat"),
    "subang": (-6.5716, 107.7583, "Kabupaten Subang"),
    "karawang": (-6.3227, 107.3375, "Kabupaten Karawang"),
    "purwakarta": (-6.5570, 107.4430, "Kabupaten Purwakarta"),
    "indramayu": (-6.3373, 108.3235, "Kabupaten Indramayu"),

        # === DKI Jakarta (5 Kotamadya) ===
    "jakarta pusat": (-6.1805, 106.8284, "Kota Jakarta Pusat, DKI Jakarta"),
    "jakarta selatan": (-6.2615, 106.8106, "Kota Jakarta Selatan, DKI Jakarta"),
    "jakarta barat": (-6.1686, 106.7588, "Kota Jakarta Barat, DKI Jakarta"),
    "jakarta timur": (-6.2250, 106.9004, "Kota Jakarta Timur, DKI Jakarta"),
    "jakarta utara": (-6.1214, 106.7741, "Kota Jakarta Utara, DKI Jakarta"),
    "kepulauan seribu": (-5.7500, 106.5833, "Kabupaten Kepulauan Seribu"),

    # === Kota Besar Tambahan ===
    "tangerang selatan": (-6.2884, 106.7179, "Kota Tangerang Selatan"),
    "bandung barat": (-6.8326, 107.4917, "Kabupaten Bandung Barat"),
    "kabupaten bandung": (-7.0500, 107.5171, "Kabupaten Bandung"),
    "kabupaten bogor": (-6.5586, 106.7876, "Kabupaten Bogor"),
    "kabupaten bekasi": (-6.3639, 107.1665, "Kabupaten Bekasi"),
    "kabupaten tangerang": (-6.2357, 106.5193, "Kabupaten Tangerang"),
    "kabupaten malang": (-8.0778, 112.6187, "Kabupaten Malang"),
    "kabupaten sukabumi": (-6.9277, 106.9300, "Kabupaten Sukabumi"),
    "kabupaten garut": (-7.2144, 107.9030, "Kabupaten Garut"),
    "kabupaten cianjur": (-6.8168, 107.1425, "Kabupaten Cianjur"),

    
}


# =========================================================
# Mapping keyword → tag OSM
# =========================================================
KEYWORD_TO_OSM = {
    "kue": ["shop=bakery", "shop=confectionery", "shop=pastry"],
    "toko kue": ["shop=bakery", "shop=confectionery"],
    "camilan": ["shop=confectionery", "shop=convenience"],
    "restoran": ["amenity=restaurant"],
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
}


# =========================================================
# Cache kota (dari API EMSIFA)
# =========================================================
_KOTA_CACHE = None


def _load_semua_kota_online():
    """Load semua kota dari EMSIFA. Cache di memory."""
    global _KOTA_CACHE
    if _KOTA_CACHE is not None:
        return _KOTA_CACHE

    print("🌐 Loading semua kota dari EMSIFA...")
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
                        'lat': None,
                        'lon': None,
                    })
            except Exception:
                continue

        print(f"✅ {len(semua_kota)} kota dimuat")
        _KOTA_CACHE = semua_kota
        return semua_kota
    except Exception as e:
        print(f"⚠️ Gagal load API: {e}")
        _KOTA_CACHE = []
        return []


# =========================================================
# cari_kota_lengkap — ANTI-CRASH
# =========================================================
def cari_kota_lengkap(keyword, limit=50):
    """
    Cari kota dari tabel `wilayah_lengkap` (514 kota + penduduk + luas).
    """
    import sqlite3
    from pathlib import Path

    keyword_lower = str(keyword).lower().strip()
    hasil_raw = []
    db_path = Path(__file__).parent.parent.parent / "market_intel.db"

    # === PRIORITAS 1: tabel wilayah_lengkap ===
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()

            # Cek tabel
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wilayah_lengkap'")
            if c.fetchone():
                c.execute("""
                    SELECT kode, nama, provinsi_nama, lat, lng, luas, penduduk, level
                    FROM wilayah_lengkap
                    WHERE LOWER(nama) LIKE ?
                       OR LOWER(provinsi_nama) LIKE ?
                    ORDER BY level DESC, penduduk DESC, nama ASC
                    LIMIT ?
                """, (f"%{keyword_lower}%", f"%{keyword_lower}%", limit))

                for row in c.fetchall():
                    kode, nama, prov, lat, lng, luas, penduduk, level = row
                    hasil_raw.append({
                        'id': kode,
                        'kota': nama,
                        'kota_nama': nama,
                        'provinsi': prov or '',
                        'provinsi_nama': prov or '',
                        'lat': lat, 'lon': lng,
                        'luas': luas,
                        'penduduk': penduduk,
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

    # === FALLBACK: KOORDINAT_KOTA manual ===
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

    return hasil_raw[:limit]

# =========================================================
# Geocode — pakai manual + fallback
# =========================================================
def geocode_lokasi(nama_lokasi):
    """Cari koordinat kota. Kalau di manual tidak ada, coba nominatim."""
    if not nama_lokasi:
        return None

    nama_lower = nama_lokasi.lower().strip()

    # Cek manual
    for kunci, (lat, lon, display) in KOORDINAT_KOTA.items():
        if kunci in nama_lower:
            return {'lat': lat, 'lon': lon, 'display': display}

    # Fallback ke Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{nama_lokasi}, Indonesia",
            "format": "json", "limit": 1, "countrycodes": "id",
        }
        headers = {
            "User-Agent": "MarketIntelApp/1.0 (contact@example.com)",
            "Accept-Language": "id-ID",
        }
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'display': data[0]['display_name']
                }
    except Exception as e:
        print(f"⚠️ Nominatim: {e}")

    return None


# =========================================================
# Scan sekitar (Overpass)
# =========================================================
# Daftar endpoint Overpass (5 server)
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def scan_sekitar(lat, lon, radius_m=5000, keyword="kue", maks=50, retry=2, smart=True):
    """Scan POI + SMART FALLBACK (query simpel dulu, baru kompleks)."""
    keyword_lower = keyword.lower()
    radius_km = radius_m / 1000

    # === 1. CACHE ===
    from backend.db.cache_db import get_cached, save_cache
    cached = get_cached(lat, lon, radius_km, keyword_lower)
    if cached:
        print(f"♻️ Cache hit: {cached['jumlah']} toko")
        return {'success': True, 'data': cached['data'][:maks], 'error': '',
                'from_cache': True}

    # === 2. DAFTAR QUERY — DARI SIMPEL KE KOMPLEKS ===
    queries = []

    # Query 1: SANGAT SIMPLE — semua shop/amenity di radius (raw)
    queries.append({
        'name': 'raw-all-shops',
        'query': f"""
[out:json][timeout:25];
(
  node["shop"](around:{radius_m},{lat},{lon});
  way["shop"](around:{radius_m},{lat},{lon});
  node["amenity"](around:{radius_m},{lat},{lon});
  way["amenity"](around:{radius_m},{lat},{lon});
);
out center {maks};
""".strip()
    })

    # Query 2: MEDIUM — pakai tag dari keyword
    if smart:
        try:
            from backend.modules.business_classifier import cari_konfigurasi_keyword
            config = cari_konfigurasi_keyword(keyword)
            tags = config.get('osm_tags', [])
        except:
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
                'query': f"""
[out:json][timeout:25];
(
  {chr(10).join(tq)}
);
out center {maks};
""".strip()
            })

    # Query 3: by name (paling akhir, untuk kasus khusus)
    queries.append({
        'name': f'name-{keyword}',
        'query': f"""
[out:json][timeout:25];
(
  node["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
  way["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
);
out center {maks};
""".strip()
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

    # === 3. LOOP: QUERY × ENDPOINT × RETRY ===
    for q in queries:
        print(f"🔍 Coba query: {q['name']}")
        for attempt in range(retry):
            for endpoint in endpoints:
                try:
                    print(f"   → {endpoint.split('/')[2]} (attempt {attempt+1})")
                    r = requests.post(endpoint, data={"data": q['query']},
                                       headers=headers, timeout=60)

                    if r.status_code == 200:
                        data = r.json()
                        raw = _parse_overpass_result(data, lat, lon, maks)
                        print(f"   ✅ {len(raw)} hasil mentah")

                        # Smart filter (kalau smart)
                        if smart and raw and q['name'] != 'raw-all-shops':
                            try:
                                from backend.modules.business_classifier import filter_bisnis_smart
                                filtered = filter_bisnis_smart(raw, keyword, threshold=8)
                                final = filtered if filtered else raw
                            except:
                                final = raw
                        else:
                            final = raw

                        if final:
                            save_cache(lat, lon, radius_km, keyword_lower, final)
                            return {'success': True, 'data': final, 'error': '',
                                    'from_cache': False, 'query_used': q['name']}

                        # Kalau 0 hasil, coba query berikutnya
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

    # === 4. SEMUA GAGAL ===
    return {
        'success': False,
        'data': [],
        'error': 'Semua server Overpass tidak merespons atau tidak ada hasil. '
                 'Coba: (1) Tunggu 60 detik, (2) Ganti kota lebih spesifik '
                 '(KOTA bukan KABUPATEN), (3) Ganti keyword ke restoran/cafe.',
    }


def _parse_overpass_result(data, lat, lon, maks):
    """Parse hasil Overpass."""
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
        kategori = [t[k] for k in ['shop', 'amenity', 'craft', 'office', 'tourism'] if t.get(k)]

        R = 6371
        dlat = radians(plat - lat)
        dlon = radians(plon - lon)
        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(plat))*sin(dlon/2)**2
        jarak = 2 * R * atan2(sqrt(a), sqrt(1-a))

        hasil.append({
            'nama': nama,
            'kategori': ", ".join(kategori) if kategori else '-',
            'alamat': t.get('addr:street', '-'),
            'lat': plat, 'lon': plon,
            'jarak_km': round(jarak, 2),
            'kontak': t.get('phone', t.get('contact:phone', '-')),
            'jam_buka': t.get('opening_hours', '-'),
        })

    hasil.sort(key=lambda x: x['jarak_km'])
    return hasil[:maks]


# =========================================================
# MAIN — Test
# =========================================================

# =========================================================
# Analisis Peluang — cari kota dengan kompetitor sedikit
# =========================================================
# =========================================================
# Analisis Peluang — FLEKSIBEL (bisa 2 format)
# =========================================================
def analisis_peluang(*args, **kwargs):
    """
    Analisis peluang buka outlet. Support 2 format:
    
    Format A (multi-kota):
        analisis_peluang("kue", daftar_kota, radius_km=5, max_kota=5)
    
    Format B (single lokasi):
        analisis_peluang(lat, lon, "kue", radius_km=5)
    """
    # Deteksi format
    if len(args) >= 3 and isinstance(args[0], str):
        # === Format A: keyword, daftar_kota ===
        keyword = args[0]
        daftar_kota = args[1] if len(args) > 1 else []
        radius_km = kwargs.get('radius_km', 5)
        max_kota = kwargs.get('max_kota', 5)
        return _analisis_peluang_multi(keyword, daftar_kota, radius_km, max_kota)

    elif len(args) >= 3 and isinstance(args[0], (int, float)):
        # === Format B: lat, lon, keyword ===
        lat = float(args[0])
        lon = float(args[1])
        keyword = str(args[2])
        radius_km = kwargs.get('radius_km', 5)
        return _analisis_peluang_single(lat, lon, keyword, radius_km)

    else:
        # Fallback: baca dari kwargs
        keyword = kwargs.get('keyword', 'kue')
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            return _analisis_peluang_single(float(lat), float(lon), keyword, kwargs.get('radius_km', 5))
        return []


def _analisis_peluang_single(lat, lon, keyword, radius_km=5, kompetitor_list=None):
    """Analisis peluang. Deteksi kalau data tidak tersedia."""
    hasil = {
        'lat': lat, 'lon': lon, 'keyword': keyword, 'radius_km': radius_km,
        'jumlah_kompetitor': 0, 'skor_peluang': None,
        'kompetitor': [], 'rekomendasi': '', 'status_data': '',
    }

    # === Ambil data kompetitor ===
    if kompetitor_list is not None:
        # Reuse
        kompetitor = kompetitor_list
        hasil['status_data'] = f'♻️ Reuse {len(kompetitor)} toko dari scan sebelumnya'
    else:
        # Scan baru
        scan_result = scan_sekitar(lat, lon, radius_m=radius_km * 1000,
                                    keyword=keyword, maks=100)
        if not scan_result['success']:
            hasil['status_data'] = f'❌ GAGAL SCAN: {scan_result["error"]}'
            hasil['skor_peluang'] = None
            hasil['rekomendasi'] = (
                '⚠️ **Data tidak tersedia** — Server Overpass API sedang rate limit.\n\n'
                '**Coba:**\n'
                '1. Tunggu 30-60 detik, klik Analisis lagi\n'
                '2. Klik "Scan Sekarang" dulu, baru "Analisis Peluang"\n'
                '3. Ganti keyword ke: `restoran`, `cafe`, `toko`'
            )
            hasil['kategori'] = 'DATA TIDAK TERSEDIA'
            # Set alias
            hasil['opportunity_score'] = None
            hasil['total_pesaing'] = 0
            hasil['competitors'] = []
            hasil['recommendation'] = hasil['rekomendasi']
            return hasil

        kompetitor = scan_result['data']
        hasil['status_data'] = f'🔍 Scan baru: {len(kompetitor)} toko ditemukan'

    hasil['jumlah_kompetitor'] = len(kompetitor)
    hasil['kompetitor'] = kompetitor[:20]

    n = hasil['jumlah_kompetitor']
    if n == 0:
        # ⚠️ 0 hasil — bisa rate limit atau benar kosong
        hasil['skor_peluang'] = None
        hasil['rekomendasi'] = (
            '⚠️ **0 pesaing terdeteksi** — TAPI ini mungkin karena:\n'
            '- Data OpenStreetMap kurang lengkap di area ini\n'
            '- Rate limit server (coba lagi 30 detik)\n'
            '- Keyword tidak sesuai\n\n'
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
    hasil['total_pesaing'] = hasil['jumlah_kompetitor']
    hasil['competitors'] = hasil['kompetitor']
    hasil['recommendation'] = hasil['rekomendasi']

    return hasil


def analisis_peluang(*args, **kwargs):
    """
    Analisis peluang buka outlet. Support 2 format + opsi reuse.

    Format A: analisis_peluang("kue", daftar_kota, radius_km=5)
    Format B: analisis_peluang(lat, lon, "kue", radius_km=5, kompetitor_list=[...])
    """
    if len(args) >= 3 and isinstance(args[0], str):
        keyword = args[0]
        daftar_kota = args[1] if len(args) > 1 else []
        return _analisis_peluang_multi(keyword, daftar_kota,
                                        kwargs.get('radius_km', 5),
                                        kwargs.get('max_kota', 5))
    elif len(args) >= 3 and isinstance(args[0], (int, float)):
        return _analisis_peluang_single(
            float(args[0]), float(args[1]), str(args[2]),
            kwargs.get('radius_km', 5),
            kwargs.get('kompetitor_list', None)  # NEW
        )
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


def _analisis_peluang_multi(keyword, daftar_kota, radius_km=5, max_kota=5):
    """Analisis peluang untuk banyak kota."""
    hasil = []

    for kota in daftar_kota[:max_kota]:
        lat = kota.get('lat')
        lon = kota.get('lon')
        if not lat or not lon:
            continue

        single = _analisis_peluang_single(lat, lon, keyword, radius_km)
        single['kota'] = kota.get('kota', '-')
        single['provinsi'] = kota.get('provinsi', '-')
        single['display'] = kota.get('display', '-')
        hasil.append(single)

    hasil.sort(key=lambda x: (-x['skor_peluang'], x['jumlah_kompetitor']))
    return hasil

if __name__ == "__main__":
    print("=" * 60)
    print("🗺️ MAPS SCANNER — Test")
    print("=" * 60)

    # Test cari kota kecil
    for kw in ["bandung", "cibadak", "sukabumi", "cianjur"]:
        print(f"\n🔍 Cari '{kw}'...")
        hasil = cari_kota_lengkap(kw, limit=3)
        if hasil:
            for h in hasil:
                print(f"   ✅ {h['display']} — lat: {h['lat']}, lon: {h['lon']}")
        else:
            print(f"   ❌ Tidak ada")