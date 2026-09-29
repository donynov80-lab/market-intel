"""
maps_scanner.py
Scan lokasi/toko pakai Overpass API + Smart Classifier + Cache.

Update terbaru:
- KEYWORD_TO_OSM diperkaya dengan 80+ sinonim Indonesia (termasuk "miras")
- Query 1 menggunakan regex multi-tag dari classifier (cari_osm_filter_dari_keyword)
- Limit raw-all dinaikkan 100 -> 300 supaya toko langka seperti miras tidak ke-skip
"""
import requests
from time import sleep
from math import radians, sin, cos, sqrt, atan2
import sys
from pathlib import Path
# === FIX: paksa print langsung flush ke stdout (biar muncul di Streamlit Cloud logs) ===
import functools
print = functools.partial(print, flush=True)

# Setup path: tambahkan ROOT project (market-intel/) dan folder ini
_THIS_DIR = Path(__file__).resolve().parent           # .../backend/modules
_PROJECT_ROOT = _THIS_DIR.parent.parent                # .../market-intel
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_THIS_DIR))


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


KEYWORD_TO_OSM = {
    # ============ MAKANAN & KUE ============
    "kue": ["shop=bakery", "shop=confectionery", "shop=pastry"],
    "toko kue": ["shop=bakery", "shop=confectionery"],
    "roti": ["shop=bakery"],
    "bolu": ["shop=bakery", "shop=confectionery"],
    "camilan": ["shop=confectionery", "shop=convenience"],
    "snack": ["shop=confectionery"],
    "martabak": ["amenity=fast_food", "amenity=restaurant"],
    "es krim": ["amenity=ice_cream", "shop=ice_cream"],
    "ice cream": ["amenity=ice_cream", "shop=ice_cream"],

    # ============ RESTORAN & KAFE ============
    "restoran": ["amenity=restaurant"],
    "resto": ["amenity=restaurant"],
    "rumah makan": ["amenity=restaurant"],
    "warung": ["amenity=fast_food", "shop=convenience"],
    "makanan": ["amenity=restaurant", "amenity=fast_food"],
    "bakso": ["amenity=restaurant", "amenity=fast_food"],
    "sate": ["amenity=restaurant"],
    "nasi": ["amenity=restaurant"],
    "ayam": ["amenity=restaurant", "amenity=fast_food"],
    "seafood": ["amenity=restaurant"],
    "pizza": ["amenity=restaurant", "amenity=fast_food"],
    "burger": ["amenity=fast_food"],
    "cafe": ["amenity=cafe"],
    "kafe": ["amenity=cafe"],
    "kopi": ["amenity=cafe", "shop=coffee"],
    "coffee": ["amenity=cafe", "shop=coffee"],
    "kedai kopi": ["amenity=cafe"],
    "teh": ["amenity=cafe", "shop=tea"],
    "jus": ["amenity=juice_bar", "amenity=cafe"],
    "catering": ["amenity=catering"],

    # ============ MINUMAN BERALKOHOL / MIRAS ============
    "miras": ["shop=alcohol", "shop=wine", "shop=beverages", "amenity=bar", "amenity=pub"],
    "minuman keras": ["shop=alcohol", "shop=wine", "amenity=bar", "amenity=pub"],
    "alkohol": ["shop=alcohol", "shop=wine", "amenity=bar", "amenity=pub"],
    "arak": ["shop=alcohol", "shop=wine"],
    "wine": ["shop=wine", "shop=alcohol"],
    "anggur": ["shop=wine"],
    "bir": ["shop=alcohol", "shop=beverages"],
    "whisky": ["shop=alcohol"],
    "bar": ["amenity=bar", "amenity=pub"],
    "pub": ["amenity=pub", "amenity=bar"],
    "nightclub": ["amenity=nightclub"],
    "klub malam": ["amenity=nightclub"],
    "minuman": ["amenity=cafe", "amenity=bar", "shop=beverages"],
    "beverages": ["shop=beverages"],

    # ============ RETAIL UMUM ============
    "kelontong": ["shop=convenience"],
    "sembako": ["shop=convenience", "shop=supermarket"],
    "supermarket": ["shop=supermarket"],
    "minimarket": ["shop=convenience"],
    "toko": ["shop=convenience", "shop=supermarket"],
    "pasar": ["amenity=marketplace"],
    "frozen food": ["shop=frozen_food", "shop=convenience"],
    "buah": ["shop=greengrocer"],
    "sayur": ["shop=greengrocer"],
    "daging": ["shop=butcher"],

    # ============ FASHION ============
    "baju": ["shop=clothes", "shop=boutique"],
    "pakaian": ["shop=clothes"],
    "sepatu": ["shop=shoes"],
    "tas": ["shop=bags"],
    "perhiasan": ["shop=jewelry"],
    "emas": ["shop=jewelry"],
    "optik": ["shop=optician"],

    # ============ KESEHATAN ============
    "apotek": ["amenity=pharmacy", "shop=chemist"],
    "apotik": ["amenity=pharmacy"],
    "obat": ["amenity=pharmacy", "shop=chemist"],
    "klinik": ["amenity=clinic", "amenity=doctors"],
    "rumah sakit": ["amenity=hospital"],
    "dokter": ["amenity=doctors"],
    "dokter gigi": ["amenity=dentist"],
    "bidan": ["amenity=clinic"],
    "veterinary": ["amenity=veterinary"],

    # ============ OTOMOTIF ============
    "bengkel": ["shop=car_repair", "shop=motorcycle_repair"],
    "bengkel mobil": ["shop=car_repair"],
    "bengkel motor": ["shop=motorcycle_repair"],
    "sparepart": ["shop=car_parts", "shop=motorcycle_parts"],
    "suku cadang": ["shop=car_parts"],
    "dealer mobil": ["shop=car"],
    "dealer motor": ["shop=motorcycle"],
    "jual mobil": ["shop=car"],
    "jual motor": ["shop=motorcycle"],
    "cuci mobil": ["amenity=car_wash"],
    "car wash": ["amenity=car_wash"],
    "ban": ["shop=tyres"],
    "spbu": ["amenity=fuel"],

    # ============ JASA KECANTIKAN & KEBERSIHAN ============
    "salon": ["shop=hairdresser", "shop=beauty"],
    "barbershop": ["shop=hairdresser"],
    "pangkas": ["shop=hairdresser"],
    "spa": ["shop=massage", "leisure=spa"],
    "pijat": ["shop=massage"],
    "laundry": ["shop=laundry", "shop=dry_cleaning"],
    "penatu": ["shop=laundry", "shop=dry_cleaning"],

    # ============ PENDIDIKAN ============
    "sekolah": ["amenity=school"],
    "kursus": ["amenity=language_school", "amenity=driving_school"],
    "bimbel": ["amenity=school", "amenity=prep_school"],
    "les": ["amenity=prep_school"],
    "universitas": ["amenity=university", "amenity=college"],
    "kampus": ["amenity=university", "amenity=college"],
    "paud": ["amenity=kindergarten"],

    # ============ JASA PROFESIONAL ============
    "kantor": ["office"],
    "pengacara": ["office=lawyer"],
    "notaris": ["office=lawyer", "office=notary"],
    "akuntan": ["office=accountant"],
    "konsultan": ["office=consulting"],
    "arsitek": ["office=architect"],
    "travel": ["shop=travel_agency", "office=travel_agent"],
    "agen travel": ["shop=travel_agency", "office=travel_agent"],

    # ============ WISATA & AKOMODASI ============
    "hotel": ["tourism=hotel"],
    "penginapan": ["tourism=hotel", "tourism=guest_house", "tourism=hostel"],
    "villa": ["tourism=chalet", "tourism=guest_house"],
    "homestay": ["tourism=guest_house"],
    "hostel": ["tourism=hostel"],
    "wisata": ["tourism=attraction", "tourism=theme_park"],
    "museum": ["tourism=museum"],
    "masjid": ["amenity=place_of_worship"],
    "gereja": ["amenity=place_of_worship"],

    # ============ OLAHRAGA ============
    "gym": ["leisure=fitness_centre"],
    "fitness": ["leisure=fitness_centre"],
    "kolam renang": ["leisure=swimming_pool", "leisure=sports_centre"],
    "stadion": ["leisure=stadium"],
    "bioskop": ["amenity=cinema"],
    "karaoke": ["amenity=nightclub"],

    # ============ LAIN-LAIN ============
    "buku": ["shop=books"],
    "mainan": ["shop=toys"],
    "elektronik": ["shop=electronics"],
    "hp": ["shop=mobile_phone"],
    "handphone": ["shop=mobile_phone"],
    "komputer": ["shop=computer"],
    "bangunan": ["shop=hardware", "shop=doityourself"],
    "material": ["shop=hardware", "shop=doityourself"],
    "cat": ["shop=paint"],
    "mebel": ["shop=furniture"],
    "furniture": ["shop=furniture"],
    "bunga": ["shop=florist"],
    "pet shop": ["shop=pet"],
    "toko hewan": ["shop=pet"],
    "masjid_besar": ["amenity=place_of_worship"],
    "bank": ["amenity=bank"],
    "fotokopi": ["shop=copyshop"],
    "percetakan": ["shop=copyshop", "craft=printer"],
    "toko emas": ["shop=jewelry"],
}


