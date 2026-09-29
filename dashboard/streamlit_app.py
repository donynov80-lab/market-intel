# dashboard/streamlit_app.py
import os
import sys
import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------
# SETUP PATH
# ---------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------
# IMPORTS MODULE
# ---------------------------------------------------------------------
from backend.modules.trends_analyzer import TrendsAnalyzer
from backend.modules.autocomplete_analyzer import AutocompleteAnalyzer
from backend.modules.location_trending import LocationTrending
from backend.modules.maps_scanner import MapsScanner, KATEGORI_LABEL
from backend.modules.wa_analyzer import WAAnalyzer
from backend.modules.opportunity_analyzer import OpportunityAnalyzer
from backend.modules.business_classifier import get_classifier

from backend.db.campaign_db import CampaignDB
from backend.db.leads_db import LeadsDB
from backend.db.kota_db import KotaDB

# ---------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------
st.set_page_config(page_title="Market Intel Dashboard", layout="wide", page_icon="📊")
st.title("📊 Market Intel Dashboard")
st.caption("Riset pasar • Scan kompetitor • Geo-fence • Lead capture — untuk UMKM")

# ---------------------------------------------------------------------
# INIT (cache biar gak reload terus)
# ---------------------------------------------------------------------
@st.cache_resource
def init_services():
    return {
        "trends": TrendsAnalyzer(),
        "autocomplete": AutocompleteAnalyzer(),
        "location": LocationTrending(),
        "scanner": MapsScanner(),
        "wa": WAAnalyzer(),
        "opp": OpportunityAnalyzer(),
        "campaigns": CampaignDB(),
        "leads": LeadsDB(),
        "kota": KotaDB(),
        "classifier": get_classifier(prefer_level=4),
    }

S = init_services()

# ---------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------
(tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9) = st.tabs([
    "📍 Trending Lokasi",
    "🗺️ Peta Kompetitor",
    "🎯 Analisis Peluang",
    "📈 Google Trends",
    "🔤 Autocomplete",
    "📣 Campaign",
    "👥 Leads",
    "💬 WA Analyzer",
    "📖 Panduan",
])

# =====================================================================
# TAB 1 — Trending per Lokasi
# =====================================================================
with tab1:
    st.header("📍 Trending per Lokasi")
    st.info("Contoh tab — pakai modul kamu yang sudah ada. Kalau versimu lebih lengkap, pertahankan.")

    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("Keyword", placeholder="contoh: kue")
    with col2:
        provinsi = st.text_input("Provinsi", placeholder="contoh: DKI Jakarta")

    if st.button("Analisis Trending", key="btn_trend1"):
        if keyword:
            with st.spinner("Mengambil data..."):
                try:
                    hasil = S["location"].analyze(keyword=keyword, region=provinsi or None)
                    st.json(hasil)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Isi keyword dulu.")

