"""
leads_db.py
Database untuk menyimpan leads (calon pembeli) yang isi form promo.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def init_leads_table():
    """Buat tabel leads kalau belum ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nama         TEXT NOT NULL,
            no_wa        TEXT NOT NULL,
            email        TEXT,
            campaign_id  INTEGER,
            lat          REAL,
            lon          REAL,
            catatan      TEXT,
            status       TEXT DEFAULT 'baru',
            dibuat       TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaign(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_campaign
        ON leads (campaign_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_status
        ON leads (status)
    """)
    conn.commit()
    conn.close()


def tambah_lead(nama, no_wa, email="", campaign_id=None,
                lat=None, lon=None, catatan=""):
    """
    Simpan lead baru.
    
    Returns:
        int: ID lead baru
    """
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads
        (nama, no_wa, email, campaign_id, lat, lon, catatan, dibuat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nama, no_wa, email, campaign_id, lat, lon, catatan,
        datetime.now().isoformat(timespec='seconds')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def ambil_leads(campaign_id=None, status=None, limit=None):
    """
    Ambil leads dari DB.
    
    Args:
        campaign_id (int): filter by campaign
        status (str): 'baru', 'followup', 'closing', 'batal'
        limit (int): batasi jumlah
    
    Returns:
        list of dict
    """
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    sql = "SELECT * FROM leads WHERE 1=1"
    params = []

    if campaign_id:
        sql += " AND campaign_id = ?"
        params.append(campaign_id)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY dibuat DESC"

    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_status_lead(id_lead, status_baru):
    """Update status lead: baru → followup → closing / batal."""
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE leads SET status = ? WHERE id = ?",
        (status_baru, id_lead)
    )
    conn.commit()
    conn.close()


def hapus_lead(id_lead):
    """Hapus lead."""
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM leads WHERE id = ?", (id_lead,))
    conn.commit()
    conn.close()


def hitung_total_leads():
    """Hitung total leads."""
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    conn.close()
    return total


def statistik_leads():
    """Statistik leads: total, per status, per campaign."""
    init_leads_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Total & per status
    c.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
    per_status = dict(c.fetchall())

    total = sum(per_status.values())

    # Per campaign
    c.execute("""
        SELECT c.nama, COUNT(l.id)
        FROM campaign c
        LEFT JOIN leads l ON l.campaign_id = c.id
        GROUP BY c.id
        ORDER BY COUNT(l.id) DESC
    """)
    per_campaign = c.fetchall()

    conn.close()
    return {
        'total': total,
        'per_status': per_status,
        'per_campaign': per_campaign
    }


# =========================================================
# MAIN — TEST
# =========================================================
if __name__ == "__main__":
    init_leads_table()
    print("=" * 55)
    print("📋 LEADS DATABASE")
    print("=" * 55)
    print(f"Total leads: {hitung_total_leads()}")

    # Sample data
    if hitung_total_leads() == 0:
        print("\n📝 Membuat sample lead...")
        id1 = tambah_lead(
            nama="Budi Santoso",
            no_wa="6281234567890",
            email="budi@example.com",
            campaign_id=1,
            lat=-6.92, lon=107.61,
            catatan="Test lead 1"
        )
        print(f"✅ Lead #1 dibuat (ID: {id1})")

        id2 = tambah_lead(
            nama="Siti Nurhaliza",
            no_wa="6289876543210",
            campaign_id=1,
            catatan="Minta info kue ultah anak"
        )
        print(f"✅ Lead #2 dibuat (ID: {id2})")

    # Statistik
    print("\n📊 Statistik:")
    stat = statistik_leads()
    print(f"  Total: {stat['total']}")
    print(f"  Per status: {stat['per_status']}")
    print(f"  Per campaign:")
    for nama, jumlah in stat['per_campaign']:
        print(f"    • {nama}: {jumlah} leads")