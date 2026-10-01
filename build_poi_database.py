"""
build_poi_database.py
Bangun database POI Indonesia via Overpass API per-kota.

Output:
  - data_osm/poi_indonesia.db  (SQLite: 1 tabel 'poi')
  - data_osm/poi_indonesia.csv  (untuk inspeksi manual)

Tabel poi:
  id, nama, kategori_osm, lat, lon, kota, provinsi, sumber
"""
import sqlite3
import requests
import time
from pathlib import Path
from math import radians, cos

# === Konfigurasi ===
DB_PATH = Path("data_osm/poi_indonesia.db")
CSV_PATH = Path("data_osm/poi_indonesia.csv")
WILAYAH_DB = Path("market_intel.db")  # DB existing kita

# Batasan: ambil kota dengan penduduk > 500rb (kira-kira 50-60 kota)
MIN_PENDUDUK = 500_000
RADIUS_KM = 15  # radius per kota
MAX_KOTA = 50   # batas maksimum kota yang diproses

ENDPOINT = "https://overpass-api.de/api/interpreter"
HEADERS = {
    "User-Agent": "MarketIntelDashboard/1.0 (contact: donynov80@gmail.com)",
    "Content-Type": "application/x-www-form-urlencoded",
}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS poi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            kategori_osm TEXT,
            lat REAL,
            lon REAL,
            kota TEXT,
            provinsi TEXT,
            sumber TEXT DEFAULT 'overpass',
            UNIQUE(nama, lat, lon, kategori_osm)
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_nama ON poi(nama)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_kategori ON poi(kategori_osm)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_kota ON poi(kota)")
    con.commit()
    con.close()

def kota_sudah_diproses(kota_nama):
    """Cek apakah kota sudah ada di DB (minimal 10 POI)."""
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM poi WHERE kota = ?", (kota_nama,))
    n = c.fetchone()[0]
    con.close()
    return n >= 10  # minimal 10 POI = sudah diproses


def get_kota_besar():
    """Ambil kota besar dari wilayah_lengkap (level 2, penduduk > MIN)."""
    con = sqlite3.connect(WILAYAH_DB)
    con.row_factory = sqlite3.Row
    c = con.cursor()
    c.execute("""
        SELECT nama, provinsi_nama, lat, lng, penduduk
        FROM wilayah_lengkap
        WHERE level = 2
          AND penduduk > ?
          AND lat IS NOT NULL
          AND lng IS NOT NULL
        ORDER BY penduduk DESC
        LIMIT ?
    """, (MIN_PENDUDUK, MAX_KOTA))
    rows = [dict(r) for r in c.fetchall()]
    con.close()
    return rows


def bbox_from_center(lat, lon, radius_km):
    """Hitung bounding box dari center + radius."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(cos(radians(lat)), 0.01))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)


ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]


def query_overpass_poi(bbox, retry=3):
    """Query Overpass: semua POI di bbox. Dengan retry & rotate endpoint."""
    south, west, north, east = bbox
    area = f"({south},{west},{north},{east})"
    q = f"""
    [out:json][timeout:180];
    (
      nwr["shop"]{area};
      nwr["amenity"]{area};
      nwr["craft"]{area};
      nwr["office"]{area};
      nwr["leisure"]{area};
      nwr["tourism"]{area};
    );
    out center 5000;
    """
    
    for attempt in range(retry):
        for ep_idx, endpoint in enumerate(ENDPOINTS):
            try:
                r = requests.post(endpoint, data={"data": q},
                                 headers=HEADERS, timeout=200)
                
                if r.status_code == 200:
                    return r.json().get("elements", [])
                
                # 429 = rate limit, 504 = timeout server
                if r.status_code in (429, 504):
                    wait = (attempt + 1) * 15  # 15s, 30s, 45s
                    print(f"      ⚠️ HTTP {r.status_code} @ {endpoint.split('//')[1].split('/')[0]}, tunggu {wait}s...")
                    time.sleep(wait)
                    continue
                
                # Status lain (500, 502) → coba endpoint lain tanpa delay
                print(f"      ⚠️ HTTP {r.status_code} @ {endpoint.split('//')[1].split('/')[0]}")
                continue
                
            except Exception as e:
                print(f"      ⚠️ {endpoint.split('//')[1].split('/')[0]}: {str(e)[:60]}")
                continue
        
        # Semua endpoint gagal di attempt ini, tunggu sebentar
        if attempt < retry - 1:
            print(f"      🔄 Retry {attempt+2}/{retry} dalam 20s...")
            time.sleep(20)
    
    print(f"      ❌ Gagal setelah {retry} retry")
    return []



def parse_poi(elements, kota, provinsi):
    """Parse elemen Overpass -> list POI."""
    hasil = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        # Ambil nama
        nama = tags.get("name")
        if not nama:
            continue
        
        # Ambil kategori utama
        kategori = None
        for k in ["shop", "amenity", "craft", "office", "leisure", "tourism"]:
            if k in tags:
                kategori = f"{k}={tags[k]}"
                break
        if not kategori:
            continue
        
        # Koordinat
        if el["type"] == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        
        if lat is None or lon is None:
            continue
        
        hasil.append({
            "nama": nama[:200],
            "kategori_osm": kategori,
            "lat": lat,
            "lon": lon,
            "kota": kota,
            "provinsi": provinsi,
        })
    return hasil


def simpan_poi(poi_list):
    """Simpan POI ke SQLite (INSERT OR IGNORE untuk dedupe)."""
    if not poi_list:
        return 0
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    inserted = 0
    for p in poi_list:
        try:
            c.execute("""
                INSERT OR IGNORE INTO poi
                (nama, kategori_osm, lat, lon, kota, provinsi)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p["nama"], p["kategori_osm"], p["lat"], p["lon"],
                  p["kota"], p["provinsi"]))
            if c.rowcount > 0:
                inserted += 1
        except Exception:
            pass
    con.commit()
    con.close()
    return inserted