# =====================================================================
# TAB 2 — Peta Kompetitor + FILTER SUBGOLONGAN  ⭐ (TASK 2)
# =====================================================================
with tab2:
    st.header("🗺️ Peta Kompetitor")
    st.caption("Scan via OpenStreetMap (Overpass) → hasil OTOMATIS diklasifikasi per subgolongan KBLI.")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    with col1:
        lat = st.number_input("Latitude", value=-6.1754, format="%.6f", key="sc_lat")
    with col2:
        lon = st.number_input("Longitude", value=106.8272, format="%.6f", key="sc_lon")
    with col3:
        radius = st.selectbox("Radius (m)", [500, 1000, 2000, 3000, 5000], index=1, key="sc_rad")
    with col4:
        kategori = st.selectbox(
            "Kategori Scan",
            options=list(KATEGORI_LABEL.keys()),
            format_func=lambda k: KATEGORI_LABEL[k],
            key="sc_kat",
        )

    if st.button("🔍 Scan Sekarang", type="primary", key="btn_scan"):
        with st.spinner(f"Scan radius {radius}m... (30-60 detik)"):
            hasil = S["scanner"].scan(lat=lat, lon=lon, radius=radius, kategori=kategori)

        if not hasil["success"]:
            st.error(hasil["error"])
        else:
            st.success(f"✅ Ditemukan {hasil['count']} bisnis.")
            st.session_state["scan_result"] = hasil

    # ----------------- Tampilkan hasil + Filter Subgolongan ---------
    if "scan_result" in st.session_state:
        hasil = st.session_state["scan_result"]
        businesses = hasil["businesses"]

        if not businesses:
            st.warning("Tidak ada bisnis ditemukan. Coba perkecil kategori atau perbesar radius.")
        else:
            df = pd.DataFrame(businesses)

            # =============== FILTER SUBGOLONGAN (4-digit) ===============
            st.subheader("🎚️ Filter Subgolongan (KBLI 4-digit)")

            subgol_options = sorted(
                [c for c in df["code_4digit"].dropna().unique().tolist() if c],
            )
            # mapping code -> "code — title (n)"
            subgol_count = df["code_4digit"].value_counts().to_dict()
            subgol_title_map = (
                df.dropna(subset=["code_4digit"])
                  .drop_duplicates("code_4digit")
                  .set_index("code_4digit")["subgolongan_title"]
                  .to_dict()
            )

            def fmt_subgol(code):
                title = subgol_title_map.get(code) or "-"
                n = subgol_count.get(code, 0)
                return f"{code} — {title[:50]}  ({n})"

            default_selection = subgol_options  # default semua tercentang
            pilihan = st.multiselect(
                "Pilih subgolongan yang ingin ditampilkan:",
                options=subgol_options,
                default=default_selection,
                format_func=fmt_subgol,
                key="filter_subgol",
            )

            search_text = st.text_input(
                "🔎 Cari nama bisnis (opsional):",
                placeholder="contoh: kue, outlet, bengkel",
                key="filter_name",
            )

            # Apply filter
            df_filtered = df.copy()
            if pilihan:
                df_filtered = df_filtered[df_filtered["code_4digit"].isin(pilihan)]
            if search_text:
                df_filtered = df_filtered[
                    df_filtered["name"].str.contains(search_text, case=False, na=False)
                ]

            st.write(f"**Menampilkan {len(df_filtered)} dari {len(df)} bisnis.**")

            # ---- Breakdown per subgolongan ----
            with st.expander("📊 Breakdown per subgolongan (4 digit)", expanded=False):
                if not df_filtered.empty:
                    summary = (
                        df_filtered.groupby(["code_4digit", "subgolongan_title"])
                          .size()
                          .reset_index(name="count")
                          .sort_values("count", ascending=False)
                    )
                    st.dataframe(summary, use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada data setelah difilter.")

            # ---- Tabel bisnis ----
            show_cols = ["name", "code_4digit", "subgolongan_title",
                         "kbli_source", "kbli_confidence", "lat", "lon"]
            show_cols = [c for c in show_cols if c in df_filtered.columns]
            st.dataframe(df_filtered[show_cols], use_container_width=True, hide_index=True)

            # ---- Peta ----
            if not df_filtered.empty:
                try:
                    import folium
                    from streamlit_folium import st_folium

                    peta = folium.Map(location=[lat, lon], zoom_start=15)
                    folium.Circle(
                        [lat, lon], radius=radius,
                        color="blue", fill=True, fill_opacity=0.05,
                    ).add_to(peta)

                    for _, row in df_filtered.iterrows():
                        tooltip = (
                            f"<b>{row['name']}</b><br>"
                            f"{row.get('subgolongan_title') or '-'}<br>"
                            f"Kode: {row.get('code_4digit') or '-'}"
                        )
                        folium.Marker(
                            [row["lat"], row["lon"]],
                            tooltip=tooltip,
                            icon=folium.Icon(color="red", icon="info-sign"),
                        ).add_to(peta)

                    st_folium(peta, width=None, height=500, key="map_comp")
                except ImportError:
                    st.warning("Install `folium` dan `streamlit-folium` untuk melihat peta.")

# =====================================================================
# TAB 3 — Analisis Peluang  ⭐ (TASK 3)
# =====================================================================
with tab3:
    st.header("🎯 Analisis Peluang")
    st.caption("Bandingkan jumlah kompetitor per subgolongan vs jumlah penduduk kota.")

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        kota_nama = st.text_input("Kota", value="Jakarta Pusat", key="opp_kota")
    with col2:
        populasi = st.number_input(
            "Jumlah Penduduk", min_value=0, value=1_050_000, step=10_000,
            key="opp_pop",
        )
    with col3:
        luas = st.number_input(
            "Luas (km², opsional)", min_value=0.0, value=48.13, step=1.0,
            key="opp_luas",
        )

    col4, col5 = st.columns([2, 2])
    with col4:
        lat3 = st.number_input("Latitude", value=-6.1862, format="%.6f", key="opp_lat")
    with col5:
        lon3 = st.number_input("Longitude", value=106.8340, format="%.6f", key="opp_lon")

    radius3 = st.selectbox("Radius scan (m)", [1000, 2000, 3000, 5000, 10000],
                           index=2, key="opp_rad")

    if st.button("🚀 Analisis Peluang", type="primary", key="btn_opp"):
        with st.spinner("Scan kompetitor dan hitung peluang..."):
            scan = S["scanner"].scan(lat=lat3, lon=lon3, radius=radius3, kategori="semua")

            if not scan["success"]:
                st.error(scan["error"])
            else:
                analysis = S["opp"].analyze(
                    businesses=scan["businesses"],
                    population=populasi,
                    city_name=kota_nama,
                    area_km2=luas if luas > 0 else None,
                )
                st.session_state["opp_result"] = analysis

    if "opp_result" in st.session_state:
        analysis = st.session_state["opp_result"]
        results = analysis["results"]

        st.success(
            f"Kota **{analysis['city']}** — penduduk {analysis['population']:,} — "
            f"{analysis['total_businesses']} bisnis terdeteksi."
        )

        if not results:
            st.info("Tidak ada subgolongan yang terdeteksi. Coba perbesar radius.")
        else:
            # ---- Ringkasan top 5 peluang ----
            st.subheader("🏆 Top 5 Peluang Terbaik")
            top5 = results[:5]
            for i, r in enumerate(top5, 1):
                st.markdown(
                    f"**{i}. {r['code_4digit']} — {r['title']}**  \n"
                    f"{r['verdict']}  \n"
                    f"• Kompetitor: **{r['count']}**  \n"
                    f"• Density: **{r['density_per_10k']}** per 10rb penduduk  \n"
                    f"• Skor: **{r['score']}/100**  \n"
                    f"• Contoh: {', '.join([n for n in r['sample_names'] if n][:3]) or '-'}"
                )
                st.divider()

            # ---- Tabel lengkap ----
            st.subheader("📋 Tabel Lengkap")
            df_opp = S["opp"].to_dataframe(analysis)
            if df_opp is not None:
                st.dataframe(df_opp, use_container_width=True, hide_index=True)

                csv = df_opp.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Unduh CSV",
                    data=csv,
                    file_name=f"analisis_peluang_{analysis['city'].replace(' ', '_')}.csv",
                    mime="text/csv",
                )

            # ---- Bar chart ----
            st.subheader("📊 Grafik Skor Peluang")
            try:
                chart_df = pd.DataFrame(results[:15])[["title", "score"]].set_index("title")
                st.bar_chart(chart_df)
            except Exception:
                pass

