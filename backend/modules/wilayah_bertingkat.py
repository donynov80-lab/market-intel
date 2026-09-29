"""
wilayah_bertingkat.py
Helper untuk dropdown wilayah bertingkat dari tabel wilayah_lengkap.

Fungsi:
  - list_provinsi()         -> daftar 38 provinsi
  - list_kota(provinsi_kode) -> daftar 514 kota/kab di provinsi tsb
  - get_lokasi(kode)         -> ambil 1 lokasi by kode
  - get_lokasi_by_nama(nama) -> cari by nama (untuk fallback)
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_intel.db"


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def list_provinsi():
    """Daftar provinsi (level=1). Return list dict."""
    con = _conn()
    c = con.cursor()
    c.execute("""
        SELECT kode, nama, lat, lng, luas, penduduk
        FROM wilayah_lengkap
        WHERE level = 1
        ORDER BY nama
    """)
    hasil = [dict(r) for r in c.fetchall()]
    con.close()
    return hasil


def list_kota(provinsi_kode):
    """Daftar kota/kab (level=2) di provinsi tertentu."""
    if not provinsi_kode:
        return []
    con = _conn()
    c = con.cursor()
    c.execute("""
        SELECT kode, nama, provinsi_nama, lat, lng, luas, penduduk
        FROM wilayah_lengkap
        WHERE level = 2 AND provinsi_kode = ?
        ORDER BY nama
    """, (provinsi_kode,))
    hasil = [dict(r) for r in c.fetchall()]
    con.close()
    return hasil


def get_lokasi(kode):
    """Ambil 1 lokasi by kode (level apapun)."""
    if not kode:
        return None
    con = _conn()
    c = con.cursor()
    c.execute("""
        SELECT kode, nama, level, provinsi_kode, provinsi_nama,
               lat, lng, luas, penduduk
        FROM wilayah_lengkap
        WHERE kode = ?
        LIMIT 1
    """, (kode,))
    row = c.fetchone()
    con.close()
    return dict(row) if row else None


def get_lokasi_by_nama(nama):
    """Cari lokasi by nama exact (case-insensitive)."""
    if not nama:
        return None
    con = _conn()
    c = con.cursor()
    c.execute("""
        SELECT kode, nama, level, provinsi_kode, provinsi_nama,
               lat, lng, luas, penduduk
        FROM wilayah_lengkap
        WHERE LOWER(nama) = LOWER(?)
        ORDER BY level
        LIMIT 1
    """, (nama,))
    row = c.fetchone()
    con.close()
    return dict(row) if row else None


# =========================================================
# Adapter: konversi ke format yang dipakai Tab Kompetitor
# =========================================================
def ke_format_kota_data(lokasi):
    """
    Konversi hasil query DB -> format dict yang dipakai Tab Kompetitor.
    Format output sama persis dengan cari_kota_lengkap().
    """
    if not lokasi:
        return None

    level = lokasi.get('level', 0)
    nama = lokasi.get('nama', '-')
    provinsi = lokasi.get('provinsi_nama') or '-'

    if level == 1:
        display = f"🏛️ {nama} (Provinsi)"
    elif level == 2:
        display = f"🏙️ {nama} — {provinsi}"
    else:
        display = f"{nama} — {provinsi}"

    return {
        'kode': lokasi.get('kode'),
        'kota': nama,                          # dipakai Tab Kompetitor
        'nama': nama,
        'provinsi': provinsi,
        'provinsi_kode': lokasi.get('provinsi_kode'),
        'display': display,
        'lat': lokasi.get('lat'),
        'lon': lokasi.get('lng'),              # note: DB pakai 'lng', UI pakai 'lon'
        'lng': lokasi.get('lng'),
        'luas': lokasi.get('luas') or 0,
        'penduduk': lokasi.get('penduduk') or 0,
        'level': level,
    }


if __name__ == "__main__":
    provs = list_provinsi()
    print(f"Total provinsi: {len(provs)}")
    if provs:
        print(f"  Contoh: {provs[0]['nama']} (kode={provs[0]['kode']})")
        kotas = list_kota(provs[0]['kode'])
        print(f"  Kota di {provs[0]['nama']}: {len(kotas)}")
        if kotas:
            print(f"    Contoh: {kotas[0]['nama']}")