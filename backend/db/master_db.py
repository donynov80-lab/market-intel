"""
master_db.py
Katalog master kompetitor — akumulasi SEMUA toko yang PERNAH terlihat.

Beda dengan cache_kompetitor & scan_snapshots:
  - cache    = memo 7 hari (dibuang kalau expired)
  - snapshot = foto album bulanan (manual milestone)
  - master   = buku telepon permanen (semua toko unik, kapan pertama & terakhir)

Setiap scan sukses otomatis di-upsert ke master:
  - Kalau toko SUDAH ADA (fingerprint sama) -> update last_seen + observation_count
  - Kalau toko BARU -> insert baris baru

Fingerprint = sha1(nama_lower + lat_4desimal + lon_4desimal)
  -> nama sama, lokasi sama (dalam ~11m) = dianggap toko yang SAMA
  -> nama beda walau lokasi sama = dianggap toko BERBEDA
"""
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


# =========================================================
# FINGERPRINT
# =========================================================
def _fingerprint(nama, lat, lon):
    """Hash unik dari nama + koordinat (dibulatkan 4 desimal ~11m)."""
    nama_norm = (nama or '').strip().lower()
    try:
        lat_r = round(float(lat), 4) if lat is not None else 0
        lon_r = round(float(lon), 4) if lon is not None else 0
    except (ValueError, TypeError):
        return None
    raw = f"{nama_norm}|{lat_r}|{lon_r}"
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]


