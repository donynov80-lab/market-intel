"""
scan_multi.py
Scan multi-keyword dengan logika OR.

Cara kerja:
  1. Loop tiap keyword, panggil scan_sekitar
  2. Gabung hasil
  3. Dedupe berdasarkan fingerprint (nama + lat + lon)
  4. Tandai kolom 'keyword_sumber' = keyword mana yang menemukan

Optimasi:
  - Maks per keyword = maks_total / jumlah_keyword (biar adil)
  - Kalau hasil 1 keyword sudah mentok, dedupe akan kurangi redundansi
"""
from backend.modules.maps_scanner import scan_sekitar


def _fingerprint(item):
    """Kunci unik: nama + lat/lon dibulatkan 4 desimal."""
    nama = (item.get('nama') or '').strip().lower()
    try:
        lat = round(float(item.get('lat') or 0), 4)
        lon = round(float(item.get('lon') or 0), 4)
    except (ValueError, TypeError):
        lat = lon = 0
    return f"{nama}|{lat}|{lon}"


def scan_multi(lat, lon, radius_m, keywords,
               maks_total=300, progress_callback=None):
    """
    Scan multi-keyword. Gabungkan hasil, dedupe, tandai sumber.

    Args:
        lat, lon        : titik pusat
        radius_m        : radius (meter)
        keywords        : list keyword (mis. ["roti", "kue", "cake"])
        maks_total      : total maks hasil akhir (dibagi rata antar keyword)
        progress_callback : function(i, total, keyword) untuk progress bar

    Return:
        {
          'success': True/False,
          'data': [item1, item2, ...],  # unik + ada 'keyword_sumber'
          'total_unik': int,
          'total_keywords': int,
          'per_keyword': {kw: jumlah},
          'error': str,
        }
    """
    # Bersihkan keyword
    keywords = [k.strip() for k in (keywords or []) if k and k.strip()]
    if not keywords:
        return {
            'success': False, 'data': [],
            'error': 'Tidak ada keyword', 'total_unik': 0,
            'total_keywords': 0, 'per_keyword': {},
        }

    # Distribusi maks per keyword (minimum 50)
    n = len(keywords)
    maks_per_kw = max(50, maks_total // n)

    seen = set()
    semua = []
    per_kw = {}
    error_list = []

    for i, kw in enumerate(keywords):
        if progress_callback:
            try:
                progress_callback(i, n, kw)
            except Exception:
                pass

        try:
            r = scan_sekitar(
                lat, lon,
                radius_m=int(radius_m),
                keyword=kw,
                maks=maks_per_kw,
            )
            data = r.get('data', []) or []
            per_kw[kw] = len(data)

            for item in data:
                fp = _fingerprint(item)
                if fp in seen:
                    continue
                seen.add(fp)
                # Tandai dari keyword mana (kalau sudah ada, gabung)
                item['keyword_sumber'] = kw
                semua.append(item)

        except Exception as e:
            per_kw[kw] = f"error: {str(e)[:80]}"
            error_list.append(f"{kw}: {e}")

    # Sort berdasarkan jarak
    semua.sort(key=lambda x: x.get('jarak_km') or 999)

    return {
        'success': len(semua) > 0,
        'data': semua[:maks_total],
        'total_unik': len(semua),
        'total_keywords': n,
        'per_keyword': per_kw,
        'error': '; '.join(error_list) if error_list and not semua else '',
        'maks_per_kw': maks_per_kw,
    }


if __name__ == "__main__":
    # Test cepat
    hasil = scan_multi(
        lat=-6.2615, lon=106.8106, radius_m=5000,
        keywords=["roti", "kue", "bakery"],
        maks_total=150,
    )
    print(f"Total unik: {hasil['total_unik']}")
    print(f"Per keyword: {hasil['per_keyword']}")