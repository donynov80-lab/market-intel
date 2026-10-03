"""rebuild_keyword_db.py — Rebuild keyword DB pakai priority override."""
import sqlite3
import json
import re
from pathlib import Path
from collections import Counter, defaultdict
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tag_kbli_priority import PRIORITY

POI_DB = Path("data_osm/poi_indonesia_full.db")
KBLI_OSM_JSON = Path("db_eksternal/kbli_osm_mapping.json")
OUTPUT_DB = Path("data_osm/keyword_kbli.db")

# === Load KBLI-OSM, build reverse dengan PRIORITY ===
print("Loading KBLI-OSM mapping...")
with KBLI_OSM_JSON.open(encoding="utf-8") as f:
    kbli_osm = json.load(f)

# Reverse: OSM tag -> KBLI
osm_to_kbli = {}

# 1) Dari kbli_osm_mapping.json (default)
for code, info in kbli_osm.items():
    for tag in info.get("osm_tags", []):
        if tag not in osm_to_kbli:
            osm_to_kbli[tag] = code

# 2) OVERRIDE dengan PRIORITY (menang)
for tag, kbli in PRIORITY.items():
    osm_to_kbli[tag] = kbli  # override paksa

print(f"   {len(osm_to_kbli)} tag OSM dipetakan ({len(PRIORITY)} override prioritas)\n")

# === Stopwords ===
STOPWORDS = {
    "dan", "atau", "di", "ke", "dari", "yang", "untuk", "pada", "dengan",
    "oleh", "ini", "itu", "the", "of", "and", "in", "at", "by", "for",
    "a", "an", "toko", "warung", "kedai", "rumah", "taman", "area",
    "kantor", "gedung", "jl", "jalan", "no", "nomor", "rt", "rw",
    "kecamatan", "kelurahan", "kabupaten", "kota", "provinsi",
}

def tokenize(text):
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = text.split()
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]

# === Baca POI ===
print("Membaca POI dari DB master...")
con = sqlite3.connect(POI_DB)
con.row_factory = sqlite3.Row
c = con.cursor()
c.execute("SELECT nama, kategori_osm FROM poi")
rows = c.fetchall()
con.close()
print(f"   {len(rows):,} POI dibaca\n")

# === Hitung frekuensi ===
print("Menghitung keyword -> KBLI...")
kw_kbli = defaultdict(Counter)
kw_total = Counter()
skipped = 0

for r in rows:
    kat = r["kategori_osm"]
    kbli = osm_to_kbli.get(kat)
    if not kbli:
        skipped += 1
        continue
    words = set(tokenize(r["nama"]))
    for w in words:
        kw_kbli[w][kbli] += 1
        kw_total[w] += 1

print(f"   {len(kw_total):,} keyword unik ({skipped:,} POI diskip tanpa KBLI)\n")

# === Simpan ===
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

MIN_SAMPLE = 3
inserted = 0
for kw, counter in kw_kbli.items():
    total = kw_total[kw]
    if total < MIN_SAMPLE:
        continue
    for kbli, cnt in counter.items():
        prob = cnt / total
        if prob >= 0.3:
            out.execute("""
                INSERT INTO keyword_kbli VALUES (?, ?, ?, ?, ?)
            """, (kw, kbli, prob, cnt, total))
            inserted += 1
out.commit()

# === Stats ===
c = out.cursor()
c.execute("SELECT COUNT(*), COUNT(DISTINCT keyword) FROM keyword_kbli")
n_rows, n_kw = c.fetchone()

print(f"\n{'='*60}")
print(f"REBUILD SELESAI")
print(f"{'='*60}")
print(f"Total baris : {n_rows:,}")
print(f"Total keyword : {n_kw:,}")
print(f"{'='*60}\n")

# === Cek keyword penting ===
print("Cek keyword penting:")
for kw in ["bakpia", "roti", "kue", "bakery", "spa", "massage", "karaoke",
           "kopi", "apotek", "hotel", "warung", "masjid"]:
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
        print(f"\n   '{kw}': (tidak ada sample >= 3)")

out.close()