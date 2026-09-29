"""
snapshot_db.py
Simpan hasil scan kompetitor sebagai SNAPSHOT (foto album).
Berbeda dengan cache_kompetitor:
  - cache  = otomatis, expired 7 hari, 1 baris per (lat,lon,radius,keyword)
  - snapshot = manual, permanen, banyak baris per kota+keyword (riwayat waktu)

Dipakai untuk:
  - Tracking bulanan (berapa kompetitor baru muncul?)
  - Bandingkan 2 kota (densitas, subgolongan, dsb.)
  - Export laporan PDF

Pola: mengikuti cache_db.py (init / get / save / stats / clear).
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


# =========================================================
# INIT
# =========================================================
def init_snapshot_table():
    """Buat tabel scan_snapshots + index kalau belum ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            kota TEXT NOT NULL,
            provinsi TEXT,
            lat REAL,
            lon REAL,
            radius_km REAL,
            keyword TEXT NOT NULL,
            jumlah INTEGER DEFAULT 0,
            jumlah_per_subgolongan TEXT,
            data_json TEXT,
            catatan TEXT,
            snapshot_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshot_lookup
        ON scan_snapshots (kota, keyword, snapshot_at DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshot_keyword
        ON scan_snapshots (keyword, snapshot_at DESC)
    """)
    conn.commit()
    conn.close()


# =========================================================
# SAVE
# =========================================================
def save_snapshot(kota, keyword, radius_km, data,
                  provinsi=None, lat=None, lon=None,
                  label=None, catatan=None):
    """
    Simpan snapshot hasil scan.

    Args:
        kota      : nama kota (mis. "Kota Denpasar, Bali")
        keyword   : kata kunci (mis. "miras")
        radius_km : radius scan
        data      : list dict hasil scan (dari scan_sekitar)
        provinsi  : opsional
        lat, lon  : opsional, koordinat center
        label     : opsional, nama milestone (mis. "Akhir Sep 2026")
        catatan   : opsional, catatan user

    Return:
        id snapshot yang baru dibuat (int) atau None kalau gagal.
    """
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat(timespec='seconds')

    # Breakdown per subgolongan (KBLI 4-digit)
    per_subgol = {}
    for b in (data or []):
        code = b.get('code_4digit') or 'UNCLASSIFIED'
        per_subgol[code] = per_subgol.get(code, 0) + 1

    try:
        cur = conn.execute("""
            INSERT INTO scan_snapshots
            (label, kota, provinsi, lat, lon, radius_km, keyword,
             jumlah, jumlah_per_subgolongan, data_json, catatan, snapshot_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            label, kota, provinsi, lat, lon, radius_km, keyword,
            len(data or []),
            json.dumps(per_subgol, ensure_ascii=False),
            json.dumps(data or [], ensure_ascii=False),
            catatan, now,
        ))
        conn.commit()
        new_id = cur.lastrowid
        return new_id
    except Exception as e:
        print(f"[Snapshot] Gagal simpan: {e}")
        return None
    finally:
        conn.close()


# =========================================================
# GET / LIST
# =========================================================
def get_snapshots(kota=None, keyword=None, limit=100):
    """
    Ambil daftar snapshot (TANPA data_json — biar ringan).
    Urut dari yang terbaru.
    """
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    q = """
        SELECT id, label, kota, provinsi, lat, lon, radius_km,
               keyword, jumlah, jumlah_per_subgolongan, catatan, snapshot_at
        FROM scan_snapshots
        WHERE 1=1
    """
    params = []
    if kota:
        q += " AND kota = ?"
        params.append(kota)
    if keyword:
        q += " AND keyword = ?"
        params.append(keyword)
    q += " ORDER BY snapshot_at DESC LIMIT ?"
    params.append(limit)

    c.execute(q, params)
    rows = c.fetchall()
    conn.close()

    hasil = []
    for r in rows:
        d = dict(r)
        try:
            d['per_subgolongan'] = json.loads(d.get('jumlah_per_subgolongan') or '{}')
        except Exception:
            d['per_subgolongan'] = {}
        d.pop('jumlah_per_subgolongan', None)
        hasil.append(d)
    return hasil


