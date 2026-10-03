"""build_keyword_db.py — Bangun kamus keyword->KBLI dari database POI."""
import sqlite3
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

# === Path ===
POI_DB = Path("data_osm/poi_indonesia_full.db")
KBLI_OSM_JSON = Path("db_eksternal/kbli_osm_mapping.json")
OUTPUT_DB = Path("data_osm/keyword_kbli.db")

# === Load KBLI->OSM mapping, lalu reverse ===
print("Loading KBLI-OSM mapping...")
with KBLI_OSM_JSON.open(encoding="utf-8") as f:
    kbli_osm = json.load(f)

# Reverse: kategori OSM -> KBLI code
osm_to_kbli = {}
for code, info in kbli_osm.items():
    for tag in info.get("osm_tags", []):
        # Kalau satu tag dipetakan ke banyak KBLI, simpan yang pertama
        # (mapping kita sudah spesifik, jadi ini aman)
        if tag not in osm_to_kbli:
            osm_to_kbli[tag] = code
print(f"   {len(osm_to_kbli)} kategori OSM dipetakan ke KBLI\n")

# === Stopwords Indonesia (buang kata umum) ===
STOPWORDS = {
    "dan", "atau", "di", "ke", "dari", "yang", "untuk", "pada", "dengan",
    "oleh", "ini", "itu", "the", "of", "and", "in", "at", "by", "for",
    "a", "an", "tokо", "toko", "warung", "kedai", "rumah", "taman", "area",
    "kantor", "gedung", "jl", "jalan", "no", "nomor", "rt", "rw",
    "kecamatan", "kelurahan", "kabupaten", "kota", "provinsi",
}

def tokenize(text):
    """Pecah teks jadi kata-kata lowercase (alfanumerik, min 3 karakter)."""
    if not text:
        return []
    text = text.lower()
    # Ganti semua non-alfanumerik jadi spasi
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = text.split()
    # Filter stopwords & panjang
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]

# === Baca semua POI ===
print("Membaca POI dari DB master...")
con = sqlite3.connect(POI_DB)
con.row_factory = sqlite3.Row
c = con.cursor()
c.execute("SELECT nama, kategori_osm FROM poi")
rows = c.fetchall()
con.close()
print(f"   {len(rows):,} POI dibaca\n")

# === Hitung frekuensi (keyword -> kbli) ===
print("Menghitung frekuensi keyword -> KBLI...")
kw_kbli_count = defaultdict(Counter)   # keyword -> {kbli: count}
kw_total = Counter()                    # keyword -> total occurrences

for r in rows:
    nama = r["nama"]
    kat = r["kategori_osm"]
    # Cari KBLI dari kategori OSM
    kbli_code = osm_to_kbli.get(kat)
    if not kbli_code:
        continue  # skip kategori tanpa mapping
    
    # Tokenize nama
    words = tokenize(nama)
    # Ambil unique words (biar satu POI hanya hitung sekali per kata)
    unique_words = set(words)
    
    for w in unique_words:
        kw_kbli_count[w][kbli_code] += 1
        kw_total[w] += 1

print(f"   {len(kw_total):,} keyword unik ditemukan\n")

# === Simpan ke SQLite ===
print("Menyimpan ke SQLite...")
OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT_DB.exists():
    OUTPUT_DB.unlink()

out = sqlite3.connect(OUTPUT_DB)
out.execute("""
    CREATE TABLE keyword_kbli (
        keyword TEXT,
        kbli_code TEXT,
        probability REAL,
        sample_count INTEGER,
        total_keyword INTEGER,
        PRIMARY KEY (keyword, kbli_code)
    )
""")
out.execute("CREATE INDEX idx_keyword ON keyword_kbli(keyword)")
out.execute("CREATE INDEX idx_kbli ON keyword_kbli(kbli_code)")

# Hanya simpan keyword dengan minimal 3 sample
MIN_SAMPLE = 3

inserted = 0
for kw, counter in kw_kbli_count.items():
    total = kw_total[kw]
    if total < MIN_SAMPLE:
        continue
    for kbli, cnt in counter.items():
        prob = cnt / total
        # Simpan hanya probabilitas >= 0.3 (biar tidak terlalu noise)
        if prob >= 0.3:
            out.execute("""
                INSERT INTO keyword_kbli
                (keyword, kbli_code, probability, sample_count, total_keyword)
                VALUES (?, ?, ?, ?, ?)
            """, (kw, kbli, prob, cnt, total))
            inserted += 1

out.commit()

# === Stats ===
c = out.cursor()
c.execute("SELECT COUNT(*) FROM keyword_kbli")
total_rows = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT keyword) FROM keyword_kbli")
total_kw = c.fetchone()[0]

print(f"\n{'='*60}")
print(f"BUILD SELESAI")
print(f"{'='*60}")
print(f"Total baris keyword->KBLI : {total_rows:,}")
print(f"Total keyword unik        : {total_kw:,}")
print(f"DB output                 : {OUTPUT_DB}")
print(f"{'='*60}\n")

# === Tampilkan contoh ===
print("Contoh 30 keyword dengan sample terbanyak:")
c.execute("""
    SELECT keyword, kbli_code, probability, sample_count, total_keyword
    FROM keyword_kbli
    ORDER BY sample_count DESC
    LIMIT 30
""")
for r in c.fetchall():
    print(f"   {r[0]:<20} -> KBLI {r[1]} | prob {r[2]:.2f} | {r[3]}/{r[4]}")

print("\nContoh kata kunci populer:")
for kw in ["bakpia", "roti", "kue", "bakery", "spa", "massage", "karaoke", "kopi", "apotek", "hotel"]:
    c.execute("""
        SELECT kbli_code, probability, sample_count, total_keyword
        FROM keyword_kbli WHERE keyword = ?
        ORDER BY probability DESC LIMIT 3
    """, (kw,))
    results = c.fetchall()
    if results:
        print(f"\n   '{kw}':")
        for r in results:
            print(f"      KBLI {r[0]} | prob {r[1]:.2f} | {r[2]}/{r[3]}")
    else:
        print(f"\n   '{kw}': (tidak ditemukan, sample < 3)")

out.close()