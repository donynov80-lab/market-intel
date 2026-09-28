"""
business_classifier.py
Smart Business Classifier — pahami konteks bisnis dari nama + tag + deskripsi.
Ide: user cari "miras", tapi toko bernama "Outlet 23" harus tetap ketemu.
"""
from rapidfuzz import fuzz, process

# =========================================================
# KAMUS SINONIM BISNIS (bisa ditambah terus)
# =========================================================
KAMUS_BISNIS = {
    # === MAKANAN & MINUMAN ===
    "kue": {
        "sinonim": ["cake", "pastry", "bakery", "roti", "bolu", "tart", "donat", "brownies"],
        "osm_tags": ["shop=bakery", "shop=confectionery", "shop=pastry"],
        "kata_kunci_nama": ["kue", "cake", "bakery", "roti", "pastry", "boulangerie"],
    },
    "camilan": {
        "sinonim": ["snack", "keripik", "cemilan", "gorengan"],
        "osm_tags": ["shop=confectionery", "shop=convenience"],
        "kata_kunci_nama": ["snack", "camilan", "cemilan", "keripik"],
    },
    "restoran": {
        "sinonim": ["resto", "warung makan", "rumah makan", "kedai", "food court"],
        "osm_tags": ["amenity=restaurant", "amenity=fast_food"],
        "kata_kunci_nama": ["resto", "restoran", "warung", "kedai", "rm ", "food"],
    },
    "cafe": {
        "sinonim": ["kafe", "coffee shop", "kopi", "kedai kopi", "coffee"],
        "osm_tags": ["amenity=cafe"],
        "kata_kunci_nama": ["cafe", "kafe", "coffee", "kopi"],
    },
    "minuman": {
        "sinonim": ["beverage", "drink", "jus", "boba", "thai tea", "es teh"],
        "osm_tags": ["amenity=cafe", "shop=beverage"],
        "kata_kunci_nama": ["drink", "beverage", "jus", "boba", "minuman"],
    },
    # === MINUMAN ALKOHOL (contoh kasus user!) ===
    "miras": {
        "sinonim": ["alkohol", "minuman keras", "wine", "bir", "beer", "anggur", "whisky", "vodka", "sake"],
        "osm_tags": ["shop=alcohol", "shop=beverage", "amenity=bar", "amenity=pub", "amenity=nightclub"],
        "kata_kunci_nama": ["outlet", "wine", "beer", "bar", "pub", "alcohol", "liquor", "miras", "bir", "anggur"],
        "kata_kunci_kategori_tambahan": ["alcohol", "bar", "pub", "nightclub", "beverage"],
    },
    "minuman alkohol": {
        "sinonim": ["miras", "alkohol", "wine", "bir", "beer", "liquor"],
        "osm_tags": ["shop=alcohol", "amenity=bar", "amenity=pub"],
        "kata_kunci_nama": ["wine", "beer", "liquor", "alcohol", "bar", "pub", "outlet"],
    },
    # === KESEHATAN ===
    "apotek": {
        "sinonim": ["farmasi", "obat", "pharmacy", "drugstore", "kimia farma"],
        "osm_tags": ["amenity=pharmacy", "shop=chemist"],
        "kata_kunci_nama": ["apotek", "farmasi", "pharmacy", "kimia", "obat"],
    },
    "klinik": {
        "sinonim": ["puskesmas", "dokter", "medical center", "klinik 24 jam"],
        "osm_tags": ["amenity=clinic", "amenity=doctors"],
        "kata_kunci_nama": ["klinik", "clinic", "puskesmas", "dokter"],
    },
    # === JASA ===
    "laundry": {
        "sinonim": ["cuci", "kiloan", "dry cleaning", "laundry kiloan"],
        "osm_tags": ["shop=laundry", "shop=dry_cleaning"],
        "kata_kunci_nama": ["laundry", "cuci", "dry clean", "kiloan"],
    },
    "salon": {
        "sinonim": ["hair", "barbershop", "potong rambut", "salon kecantikan"],
        "osm_tags": ["shop=hairdresser", "shop=beauty"],
        "kata_kunci_nama": ["salon", "barber", "hair", "beauty"],
    },
    "bengkel": {
        "sinonim": ["service motor", "service mobil", "workshop", "auto repair"],
        "osm_tags": ["shop=car_repair", "shop=motorcycle_repair"],
        "kata_kunci_nama": ["bengkel", "service", "workshop", "auto"],
    },
    # === RETAIL ===
    "baju": {
        "sinonim": ["pakaian", "clothing", "fashion", "toko baju", "butik"],
        "osm_tags": ["shop=clothes", "shop=boutique", "shop=fashion"],
        "kata_kunci_nama": ["baju", "clothes", "fashion", "butik", "boutique"],
    },
    "sepatu": {
        "sinonim": ["sneakers", "shoes", "toko sepatu"],
        "osm_tags": ["shop=shoes"],
        "kata_kunci_nama": ["sepatu", "shoes", "sneaker"],
    },
    "sembako": {
        "sinonim": ["kelontong", "grosir", "minimarket", "warung", "toko sembako"],
        "osm_tags": ["shop=convenience", "shop=supermarket", "shop=general"],
        "kata_kunci_nama": ["sembako", "kelontong", "grosir", "warung", "toko"],
    },
    "buah": {
        "sinonim": ["sayur", "greengrocer", "toko buah", "toko sayur"],
        "osm_tags": ["shop=greengrocer", "shop=vegetables"],
        "kata_kunci_nama": ["buah", "sayur", "fruit", "vegetable"],
    },
    # === LAINNYA ===
    "hotel": {
        "sinonim": ["penginapan", "losmen", "guest house", "homestay"],
        "osm_tags": ["tourism=hotel", "tourism=guest_house", "tourism=hostel"],
        "kata_kunci_nama": ["hotel", "losmen", "guest", "inn", "hostel"],
    },
    "spbu": {
        "sinonim": ["pom bensin", "gas station", "pertamina"],
        "osm_tags": ["amenity=fuel"],
        "kata_kunci_nama": ["spbu", "bensin", "fuel", "pertamina"],
    },
    "masjid": {
        "sinonim": ["musala", "musholla", "islamic center"],
        "osm_tags": ["amenity=place_of_worship"],
        "kata_kunci_nama": ["masjid", "musala", "musholla"],
    },
    "sekolah": {
        "sinonim": ["sd", "smp", "sma", "smk", "school"],
        "osm_tags": ["amenity=school", "amenity=kindergarten"],
        "kata_kunci_nama": ["sekolah", "sd", "smp", "sma", "smk", "school"],
    },
}