KATEGORI_KE_KEYWORD = {
    "semua": "toko", "makanan": "restoran", "minuman": "minuman",
    "retail": "sembako", "kesehatan": "apotek", "pendidikan": "buku",
    "otomotif": "bengkel", "jasa": "salon", "wisata": "hotel",
    "olahraga": "cafe", "miras": "miras",
}


_KOTA_CACHE = None


def _load_semua_kota_online():
    global _KOTA_CACHE
    if _KOTA_CACHE is not None:
        return _KOTA_CACHE
    try:
        r = requests.get("https://www.emsifa.com/api-wilayah-indonesia/api/provinces.json", timeout=10)
        provinsi_list = r.json()
        semua_kota = []
        for prov in provinsi_list:
            try:
                r2 = requests.get(f"https://www.emsifa.com/api-wilayah-indonesia/api/regencies/{prov['id']}.json", timeout=5)
                for kota in r2.json():
                    semua_kota.append({
                        'id': kota['id'], 'provinsi': prov['name'],
                        'kota': kota['name'],
                        'display': f"{kota['name']}, {prov['name']}",
                        'lat': None, 'lon': None,
                    })
            except Exception:
                continue
        _KOTA_CACHE = semua_kota
        return semua_kota
    except Exception:
        _KOTA_CACHE = []
        return []


