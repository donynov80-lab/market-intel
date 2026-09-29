"""test_master.py — tes akumulasi master kompetitor."""
from backend.db.master_db import (
    upsert_master_batch, get_master, get_master_stats, clear_master
)

# Bersihkan dulu (biar tes bersih)
clear_master()
print("[1] Master dibersihkan\n")

# === SCAN PERTAMA: 3 toko ===
scan1 = [
    {"nama": "Warung Tuak", "lat": -8.65, "lon": 115.21,
     "code_4digit": "4722", "subgolongan_title": "Perdagangan Eceran Minuman",
     "alamat": "Jl. Legian", "kontak": "+62811"},
    {"nama": "Bali Wine", "lat": -8.66, "lon": 115.22,
     "code_4digit": "4722", "subgolongan_title": "Perdagangan Eceran Minuman"},
    {"nama": "Toko Arak", "lat": -8.67, "lon": 115.23,
     "code_4digit": "4722", "subgolongan_title": "Perdagangan Eceran Minuman"},
]
r1 = upsert_master_batch(scan1, keyword="miras", kota="Kota Denpasar, Bali")
print(f"[2] Scan 1: {r1}\n")

# === SCAN KEDUA (bulan depan): 2 toko lama + 1 toko BARU ===
scan2 = [
    {"nama": "Warung Tuak", "lat": -8.65, "lon": 115.21,
     "code_4digit": "4722"},  # sudah ada
    {"nama": "Bali Wine", "lat": -8.66, "lon": 115.22,
     "code_4digit": "4722"},  # sudah ada
    {"nama": "Spirit Baru", "lat": -8.68, "lon": 115.24,
     "code_4digit": "4722"},  # BARU!
]
r2 = upsert_master_batch(scan2, keyword="miras", kota="Kota Denpasar, Bali")
print(f"[3] Scan 2: {r2}")
print(f"    (harusnya: baru=1, update=2, skip=0)\n")

# === SCAN KETIGA: keyword BERBEDA, toko yang sama ===
scan3 = [
    {"nama": "Warung Tuak", "lat": -8.65, "lon": 115.21,
     "code_4digit": "4722"},
]
r3 = upsert_master_batch(scan3, keyword="alkohol", kota="Kota Denpasar, Bali")
print(f"[4] Scan 3 (keyword 'alkohol'): {r3}")
print(f"    (harusnya: update=1 — 'Warung Tuak' dapat keyword baru)\n")

# === LIHAT HASIL ===
print("=== MASTER KATALOG ===")
for m in get_master():
    print(f"  [{m['observation_count']}x] {m['nama']:<15} | "
          f"first={m['first_seen']} | keywords={m['keywords']}")

print(f"\n=== Stats ===\n{get_master_stats()}")