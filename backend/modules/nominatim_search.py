"""
nominatim_search.py
Pencarian nama tempat via Nominatim (OSM).
Gratis, tanpa API key. Rate limit resmi: 1 req/detik.

Fungsi:
  search_nominatim(keyword, lat, lon, radius_km, limit) -> list of dict

Kompatibel dengan output scan_sekitar().
"""
import requests
import math

USER_AGENT = "MarketIntelDashboard/1.0 (contact: donynov80@gmail.com)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def search_nominatim(keyword, lat, lon, radius_km=5, limit=50):
    """
    Cari tempat via Nominatim berdasarkan nama.

    Args:
        keyword:   kata kunci (spa, massage, karaoke)
        lat, lon:  pusat pencarian
        radius_km: radius
        limit:     maksimum hasil (max 50 dari Nominatim)

    Return:
        list of dict: {nama, lat, lon, alamat, kategori, jarak_km,
                        kontak, jam_buka, sumber}
    """
    if not keyword or not lat or not lon:
        return []

    # Bounding box dari radius
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    viewbox = f"{lon - dlon},{lat + dlat},{lon + dlon},{lat - dlat}"

    params = {
        "q": keyword,
        "format": "json",
        "limit": min(limit, 50),
        "addressdetails": 1,
        "extratags": 1,
        "bounded": 1,
        "viewbox": viewbox,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        r = requests.get(NOMINATIM_URL, params=params,
                         headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"[Nominatim] HTTP {r.status_code}")
            return []

        data = r.json()
        results = []
        for item in data:
            try:
                plat = float(item["lat"])
                plon = float(item["lon"])
            except (KeyError, ValueError):
                continue

            tags = item.get("extratags") or {}
            kategori = []
            for k in ["shop", "amenity", "leisure", "tourism", "craft"]:
                if k in tags:
                    kategori.append(f"{k}={tags[k]}")

            nama = item.get("name") or \
                item.get("display_name", "").split(",")[0].strip()

            results.append({
                "nama": nama or "Tanpa nama",
                "lat": plat,
                "lon": plon,
                "alamat": (item.get("display_name") or "-")[:200],
                "kategori": ", ".join(kategori) if kategori else "-",
                "jarak_km": round(_haversine(lat, lon, plat, plon), 2),
                "kontak": "-",
                "jam_buka": "-",
                "sumber": "nominatim",
            })

        # Filter ketat radius
        results = [r for r in results if r["jarak_km"] <= radius_km * 1.1]

        # === FILTER NOISE ===
        # 1. Buang gelar dokter: "dr X SpA", "Dr. Y Sp.A", "SpOG", dll.
        # 2. Buang jika nama diawali "dr " atau "drg " dan mengandung "Sp"
        import re as _re
        _gelar_dokter = _re.compile(
            r'\b(dr|drg|dr\.|drg\.)\s+\S+.*\b(sp\.?[a-z]{2,4}|spa)\b',
            _re.IGNORECASE
        )

        filtered = []
        for r in results:
            nama = r["nama"]
            # Skip kalau nama match pattern dokter
            if _gelar_dokter.search(nama):
                continue
            # Skip kalau nama berakhir dengan " SpA" dan ada "dr "
            if _re.search(r'\b(dr|drg)\b', nama, _re.IGNORECASE) and \
               _re.search(r'\bsp\.?a\b', nama, _re.IGNORECASE):
                continue
            filtered.append(r)

        return filtered

    except Exception as e:
        print(f"[Nominatim] Exception: {e}")
        return []


if __name__ == "__main__":
    test_kw = "spa"
    test_lat = -6.2615
    test_lon = 106.8106  # Jakarta Selatan
    test_radius = 15

    print(f"🔍 Test: '{test_kw}' di ({test_lat}, {test_lon}), "
          f"radius {test_radius} km\n")
    hasil = search_nominatim(test_kw, test_lat, test_lon,
                             radius_km=test_radius, limit=30)
    print(f"Total: {len(hasil)} hasil\n")
    for i, h in enumerate(hasil[:15], 1):
        print(f"{i:2}. {h['nama'][:42]:44} | "
              f"{h['jarak_km']:>5.1f} km | {h['kategori'][:30]}")