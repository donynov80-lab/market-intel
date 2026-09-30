"""generate_kbli_osm.py — auto-generate OSM mapping untuk semua KBLI 4-digit."""
import json
from pathlib import Path
from collections import Counter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.db.kbli_osm_rules import suggest_osm_tags

# Baca KBLI lengkap
with Path("db_eksternal/kbli_lengkap.json").open(encoding="utf-8") as f:
    data = json.load(f)

# Filter KBLI 4-digit saja
kbli_4d = {}
for entry in data:
    code = str(entry.get("code", "")).strip()
    base = code.split(".")[0]
    if len(base) == 4:
        kbli_4d[base] = entry.get("title", "")

print(f"📊 Total KBLI 4-digit: {len(kbli_4d)}\n")

# Generate mapping
mapping = {}
stats = Counter()
for kode, title in sorted(kbli_4d.items()):
    tags = suggest_osm_tags(title)
    mapping[kode] = {
        "title": title,
        "osm_tags": tags,
        "auto": True,
    }
    if tags:
        stats["dengan_mapping"] += 1
    else:
        stats["tanpa_mapping"] += 1

print(f"✅ KBLI dengan mapping OSM: {stats['dengan_mapping']}")
print(f"⚠️  KBLI tanpa mapping (auto-reject): {stats['tanpa_mapping']}\n")

# Simpan
out = Path("db_eksternal/kbli_osm_mapping.json")
with out.open("w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"💾 Tersimpan: {out}")
print(f"   Ukuran: {out.stat().st_size / 1024:.1f} KB\n")

# Tampilkan 30 KBLI yang PUNYA mapping (untuk spot check)
print("=== 30 KBLI pertama yang punya mapping ===")
count = 0
for kode, v in mapping.items():
    if v["osm_tags"]:
        print(f"  {kode}: {v['title'][:55]}")
        print(f"        → {v['osm_tags']}")
        count += 1
        if count >= 30:
            break

print(f"\n=== 20 KBLI yang TIDAK punya mapping (auto-reject) ===")
count = 0
for kode, v in mapping.items():
    if not v["osm_tags"]:
        print(f"  {kode}: {v['title'][:60]}")
        count += 1
        if count >= 20:
            break