def export_csv():
    """Export ke CSV untuk inspeksi."""
    import csv
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    c = con.cursor()
    c.execute("SELECT nama, kategori_osm, lat, lon, kota, provinsi FROM poi")
    rows = c.fetchall()
    con.close()
    
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nama", "kategori_osm", "lat", "lon", "kota", "provinsi"])
        for r in rows:
            w.writerow([r["nama"], r["kategori_osm"], r["lat"], r["lon"],
                       r["kota"], r["provinsi"]])
    print(f"\n💾 CSV: {CSV_PATH} ({len(rows)} baris)")


# === Main ===
if __name__ == "__main__":
    print("=" * 60)
    print("🏗️  BUILD POI DATABASE INDONESIA")
    print("=" * 60)
    
    init_db()
    kotas = get_kota_besar()
    print(f"\n📍 {len(kotas)} kota besar akan diproses (radius {RADIUS_KM} km)\n")
    
    total_inserted = 0
    for i, kota in enumerate(kotas, 1):
        nama = kota["nama"]
        prov = kota["provinsi_nama"]
        lat, lon = kota["lat"], kota["lng"]
        penduduk = kota["penduduk"]
        
        # === AUTO-SKIP kota yang sudah diproses ===
        if kota_sudah_diproses(nama):
            print(f"[{i:>2}/{len(kotas)}] {nama:35} ⏩ sudah diproses, skip")
            continue
        
        print(f"[{i:>2}/{len(kotas)}] {nama} ({prov}) — {penduduk:,} jiwa")
        
        bbox = bbox_from_center(lat, lon, RADIUS_KM)
        elements = query_overpass_poi(bbox)
        poi_list = parse_poi(elements, nama, prov)
        inserted = simpan_poi(poi_list)
        total_inserted += inserted
        
        print(f"       → {len(elements)} element, {len(poi_list)} valid POI, {inserted} baru")
        
        # Jeda sopan ke server (naikkan dari 3s ke 8s karena server sensitif)
        if i < len(kotas):
            time.sleep(8)
    
    print(f"\n{'='*60}")
    print(f"✅ SELESAI: {total_inserted} POI baru ditambahkan")
    print(f"💾 DB: {DB_PATH}")
    print(f"{'='*60}")
    
    export_csv()
    
    # Show stats
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM poi")
    print(f"\n📊 Total POI di DB: {c.fetchone()[0]:,}")
    c.execute("""
        SELECT kategori_osm, COUNT(*) as n FROM poi
        GROUP BY kategori_osm ORDER BY n DESC LIMIT 15
    """)
    print(f"\n🏆 Top 15 kategori:")
    for row in c.fetchall():
        print(f"   {row[0]:<40} {row[1]:>6}")
    con.close()