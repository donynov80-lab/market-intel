"""
trends_analyzer.py
Modul Pilar 2 — Analisis tren regional via Google Trends.

Fitur:
- analisis_tren_per_kota(keyword)     : 1 keyword → wilayah teratas
- bandingkan_keywords([kw1, kw2])     : bandingkan beberapa keyword
- get_trending_searches()             : trending Google Indonesia (RSS)

Catatan:
    Google Trends mengembalikan SKOR 0-100 (relatif), BUKAN angka asli.
    Kolom "estimasi_volume" = skor × 5.000 (perkiraan kasar untuk Indonesia).
"""
from pytrends.request import TrendReq
import pandas as pd
from time import sleep


FAKTOR_VOLUME = 5000  # skor 100 ≈ 500.000 pencarian/bulan di Indonesia


# =========================================================
# FUNGSI 1: Analisis satu keyword per wilayah
# =========================================================
def analisis_tren_per_kota(keyword, top_n=15):
    """
    Return: DataFrame wilayah di Indonesia yang paling berminat.
    Kolom: [wilayah, skor_0_100, persentase, estimasi_volume]
    """
    pytrends = TrendReq(hl='id-ID', tz=360)
    pytrends.build_payload(
        kw_list=[keyword],
        cat=0,
        timeframe='today 3-m',
        geo='ID',
        gprop=''
    )
    df = pytrends.interest_by_region(
        resolution='CITY',
        inc_low_vol=True,
        inc_geo_code=False
    )
    df = df.reset_index()
    df = df[df[keyword] > 0]

    if df.empty:
        return pd.DataFrame()

    # Hitung persentase
    total_skor = df[keyword].sum()
    df['persentase'] = (df[keyword] / total_skor * 100).round(1)

    # Estimasi volume
    df['estimasi_volume'] = (df[keyword] * FAKTOR_VOLUME).round(0).astype(int)

    # Sort & rename
    df = df.sort_values(by=keyword, ascending=False).head(top_n)
    df = df.rename(columns={
        'geoName': 'wilayah',
        keyword: 'skor_0_100'
    })

    # Urutkan kolom
    df = df[['wilayah', 'skor_0_100', 'persentase', 'estimasi_volume']]

    return df


# =========================================================
# FUNGSI 2: Bandingkan beberapa keyword
# =========================================================
def bandingkan_keywords(daftar_keyword):
    """
    Bandingkan popularitas relatif beberapa keyword.
    Kolom: [keyword, skor_0_100, persentase_pct, estimasi_volume_per_bulan]
    """
    pytrends = TrendReq(hl='id-ID', tz=360)
    pytrends.build_payload(
        kw_list=daftar_keyword,
        cat=0,
        timeframe='today 3-m',
        geo='ID'
    )
    df = pytrends.interest_over_time()
    if df.empty:
        return pd.DataFrame()

    df = df.drop(columns=['isPartial'], errors='ignore')

    # Rata-rata skor per keyword
    rata = df.mean().reset_index()
    rata.columns = ['keyword', 'skor_0_100']

    # Persentase
    total_skor = rata['skor_0_100'].sum()
    rata['persentase_pct'] = (rata['skor_0_100'] / total_skor * 100).round(1)

    # Estimasi volume
    rata['estimasi_volume_per_bulan'] = (
        rata['skor_0_100'] * FAKTOR_VOLUME
    ).round(0).astype(int)

    # Sort
    rata = rata.sort_values('skor_0_100', ascending=False).reset_index(drop=True)

    return rata


# =========================================================
# FUNGSI 3: Trending searches (RSS feed)
# =========================================================
def get_trending_searches(region='ID', top_n=20):
    """
    Return: list keyword trending di Google Indonesia via RSS feed resmi.
    """
    import requests
    from xml.etree import ElementTree as ET

    url = f"https://trends.google.com/trending/rss?geo={region}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        root = ET.fromstring(r.content)
        results = []

        for item in root.iter():
            if item.tag.endswith("item"):
                title_el = None
                for child in item:
                    if child.tag.endswith("title"):
                        title_el = child
                        break
                if title_el is not None and title_el.text:
                    results.append(title_el.text.strip())
                if len(results) >= top_n:
                    break

        return results if results else ["(kosong — coba lagi nanti)"]

    except Exception as e:
        return [f"⚠️ Gagal ambil trending: {type(e).__name__}: {e}"]


# =========================================================
# MAIN — Test
# =========================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📊 TEST 1 — Bandingkan 4 keyword")
    print("=" * 60)
    hasil = bandingkan_keywords(["kue", "bolu", "lapis", "pastry"])
    if not hasil.empty:
        print(hasil.to_string(index=False))

    sleep(3)

    print("\n" + "=" * 60)
    print("📍 TEST 2 — Wilayah teratas untuk 'kue'")
    print("=" * 60)
    try:
        df = analisis_tren_per_kota("kue", top_n=10)
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("(kosong)")
    except Exception as e:
        print(f"⚠️ Error: {e}")