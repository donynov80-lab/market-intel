"""
kota_db.py
Database semua kota/kabupaten Indonesia + koordinat.
Sumber: EMSIFA API (514 wilayah) + geocoding.
"""
import sqlite3
import requests
from time import sleep
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def init_kota_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kota (
            id              TEXT PRIMARY KEY,
            provinsi_id     TEXT,
            provinsi_nama   TEXT,
            kota_nama       TEXT,
            lat             REAL,
            lon             REAL,
            geocoded        INTEGER DEFAULT 0,
            opportunity_score REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provinsi ON kota(provinsi_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_geocoded ON kota(geocoded)")
    conn.commit()
    conn.close()


def download_semua_kota():
    """Download 514 kota dari EMSIFA. Sekali jalan."""
    init_kota_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM kota")
    if c.fetchone()[0] > 0:
        print(f"ℹ️ Database sudah berisi kota. Skip download.")
        conn.close()
        return

    print("📥 Download provinsi...")
    prov = requests.get(
        "https://www.emsifa.com/api-wilayah-indonesia/api/provinces.json",
        timeout=15
    ).json()

    total = 0
    for p in prov:
        print(f"  📍 {p['name']}...")
        try:
            kota_list = requests.get(
                f"https://www.emsifa.com/api-wilayah-indonesia/api/regencies/{p['id']}.json",
                timeout=15
            ).json()

            for k in kota_list:
                c.execute("""
                    INSERT OR IGNORE INTO kota
                    (id, provinsi_id, provinsi_nama, kota_nama)
                    VALUES (?, ?, ?, ?)
                """, (k['id'], p['id'], p['name'], k['name']))
                total += 1

            conn.commit()
        except Exception as e:
            print(f"    ⚠️ {e}")
        sleep(0.3)

    conn.close()
    print(f"\n✅ Selesai. {total} kota tersimpan.")


# =========================================================
# GEOCODING via PHOTON (komoot) — Lebih toleran dari Nominatim
# =========================================================
def photon_geocode(nama_lokasi):
    """Geocoding via Photon (komoot) — gratis, lebih toleran."""
    url = "https://photon.komoot.io/api/"
    params = {
        "q": f"{nama_lokasi}, Indonesia",
        "limit": 1,
        "lang": "id"
    }
    headers = {"User-Agent": "MarketIntelApp/1.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            features = data.get('features', [])
            if features:
                coords = features[0]['geometry']['coordinates']
                return {'lon': coords[0], 'lat': coords[1]}
    except Exception as e:
        print(f"    ⚠️ Photon: {str(e)[:60]}")
    return None


def nominatim_geocode(nama_lokasi):
    """Fallback: Nominatim dengan proper headers."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{nama_lokasi}, Indonesia",
        "format": "json",
        "limit": 1,
        "countrycodes": "id"
    }
    # WAJIB: User-Agent unik dengan kontak
    headers = {
        "User-Agent": "MarketIntelApp/1.0 (contact@market-intel.app)",
        "Accept-Language": "id-ID,id;q=0.9"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon'])
                }
    except Exception:
        pass
    return None


def geocode_batch(limit=50, delay=1.2):
    """
    Geocode kota satu-satu. Default 50 kota per run biar tidak diblokir.
    Bisa dijalankan berulang untuk sisa kota.
    """
    init_kota_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, kota_nama, provinsi_nama
        FROM kota
        WHERE geocoded = 0
        LIMIT ?
    """, (limit,))

    rows = [dict(r) for r in c.fetchall()]

    if not rows:
        print("✅ Semua kota sudah di-geocode!")
        conn.close()
        return 0

    print(f"🌐 Geocode {len(rows)} kota...")
    sukses = 0

    for i, row in enumerate(rows, 1):
        query = f"{row['kota_nama']}, {row['provinsi_nama']}"

        # Coba Photon dulu
        lok = photon_geocode(query)
        sumber = "Photon"

        # Fallback Nominatim
        if not lok:
            sleep(1)  # jeda sebelum Nominatim
            lok = nominatim_geocode(query)
            sumber = "Nominatim"

        if lok:
            c.execute("""
                UPDATE kota SET lat = ?, lon = ?, geocoded = 1
                WHERE id = ?
            """, (lok['lat'], lok['lon'], row['id']))
            sukses += 1
            print(f"  {i:3}. ✅ [{sumber}] {query}")
        else:
            print(f"  {i:3}. ❌ {query}")

        sleep(delay)
        if i % 20 == 0:
            conn.commit()
            print(f"     💾 Progress saved ({i}/{len(rows)})")

    conn.commit()

    # Hitung sisa
    c.execute("SELECT COUNT(*) FROM kota WHERE geocoded = 0")
    sisa = c.fetchone()[0]
    conn.close()

    print(f"\n✅ Selesai: {sukses}/{len(rows)} sukses. Sisa: {sisa} kota")
    return sukses


def cari_kota(keyword, limit=20):
    """Cari kota by keyword."""
    init_kota_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, provinsi_nama, kota_nama, lat, lon, geocoded
        FROM kota
        WHERE kota_nama LIKE ? OR provinsi_nama LIKE ?
        ORDER BY kota_nama
        LIMIT ?
    """, (f"%{keyword}%", f"%{keyword}%", limit))

    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def statistik():
    """Cek berapa kota sudah tersedia & ter-geocode."""
    init_kota_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM kota")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM kota WHERE geocoded = 1")
    geocoded = c.fetchone()[0]

    conn.close()
    return {'total': total, 'geocoded': geocoded, 'sisa': total - geocoded}


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "download":
            download_semua_kota()

        elif cmd == "geocode":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            geocode_batch(limit=limit)

        elif cmd == "status":
            s = statistik()
            print(f"📊 Total kota: {s['total']}")
            print(f"✅ Geocoded: {s['geocoded']}")
            print(f"⏳ Sisa: {s['sisa']}")

        elif cmd == "cari":
            keyword = sys.argv[2] if len(sys.argv) > 2 else "bandung"
            for k in cari_kota(keyword):
                status = "✅" if k['geocoded'] else "⏳"
                print(f"{status} {k['kota_nama']}, {k['provinsi_nama']}")

        else:
            print("Commands: download | geocode [N] | status | cari [keyword]")
    else:
        s = statistik()
        print(f"📊 Total kota: {s['total']}")
        print(f"✅ Geocoded: {s['geocoded']}")
        print(f"⏳ Sisa: {s['sisa']}")
        print("\nPerintah:")
        print("  python backend/db/kota_db.py download")
        print("  python backend/db/kota_db.py geocode 50")
        print("  python backend/db/kota_db.py status")
        print("  python backend/db/kota_db.py cari bandung")