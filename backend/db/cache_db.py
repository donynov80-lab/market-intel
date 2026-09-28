"""
cache_db.py
Cache hasil scan kompetitor — biar tidak hit Overpass API terus.
Data disimpan 7 hari, kalau ada cache pakai langsung.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def init_cache_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_kompetitor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            radius_km REAL NOT NULL,
            keyword TEXT NOT NULL,
            jumlah INTEGER DEFAULT 0,
            data_json TEXT,
            cached_at TEXT NOT NULL,
            UNIQUE(lat, lon, radius_km, keyword)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_lookup
        ON cache_kompetitor (lat, lon, radius_km, keyword)
    """)
    conn.commit()
    conn.close()


def get_cached(lat, lon, radius_km, keyword, max_age_hours=168):
    """Ambil dari cache kalau ada dan belum expired."""
    init_cache_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

    c.execute("""
        SELECT data_json, cached_at, jumlah FROM cache_kompetitor
        WHERE lat = ? AND lon = ? AND radius_km = ? AND keyword = ?
          AND cached_at > ?
    """, (lat, lon, radius_km, keyword, cutoff))

    row = c.fetchone()
    conn.close()

    if row:
        return {
            'data': json.loads(row['data_json']),
            'cached_at': row['cached_at'],
            'jumlah': row['jumlah'],
        }
    return None


def save_cache(lat, lon, radius_km, keyword, data):
    """Simpan hasil scan ke cache."""
    init_cache_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat(timespec='seconds')

    try:
        conn.execute("""
            INSERT OR REPLACE INTO cache_kompetitor
            (lat, lon, radius_km, keyword, jumlah, data_json, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lat, lon, radius_km, keyword, len(data),
              json.dumps(data, ensure_ascii=False), now))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Gagal simpan cache: {e}")
    finally:
        conn.close()


def stats_cache():
    """Statistik cache."""
    init_cache_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(jumlah) FROM cache_kompetitor")
    total_entries, total_rows = c.fetchone()
    conn.close()
    return {
        'entries': total_entries or 0,
        'total_data': total_rows or 0,
    }


def clear_cache(keyword=None):
    """Hapus cache (semua atau per keyword)."""
    init_cache_table()
    conn = sqlite3.connect(DB_PATH)
    if keyword:
        conn.execute("DELETE FROM cache_kompetitor WHERE keyword = ?", (keyword,))
    else:
        conn.execute("DELETE FROM cache_kompetitor")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_cache_table()
    print(f"✅ Cache DB siap: {DB_PATH}")
    print(f"📊 Stats: {stats_cache()}")