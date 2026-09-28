"""
campaign_db.py
Menyimpan data kampanye geo-fence: nama promo, lokasi toko, 
radius, konten promo.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def init_campaign_table():
    """Buat tabel campaign kalau belum ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nama        TEXT NOT NULL,
            deskripsi   TEXT,
            lat_toko    REAL NOT NULL,
            lon_toko    REAL NOT NULL,
            radius_km   REAL NOT NULL,
            konten      TEXT NOT NULL,
            wa_link     TEXT,
            aktif       INTEGER DEFAULT 1,
            dibuat      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def tambah_campaign(nama, lat, lon, radius_km, konten,
                    deskripsi="", wa_link=""):
    """
    Tambah kampanye baru.
    
    Args:
        nama (str): nama kampanye, contoh "Promo Kue Bandung"
        lat, lon (float): koordinat toko (Google Maps)
        radius_km (float): radius promo dalam km
        konten (str): teks promo yang ditampilkan
        deskripsi (str): catatan internal
        wa_link (str): link WhatsApp untuk CTA
    
    Returns:
        int: ID campaign baru
    """
    init_campaign_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO campaign
        (nama, deskripsi, lat_toko, lon_toko, radius_km,
         konten, wa_link, dibuat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nama, deskripsi, lat, lon, radius_km,
        konten, wa_link,
        datetime.now().isoformat(timespec='seconds')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def ambil_campaign(id_campaign=None, hanya_aktif=True):
    """
    Ambil campaign dari DB.
    
    Args:
        id_campaign (int): kalau diisi, ambil satu saja
        hanya_aktif (bool): filter yang aktif saja
    
    Returns:
        list of dict atau dict (kalau id_campaign diisi)
    """
    init_campaign_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if id_campaign:
        c.execute("SELECT * FROM campaign WHERE id = ?", (id_campaign,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    sql = "SELECT * FROM campaign"
    if hanya_aktif:
        sql += " WHERE aktif = 1"
    sql += " ORDER BY dibuat DESC"

    c.execute(sql)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_campaign(id_campaign, **kwargs):
    """Update field campaign. Contoh: update_campaign(1, aktif=0)"""
    init_campaign_table()
    if not kwargs:
        return False

    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [id_campaign]

    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"UPDATE campaign SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def hapus_campaign(id_campaign):
    """Hapus campaign."""
    init_campaign_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM campaign WHERE id = ?", (id_campaign,))
    conn.commit()
    conn.close()


def hitung_total_campaign():
    """Hitung total campaign."""
    init_campaign_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM campaign")
    total = c.fetchone()[0]
    conn.close()
    return total


# =========================================================
# MAIN — Test & Sample Data
# =========================================================
if __name__ == "__main__":
    init_campaign_table()
    print("=" * 55)
    print("📢 CAMPAIGN DATABASE")
    print("=" * 55)

    # Cek apakah sudah ada data
    total = hitung_total_campaign()
    print(f"Total campaign saat ini: {total}")

    if total == 0:
        print("\n📝 Membuat sample campaign...")

        # Sample 1: Toko kue di Bandung
        id1 = tambah_campaign(
            nama="Promo Kue Bandung",
            lat=-6.9147,        # Alun-alun Bandung
            lon=107.6098,
            radius_km=5,
            konten="🎉 Diskon 20% untuk kue ulang tahun! Khusus warga Bandung!",
            deskripsi="Kampanye percobaan untuk UMKM kue",
            wa_link="https://wa.me/6281234567890?text=Halo%20saya%20mau%20order%20kue"
        )
        print(f"✅ Campaign #1 dibuat (ID: {id1})")

        # Sample 2: Toko pastry di Jakarta
        id2 = tambah_campaign(
            nama="Promo Pastry Jakarta",
            lat=-6.1751,        # Monas Jakarta
            lon=106.8272,
            radius_km=10,
            konten="🥐 Beli 2 gratis 1 untuk pastry! Khusus area Jakarta Pusat.",
            deskripsi="Kampanye pastry",
            wa_link="https://wa.me/6281234567890"
        )
        print(f"✅ Campaign #2 dibuat (ID: {id2})")

    # Tampilkan semua campaign
    print("\n📋 Daftar Campaign:")
    print("-" * 55)
    for c in ambil_campaign():
        print(f"\n#{c['id']} — {c['nama']}")
        print(f"   📍 Lokasi: ({c['lat_toko']}, {c['lon_toko']})")
        print(f"   📏 Radius: {c['radius_km']} km")
        print(f"   💬 Konten: {c['konten'][:60]}...")
        print(f"   🟢 Aktif: {'Ya' if c['aktif'] else 'Tidak'}")