# =========================================================
# FUNGSI 1 — Cari konfigurasi keyword
# =========================================================
def cari_konfigurasi_keyword(keyword):
    """
    Cari config dari kamus bisnis. Fuzzy match kalau tidak ada exact.
    """
    keyword_lower = keyword.lower().strip()

    # Exact match
    if keyword_lower in KAMUS_BISNIS:
        return KAMUS_BISNIS[keyword_lower]

    # Fuzzy match dengan nama key
    for key in KAMUS_BISNIS.keys():
        if fuzz.ratio(keyword_lower, key) > 80:
            return KAMUS_BISNIS[key]

    # Cari di sinonim
    for key, config in KAMUS_BISNIS.items():
        for sin in config.get('sinonim', []):
            if keyword_lower in sin.lower() or sin.lower() in keyword_lower:
                return config

    # Default: keyword itu sendiri
    return {
        "sinonim": [keyword_lower],
        "osm_tags": [f'shop={keyword_lower}', f'amenity={keyword_lower}'],
        "kata_kunci_nama": [keyword_lower],
    }


# =========================================================
# FUNGSI 2 — Smart Match: cek apakah bisnis cocok dengan keyword
# =========================================================
def cek_kecocokan(bisnis, keyword):
    """
    Cek apakah bisnis (dict dengan nama/kategori) cocok dengan keyword.
    Return: {'cocok': bool, 'skor': int, 'alasan': str}
    """
    config = cari_konfigurasi_keyword(keyword)

    nama = bisnis.get('nama', '').lower()
    kategori = bisnis.get('kategori', '').lower()

    skor = 0
    alasan = []

    # === 1. Match di NAMA BISNIS ===
    for kk in config.get('kata_kunci_nama', []):
        if kk.lower() in nama:
            skor += 10
            alasan.append(f'Nama mengandung "{kk}" (+10)')
            break
    else:
        # Fuzzy match nama
        for kk in config.get('kata_kunci_nama', []):
            ratio = fuzz.partial_ratio(kk.lower(), nama)
            if ratio > 75:
                skor += 5
                alasan.append(f'Nama mirip "{kk}" ({ratio}%) (+5)')
                break

    # === 2. Match di KATEGORI (OSM tag) ===
    for kk in config.get('kata_kunci_kategori_tambahan', []):
        if kk.lower() in kategori:
            skor += 8
            alasan.append(f'Kategori mengandung "{kk}" (+8)')
            break
    else:
        for tag in config.get('osm_tags', []):
            if '=' in tag:
                val = tag.split('=')[1]
                if val.lower() in kategori:
                    skor += 8
                    alasan.append(f'Kategori OSM "{val}" (+8)')
                    break

    # === 3. Match di SINONIM (untuk nama) ===
    for sin in config.get('sinonim', []):
        if sin.lower() in nama:
            skor += 6
            alasan.append(f'Nama mengandung sinonim "{sin}" (+6)')
            break

    # === 4. Boost untuk keyword umum (misal "outlet" untuk miras) ===
    keyword_lower = keyword.lower()
    if keyword_lower in ['miras', 'minuman alkohol', 'alkohol']:
        # Boost kalau nama mengandung kata umum
        if any(k in nama for k in ['outlet', 'toko', 'toserba', 'mart']):
            # Tapi hanya kalau kategori OSM match
            if 'alcohol' in kategori or 'bar' in kategori or 'beverage' in kategori:
                skor += 5
                alasan.append('Keyword miras + kategori match (+5)')

    cocok = skor >= 8  # threshold

    return {
        'cocok': cocok,
        'skor': skor,
        'alasan': ', '.join(alasan) if alasan else 'Tidak match',
    }


