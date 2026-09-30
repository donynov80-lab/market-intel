"""
keyword_whitelist.py
Whitelist keyword populer dengan mapping OSM yang sudah diverifikasi manual.

Ini LAPIS PERTAMA sebelum sistem cari fuzzy.
Manfaat: keyword umum (roti, kue, bakpia, dll.) tidak akan salah mapping.

Cara tambah keyword baru:
  1. Tambah entry baru di bawah
  2. Test: cari_osm_filter_dari_keyword('keyword_baru')
"""

# Mapping langsung keyword -> filter OSM (key: regex)
WHITELIST = {
    # ===== BAKERY & KUE =====
    "roti":       {"shop": "bakery", "craft": "bakery"},
    "kue":        {"shop": "bakery|pastry|confectionery", "craft": "bakery"},
    "bakery":     {"shop": "bakery", "craft": "bakery"},
    "bakpia":     {"shop": "bakery|pastry", "craft": "bakery"},
    "cake":       {"shop": "bakery|pastry|confectionery", "craft": "bakery"},
    "pastry":     {"shop": "pastry|bakery", "craft": "bakery"},
    "donat":      {"shop": "bakery|pastry", "craft": "bakery"},
    "bolu":       {"shop": "bakery|pastry", "craft": "bakery"},
    "lapis":      {"shop": "bakery|pastry", "craft": "bakery"},
    "toko roti":  {"shop": "bakery|pastry", "craft": "bakery"},
    "roti bakar": {"shop": "bakery", "amenity": "fast_food"},
    "jajan":      {"shop": "bakery|pastry|confectionery"},
    "snack":      {"shop": "bakery|pastry|confectionery"},
    
    # ===== MINUMAN =====
    "miras":      {"shop": "alcohol|wine|beverages", "amenity": "bar|pub"},
    "alkohol":    {"shop": "alcohol|wine"},
    "bir":        {"shop": "alcohol|beverages"},
    "wine":       {"shop": "wine|alcohol"},
    "kopi":       {"amenity": "cafe", "shop": "coffee"},
    "cafe":       {"amenity": "cafe"},
    "kafe":       {"amenity": "cafe"},
    "teh":        {"shop": "tea", "amenity": "cafe"},
    "jus":        {"shop": "beverages|juice"},
    "minuman":    {"shop": "beverages"},

    # ===== MAKANAN =====
    "restoran":   {"amenity": "restaurant"},
    "rumah makan": {"amenity": "restaurant"},
    "warung":     {"amenity": "fast_food|cafe"},
    "kedai":      {"amenity": "cafe|fast_food"},
    "katering":   {"craft": "caterer"},
    "makanan":    {"amenity": "restaurant|fast_food"},

    # ===== RETAIL UMUM =====
    "minimarket": {"shop": "convenience"},
    "supermarket": {"shop": "supermarket"},
    "toko":       {"shop": "convenience|supermarket"},
    "pasar":      {"amenity": "marketplace"},

    # ===== KESEHATAN =====
    "apotek":     {"amenity": "pharmacy", "shop": "chemist"},
    "farmasi":    {"amenity": "pharmacy", "shop": "chemist"},
    "klinik":     {"amenity": "clinic|doctors"},
    "rumah sakit": {"amenity": "hospital"},

    # ===== JASA KECANTIKAN =====
    "salon":      {"shop": "hairdresser|beauty"},
    "barbershop": {"shop": "hairdresser"},
    "pangkas rambut": {"shop": "hairdresser"},
    "spa":        {"leisure": "spa", "shop": "massage"},
    "pijat":      {"shop": "massage"},
    "laundry":    {"shop": "laundry"},

    # ===== OTOMOTIF =====
    "bengkel":    {"shop": "car_repair|motorcycle_repair"},
    "bengkel mobil": {"shop": "car_repair"},
    "bengkel motor": {"shop": "motorcycle_repair"},
    "pom bensin": {"amenity": "fuel"},
    "spbu":       {"amenity": "fuel"},

    # ===== PENDIDIKAN =====
    "sekolah":    {"amenity": "school"},
    "universitas": {"amenity": "university"},
    "kampus":     {"amenity": "university|college"},
    "paud":       {"amenity": "kindergarten"},

    # ===== AKOMODASI =====
    "hotel":      {"tourism": "hotel"},
    "penginapan": {"tourism": "hotel|guest_house"},
    "homestay":   {"tourism": "guest_house"},

    # ===== SPA & MASSAGE =====
    "spa":            {"leisure": "spa", "shop": "massage"},
    "massage":        {"shop": "massage", "leisure": "spa"},
    "pijat":          {"shop": "massage", "leisure": "spa"},
    "refleksi":       {"shop": "massage", "leisure": "spa"},
    "refleksologi":   {"shop": "massage", "leisure": "spa"},
    "urut":           {"shop": "massage"},
    "sauna":          {"leisure": "sauna"},
    "wellness":       {"leisure": "spa"},

    # ===== HIBURAN MALAM =====
    "karaoke":        {"amenity": "nightclub|karaoke_box"},
    "diskotik":       {"amenity": "nightclub"},
    "disko":          {"amenity": "nightclub"},
    "disco":          {"amenity": "nightclub"},
    "klub malam":     {"amenity": "nightclub"},
    "nightclub":      {"amenity": "nightclub"},
    "pub":            {"amenity": "pub|bar"},
    "bar":            {"amenity": "bar|pub"},
    "club":           {"amenity": "nightclub|bar"},

    # ===== HIBURAN UMUM =====
    "bioskop":        {"amenity": "cinema"},
    "cinema":         {"amenity": "cinema"},
    "gym":            {"leisure": "fitness_centre"},
    "fitness":        {"leisure": "fitness_centre"},
    "yoga":           {"leisure": "fitness_centre", "sport": "yoga"},
    "futsal":         {"leisure": "pitch", "sport": "soccer"},
    "kolam renang":   {"leisure": "swimming_pool"},
    
       
    # ===== INDUSTRI (untuk supply chain) =====
    "pabrik roti": {"landuse": "industrial", "industrial": "food"},
    "pabrik tekstil": {"landuse": "industrial", "industrial": "textile"},
    "pabrik kayu": {"landuse": "industrial", "industrial": "wood"},
    "pabrik rokok": {"landuse": "industrial", "industrial": "tobacco"},
    "pabrik kulit": {"landuse": "industrial", "industrial": "leather"},
}


def cari_whitelist(keyword: str):
    """
    Return filter OSM kalau keyword ada di whitelist, else None.
    """
    if not keyword:
        return None
    return WHITELIST.get(keyword.lower().strip())