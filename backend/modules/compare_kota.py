"""
compare_kota.py
Bandingkan 2 kota side-by-side untuk keyword & radius yang sama.

Fungsi utama:
  bandingkan_2_kota(kota_a, kota_b, keyword, radius_km=5)

Return dict berisi:
  - metrik per kota (total toko, density, KBLI, rata-rata jarak)
  - pemenang density
  - rekomendasi naratif
  - data chart (per KBLI)
  - snapshot_id (kalau berhasil auto-save)
"""
from typing import Optional


def _metrik_kota(kota: dict, keyword: str, radius_km: float,
                 kompetitor: Optional[list] = None) -> dict:
    """
    Hitung metrik lengkap untuk 1 kota.
    kota: dict dari cari_kota_lengkap() -> {kota, lat, lon, penduduk, luas, ...}
    """
    from backend.modules.maps_scanner import scan_sekitar, _analisis_peluang_single

    lat = kota.get('lat')
    lon = kota.get('lon')
    nama = kota.get('kota') or kota.get('nama') or '-'
    penduduk = kota.get('penduduk') or 0
    luas = kota.get('luas') or 0

    hasil = {
        'nama': nama,
        'lat': lat, 'lon': lon,
        'penduduk': penduduk,
        'luas': luas,
        'total_toko': 0,
        'density_per_10rb': None,
        'kblis': {},
        'rata_jarak_km': None,
        'jarak_max_km': None,
        'skor_peluang': None,
        'kategori': 'DATA TIDAK TERSEDIA',
        'rekomendasi': '',
        'top_toko': [],
        'error': None,
    }

    if not lat or not lon:
        hasil['error'] = f"{nama} tidak punya koordinat"
        return hasil

    # Scan atau pakai list yang sudah ada
    if kompetitor is None:
        try:
            scan = scan_sekitar(lat, lon, radius_m=int(radius_km * 1000),
                                keyword=keyword, maks=300)
        except Exception as e:
            hasil['error'] = f"Scan error: {str(e)[:120]}"
            return hasil

        if not scan.get('success'):
            hasil['error'] = scan.get('error', 'Scan gagal')
            return hasil
        kompetitor = scan.get('data', []) or []

    hasil['total_toko'] = len(kompetitor)

    # Density
    if penduduk > 0:
        hasil['density_per_10rb'] = round(len(kompetitor) / (penduduk / 10000), 3)

    # Breakdown per KBLI 4-digit
    per_kbli = {}
    for b in kompetitor:
        code = b.get('code_4digit') or 'UNCLASSIFIED'
        per_kbli[code] = per_kbli.get(code, 0) + 1
    hasil['kblis'] = per_kbli

    # Jarak
    jaraks = [b.get('jarak_km') for b in kompetitor if b.get('jarak_km') is not None]
    if jaraks:
        hasil['rata_jarak_km'] = round(sum(jaraks) / len(jaraks), 2)
        hasil['jarak_max_km'] = round(max(jaraks), 2)

    # Skor peluang (pakai fungsi existing)
    try:
        peluang = _analisis_peluang_single(
            lat, lon, keyword, radius_km=radius_km,
            kompetitor_list=kompetitor,
        )
        hasil['skor_peluang'] = peluang.get('skor_peluang')
        hasil['kategori'] = peluang.get('kategori', '-')
        hasil['rekomendasi'] = peluang.get('rekomendasi', '')
    except Exception as e:
        hasil['error'] = f"Analisis error: {str(e)[:120]}"

    # SEMUA toko (sorted by jarak)
    hasil['semua_toko'] = sorted(
        kompetitor,
        key=lambda x: x.get('jarak_km') or 999,
    )
    # Top 5 (untuk kompatibilitas kalau ada yang pakai)
    hasil['top_toko'] = hasil['semua_toko'][:5]

    return hasil


