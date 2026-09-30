"""diagnose_kbli.py — lihat distribusi KBLI dari kbli_lengkap.json"""
import json
from collections import Counter
from pathlib import Path

# Baca file
path = Path("db_eksternal/kbli_lengkap.json")
with path.open(encoding="utf-8") as f:
    data = json.load(f)

print(f"📊 Total entry: {len(data)}\n")

# === Distribusi per level (panjang kode) ===
levels = Counter()
for entry in data:
    code = str(entry.get("code", "")).strip()
    # Ambil bagian sebelum titik, hitung panjang
    base = code.split(".")[0]
    levels[len(base)] += 1

print("=== Distribusi per Level ===")
for lvl in sorted(levels.keys()):
    nama_lvl = {2: "Golongan Pokok", 3: "Golongan",
                4: "Subgolongan", 5: "Kelompok"}.get(lvl, "?")
    print(f"  Level {lvl} ({nama_lvl:16}): {levels[lvl]:>5} entry")

# === Distribusi per kategori (2-digit) ===
print("\n=== Distribusi per Kategori (2-digit) ===")
kat = Counter()
contoh = {}
for entry in data:
    code = str(entry.get("code", "")).strip()
    base = code.split(".")[0]
    if len(base) == 2:
        kat[base] += 1
        if base not in contoh:
            contoh[base] = entry.get("title", "")[:60]

for kode in sorted(kat.keys()):
    print(f"  {kode}: {kat[kode]:>5} | {contoh.get(kode, '')}")

# === KBLI 4-digit terkait MAKANAN/MINUMAN ===
print("\n=== KBLI 4-digit: MAKANAN/MINUMAN (relevan UMKM) ===")
keywords_fnb = ["roti", "kue", "makanan", "minuman", "kopi", "restoran",
                "katering", "kedai", "warung", "bakery", "pastry"]
count = 0
for entry in data:
    code = str(entry.get("code", "")).strip()
    base = code.split(".")[0]
    title = entry.get("title", "").lower()
    if len(base) == 4 and any(k in title for k in keywords_fnb):
        print(f"  {base}: {entry['title'][:75]}")
        count += 1
print(f"  → Total: {count} KBLI 4-digit terkait F&B\n")

# === KBLI 4-digit terkait JASA ===
print("=== KBLI 4-digit: JASA (relevan UMKM) ===")
keywords_jasa = ["reparasi", "perawatan", "salon", "laundry",
                 "penginapan", "hotel", "klinik", "pendidikan",
                 "hiburan", "pijat", "fotografi"]
count = 0
for entry in data:
    code = str(entry.get("code", "")).strip()
    base = code.split(".")[0]
    title = entry.get("title", "").lower()
    if len(base) == 4 and any(k in title for k in keywords_jasa):
        print(f"  {base}: {entry['title'][:75]}")
        count += 1
print(f"  → Total: {count} KBLI 4-digit terkait Jasa")