# =========================================================
# INIT
# =========================================================
def init_master_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS master_kompetitor (
            fingerprint TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            lat REAL,
            lon REAL,
            alamat TEXT,
            kontak TEXT,
            kategori_osm TEXT,
            code_4digit TEXT,
            subgolongan_title TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            observation_count INTEGER DEFAULT 1,
            keywords TEXT,
            kotas TEXT,
            status TEXT DEFAULT 'aktif',
            data_json TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_master_first_seen
        ON master_kompetitor (first_seen DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_master_last_seen
        ON master_kompetitor (last_seen DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_master_code
        ON master_kompetitor (code_4digit)
    """)
    conn.commit()
    conn.close()


# =========================================================
# UPSERT
# =========================================================
def upsert_master(business, keyword=None, kota=None):
    """
    Insert atau update 1 bisnis ke master.

    Return: 'baru' | 'update' | None (kalau di-skip, mis. tanpa koordinat)
    """
    init_master_table()

    nama = business.get('nama') or business.get('name') or 'Tanpa nama'
    lat = business.get('lat')
    lon = business.get('lon')

    fp = _fingerprint(nama, lat, lon)
    if not fp:
        return None

    now = datetime.now().isoformat(timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM master_kompetitor WHERE fingerprint = ?", (fp,))
    existing = c.fetchone()

    if existing:
        # Update observasi
        keywords = json.loads(existing['keywords'] or '[]')
        if keyword and keyword not in keywords:
            keywords.append(keyword)
        kotas = json.loads(existing['kotas'] or '[]')
        if kota and kota not in kotas:
            kotas.append(kota)

        # Update alamat/kontak hanya kalau yang baru lebih informatif
        alamat_baru = business.get('alamat')
        if alamat_baru in ('-', None, ''):
            alamat_baru = existing['alamat']
        kontak_baru = business.get('kontak')
        if kontak_baru in ('-', None, ''):
            kontak_baru = existing['kontak']

        conn.execute("""
            UPDATE master_kompetitor
            SET last_seen = ?,
                observation_count = observation_count + 1,
                keywords = ?,
                kotas = ?,
                alamat = ?,
                kontak = ?,
                subgolongan_title = COALESCE(?, subgolongan_title),
                code_4digit = COALESCE(?, code_4digit),
                data_json = ?
            WHERE fingerprint = ?
        """, (
            now,
            json.dumps(keywords, ensure_ascii=False),
            json.dumps(kotas, ensure_ascii=False),
            alamat_baru,
            kontak_baru,
            business.get('subgolongan_title'),
            business.get('code_4digit'),
            json.dumps(business, ensure_ascii=False),
            fp,
        ))
        conn.commit()
        conn.close()
        return 'update'
    else:
        keywords = [keyword] if keyword else []
        kotas = [kota] if kota else []
        alamat_baru = business.get('alamat')
        if alamat_baru in ('-', None, ''):
            alamat_baru = None
        kontak_baru = business.get('kontak')
        if kontak_baru in ('-', None, ''):
            kontak_baru = None

        conn.execute("""
            INSERT INTO master_kompetitor
            (fingerprint, nama, lat, lon, alamat, kontak, kategori_osm,
             code_4digit, subgolongan_title, first_seen, last_seen,
             observation_count, keywords, kotas, status, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'aktif', ?)
        """, (
            fp, nama, lat, lon, alamat_baru, kontak_baru,
            business.get('kategori'),
            business.get('code_4digit'),
            business.get('subgolongan_title'),
            now, now,
            json.dumps(keywords, ensure_ascii=False),
            json.dumps(kotas, ensure_ascii=False),
            json.dumps(business, ensure_ascii=False),
        ))
        conn.commit()
        conn.close()
        return 'baru'


def upsert_master_batch(businesses, keyword=None, kota=None):
    """Upsert banyak. Return {'baru':N, 'update':N, 'skip':N}."""
    stats = {'baru': 0, 'update': 0, 'skip': 0}
    for b in businesses or []:
        r = upsert_master(b, keyword=keyword, kota=kota)
        if r == 'baru':
            stats['baru'] += 1
        elif r == 'update':
            stats['update'] += 1
        else:
            stats['skip'] += 1
    return stats


# =========================================================
# GET / LIST
# =========================================================
def get_master(keyword=None, kota=None, code_4digit=None,
               baru_dalam_hari=None, cari_nama=None,
               limit=500, offset=0):
    """Ambil daftar master dengan filter."""
    init_master_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    q = "SELECT * FROM master_kompetitor WHERE 1=1"
    params = []

    if keyword:
        q += " AND keywords LIKE ?"
        params.append(f'%"{keyword}"%')
    if kota:
        q += " AND kotas LIKE ?"
        params.append(f'%"{kota}"%')
    if code_4digit:
        q += " AND code_4digit = ?"
        params.append(code_4digit)
    if cari_nama:
        q += " AND nama LIKE ?"
        params.append(f'%{cari_nama}%')
    if baru_dalam_hari:
        cutoff = (datetime.now() - timedelta(days=baru_dalam_hari)).isoformat()
        q += " AND first_seen >= ?"
        params.append(cutoff)

    q += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    c.execute(q, params)
    rows = c.fetchall()
    conn.close()

    hasil = []
    for r in rows:
        d = dict(r)
        try:
            d['keywords'] = json.loads(d.get('keywords') or '[]')
            d['kotas'] = json.loads(d.get('kotas') or '[]')
        except Exception:
            d['keywords'] = []
            d['kotas'] = []
        d.pop('data_json', None)
        hasil.append(d)
    return hasil


def get_master_by_fingerprint(fp):
    init_master_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM master_kompetitor WHERE fingerprint = ?", (fp,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# =========================================================
# STATS
# =========================================================
def get_master_stats():
    init_master_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM master_kompetitor")
    total = c.fetchone()[0] or 0

    cutoff_30 = (datetime.now() - timedelta(days=30)).isoformat()
    c.execute("SELECT COUNT(*) FROM master_kompetitor WHERE first_seen >= ?",
              (cutoff_30,))
    baru_30 = c.fetchone()[0] or 0

    c.execute("""SELECT code_4digit, COUNT(*) FROM master_kompetitor
                 WHERE code_4digit IS NOT NULL
                 GROUP BY code_4digit ORDER BY COUNT(*) DESC LIMIT 10""")
    top_kbli = [{'code': r[0], 'jumlah': r[1]} for r in c.fetchall()]

    c.execute("""SELECT keywords, COUNT(*) FROM master_kompetitor
                 GROUP BY keywords ORDER BY COUNT(*) DESC LIMIT 5""")
    top_keywords = [{'keywords': r[0], 'jumlah': r[1]} for r in c.fetchall()]

    conn.close()
    return {
        'total': total,
        'baru_30_hari': baru_30,
        'top_kbli': top_kbli,
        'top_keywords': top_keywords,
    }


# =========================================================
# DELETE / RESET
# =========================================================
def delete_master(fp):
    init_master_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM master_kompetitor WHERE fingerprint = ?", (fp,))
    conn.commit()
    conn.close()


def clear_master():
    init_master_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM master_kompetitor")
    conn.commit()
    conn.close()


# =========================================================
# CLI
# =========================================================
if __name__ == "__main__":
    init_master_table()
    print(f"[OK] Master DB siap: {DB_PATH}")
    print(f"[INFO] Stats: {get_master_stats()}")