def bandingkan_2_kota(kota_a: dict, kota_b: dict, keyword: str,
                      radius_km: float = 5, auto_snapshot: bool = True) -> dict:
    """
    Bandingkan 2 kota. Kota = dict dari cari_kota_lengkap().

    Return:
      {
        'keyword': str,
        'radius_km': float,
        'a': {...metrik A...},
        'b': {...metrik B...},
        'pemenang_density': 'a' | 'b' | 'tie',
        'delta_toko': int,
        'rekomendasi': str (narasi perbandingan),
        'chart_kbli': pd-ready dict {kode: {'a': n, 'b': m}},
        'snapshot_ids': {'a': id|None, 'b': id|None},
      }
    """
    a = _metrik_kota(kota_a, keyword, radius_km)
    b = _metrik_kota(kota_b, keyword, radius_km)

    # Bandingkan density
    da = a.get('density_per_10rb')
    db = b.get('density_per_10rb')
    if da is None or db is None:
        pemenang = 'unknown'
    elif da < db:
        pemenang = 'a'  # density rendah = peluang lebih baik
    elif db < da:
        pemenang = 'b'
    else:
        pemenang = 'tie'

    # Delta toko
    delta_toko = (b.get('total_toko') or 0) - (a.get('total_toko') or 0)

    # Chart data per KBLI (union kode dari keduanya)
    semua_kode = sorted(set(list(a['kblis'].keys()) + list(b['kblis'].keys())))
    chart_kbli = {
        kode: {
            'a': a['kblis'].get(kode, 0),
            'b': b['kblis'].get(kode, 0),
        }
        for kode in semua_kode
    }

    # Narasi rekomendasi
    reko_lines = []
    reko_lines.append(f"**Perbandingan '{keyword}' ({radius_km} km)**")
    reko_lines.append(f"• {a['nama']}: {a['total_toko']} toko | "
                      f"density {da if da is not None else 'N/A'} per 10rb")
    reko_lines.append(f"• {b['nama']}: {b['total_toko']} toko | "
                      f"density {db if db is not None else 'N/A'} per 10rb")
    reko_lines.append("")

    if pemenang == 'a':
        reko_lines.append(f"🏆 **{a['nama']} lebih menjanjikan** — "
                          f"density lebih rendah (pasar belum jenuh).")
    elif pemenang == 'b':
        reko_lines.append(f"🏆 **{b['nama']} lebih menjanjikan** — "
                          f"density lebih rendah (pasar belum jenuh).")
    elif pemenang == 'tie':
        reko_lines.append("⚖️ Density **seimbang** antara kedua kota.")
    else:
        reko_lines.append("⚠️ Density tidak bisa dibandingkan (data penduduk kurang).")

    if abs(delta_toko) > 0:
        lebih_banyak = b['nama'] if delta_toko > 0 else a['nama']
        reko_lines.append(f"• {lebih_banyak} punya **{abs(delta_toko)} toko lebih banyak** "
                          f"→ kompetisi lebih ketat.")

    # Auto-save snapshot kalau diminta
    snapshot_ids = {'a': None, 'b': None}
    if auto_snapshot:
        try:
            from backend.db.snapshot_db import save_snapshot
            from datetime import datetime
            label_auto = f"Bandingkan {datetime.now().strftime('%d %b %H:%M')}"


            # Simpan snapshot pakai data yang SUDAH di-scan (jangan scan 2x!)
            for key, metrik in [('a', a), ('b', b)]:
                if metrik.get('error'):
                    continue
                try:
                    sid = save_snapshot(
                        kota=metrik['nama'],
                        keyword=keyword,
                        radius_km=radius_km,
                        data=metrik.get('semua_toko', []),  # ← batasan: hanya top 5
                        lat=metrik['lat'], lon=metrik['lon'],
                        label=label_auto,
                        catatan=f"Auto-save dari Bandingkan Kota (partial)",
                    )
                    snapshot_ids[key] = sid
                except Exception as e:
                    print(f"[Compare] Gagal snapshot {key}: {e}")
        except Exception as e:
            print(f"[Compare] Snapshot module tidak tersedia: {e}")

    return {
        'keyword': keyword,
        'radius_km': radius_km,
        'a': a,
        'b': b,
        'pemenang_density': pemenang,
        'delta_toko': delta_toko,
        'rekomendasi': "\n".join(reko_lines),
        'chart_kbli': chart_kbli,
        'snapshot_ids': snapshot_ids,
    }