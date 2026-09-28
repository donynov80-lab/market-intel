"""
trending_db.py
SQLite manager untuk menyimpan data trending Google.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def init_db():
    """Buat tabel kalau belum ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trending (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            region      TEXT NOT NULL,
            rank        INTEGER NOT NULL,
            keyword     TEXT NOT NULL,
            source      TEXT DEFAULT 'google_rss',
            collected_at TEXT NOT NULL,
            UNIQUE(region, keyword, collected_at)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_region_rank
        ON trending (region, rank)
    """)
    conn.commit()
    conn.close()


def simpan_trending(region, keywords, source='google_rss'):
    """
    Simpan list keyword trending ke DB.
    
    Args:
        region (str): kode region, contoh 'ID', 'US'
        keywords (list): list of dict {'rank': 1, 'keyword': 'xxx'}
        source (str): sumber data
    
    Returns:
        int: jumlah baris yang disimpan
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat(timespec='seconds')

    count = 0
    for item in keywords:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO trending 
                (region, rank, keyword, source, collected_at)
                VALUES (?, ?, ?, ?, ?)
            """, (region, item['rank'], item['keyword'], source, now))
            count += 1
        except Exception as e:
            print(f"⚠️ Skip '{item.get('keyword')}': {e}")

    conn.commit()
    conn.close()
    return count


def ambil_trending(region='ID', limit=None, urut_terbaru=True):
    """
    Ambil trending dari DB, sorted by rank.
    
    Args:
        region (str): filter region
        limit (int): batasi jumlah. None = semua
        urut_terbaru (bool): ambil hanya snapshot terbaru
    
    Returns:
        list of tuples: [(rank, keyword, collected_at), ...]
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if urut_terbaru:
        # Ambil snapshot terbaru saja
        c.execute("""
            SELECT rank, keyword, collected_at
            FROM trending
            WHERE region = ?
              AND collected_at = (
                  SELECT MAX(collected_at) FROM trending WHERE region = ?
              )
            ORDER BY rank ASC
        """, (region, region))
    else:
        c.execute("""
            SELECT rank, keyword, collected_at
            FROM trending
            WHERE region = ?
            ORDER BY collected_at DESC, rank ASC
        """, (region,))

    rows = c.fetchall()
    if limit:
        rows = rows[:limit]

    conn.close()
    return rows


def hitung_total(region=None):
    """Hitung total row di DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if region:
        c.execute("SELECT COUNT(*) FROM trending WHERE region = ?", (region,))
    else:
        c.execute("SELECT COUNT(*) FROM trending")
    total = c.fetchone()[0]
    conn.close()
    return total


def list_region():
    """List semua region yang ada di DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT region FROM trending ORDER BY region")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print(f"✅ Database dibuat di: {DB_PATH}")
    print(f"📊 Total trending tersimpan: {hitung_total()}")
    print(f"🌏 Region tersedia: {list_region()}")

# =========================================================
# FUNGSI UNTUK AUTOCOMPLETE
# =========================================================

def init_autocomplete_table():
    """Buat tabel untuk menyimpan autocomplete keyword."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS autocomplete (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            seed        TEXT NOT NULL,
            keyword     TEXT NOT NULL,
            kategori    TEXT,
            level       INTEGER DEFAULT 1,
            collected_at TEXT NOT NULL,
            UNIQUE(seed, keyword)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_autocomplete_seed
        ON autocomplete (seed)
    """)
    conn.commit()
    conn.close()


def simpan_autocomplete(seed, keywords, level=1):
    """Simpan list keyword autocomplete."""
    init_autocomplete_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat(timespec='seconds')

    count = 0
    for kw in keywords:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO autocomplete
                (seed, keyword, level, collected_at)
                VALUES (?, ?, ?, ?)
            """, (seed, kw, level, now))
            count += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    return count


def ambil_autocomplete_db(seed=None, limit=None):
    """Ambil autocomplete dari DB."""
    init_autocomplete_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if seed:
        c.execute("""
            SELECT DISTINCT keyword FROM autocomplete
            WHERE seed = ?
            ORDER BY keyword ASC
        """, (seed,))
    else:
        c.execute("""
            SELECT DISTINCT keyword FROM autocomplete
            ORDER BY seed ASC, keyword ASC
        """)

    rows = [r[0] for r in c.fetchall()]
    if limit:
        rows = rows[:limit]
    conn.close()
    return rows


def hitung_total_autocomplete():
    """Hitung total autocomplete."""
    init_autocomplete_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM autocomplete")
    total = c.fetchone()[0]
    conn.close()
    return total