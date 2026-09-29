"""cek_db.py — Diagnosa isi market_intel.db"""
import sqlite3
import os

DB = "market_intel.db"

if not os.path.exists(DB):
    print(f"❌ {DB} tidak ditemukan")
    raise SystemExit(1)

print(f"\n📦 DB: {DB} ({os.path.getsize(DB)/1024:.1f} KB)\n")

con = sqlite3.connect(DB)
c = con.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]

print(f"=== {len(tables)} TABEL DITEMUKAN ===\n")
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    n = c.fetchone()[0]
    print(f"  📋 {t:<30} {n:>6} baris")
    c.execute(f"PRAGMA table_info({t})")
    cols = c.fetchall()
    for col in cols:
        print(f"       - {col[1]:<25} {col[2]}")
    print()

con.close()
print("=== SELESAI ===")