# =====================================================================
# TAB 4 — Google Trends
# =====================================================================
with tab4:
    st.header("📈 Google Trends per Wilayah")
    keyword = st.text_input("Keyword", key="gt_kw")
    region = st.text_input("Region (opsional)", key="gt_reg")
    if st.button("Analisis", key="btn_gt") and keyword:
        with st.spinner("Mengambil data..."):
            try:
                st.json(S["trends"].analyze(keyword=keyword, region=region or None))
            except Exception as e:
                st.error(f"Error: {e}")

# =====================================================================
# TAB 5 — Autocomplete
# =====================================================================
with tab5:
    st.header("🔤 Keyword Autocomplete")
    seed = st.text_input("Seed keyword", placeholder="contoh: kue", key="ac_seed")
    if st.button("Generate", key="btn_ac") and seed:
        with st.spinner("Mengambil saran..."):
            try:
                st.json(S["autocomplete"].analyze(seed))
            except Exception as e:
                st.error(f"Error: {e}")

# =====================================================================
# TAB 6 — Campaign
# =====================================================================
with tab6:
    st.header("📣 Campaign (Geo-fence)")
    st.info("Kelola campaign di sini — modul `campaign_db` kamu.")
    try:
        campaigns = S["campaigns"].list_all()
        st.dataframe(pd.DataFrame(campaigns), use_container_width=True)
    except Exception as e:
        st.warning(f"Belum bisa load campaign: {e}")

