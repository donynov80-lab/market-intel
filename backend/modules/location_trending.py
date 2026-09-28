"""
location_trending.py
Analisis trending per lokasi + skor via Google Trends.
"""
import sys
from pathlib import Path
from time import sleep

sys.path.insert(0, str(Path(__file__).parent))

from trends_analyzer import analisis_tren_per_kota, bandingkan_keywords
from autocomplete_analyzer import ambil_autocomplete


# =========================================================
# FUNGSI 1 — Related Queries
# =========================================================
def get_related_queries(keyword, geo='ID'):
    """Ambil related queries + estimasi volume."""
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl='id-ID', tz=360)
    FAKTOR = 5000

    try:
        pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=geo)
        related = pytrends.related_queries()
        data = related.get(keyword, {})

        top_df = data.get('top')
        rising_df = data.get('rising')

        top = []
        if top_df is not None and not top_df.empty:
            for _, row in top_df.iterrows():
                top.append({
                    'query': row['query'],
                    'value': int(row['value']),
                    'estimasi_volume': int(row['value'] * FAKTOR),
                })

        rising = []
        if rising_df is not None and not rising_df.empty:
            for _, row in rising_df.iterrows():
                val = row['value']
                # Rising value = % kenaikan, bukan volume. Estimasi dari persen × faktor kecil
                rising.append({
                    'query': row['query'],
                    'value': f"+{val}%",
                    'value_raw': val,
                    'estimasi_volume': int(min(val * 100, 500000)),  # cap 500k
                })

        return {'top': top, 'rising': rising}
    except Exception as e:
        return {'top': [], 'rising': [], 'error': str(e)}


# =========================================================
# FUNGSI 2 — Skor Autocomplete via Google Trends
# =========================================================
def skor_autocomplete(daftar_keyword, maks=5):
    """
    Hitung skor 0-100 untuk keyword via Google Trends.
    Kalau gagal (rate limit/error), kembalikan '-' — TIDAK crash.
    """
    if not daftar_keyword:
        return []

    # Coba maksimal 3 keyword dulu (lebih stabil)
    jumlah = min(len(daftar_keyword), maks, 3)
    kw_test = daftar_keyword[:jumlah]

    try:
        df = bandingkan_keywords(kw_test)
        if df is None or df.empty:
            raise Exception("Tidak ada data dari Google Trends")

        hasil = []
        kw_terhitung = set()
        for _, row in df.iterrows():
            kw_terhitung.add(row['keyword'])
            hasil.append({
                'keyword': row['keyword'],
                'skor': round(float(row['skor_0_100']), 1),
                'persen': float(row['persentase_pct']),
                'volume': int(row['estimasi_volume_per_bulan']),
            })

        # Sisanya beri tanda "-"
        for kw in daftar_keyword:
            if kw not in kw_terhitung:
                hasil.append({'keyword': kw, 'skor': '-', 'persen': '-', 'volume': '-'})

        return hasil

    except Exception as e:
        print(f"⚠️ skor_autocomplete gagal: {str(e)[:100]}")
        # Fallback: kembalikan semua dengan tanda "-"
        return [{'keyword': kw, 'skor': '-', 'persen': '-', 'volume': '-'}
                for kw in daftar_keyword]