# =========================================================
# FUNGSI 3 — Filter daftar bisnis pakai smart matching
# =========================================================
def filter_bisnis_smart(daftar_bisnis, keyword, threshold=8):
    """
    Filter daftar bisnis: hanya yang cocok dengan keyword.
    Return: list bisnis dengan tambahan field '_skor' dan '_alasan'.
    """
    hasil = []

    for b in daftar_bisnis:
        cocok_info = cek_kecocokan(b, keyword)
        if cocok_info['skor'] >= threshold:
            b_copy = dict(b)
            b_copy['_skor'] = cocok_info['skor']
            b_copy['_alasan'] = cocok_info['alasan']
            hasil.append(b_copy)

    # Sort by skor tertinggi
    hasil.sort(key=lambda x: -x['_skor'])
    return hasil


# =========================================================
# FUNGSI 4 — Expand keyword jadi daftar pencarian
# =========================================================
def expand_keyword(keyword):
    """
    Ubah keyword jadi list kata kunci untuk dicari.
    Contoh: "miras" → ["miras", "minuman alkohol", "wine", "beer", "liquor"]
    """
    config = cari_konfigurasi_keyword(keyword)
    daftar = [keyword]
    daftar.extend(config.get('sinonim', []))

    # Unik
    seen = set()
    hasil = []
    for k in daftar:
        if k.lower() not in seen:
            seen.add(k.lower())
            hasil.append(k)

    return hasil[:6]  # max 6


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 SMART BUSINESS CLASSIFIER — TEST")
    print("=" * 60)

    # Test 1: Cari konfigurasi
    print("\n🔍 Test 1: Konfigurasi 'miras'")
    config = cari_konfigurasi_keyword("miras")
    print(f"   Sinonim: {config['sinonim']}")
    print(f"   Tags: {config['osm_tags']}")

    # Test 2: Cek kecocokan bisnis
    print("\n🔍 Test 2: Cek kecocokan bisnis dengan 'miras'")
    daftar_bisnis = [
        {'nama': 'Outlet 23 Kemang', 'kategori': 'shop=alcohol'},
        {'nama': 'Outlet 23 Tebet', 'kategori': 'shop=beverage'},
        {'nama': 'Toko Kue ABC', 'kategori': 'shop=bakery'},
        {'nama': 'Wine Cellar', 'kategori': 'shop=alcohol'},
        {'nama': 'Kelontong Pak Budi', 'kategori': 'shop=convenience'},
    ]

    for b in daftar_bisnis:
        info = cek_kecocokan(b, "miras")
        status = "✅" if info['cocok'] else "❌"
        print(f"   {status} {b['nama']} ({b['kategori']}) — skor: {info['skor']} — {info['alasan']}")

    # Test 3: Filter
    print("\n🔍 Test 3: Filter bisnis smart")
    hasil = filter_bisnis_smart(daftar_bisnis, "miras")
    print(f"   Ditemukan {len(hasil)} yang cocok:")
    for b in hasil:
        print(f"   • {b['nama']} (skor: {b['_skor']})")

    # Test 4: Expand keyword
    print("\n🔍 Test 4: Expand keyword")
    for kw in ["miras", "kue", "apotek"]:
        expanded = expand_keyword(kw)
        print(f"   '{kw}' → {expanded}")