# =====================================================================
# TAB 7 — Leads
# =====================================================================
with tab7:
    st.header("👥 Leads (CRM)")
    try:
        leads = S["leads"].list_all()
        st.dataframe(pd.DataFrame(leads), use_container_width=True)
    except Exception as e:
        st.warning(f"Belum bisa load leads: {e}")

# =====================================================================
# TAB 8 — WA Analyzer
# =====================================================================
with tab8:
    st.header("💬 WA Analyzer")
    nomor = st.text_input("Nomor WA", placeholder="+62812...", key="wa_nomor")
    if st.button("Analisis", key="btn_wa") and nomor:
        with st.spinner("Menganalisis..."):
            try:
                st.json(S["wa"].analyze(nomor))
            except Exception as e:
                st.error(f"Error: {e}")

# =====================================================================
# TAB 9 — Panduan
# =====================================================================
with tab9:
    st.header("📖 Panduan")
    st.markdown("""
    ### Alur Kerja
    1. **Trending Lokasi** → cek dulu keyword tren di kotamu.
    2. **Peta Kompetitor** → scan sekitar, filter per subgolongan KBLI.
    3. **Analisis Peluang** → lihat skor peluang per subgolongan.
    4. **Google Trends** → verifikasi tren.
    5. **Autocomplete** → cari keyword turunan.
    6. **Campaign** → buat geo-fence iklan.
    7. **Leads** → tangkap calon pembeli.
    8. **WA Analyzer** → validasi nomor WA leads.

    ### Subgolongan KBLI
    Filter di Tab 2 dan Tab 3 memakai **4 digit** dari kode KBLI.
    Contoh: `4722` = Perdagangan Eceran Minuman (termasuk miras).

    ### Kalau Scan Gagal (Rate Limit)
    - Tunggu 1–2 menit, klik Scan lagi.
    - Perkecil radius (500m).
    - Ganti kategori (jangan "semua").
    """)

# ---------------------------------------------------------------------
# Sidebar info classifier
# ---------------------------------------------------------------------
with st.sidebar:
    st.subheader("ℹ️ Classifier Status")
    try:
        stats = S["classifier"].stats()
        st.write(f"KBLI loaded: **{stats['total']}** entries")
        st.write(f"• Golpok (2d): {stats.get('golpok', 0)}")
        st.write(f"• Gol (3d): {stats.get('gol', 0)}")
        st.write(f"• Subgol (4d): {stats.get('subgol', 0)}")
        st.write(f"• Kelompok (5d): {stats.get('kelompok', 0)}")
        st.write(f"Kamus manual: {stats.get('kamus_bisnis', 0)}")
        st.write(f"Kamus OSM: {stats.get('kamus_osm', 0)}")
    except Exception as e:
        st.warning(f"Classifier belum siap: {e}")