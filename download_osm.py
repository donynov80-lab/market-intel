"""download_osm.py — Download OSM PBF per-kota dari BBBike."""
import requests
from pathlib import Path
from time import sleep

# Daftar kota besar Indonesia (BBBike naming)
CITIES = [
    "Jakarta",
    "Surabaya",
    "Bandung",
    "Medan",
    "Semarang",
    "Makassar",
    "Denpasar",
    "Yogyakarta",
    "Palembang",
    "Balikpapan",
]

BASE_URL = "https://download.bbbike.org/osm/bbbike/{city}/{city}.osm.pbf"
DEST_DIR = Path("data_osm/raw")
DEST_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "MarketIntelDashboard/1.0 (contact: donynov80@gmail.com)",
}

total_ok = 0
total_skip = 0
total_fail = 0

for city in CITIES:
    url = BASE_URL.format(city=city)
    dest = DEST_DIR / f"{city.lower()}.osm.pbf"
    
    # Skip kalau sudah ada
    if dest.exists() and dest.stat().st_size > 1_000_000:
        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"⏩ {city:15} — sudah ada ({size_mb:.1f} MB), skip")
        total_skip += 1
        continue
    
    print(f"\n📥 {city} — {url}")
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60,
                         allow_redirects=True)
        
        if r.status_code != 200:
            print(f"   ❌ HTTP {r.status_code}")
            total_fail += 1
            continue
        
        total_size = int(r.headers.get("Content-Length", 0))
        print(f"   📦 Ukuran: {total_size / 1024 / 1024:.1f} MB")
        
        downloaded = 0
        with dest.open("wb") as f:
            last_mb = 0
            for chunk in r.iter_content(chunk_size=1024 * 256):  # 256 KB
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                mb = downloaded / 1024 / 1024
                if mb - last_mb >= 5:
                    pct = (downloaded / total_size * 100) if total_size else 0
                    print(f"      ⏳ {mb:.0f} MB ({pct:.0f}%)")
                    last_mb = mb
        
        final_mb = dest.stat().st_size / 1024 / 1024
        print(f"   ✅ Selesai: {final_mb:.1f} MB")
        total_ok += 1
        sleep(1)  # Sopan ke server
    
    except KeyboardInterrupt:
        print("\n\n⚠️  User cancel.")
        break
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:80]}")
        total_fail += 1

print(f"\n{'='*60}")
print(f"📊 Ringkasan:")
print(f"   ✅ Sukses download : {total_ok}")
print(f"   ⏩ Sudah ada       : {total_skip}")
print(f"   ❌ Gagal           : {total_fail}")
print(f"{'='*60}")

# List file yang ada
print(f"\n📁 File di {DEST_DIR}:")
total_mb = 0
for f in sorted(DEST_DIR.glob("*.osm.pbf")):
    mb = f.stat().st_size / 1024 / 1024
    total_mb += mb
    print(f"   {f.name:25} {mb:>7.1f} MB")
print(f"   {'TOTAL':25} {total_mb:>7.1f} MB")