# =========================================================
# FUNGSI 3 — Trending per Lokasi (dengan hirarki)
# =========================================================
def trending_per_lokasi(keyword_seed, provinsi, kota='', kecamatan='', kelurahan=''):
    """
    Field OPSIONAL: cukup isi provinsi saja, atau provinsi+kota, dst.
    """
    # Susun label & keyword
    label_parts = [p for p in [kelurahan, kecamatan, kota, provinsi] if p]
    label_lokasi = ", ".join(label_parts)

    # Prioritas keyword: makin spesifik makin bagus
    if kelurahan:
        keyword_lokal = f"{keyword_seed} {kelurahan}"
    elif kecamatan:
        keyword_lokal = f"{keyword_seed} {kecamatan}"
    elif kota:
        kota_clean = kota.replace('Kota ', '').replace('Kabupaten ', '')
        keyword_lokal = f"{keyword_seed} {kota_clean}"
    else:
        keyword_lokal = f"{keyword_seed} {provinsi}"

    hasil = {
        'provinsi': provinsi, 'kota': kota,
        'kecamatan': kecamatan, 'kelurahan': kelurahan,
        'label_lokasi': label_lokasi,
        'keyword_seed': keyword_seed,
        'keyword_lokal': keyword_lokal,
        'level': 'kelurahan' if kelurahan else ('kecamatan' if kecamatan
                  else ('kota' if kota else 'provinsi')),
        'tren_provinsi': [], 'tren_provinsi_top10': [],
        'autocomplete_lokal': [], 'autocomplete_dengan_skor': [],
        'related_queries': {'top': [], 'rising': []},
        'trending_umum': [], 'ide_konten': [],
    }

    # 1. Tren provinsi (level Indonesia, tapi cari provinsi terpilih)
    try:
        df = analisis_tren_per_kota(keyword_seed, top_n=20)
        if not df.empty:
            baris_prov = df[df['wilayah'].str.contains(provinsi, case=False, na=False)]
            if not baris_prov.empty:
                hasil['tren_provinsi'] = baris_prov.to_dict('records')
            hasil['tren_provinsi_top10'] = df.head(10).to_dict('records')
    except Exception as e:
        hasil['error_trends'] = str(e)

    # 2. Autocomplete lokal
    try:
        ac = ambil_autocomplete(keyword_lokal)
        if ac and not ac[0].startswith("⚠️"):
            hasil['autocomplete_lokal'] = ac
    except Exception as e:
        hasil['error_autocomplete'] = str(e)

    # 3. Skor autocomplete
    if hasil['autocomplete_lokal']:
        from time import sleep as _s
        _s(2)
        try:
            hasil['autocomplete_dengan_skor'] = skor_autocomplete(
                hasil['autocomplete_lokal'], maks=5)
        except Exception as e:
            hasil['error_skor'] = str(e)

    # 4. Related queries
    try:
        hasil['related_queries'] = get_related_queries(keyword_seed, geo='ID')
    except Exception as e:
        hasil['error_related'] = str(e)

    # 5. Trending umum
    try:
        from trends_analyzer import get_trending_searches
        hasil['trending_umum'] = get_trending_searches(region='ID', top_n=10)
    except Exception as e:
        hasil['error_trending'] = str(e)

    # 6. Ide konten
    ide = []
    for item in hasil['related_queries'].get('rising', [])[:5]:
        kw = item.get('query', '')
        if kw:
            ide.append({
                'judul': f"{kw.title()} — Sedang Naik!",
                'hashtag': f"#{kw.replace(' ', '')}",
                'tipe': '🔥 RISING', 'skor': item.get('value', 0),
            })
    for kw in hasil['autocomplete_lokal'][:5]:
        ide.append({
            'judul': kw.title(),
            'hashtag': f"#{kw.replace(' ', '')}",
            'tipe': '📍 LOKAL', 'skor': '-',
        })
    hasil['ide_konten'] = ide

    return hasil


# =========================================================
# MAIN — Test
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("📍 TEST — Trending di Bandung (kue)")
    print("=" * 60)

    hasil = trending_per_lokasi("kue", "Jawa Barat", "Kota Bandung")

    print(f"\n📍 Lokasi: {hasil['label_lokasi']}")
    print(f"🔍 Keyword: {hasil['keyword_seed']}")

    print("\n📊 Provinsi Terpilih:")
    for item in hasil.get('tren_provinsi', []):
        print(f"  • {item.get('wilayah')}: {item.get('skor_0_100')}")

    print("\n🔍 Autocomplete Lokal (dengan skor):")
    for item in hasil['autocomplete_dengan_skor']:
        print(f"  • [{item['skor']}] {item['keyword']}  (volume: {item['volume']})")