def cari_kota_lengkap(keyword, limit=50):
    import sqlite3

    keyword_lower = str(keyword).lower().strip()
    hasil_raw = []
    db_path = Path(__file__).parent.parent.parent / "market_intel.db"

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
                        'lat': lat, 'lon': lng, 'luas': luas, 'penduduk': penduduk,
                        'level': level,
                        'geocoded': lat is not None and lng is not None,
                        'display': f"{nama}, {prov}" if prov else nama,
                        'name': f"{nama}, {prov}" if prov else nama,
                    })
            conn.close()
            if hasil_raw:
                return hasil_raw[:limit]
        except Exception:
            pass

    for kunci, (lat, lon, display) in KOORDINAT_KOTA.items():
        if keyword_lower in kunci or kunci in keyword_lower:
            hasil_raw.append({
                'id': kunci, 'kota': display.split(',')[0].strip(),
                'kota_nama': display.split(',')[0].strip(),
                'provinsi': display.split(',')[-1].strip() if ',' in display else '',
                'provinsi_nama': display.split(',')[-1].strip() if ',' in display else '',
                'lat': lat, 'lon': lon, 'luas': None, 'penduduk': None, 'level': 2,
                'geocoded': True, 'display': display, 'name': display,
            })
    if hasil_raw:
        return hasil_raw[:limit]

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