def get_snapshot_by_id(snapshot_id):
    """Ambil 1 snapshot LENGKAP (dengan data_json)."""
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM scan_snapshots WHERE id = ?", (snapshot_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d['data'] = json.loads(d.get('data_json') or '[]')
        d['per_subgolongan'] = json.loads(d.get('jumlah_per_subgolongan') or '{}')
    except Exception:
        d['data'] = []
        d['per_subgolongan'] = {}
    return d


# =========================================================
# TREN (untuk grafik)
# =========================================================
def get_tren(kota, keyword, limit=24):
    """
    Data tren jumlah kompetitor dari waktu ke waktu.
    Return: list dict { snapshot_at, label, jumlah }.
    Urut dari lama -> baru (biar langsung bisa di-plot).
    """
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT snapshot_at, label, jumlah
        FROM scan_snapshots
        WHERE kota = ? AND keyword = ?
        ORDER BY snapshot_at ASC
        LIMIT ?
    """, (kota, keyword, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_kombinasi():
    """
    Semua pasangan (kota, keyword) yang punya snapshot.
    Dipakai untuk dropdown di UI.
    Return: list of dict { kota, keyword, jumlah_snapshot, terakhir }.
    """
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT kota, keyword,
               COUNT(*) AS jumlah_snapshot,
               MAX(snapshot_at) AS terakhir
        FROM scan_snapshots
        GROUP BY kota, keyword
        ORDER BY terakhir DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================================================
# COMPARE (untuk fitur B: bandingkan 2 snapshot)
# =========================================================
def compare_snapshots(id1, id2):
    """
    Bandingkan 2 snapshot.
    Return dict dengan:
      - snapshot_1, snapshot_2 (metadata + data lengkap)
      - kota_sama: bool
      - baru: list item yang ADA di snapshot 2 tapi TIDAK di snapshot 1
      - hilang: list item yang ADA di snapshot 1 tapi TIDAK di snapshot 2
      - tetap: list item yang ADA di keduanya
      - delta_jumlah: int (jumlah2 - jumlah1)
    """
    s1 = get_snapshot_by_id(id1)
    s2 = get_snapshot_by_id(id2)
    if not s1 or not s2:
        return None

    def _key(item):
        # Kunci unik: nama + jarak (biar tidak false-match)
        nama = (item.get('nama') or '').strip().lower()
        jarak = round(float(item.get('jarak_km') or 0), 2)
        return f"{nama}|{jarak}"

    set1 = {_key(b): b for b in s1.get('data', [])}
    set2 = {_key(b): b for b in s2.get('data', [])}

    baru = [set2[k] for k in set2 if k not in set1]
    hilang = [set1[k] for k in set1 if k not in set2]
    tetap = [set2[k] for k in set2 if k in set1]

    return {
        'snapshot_1': s1,
        'snapshot_2': s2,
        'kota_sama': (s1.get('kota') == s2.get('kota')
                      and s1.get('keyword') == s2.get('keyword')),
        'baru': baru,
        'hilang': hilang,
        'tetap': tetap,
        'delta_jumlah': (s2.get('jumlah') or 0) - (s1.get('jumlah') or 0),
    }


# =========================================================
# DELETE / STATS
# =========================================================
def delete_snapshot(snapshot_id):
    """Hapus 1 snapshot."""
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM scan_snapshots WHERE id = ?", (snapshot_id,))
    conn.commit()
    conn.close()


def stats_snapshot():
    """Statistik tabel snapshot."""
    init_snapshot_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(jumlah) FROM scan_snapshots")
    total_entries, total_data = c.fetchone()
    c.execute("""SELECT kota, keyword, COUNT(*) FROM scan_snapshots
                 GROUP BY kota, keyword ORDER BY COUNT(*) DESC LIMIT 5""")
    top = c.fetchall()
    conn.close()
    return {
        'entries': total_entries or 0,
        'total_data': total_data or 0,
        'top_kombinasi': [
            {'kota': r[0], 'keyword': r[1], 'jumlah_snapshot': r[2]} for r in top
        ],
    }


# =========================================================
# CLI: python backend/db/snapshot_db.py
# =========================================================
if __name__ == "__main__":
    init_snapshot_table()
    print(f"[OK] Snapshot DB siap: {DB_PATH}")
    print(f"[INFO] Stats: {stats_snapshot()}")