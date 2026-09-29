"""test_snapshot.py — tes simpan & baca snapshot."""
from backend.db.snapshot_db import (
    save_snapshot, get_snapshots, get_tren, stats_snapshot
)

data_dummy = [
    {"nama": "Toko A", "code_4digit": "4722", "jarak_km": 1.2, "kategori": "shop=alcohol"},
    {"nama": "Toko B", "code_4digit": "4722", "jarak_km": 2.5, "kategori": "shop=wine"},
    {"nama": "Warung C", "code_4digit": "5610", "jarak_km": 3.0, "kategori": "amenity=restaurant"},
]

sid = save_snapshot(
    kota="Kota Denpasar, Bali",
    keyword="miras",
    radius_km=7,
    data=data_dummy,
    provinsi="Bali",
    lat=-8.65, lon=115.21,
    label="Tes Snapshot Pertama",
    catatan="Tes dari CLI",
)
print(f"Snapshot dibuat, id={sid}")

print("\n=== Daftar snapshot ===")
for s in get_snapshots():
    print(f"  id={s['id']} | {s['label']} | {s['kota']} | {s['keyword']} | {s['jumlah']} item")

print("\n=== Tren ===")
for t in get_tren("Kota Denpasar, Bali", "miras"):
    print(f"  {t['snapshot_at']} | {t['label']} | {t['jumlah']}")

print(f"\n=== Stats ===\n{stats_snapshot()}")