# =====================================================================
# ENRICHMENT KBLI
# =====================================================================
def _enrich_dengan_kbli(businesses, prefer_level=4):
    if not businesses:
        return businesses
    try:
        from backend.modules.business_classifier import get_classifier
        clf = get_classifier(prefer_level=prefer_level)
    except Exception as e:
        print(f"[Enrich] Classifier tidak tersedia: {e}")
        for b in businesses:
            b.setdefault('code_4digit', None)
            b.setdefault('subgolongan_title', None)
        return businesses

    for b in businesses:
        kat_str = b.get('kategori', '') or ''
        tags = [t.strip() for t in kat_str.split(',') if '=' in t]
        # fallback: pakai 'name' kalau 'nama' kosong
        nama = b.get('nama') or b.get('name') or ''
        try:
            cls = clf.classify(name=nama, tags=tags)
            hier = cls.get('hierarchy') or {}
            sub = hier.get('subgol') or {}
            gol = hier.get('gol') or {}
            b['code_2digit'] = cls.get('code_2digit')
            b['code_3digit'] = cls.get('code_3digit')
            b['code_4digit'] = cls.get('code_4digit')
            b['code_5digit'] = cls.get('code_5digit')
            b['kbli_title'] = cls.get('title')
            b['kbli_source'] = cls.get('source')
            b['kbli_confidence'] = cls.get('confidence', 0.0)
            # === FIX: subgolongan_title — 3 lapis fallback ===
            subgol_title = None
            if isinstance(sub, dict):
                subgol_title = sub.get('title')
            if not subgol_title:
                subgol_title = cls.get('title')  # fallback ke title KBLI
            b['subgolongan_title'] = subgol_title or '-'
            b['golongan_title'] = (
                gol.get('title') if isinstance(gol, dict) else None
            ) or '-'
        except Exception as e:
            print(f"[Enrich] Gagal klasifikasi '{nama}': {e}")
            b.setdefault('code_4digit', None)
            b.setdefault('subgolongan_title', '-')
    return businesses


def group_by_subgolongan(businesses):
    groups = {}
    for b in businesses or []:
        code = b.get('code_4digit') or 'UNCLASSIFIED'
        if code not in groups:
            groups[code] = {
                'code_4digit': code,
                'title': b.get('subgolongan_title') or 'Tidak terklasifikasi',
                'count': 0, 'businesses': [],
            }
        groups[code]['count'] += 1
        groups[code]['businesses'].append(b)
    return groups


# =====================================================================
# PARSER
# =====================================================================
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
        for key in ['shop', 'amenity', 'craft', 'office', 'tourism', 'leisure']:
            if t.get(key):
                kategori_list.append(f"{key}={t[key]}")

        alamat_parts = [t.get('addr:street', ''), t.get('addr:city', '')]
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


