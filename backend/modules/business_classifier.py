"""
business_classifier.py
Smart Business Classifier — pahami konteks bisnis.
"""
from rapidfuzz import fuzz


KAMUS_BISNIS = {
    "kue": {
        "sinonim": ["cake", "pastry", "bakery", "roti", "bolu", "tart", "donat", "brownies"],
        "osm_tags": ["shop=bakery", "shop=confectionery", "shop=pastry"],
        "kata_kunci_nama": ["kue", "cake", "bakery", "roti", "pastry", "bolu"],
        "kata_kunci_kategori": ["bakery", "confectionery", "pastry"],
    },
    "camilan": {
        "sinonim": ["snack", "keripik", "cemilan"],
        "osm_tags": ["shop=confectionery", "shop=convenience"],
        "kata_kunci_nama": ["snack", "camilan", "cemilan", "keripik"],
        "kata_kunci_kategori": ["confectionery", "convenience"],
    },
    "restoran": {
        "sinonim": ["resto", "warung makan", "rumah makan", "kedai"],
        "osm_tags": ["amenity=restaurant", "amenity=fast_food"],
        "kata_kunci_nama": ["resto", "restoran", "warung", "kedai", "rm "],
        "kata_kunci_kategori": ["restaurant", "fast_food"],
    },
    "cafe": {
        "sinonim": ["kafe", "coffee shop", "kopi", "kedai kopi"],
        "osm_tags": ["amenity=cafe"],
        "kata_kunci_nama": ["cafe", "kafe", "coffee", "kopi"],
        "kata_kunci_kategori": ["cafe"],
    },
    "miras": {
        "sinonim": ["alkohol", "wine", "bir", "beer", "liquor"],
        "osm_tags": ["shop=alcohol", "amenity=bar", "amenity=pub"],
        "kata_kunci_nama": ["wine", "beer", "liquor", "alcohol", "bar", "pub", "outlet"],
        "kata_kunci_kategori": ["alcohol", "bar", "pub", "nightclub", "beverage"],
    },
    "apotek": {
        "sinonim": ["farmasi", "obat", "pharmacy", "kimia farma"],
        "osm_tags": ["amenity=pharmacy", "shop=chemist"],
        "kata_kunci_nama": ["apotek", "farmasi", "pharmacy", "kimia"],
        "kata_kunci_kategori": ["pharmacy", "chemist"],
    },
    "laundry": {
        "sinonim": ["cuci", "kiloan", "dry cleaning"],
        "osm_tags": ["shop=laundry", "shop=dry_cleaning"],
        "kata_kunci_nama": ["laundry", "cuci", "dry clean", "kiloan"],
        "kata_kunci_kategori": ["laundry", "dry_cleaning"],
    },
    "salon": {
        "sinonim": ["hair", "barbershop", "potong rambut"],
        "osm_tags": ["shop=hairdresser", "shop=beauty"],
        "kata_kunci_nama": ["salon", "barber", "hair", "beauty"],
        "kata_kunci_kategori": ["hairdresser", "beauty"],
    },
    "bengkel": {
        "sinonim": ["service motor", "service mobil", "workshop"],
        "osm_tags": ["shop=car_repair", "shop=motorcycle_repair"],
        "kata_kunci_nama": ["bengkel", "service", "workshop", "auto"],
        "kata_kunci_kategori": ["car_repair", "motorcycle_repair"],
    },
    "baju": {
        "sinonim": ["pakaian", "clothing", "fashion", "butik"],
        "osm_tags": ["shop=clothes", "shop=boutique"],
        "kata_kunci_nama": ["baju", "clothes", "fashion", "butik"],
        "kata_kunci_kategori": ["clothes", "boutique", "fashion"],
    },
    "sembako": {
        "sinonim": ["kelontong", "grosir", "minimarket", "warung"],
        "osm_tags": ["shop=convenience", "shop=supermarket"],
        "kata_kunci_nama": ["sembako", "kelontong", "grosir", "warung", "toko"],
        "kata_kunci_kategori": ["convenience", "supermarket", "general"],
    },
    "hotel": {
        "sinonim": ["penginapan", "losmen", "guest house"],
        "osm_tags": ["tourism=hotel", "tourism=guest_house"],
        "kata_kunci_nama": ["hotel", "losmen", "guest", "inn", "hostel"],
        "kata_kunci_kategori": ["hotel", "guest_house", "hostel"],
    },
}


def cari_konfigurasi_keyword(keyword):
    keyword_lower = keyword.lower().strip()
    if keyword_lower in KAMUS_BISNIS:
        return KAMUS_BISNIS[keyword_lower]
    for key, config in KAMUS_BISNIS.items():
        if fuzz.ratio(keyword_lower, key) > 80:
            return config
        for sin in config.get('sinonim', []):
            if keyword_lower in sin.lower() or sin.lower() in keyword_lower:
                return config
    return {
        "sinonim": [keyword_lower],
        "osm_tags": [f'shop={keyword_lower}'],
        "kata_kunci_nama": [keyword_lower],
        "kata_kunci_kategori": [keyword_lower],
    }


def cek_kecocokan(bisnis, keyword):
    config = cari_konfigurasi_keyword(keyword)
    nama = bisnis.get('nama', '').lower()
    kategori = bisnis.get('kategori', '').lower()

    skor = 0
    alasan = []

    # 1. Match nama (cocok persis)
    for kk in config.get('kata_kunci_nama', []):
        if kk.lower() in nama:
            skor += 10
            alasan.append(f'Nama: "{kk}" (+10)')
            break
    else:
        # Fuzzy nama
        for kk in config.get('kata_kunci_nama', []):
            if fuzz.partial_ratio(kk.lower(), nama) > 75:
                skor += 5
                alasan.append(f'Nama mirip "{kk}" (+5)')
                break

    # 2. Match kategori
    for kk in config.get('kata_kunci_kategori', []):
        if kk.lower() in kategori:
            skor += 8
            alasan.append(f'Kategori: "{kk}" (+8)')
            break

    # 3. Match sinonim
    for sin in config.get('sinonim', []):
        if sin.lower() in nama:
            skor += 6
            alasan.append(f'Sinonim: "{sin}" (+6)')
            break

    cocok = skor >= 6

    return {
        'cocok': cocok,
        'skor': skor,
        'alasan': ', '.join(alasan) if alasan else 'Tidak match',
    }


def filter_bisnis_smart(daftar_bisnis, keyword, threshold=6):
    hasil = []
    for b in daftar_bisnis:
        info = cek_kecocokan(b, keyword)
        if info['skor'] >= threshold:
            b_copy = dict(b)
            b_copy['_skor'] = info['skor']
            b_copy['_alasan'] = info['alasan']
            hasil.append(b_copy)
    hasil.sort(key=lambda x: -x['_skor'])
    return hasil


def expand_keyword(keyword):
    config = cari_konfigurasi_keyword(keyword)
    daftar = [keyword] + config.get('sinonim', [])
    seen = set()
    hasil = []
    for k in daftar:
        if k.lower() not in seen:
            seen.add(k.lower())
            hasil.append(k)
    return hasil[:6]