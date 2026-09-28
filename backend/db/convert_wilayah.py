"""
convert_wilayah.py
Convert file SQL cahyadsn (MySQL dump) → SQLite tabel `wilayah_lengkap`.
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"
DB_EKSTERNAL = Path(__file__).parent.parent.parent / "db_eksternal"


def parse_sql_file(filepath):
    """Parse SQL file cahyadsn → list of dict."""
    print(f"📖 Baca {filepath.name}...")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Regex: match tuple dari (' sampai path start (')
    pattern = re.compile(
        r"\("
        r"'([^']+)',"                         # kode
        r"'([^']+)',"                         # nama
        r"'([^']*)',\s*"                      # ibukota
        r"([\d.eE+-]+|NULL),\s*"              # lat
        r"([\d.eE+-]+|NULL),\s*"              # lng
        r"([\d.eE+-]+|NULL),\s*"              # elv
        r"([\d.eE+-]+|NULL),\s*"              # tz
        r"([\d.eE+-]+|NULL),\s*"              # luas
        r"([\d.eE+-]+|NULL),\s*"              # penduduk
        r"'",                                  # path start marker
        re.DOTALL
    )

    hasil = []
    for m in pattern.finditer(content):
        kode, nama, ibukota, lat, lng, elv, tz, luas, penduduk = m.groups()

        def to_float(x):
            if x == 'NULL' or not x:
                return None
            try:
                return float(x)
            except:
                return None

        def to_int(x):
            v = to_float(x)
            return int(v) if v is not None else None

        hasil.append({
            'kode': kode.strip(),
            'nama': nama.strip(),
            'ibukota': ibukota.strip() if ibukota else '',
            'lat': to_float(lat),
            'lng': to_float(lng),
            'luas': to_float(luas),
            'penduduk': to_int(penduduk),
        })

    return hasil


def init_wilayah_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wilayah_lengkap (
            kode            TEXT PRIMARY KEY,
            nama            TEXT NOT NULL,
            ibukota         TEXT,
            level           INTEGER,
            provinsi_kode   TEXT,
            provinsi_nama   TEXT,
            lat             REAL,
            lng             REAL,
            luas            REAL,
            penduduk       INTEGER
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_wilayah_nama
        ON wilayah_lengkap (nama)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_wilayah_prov
        ON wilayah_lengkap (provinsi_kode)
    """)
    conn.commit()
    conn.close()


def insert_wilayah(rows):
    """Insert ke SQLite + isi kolom provinsi otomatis."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Kumpulkan provinsi dulu (level 1)
    provinsi_map = {}
    for r in rows:
        if '.' not in r['kode']:
            provinsi_map[r['kode']] = r['nama']

    count = 0
    for r in rows:
        kode = r['kode']
        level = 1 if '.' not in kode else 2
        prov_kode = kode.split('.')[0] if '.' in kode else kode
        prov_nama = provinsi_map.get(prov_kode, '') if level == 2 else r['nama']

        try:
            c.execute("""
                INSERT OR REPLACE INTO wilayah_lengkap
                (kode, nama, ibukota, level, provinsi_kode, provinsi_nama,
                 lat, lng, luas, penduduk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (kode, r['nama'], r['ibukota'], level, prov_kode, prov_nama,
                  r['lat'], r['lng'], r['luas'], r['penduduk']))
            count += 1
        except Exception as e:
            print(f"⚠️ {kode}: {e}")

    conn.commit()
    conn.close()
    return count


def main():
    init_wilayah_table()

    # Cari semua file SQL
    sql_files = [
        "wilayah_level_1_2.sql",
        "wilayah_2025.sql",
        "wilayah_2023.sql",
    ]

    total_inserted = 0
    for filename in sql_files:
        filepath = DB_EKSTERNAL / filename
        if not filepath.exists():
            print(f"⚠️ Skip {filename} (tidak ada)")
            continue

        rows = parse_sql_file(filepath)
        print(f"   Ditemukan {len(rows)} baris")

        count = insert_wilayah(rows)
        print(f"   ✅ {count} baris di-insert")
        total_inserted += count

    # Verifikasi
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wilayah_lengkap")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wilayah_lengkap WHERE level=1")
    prov = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wilayah_lengkap WHERE level=2")
    kab = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wilayah_lengkap WHERE lat IS NOT NULL")
    ber_koordinat = c.fetchone()[0]

    print(f"\n📊 Hasil:")
    print(f"   Total: {total}")
    print(f"   Provinsi: {prov}")
    print(f"   Kab/Kota: {kab}")
    print(f"   Ber-koordinat: {ber_koordinat}")

    # Test cari
    print(f"\n🔍 Test cari 'jakarta':")
    c.execute("""
        SELECT kode, nama, provinsi_nama, lat, lng, penduduk
        FROM wilayah_lengkap
        WHERE LOWER(nama) LIKE '%jakarta%'
        ORDER BY level DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"   {row[0]} | {row[1]} | {row[2]} | lat: {row[3]} | penduduk: {row[5]}")

    conn.close()


if __name__ == "__main__":
    main()