# =====================================================================
# SCAN UTAMA (diperbaiki)
# =====================================================================
def scan_sekitar(lat, lon, radius_m=5000, keyword="kue", maks=50, retry=2, smart=True):
    keyword_lower = keyword.lower().strip()
    radius_km = radius_m / 1000

    from backend.db.cache_db import get_cached, save_cache
    cached = get_cached(lat, lon, radius_km, keyword_lower)
    if cached:
        data = _enrich_dengan_kbli(cached['data'][:maks])
        return {'success': True, 'data': data,
                'error': '', 'from_cache': True, 'query_used': 'cache'}

    # === BUILD QUERIES ===
    queries = []

    # ---------- Query 1: TAG dari classifier (paling pintar) ----------
    osm_filter: Dict[str, str] = {}
    try:
        from backend.modules.business_classifier import cari_osm_filter_dari_keyword
        osm_filter = cari_osm_filter_dari_keyword(keyword) or {}
    except Exception as e:
        print(f"[Scan] Classifier tidak tersedia: {e}")

    # Fallback: pakai KEYWORD_TO_OSM lokal
    if not osm_filter:
        local_tags = KEYWORD_TO_OSM.get(keyword_lower, [])
        for tag in local_tags:
            if "=" in tag:
                k, v = tag.split("=", 1)
                if k in osm_filter:
                    osm_filter[k] = osm_filter[k] + "|" + v
                else:
                    osm_filter[k] = v

    if osm_filter:
        tq = []
        for k, v in osm_filter.items():
            # Split pipe jadi OR-statement LANGSUNG (tanpa regex — jauh lebih cepat)
            for val in str(v).split("|"):
                val = val.strip()
                if not val:
                    continue
                # 'nwr' = node + way + relation, lebih clean & cepat
                tq.append(f'nwr["{k}"="{val}"](around:{radius_m},{lat},{lon});')
        if tq:
            queries.append({
                'name': f'osm-filter-{keyword}',
                'query': f"""[out:json][timeout:90];
(
{chr(10).join(tq)}
);
out center 500;"""
            })

    # ---------- Query 2: BY NAME (fallback) ----------
    queries.append({
        'name': f'name-{keyword}',
        'query': f"""[out:json][timeout:60];
(
  node["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
  way["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
);
out center {maks};"""
    })

    # ---------- Query 3: RAW-ALL (naikkan limit 100 -> 300) ----------
    queries.append({
        'name': 'raw-all',
        'query': f"""[out:json][timeout:60];
(
  node["shop"](around:{radius_m},{lat},{lon});
  way["shop"](around:{radius_m},{lat},{lon});
  node["amenity"](around:{radius_m},{lat},{lon});
  way["amenity"](around:{radius_m},{lat},{lon});
  node["craft"](around:{radius_m},{lat},{lon});
  way["craft"](around:{radius_m},{lat},{lon});
);
out center 300;"""
    })

    endpoints = [
        # Diurut dari yang PALING stabil
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass.osm.ch/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    # Timeout lebih longgar: Streamlit Cloud → server Eropa butuh waktu
    HTTP_TIMEOUT = 120

    headers = {
        "User-Agent": "MarketIntelDashboard/1.0 (contact: donynov80@gmail.com)",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for q in queries:
        print(f"🔍 Query: {q['name']}")
        for attempt in range(retry):
            for endpoint in endpoints:
                try:
                    r = requests.post(endpoint, data={"data": q['query']},
                                       headers=headers, timeout=HTTP_TIMEOUT)
                    if r.status_code == 200:
                        data = r.json()
                        raw = _parse_overpass_result(data, lat, lon, maks)

                        # Filter smart — threshold DINAMIS per jenis query
                        #   osm-filter-*  -> query sudah presisi, threshold rendah (4)
                        #   name-*        -> sedang (6)
                        #   raw-all       -> semua shop/amenity, threshold tinggi (7)
                        #   jika raw < 5  -> turunkan 2 poin (longgarkan)
                        qname = q['name']
                        if qname.startswith('osm-filter'):
                            threshold = 4
                        elif qname.startswith('name-'):
                            threshold = 6
                        else:  # raw-all
                            threshold = 7
                        if len(raw) < 5:
                            threshold = max(2, threshold - 2)

                        if smart and raw:
                            try:
                                from backend.modules.business_classifier import filter_bisnis_smart
                                filtered = filter_bisnis_smart(raw, keyword, threshold=threshold)
                                print(f"      [filter] threshold={threshold}, raw={len(raw)}, lolos={len(filtered)}")
                                final = filtered
                            except Exception as e:
                                print(f"   Filter error: {e}")
                                final = []
                        else:
                            final = raw

                        # Fallback: query osm-filter sudah presisi, kalau filter buang semua
                        # lebih baik pakai raw daripada dapat 0
                        if (not final) and raw and qname.startswith('osm-filter'):
                            print(f"      [fallback] filter buang semua -> pakai raw (query presisi)")
                            final = raw

                        print(f"   ✅ {len(raw)} mentah → {len(final)} setelah filter")

                        if final:
                            final = _enrich_dengan_kbli(final)
                            save_cache(lat, lon, radius_km, keyword_lower, final)
                            return {'success': True, 'data': final,
                                    'error': '', 'from_cache': False,
                                    'query_used': q['name'],
                                    'total_raw': len(raw)}
                        break
                    elif r.status_code in [429, 504]:
                        sleep(3)
                        continue
                except Exception as e:
                    print(f"   ⚠️ {str(e)[:60]}")
                    continue

            if attempt < retry - 1:
                sleep(2)

    old = get_cached(lat, lon, radius_km, keyword_lower, max_age_hours=8760)
    if old:
        data = _enrich_dengan_kbli(old['data'][:maks])
        return {'success': True, 'data': data,
                'error': '', 'from_cache': True, 'query_used': 'old-cache'}

    return {
        'success': False, 'data': [],
        'error': f'Tidak ada "{keyword}" di area ini. Coba keyword lain atau kota lain.',
    }


# =====================================================================
# ANALISIS PELUANG (existing)
# =====================================================================
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
            hasil['status_data'] = '❌ GAGAL SCAN'
            hasil['rekomendasi'] = f'⚠️ {scan_result["error"]}'
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
        hasil['rekomendasi'] = '⚠️ 0 pesaing terdeteksi. Coba "Scan Sekarang" dulu.'
        hasil['kategori'] = 'PERLU VERIFIKASI'
    elif n <= 2:
        hasil['skor_peluang'] = 9
        hasil['rekomendasi'] = '🟢 BAIK — pesaing sedikit.'
        hasil['kategori'] = 'PELUANG BESAR'
    elif n <= 5:
        hasil['skor_peluang'] = 7
        hasil['rekomendasi'] = '🟡 CUKUP.'
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
        hasil['rekomendasi'] = '🔴 JENUH.'
        hasil['kategori'] = 'PELUANG KECIL'

    hasil['opportunity_score'] = hasil['skor_peluang']
    hasil['total_kompetitor'] = hasil['jumlah_kompetitor']
    hasil['total_pesaing'] = hasil['jumlah_kompetitor']
    hasil['competitors'] = hasil['kompetitor']
    hasil['recommendation'] = hasil['rekomendasi']
    return hasil


def analisis_peluang(*args, **kwargs):
    if len(args) >= 3 and isinstance(args[0], (int, float)):
        return _analisis_peluang_single(
            float(args[0]), float(args[1]), str(args[2]),
            kwargs.get('radius_km', 5), kwargs.get('kompetitor_list', None))
    elif len(args) >= 3 and isinstance(args[0], str):
        keyword = args[0]
        daftar_kota = args[1] if len(args) > 1 else []
        hasil = []
        for kota in daftar_kota[:kwargs.get('max_kota', 5)]:
            lat, lon = kota.get('lat'), kota.get('lon')
            if not lat or not lon:
                continue
            single = _analisis_peluang_single(lat, lon, keyword, kwargs.get('radius_km', 5))
            single['kota'] = kota.get('kota', '-')
            single['provinsi'] = kota.get('provinsi', '-')
            hasil.append(single)
        hasil.sort(key=lambda x: (-(x['skor_peluang'] or 0), x['jumlah_kompetitor']))
        return hasil
    else:
        lat = kwargs.get('lat'); lon = kwargs.get('lon')
        if lat and lon:
            return _analisis_peluang_single(float(lat), float(lon),
                kwargs.get('keyword', 'kue'), kwargs.get('radius_km', 5),
                kwargs.get('kompetitor_list', None))
        return []


# =====================================================================
# ADAPTER CLASS
# =====================================================================
class MapsScanner:
    def scan(self, lat, lon, radius=1000, kategori="semua"):
        keyword = KATEGORI_KE_KEYWORD.get(kategori, "toko")
        hasil = scan_sekitar(lat, lon, radius_m=radius, keyword=keyword, maks=200)
        data = hasil.get('data', []) or []
        return {
            'success': hasil.get('success', False),
            'count': len(data),
            'businesses': data,
            'by_subgolongan': group_by_subgolongan(data),
            'error': hasil.get('error', ''),
            'from_cache': hasil.get('from_cache', False),
            'query_used': hasil.get('query_used', ''),
        }

    def scan_dan_filter_miras(self, lat, lon, radius=1000):
        hasil = self.scan(lat, lon, radius, kategori="miras")
        if not hasil['success']:
            return hasil
        hasil['businesses'] = [
            b for b in hasil['businesses'] if b.get('code_4digit') == "4722"
        ]
        hasil['count'] = len(hasil['businesses'])
        hasil['by_subgolongan'] = group_by_subgolongan(hasil['businesses'])
        return hasil


# =====================================================================
# Quick test
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MAPS SCANNER - SELF TEST (miras fix)")
    print("=" * 60)

    # Test classifier: "miras" -> filter
    from backend.modules.business_classifier import cari_osm_filter_dari_keyword
    for kw in ["miras", "kue", "bengkel", "apotek"]:
        print(f"\n'{kw}' -> {cari_osm_filter_dari_keyword(kw)}")

    # Test scan miras di Jakarta Selatan
    print("\n" + "=" * 60)
    print("Scan 'miras' di Jakarta Selatan (-6.2615, 106.8106)")
    print("=" * 60)
    hasil = scan_sekitar(lat=-6.2615, lon=106.8106, radius_m=3000,
                          keyword="miras", maks=50)
    print(f"Success={hasil['success']}, N={len(hasil.get('data', []))}, "
          f"query={hasil.get('query_used')}")
    if hasil['success']:
        for b in hasil['data'][:10]:
            print(f"  • {b['nama']:35} | {b.get('code_4digit')} | "
                  f"{(b.get('subgolongan_title') or '')[:40]}")