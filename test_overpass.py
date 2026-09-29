"""
test_overpass.py — v2
Tes Overpass API dengan User-Agent resmi + delay antar request.
"""
import requests
from time import sleep

AREAS = {
    "Jakarta Pusat": (-6.22, 106.79, -6.14, 106.87),
    "Denpasar":      (-8.72, 115.15, -8.60, 115.28),
}

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# UA resmi — wajib ada kontak, jangan "Mozilla/5.0" polos
HEADERS = {
    "User-Agent": "MarketIntelDashboard/1.0 (contact: donynov80@gmail.com)",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}

def query(endpoint, bbox):
    s, w, n, e = bbox
    q = (
        f'[out:json][timeout:30];'
        f'node["shop"~"alcohol|wine|beverages"]({s},{w},{n},{e});'
        f'out center 30;'
    )
    try:
        r = requests.post(endpoint, data={"data": q}, headers=HEADERS, timeout=60)
        if r.status_code != 200:
            return f"HTTP {r.status_code} | {r.text[:100]}"
        elems = r.json().get("elements", [])
        names = [e.get("tags", {}).get("name", "?") for e in elems[:5]]
        return f"✅ {len(elems)} element(s) | contoh: {names}"
    except Exception as e:
        return f"ERROR: {str(e)[:80]}"


if __name__ == "__main__":
    for name, bbox in AREAS.items():
        print(f"\n=== {name} ===")
        for ep in ENDPOINTS:
            ep_short = ep.split("//")[1].split("/")[0]
            print(f"  [{ep_short:<28}] ", end="", flush=True)
            print(query(ep, bbox))
            sleep(2)  # JEDA 2 detik — jangan tembak cepat-cepat
    print("\n=== SELESAI ===")