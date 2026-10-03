"""merge_poi_db.py — Gabung 2+ DB POI jadi 1 master."""
import sqlite3
from pathlib import Path

# Cari file DB di berbagai lokasi
CANDIDATES = [
    Path("data_osm/poi_indonesia.db"),
    Path("data_osm/poi_indonesia_extra.db"),
    Path("data_osm/poi_indonesia_PC.db"),
    Path.home() / "Downloads/poi_indonesia.db",
    Path.home() / "Downloads/poi_indonesia_extra.db",
    Path.home() / "Downloads/poi_indonesia_PC.db",
    Path.home() / "Downloads/Telegram Desktop/poi_indonesia.db",
    Path.home() / "Downloads/Telegram Desktop/poi_indonesia_extra.db",
    Path.home() / "Desktop/poi_indonesia.db",
    Path.home() / "Desktop/poi_indonesia_extra.db",
    Path.home() / "Desktop/poi_indonesia_PC.db",
]

# Cari file yang ada
found = []
seen_paths = set()
for p in CANDIDATES:
    try:
        p_resolved = p.resolve()
        if p.exists() and p.stat().st_size > 100_000 and p_resolved not in seen_paths:
            found.append(p)
            seen_paths.add(p_resolved)
            print(f"[FOUND] {p} ({p.stat().st_size/1024/1024:.1f} MB)")
    except Exception:
        pass

if len(found) < 1:
    print("\n[ERROR] Tidak ada file DB ditemukan.")
    print("Cek lokasi file. Kemungkinan ada di Downloads atau Desktop.")
    exit(1)

print(f"\nTotal {len(found)} file DB akan digabung.\n")

# Target master DB
TARGET = Path("data_osm/poi_indonesia_full.db")
TARGET.parent.mkdir(parents=True, exist_ok=True)

if TARGET.exists():
    TARGET.unlink()

# Buat DB target
con = sqlite3.connect(TARGET)
con.execute("""
    CREATE TABLE poi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        kategori_osm TEXT,
        lat REAL, lon REAL,
        kota TEXT, provinsi TEXT,
        sumber TEXT,
        UNIQUE(nama, lat, lon, kategori_osm)
    )
""")
con.execute("CREATE INDEX idx_nama ON poi(nama)")
con.execute("CREATE INDEX idx_kategori ON poi(kategori_osm)")
con.execute("CREATE INDEX idx_kota ON poi(kota)")
con.commit()

# Import dari setiap source
grand_total = 0
for source in found:
    print(f"[IMPORT] {source.name}")
    src_con = sqlite3.connect(source)
    src_con.row_factory = sqlite3.Row
    c = src_con.cursor()
    c.execute("SELECT nama, kategori_osm, lat, lon, kota, provinsi FROM poi")
    rows = c.fetchall()
    src_con.close()

    inserted = 0
    tcon = con.cursor()
    for r in rows:
        try:
            tcon.execute("""
                INSERT OR IGNORE INTO poi
                (nama, kategori_osm, lat, lon, kota, provinsi, sumber)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (r["nama"], r["kategori_osm"], r["lat"], r["lon"],
                  r["kota"], r["provinsi"], source.stem))
            if tcon.rowcount > 0:
                inserted += 1
        except Exception:
            pass
    con.commit()
    print(f"         {len(rows):>7} rows -> {inserted:>7} new")
    grand_total += inserted

# Stats
c = con.cursor()
c.execute("SELECT COUNT(*) FROM poi")
total_poi = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT kota) FROM poi")
total_kota = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT provinsi) FROM poi")
total_prov = c.fetchone()[0]

print(f"\n{'='*60}")
print(f"MERGE SELESAI")
print(f"{'='*60}")
print(f"Total POI unik  : {total_poi:,}")
print(f"Total kota unik : {total_kota}")
print(f"Total provinsi  : {total_prov}")
print(f"DB master       : {TARGET}")
print(f"{'='*60}\n")

c.execute("""
    SELECT kategori_osm, COUNT(*) as n
    FROM poi GROUP BY kategori_osm ORDER BY n DESC LIMIT 15
""")
print("Top 15 kategori:")
for row in c.fetchall():
    print(f"   {row[0]:<45} {row[1]:>7,}")

con.close()