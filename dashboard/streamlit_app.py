"""
streamlit_app.py — Dashboard Market Intel
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.db.campaign_db import ambil_campaign
from backend.db.leads_db import ambil_leads, statistik_leads
from backend.modules.trends_analyzer import analisis_tren_per_kota, bandingkan_keywords
from backend.modules.autocomplete_analyzer import ambil_autocomplete
from backend.modules.wa_analyzer import analisis_daftar_nomor
from backend.modules.location_trending import trending_per_lokasi, skor_autocomplete
from backend.modules.maps_scanner import cari_kota_lengkap, scan_sekitar, analisis_peluang


KOTA_PER_PROVINSI = {
    "DKI Jakarta": ["Jakarta Pusat", "Jakarta Selatan", "Jakarta Barat", "Jakarta Timur", "Jakarta Utara"],
    "Jawa Barat": ["Bandung", "Bekasi", "Bogor", "Depok", "Cimahi", "Cirebon", "Sukabumi"],
    "Jawa Tengah": ["Semarang", "Surakarta", "Magelang", "Tegal"],
    "DI Yogyakarta": ["Yogyakarta", "Sleman", "Bantul"],
    "Jawa Timur": ["Surabaya", "Malang", "Kediri", "Sidoarjo", "Jember"],
    "Banten": ["Tangerang", "Serang", "Tangerang Selatan"],
    "Bali": ["Denpasar", "Badung"],
    "Sumatera Utara": ["Medan", "Binjai"],
    "Sumatera Barat": ["Padang"],
    "Sumatera Selatan": ["Palembang"],
    "Riau": ["Pekanbaru"],
    "Kalimantan Timur": ["Samarinda", "Balikpapan"],
    "Kalimantan Selatan": ["Banjarmasin"],
    "Kalimantan Barat": ["Pontianak"],
    "Sulawesi Selatan": ["Makassar"],
    "Sulawesi Utara": ["Manado"],
    "Papua": ["Jayapura"],
    "Maluku": ["Ambon"],
}


st.set_page_config(page_title="Market Intel Dashboard", page_icon="🧠",
                    layout="wide", initial_sidebar_state="expanded")

# === Session state ===
for key in ['hasil_scan', 'hasil_analisis', 'info_scan', 'info_analisis', 'hasil_trending']:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.title("🧠 Market Intel")
    st.caption("Dashboard Marketing UMKM")
    st.divider()
    st.markdown("""
    ### 📌 Menu
    - 📍 **Lokasi**
    - 🗺️ **Kompetitor**
    - 📊 **Trends**
    - 🔍 **Keyword**
    - 🗺️ **Campaign**
    - 👥 **Leads**
    - 📱 **WA Analyzer**
    - 📖 **Panduan**
    """)
    st.divider()
    st.caption("Made with Python + Streamlit")

st.title("🧠 Market Intel Dashboard")
st.caption("Pusat data marketing untuk UMKM")
st.divider()

tab_lokasi, tab_maps, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 Trending per Lokasi", "🗺️ Peta Kompetitor", "📊 Trends",
    "🔍 Keyword", "🗺️ Campaign", "👥 Leads", "📱 WA Analyzer", "📖 Panduan"
])


# =========================================================
# TAB 1 — TRENDING PER LOKASI
# =========================================================
with tab_lokasi:
    st.header("📍 Trending per Lokasi")
    st.caption("Field bertingkat — cukup isi yang perlu, sisanya boleh kosong")

    @st.cache_data(ttl=86400, show_spinner=False)
    def load_provinsi():
        import requests
        return requests.get("https://www.emsifa.com/api-wilayah-indonesia/api/provinces.json", timeout=10).json()

    @st.cache_data(ttl=86400, show_spinner=False)
    def load_kota(pid):
        import requests
        return requests.get(f"https://www.emsifa.com/api-wilayah-indonesia/api/regencies/{pid}.json", timeout=10).json()

    @st.cache_data(ttl=86400, show_spinner=False)
    def load_kecamatan(kid):
        import requests
        return requests.get(f"https://www.emsifa.com/api-wilayah-indonesia/api/districts/{kid}.json", timeout=10).json()

    @st.cache_data(ttl=86400, show_spinner=False)
    def load_kelurahan(kecid):
        import requests
        return requests.get(f"https://www.emsifa.com/api-wilayah-indonesia/api/villages/{kecid}.json", timeout=10).json()

    keyword_lokasi = st.text_input("Keyword", value="kue", key="lok_kw")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        prov_list = load_provinsi()
        prov = st.selectbox(
            "🏙️ Provinsi (WAJIB)",
            prov_list, format_func=lambda x: x['name'],
            index=9, key="lp",
            help="Pilih provinsi dulu. Kota/Kecamatan/Kelurahan opsional."
        )
    with c2:
        kota_list = load_kota(prov['id']) if prov else []
        opsi_kota = [{'id': '', 'name': '-- Semua Kota (opsional) --'}] + kota_list
        kota = st.selectbox(
            "🏘️ Kota (opsional)",
            opsi_kota, format_func=lambda x: x['name'],
            key="lk",
            help="Kosongkan untuk cek level provinsi saja"
        )
    with c3:
        kec_list = load_kecamatan(kota['id']) if kota and kota.get('id') else []
        opsi_kec = [{'id': '', 'name': '-- Semua Kecamatan (opsional) --'}] + kec_list
        kec = st.selectbox(
            "🏡 Kecamatan (opsional)",
            opsi_kec, format_func=lambda x: x['name'],
            key="lkc",
            help="Kosongkan untuk cek level kota saja"
        )
    with c4:
        kel_list = load_kelurahan(kec['id']) if kec and kec.get('id') else []
        opsi_kel = [{'id': '', 'name': '-- Semua Kelurahan (opsional) --'}] + kel_list
        kel = st.selectbox(
            "🏠 Kelurahan (opsional)",
            opsi_kel, format_func=lambda x: x['name'],
            key="lkl",
            help="Kosongkan untuk cek level kecamatan saja"
        )

    n_prov = prov['name'] if prov else ''
    n_kota = kota['name'] if kota and kota.get('id') else ''
    n_kec = kec['name'] if kec and kec.get('id') else ''
    n_kel = kel['name'] if kel and kel.get('id') else ''

    label = ", ".join([x for x in [n_kel, n_kec, n_kota, n_prov] if x])
    level = ('kelurahan' if n_kel else ('kecamatan' if n_kec
             else ('kota' if n_kota else 'provinsi')))

    st.success(f"📍 **Lokasi**: {label}")
    st.caption(f"🎯 Level analisis: **{level.title()}**")

    if st.button("🔍 Cek Trending", key="btn_lok", type="primary"):
        if not keyword_lokasi.strip() or not n_prov:
            st.warning("Isi keyword + provinsi (minimal).")
        else:
            with st.spinner("Menganalisis..."):
                try:
                    st.session_state.hasil_trending = trending_per_lokasi(
                        keyword_lokasi, n_prov, n_kota, n_kec, n_kel)
                except Exception as e:
                    st.error(f"❌ {e}")

    if st.session_state.get('hasil_trending'):
        hasil = st.session_state.hasil_trending
        st.divider()

        kw_lokal = hasil.get('keyword_lokal', '')
        st.info(f"🔍 Query analisis: **{kw_lokal}**")

        a, b, c = st.columns(3)
        with a:
            st.subheader("🎯 Real Query + Skor")
            ac = hasil.get('autocomplete_dengan_skor', [])
            if ac:
                st.dataframe(pd.DataFrame(ac), use_container_width=True, hide_index=True)
            else:
                for i, kw in enumerate(hasil.get('autocomplete_lokal', [])[:10], 1):
                    st.markdown(f"**{i}.** {kw}")
        with b:
            st.subheader("🔥 Rising")
            rising = hasil.get('related_queries', {}).get('rising', [])
            if rising:
                st.dataframe(pd.DataFrame([{
                    'Query': x.get('query'), 'Naik': x.get('value'),
                    'Est. Volume': x.get('estimasi_volume', '-')
                } for x in rising[:10]]), use_container_width=True, hide_index=True)
        with c:
            st.subheader("📈 Top Related")
            top = hasil.get('related_queries', {}).get('top', [])
            if top:
                st.dataframe(pd.DataFrame([{
                    'Query': x.get('query'), 'Skor': x.get('value'),
                    'Est. Volume': x.get('estimasi_volume', '-')
                } for x in top[:10]]), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("💡 Ide Konten")
        for x in hasil.get('ide_konten', [])[:15]:
            icon = "🔥" if "RISING" in x.get('tipe','') else "📍"
            st.markdown(f"{icon} **{x.get('judul')}** `{x.get('hashtag')}`")


# =========================================================
# TAB 2 — PETA KOMPETITOR & PELUANG
# =========================================================
with tab_maps:
    st.header("🗺️ Peta Kompetitor & Peluang Pasar")
    st.caption("Scan pesaing + analisis peluang buka outlet")

    st.info("""
    **ℹ️ Alur Pakai:**
    1. Ketik nama kota → pilih dari dropdown
    2. Klik **🔍 Scan Sekarang** (untuk lihat daftar toko)
    3. Klik **🎯 Analisis Peluang** (untuk hitung skor)
    4. Hasil **tersimpan** — tidak hilang saat ganti input
    """)

    # === Input Kota ===
    keyword_kota = st.text_input("🔍 Cari Kota/Kabupaten", value="Bandung", key="mk_kota")
    hasil_kota = cari_kota_lengkap(keyword_kota, limit=20)

    kota_data = None
    kota_pilih = None
    if not hasil_kota:
        st.warning(f"Kota '{keyword_kota}' tidak ditemukan.")
    else:
        opsi_kota = {}
        for k in hasil_kota:
            label_k = k.get('display', k.get('name', str(k)))
            opsi_kota[label_k] = k

        st.caption(f"📋 Ditemukan **{len(opsi_kota)}** kota. Pilih yang sesuai:")
        kota_pilih = st.selectbox("📌 Pilih Kota", list(opsi_kota.keys()), key="mk_pilih")
        kota_data = opsi_kota[kota_pilih]

        # === INFO PENDUDUK & LUAS ===
        if kota_data.get('penduduk'):
            pend = kota_data['penduduk']
            luas = kota_data.get('luas') or 0
            info = f"👥 **Penduduk**: {pend:,} orang"
            if luas:
                info += f" | 📐 **Luas**: {luas:.1f} km² | 📊 **Kepadatan**: {pend/luas:.0f} org/km²"
            st.caption(info)

        # Warning kalau belum geocoded
        if kota_data and not kota_data.get('geocoded', False):
            st.warning(
                f"⚠️ **{kota_data.get('kota', 'Kota ini')}** belum punya koordinat. "
                "Scan tidak akan jalan. Coba pilih kota lain."
            )

    # === Input Keyword & Radius ===
    c1, c2 = st.columns([3, 1])
    with c1:
        keyword_scan = st.text_input("Keyword Usaha", value="kue", key="mk_kw")
    with c2:
        radius_scan = st.number_input(
            "Radius (km)", 1, 30, 5, key="mk_rad",
            help="Untuk kota besar (Jakarta/Bandung/Surabaya), pakai 3-8 km. "
                 "Radius besar bikin scan lambat/gagal."
        )

    if radius_scan > 10:
        st.warning("⚠️ Radius > 10 km bisa gagal karena server Overpass timeout. "
                   "Saran: pecah jadi beberapa scan radius kecil.")

    # === 3 Tombol ===
    col1, col2, col3 = st.columns(3)
    with col1:
        btn_scan = st.button("🔍 Scan Sekarang", key="btn_scan", use_container_width=True)
    with col2:
        btn_analisis = st.button("🎯 Analisis Peluang", key="btn_anl", type="primary", use_container_width=True)
    with col3:
        btn_reset = st.button("🔄 Reset", key="btn_reset", use_container_width=True)

    # ====== AKSI: SCAN ======
    if btn_scan and kota_data:
        lat, lon = kota_data.get('lat'), kota_data.get('lon')
        if not lat or not lon:
            st.error("Kota tidak punya koordinat.")
        else:
            with st.spinner(f"Scan {keyword_scan} di radius {radius_scan} km..."):
                scan_result = scan_sekitar(lat, lon,
                                            radius_m=int(radius_scan * 1000),
                                            keyword=keyword_scan, maks=100)

                if scan_result.get('success') and not scan_result.get('data'):
                    if keyword_scan.lower() not in ['restoran', 'cafe', 'toko', 'hotel']:
                        st.info(f"Keyword '{keyword_scan}' tidak ada hasil. Fallback ke 'restoran'...")
                        scan_result = scan_sekitar(lat, lon,
                                                    radius_m=int(radius_scan * 1000),
                                                    keyword='restoran', maks=100)

            if not scan_result.get('success'):
                st.error(f"❌ {scan_result.get('error', 'Gagal scan')}")
                st.warning("💡 Server Overpass sedang rate limit. Tunggu 30-60 detik, coba lagi.")
            else:
                st.session_state.hasil_scan = scan_result.get('data', [])
                st.session_state.info_scan = {
                    'kota': kota_pilih, 'keyword': keyword_scan,
                    'radius': radius_scan, 'lat': lat, 'lon': lon,
                }
                st.session_state.hasil_analisis = None

    # ====== AKSI: ANALISIS ======
    if btn_analisis and kota_data:
        lat, lon = kota_data.get('lat'), kota_data.get('lon')
        if not lat or not lon:
            st.error("Kota tidak punya koordinat.")
        else:
            reuse = None
            info_s = st.session_state.get('info_scan')
            if info_s and st.session_state.get('hasil_scan') is not None:
                if (info_s['kota'] == kota_pilih and
                    info_s['keyword'] == keyword_scan and
                    info_s['radius'] == radius_scan):
                    reuse = st.session_state.hasil_scan
                    if reuse:
                        st.info(f"♻️ Reuse {len(reuse)} toko dari scan sebelumnya — tidak scan ulang.")

            with st.spinner(f"Menganalisis peluang di {kota_pilih}..."):
                peluang = analisis_peluang(
                    lat, lon, keyword_scan,
                    radius_km=radius_scan,
                    kompetitor_list=reuse
                )
            st.session_state.hasil_analisis = peluang
            st.session_state.info_analisis = {
                'kota': kota_pilih, 'keyword': keyword_scan,
                'radius': radius_scan, 'lat': lat, 'lon': lon,
            }

    # ====== RESET ======
    if btn_reset:
        st.session_state.hasil_scan = None
        st.session_state.hasil_analisis = None
        st.session_state.info_scan = None
        st.session_state.info_analisis = None
        st.rerun()

    # ============================================
    # TAMPILKAN HASIL SCAN
    # ============================================
    if st.session_state.get('hasil_scan') is not None:
        hasil = st.session_state.hasil_scan
        info = st.session_state.info_scan
        st.divider()

        if not hasil:
            st.warning("Tidak ada toko/usaha ditemukan. Coba keyword lain atau perbesar radius.")
        else:
            st.success(f"✅ **{len(hasil)}** lokasi ditemukan di **{info['kota']}** (radius {info['radius']} km)")

            df = pd.DataFrame([{
                'No': i+1,
                'Nama': h['nama'],
                'Jarak (km)': h['jarak_km'],
                'Kategori': h['kategori'],
                'Skor Match': h.get('_skor', '-'),
                'Alasan': h.get('_alasan', '-'),
                'Alamat': h['alamat'],
                'Kontak': h['kontak'],
            } for i, h in enumerate(hasil)])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("🗺️ Peta Sebaran")
            try:
                import folium
                from streamlit_folium import st_folium
                m = folium.Map(location=[info['lat'], info['lon']], zoom_start=13)
                folium.Marker([info['lat'], info['lon']], popup="Pusat Scan",
                              icon=folium.Icon(color='red', icon='star', prefix='fa')).add_to(m)
                folium.Circle([info['lat'], info['lon']], radius=info['radius']*1000,
                              color='red', fill=True, fill_opacity=0.05).add_to(m)
                for h in hasil:
                    folium.Marker([h['lat'], h['lon']],
                                  popup=f"<b>{h['nama']}</b><br>{h['jarak_km']} km",
                                  tooltip=h['nama'],
                                  icon=folium.Icon(color='purple', icon='store', prefix='fa')).add_to(m)
                st_folium(m, width=None, height=450, key="map_scan")
            except Exception as e:
                st.warning(f"Peta error: {e}")

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv,
                               file_name=f"kompetitor_{info['keyword']}.csv",
                               mime="text/csv", key="dl_scan")

    # ============================================
    # TAMPILKAN HASIL ANALISIS
    # ============================================
    if st.session_state.get('hasil_analisis'):
        peluang = st.session_state.hasil_analisis
        info = st.session_state.info_analisis

        st.divider()
        st.success(f"✅ Analisis untuk **{info['kota']}** (keyword `{info['keyword']}`)")

        status = peluang.get('status_data', '')
        if status:
            st.caption(f"📊 **Sumber data**: {status}")

        skor = peluang.get('skor_peluang')

        c1, c2, c3 = st.columns(3)
        with c1:
            if skor is None:
                st.metric("⚠️ Skor Peluang", "N/A", help="Data tidak tersedia")
            else:
                warna = "🟢" if skor >= 7 else ("🟡" if skor >= 4 else "🔴")
                st.metric(f"{warna} Skor Peluang", f"{skor}/10")
        with c2:
            st.metric("🏪 Total Pesaing", peluang.get('jumlah_kompetitor', 0))
        with c3:
            st.metric("📏 Radius", f"{info['radius']} km")

        st.divider()
        st.subheader("💬 Rekomendasi")
        rekomendasi = peluang.get('rekomendasi', '-')
        kategori = peluang.get('kategori', '')

        if skor is None or 'PERLU VERIFIKASI' in kategori:
            st.warning(rekomendasi)
        elif skor >= 7:
            st.success(rekomendasi)
        elif skor >= 4:
            st.info(rekomendasi)
        else:
            st.error(rekomendasi)

        kompetitor = peluang.get('kompetitor', [])
        if kompetitor:
            st.divider()
            st.subheader(f"🏪 Daftar {len(kompetitor)} Pesaing Terdeteksi")

            df_pesaing = pd.DataFrame([{
                'No': i+1, 'Nama Toko': k['nama'], 'Jarak (km)': k['jarak_km'],
                'Kategori': k['kategori'], 'Alamat': k['alamat'],
                'Kontak': k['kontak'], 'Jam Buka': k['jam_buka'],
            } for i, k in enumerate(kompetitor)])
            st.dataframe(df_pesaing, use_container_width=True, hide_index=True)

            st.subheader("🗺️ Peta Pesaing")
            try:
                import folium
                from streamlit_folium import st_folium
                m = folium.Map(location=[info['lat'], info['lon']], zoom_start=13)
                folium.Marker([info['lat'], info['lon']], popup="Lokasi Anda",
                              icon=folium.Icon(color='red', icon='star', prefix='fa')).add_to(m)
                folium.Circle([info['lat'], info['lon']], radius=info['radius']*1000,
                              color='red', fill=True, fill_opacity=0.05).add_to(m)
                for k in kompetitor:
                    folium.Marker([k['lat'], k['lon']],
                                  popup=f"<b>{k['nama']}</b><br>{k['jarak_km']} km",
                                  tooltip=k['nama'],
                                  icon=folium.Icon(color='orange', icon='store', prefix='fa')).add_to(m)
                st_folium(m, width=None, height=450, key="map_pesaing")
            except Exception as e:
                st.warning(f"Peta error: {e}")

            csv2 = df_pesaing.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Daftar Pesaing", data=csv2,
                               file_name=f"pesaing_{info['keyword']}.csv",
                               mime="text/csv", key="dl_pesaing")
        elif skor is None:
            st.info("💡 **Tips**: Klik **🔍 Scan Sekarang** dulu untuk verifikasi apakah area ini benar-benar kosong atau cuma rate limit server.")
        else:
            st.success("🎉 **Tidak ada pesaing ditemukan!** Peluang EMAS.")

        st.divider()
        st.subheader("📊 Interpretasi Skor")
        st.markdown("""
        | Skor | Arti |
        |---|---|
        | **9-10** | 🟢 Peluang Emas (pesaing 0-2) |
        | **7-8** | 🟢 Peluang Baik (pesaing 3-5) |
        | **5-6** | 🟡 Sedang (pesaing 6-10) |
        | **3-4** | 🔴 Sulit (pesaing 11-20) |
        | **1-2** | 🔴 Jenuh (pesaing >20) |
        | **N/A** | ⚠️ Data tidak tersedia — coba lagi |
        """)


# =========================================================
# TAB 3 — TRENDS
# =========================================================
with tab1:
    st.header("📊 Google Trends per Wilayah")
    c1, c2 = st.columns([3, 1])
    with c1:
        kw = st.text_input("Kata kunci", value="kue", key="t_kw")
    with c2:
        top_n = st.number_input("Top N", 5, 30, 15, key="t_n")

    if st.button("🔍 Analisis", key="btn_t"):
        if kw.strip():
            with st.spinner("..."):
                try:
                    df = analisis_tren_per_kota(kw, top_n=int(top_n))
                    if not df.empty:
                        st.bar_chart(df.set_index('wilayah')['skor_0_100'])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"❌ {e}")

    st.divider()
    kws = st.text_input("Bandingkan (pisahkan koma)", value="kue, bolu, lapis, pastry", key="t_cmp")
    if st.button("⚖️ Bandingkan", key="btn_cmp"):
        daftar = [x.strip() for x in kws.split(',') if x.strip()]
        if len(daftar) >= 2:
            with st.spinner("..."):
                try:
                    hasil = bandingkan_keywords(daftar)
                    if not hasil.empty:
                        st.dataframe(hasil, use_container_width=True, hide_index=True)
                        st.bar_chart(hasil.set_index('keyword')['skor_0_100'])
                except Exception as e:
                    st.error(f"❌ {e}")


# =========================================================
# TAB 4 — KEYWORD
# =========================================================
with tab2:
    st.header("🔍 Autocomplete Explorer")
    kw_ac = st.text_input("Kata kunci", value="kue", key="ac_kw")
    c1, c2 = st.columns(2)
    with c1:
        prov_ac = st.selectbox("Provinsi", ["-- Semua --"] + list(KOTA_PER_PROVINSI.keys()), key="ac_p")
    with c2:
        if prov_ac and prov_ac != "-- Semua --":
            kota_list_ac = ["-- Semua --"] + KOTA_PER_PROVINSI.get(prov_ac, [])
        else:
            kota_list_ac = ["-- Pilih Provinsi --"]
        kota_ac = st.selectbox("Kota", kota_list_ac, key="ac_k")

    if kota_ac and kota_ac not in ["-- Semua --", "-- Pilih Provinsi --"]:
        kw_q = f"{kw_ac} {kota_ac}"
    elif prov_ac and prov_ac != "-- Semua --":
        kw_q = f"{kw_ac} {prov_ac}"
    else:
        kw_q = kw_ac

    st.info(f"🔍 Query: **{kw_q}**")
    hitung = st.checkbox("🎯 Hitung skor", value=True, key="ac_h")

    if st.button("🔍 Cari", key="btn_ac"):
        with st.spinner("..."):
            try:
                saran = ambil_autocomplete(kw_q)
                if saran and not saran[0].startswith("⚠️"):
                    if hitung:
                        skor = skor_autocomplete(saran, maks=5)
                        df_s = pd.DataFrame(skor)
                        df_s.columns = ['Keyword', 'Skor', '%', 'Est. Volume']
                        st.dataframe(df_s, use_container_width=True, hide_index=True)
                    else:
                        for i, s in enumerate(saran, 1):
                            st.markdown(f"**{i}.** {s}")
            except Exception as e:
                st.error(f"❌ {e}")


# =========================================================
# TAB 5 — CAMPAIGN
# =========================================================
with tab3:
    st.header("🗺️ Campaign")
    try:
        camps = ambil_campaign(hanya_aktif=False)
        if not camps:
            st.info("Belum ada campaign.")
        else:
            df_c = pd.DataFrame([{
                'ID': c['id'], 'Nama': c['nama'],
                'Lat': c['lat_toko'], 'Lon': c['lon_toko'],
                'Radius': c['radius_km'],
                'Status': '🟢' if c.get('aktif') else '🔴',
            } for c in camps])
            st.dataframe(df_c, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"❌ {e}")


# =========================================================
# TAB 6 — LEADS
# =========================================================
with tab4:
    st.header("👥 Leads")
    try:
        stat = statistik_leads()
        leads = ambil_leads()
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total", stat['total'])
        with c2: st.metric("Baru", stat['per_status'].get('baru', 0))
        with c3: st.metric("Follow-up", stat['per_status'].get('followup', 0))
        with c4: st.metric("Closing", stat['per_status'].get('closing', 0))
        if leads:
            df_l = pd.DataFrame([{
                'Nama': l['nama'], 'No WA': l['no_wa'],
                'Campaign': f"#{l['campaign_id']}" if l['campaign_id'] else '-',
                'Status': l['status'],
            } for l in leads])
            st.dataframe(df_l, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"❌ {e}")


# =========================================================
# TAB 7 — WA ANALYZER
# =========================================================
with tab5:
    st.header("📱 WA Analyzer")
    teks = st.text_area("Paste nomor (1/baris)", height=150, key="wa_in")
    if st.button("🔍 Analisis", key="btn_wa"):
        daftar = [l.strip() for l in teks.split('\n') if l.strip()]
        if daftar:
            with st.spinner("..."):
                hasil = analisis_daftar_nomor(daftar)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total", hasil['total'])
            with c2: st.metric("Valid", hasil['valid'])
            with c3: st.metric("Invalid", hasil['invalid'])
            with c4: st.metric("Duplikat", hasil['duplikat'])
            if hasil['per_operator']:
                st.dataframe(pd.DataFrame([
                    {'Operator': op, 'Jumlah': c}
                    for op, c in sorted(hasil['per_operator'].items(), key=lambda x: -x[1])
                ]), use_container_width=True, hide_index=True)


# =========================================================
# TAB 8 — PANDUAN
# =========================================================
with tab6:
    st.header("📖 Panduan")

    with st.expander("🗺️ Cara Pakai Tab Kompetitor", expanded=True):
        st.markdown("""
        ### 3 Tombol
        - **🔍 Scan Sekarang** — cari daftar toko/usaha di area
        - **🎯 Analisis Peluang** — hitung skor peluang buka outlet
        - **🔄 Reset** — bersihkan hasil

        ### Alur Terbaik
        1. Ketik nama kota → pilih dari dropdown
        2. Isi keyword usaha + radius
        3. Klik **Scan Sekarang** dulu (lihat daftar toko)
        4. **Langsung** klik **Analisis Peluang** → pakai data scan (cepat + hindari rate limit)

        ### Skor Peluang
        | Skor | Arti |
        |---|---|
        | **9-10** | 🟢 Peluang Emas (pesaing 0-2) |
        | **7-8** | 🟢 Peluang Baik (3-5) |
        | **5-6** | 🟡 Sedang (6-10) |
        | **3-4** | 🔴 Sulit (11-20) |
        | **1-2** | 🔴 Jenuh (>20) |
        | **N/A** | ⚠️ Rate limit — coba lagi 30 detik |
        """)

    with st.expander("🔬 Sumber Data"):
        st.markdown("""
        - **Google Trends** — skor relatif keyword
        - **Google Autocomplete** — real query orang Indonesia
        - **OpenStreetMap** (Overpass API) — data toko/usaha gratis
        - **EMSIFA API** — data wilayah Indonesia (514 kota)
        - **Rising Queries** — keyword sedang naik
        """)

    with st.expander("⚠️ Kenapa Skor N/A?"):
        st.markdown("""
        Skor **N/A** muncul kalau:
        - Server Overpass API sedang **rate limit** (banyak request)
        - Data OpenStreetMap di area tersebut memang kosong
        - Koneksi internet terputus

        **Solusi:**
        1. Tunggu 30-60 detik
        2. Klik **🔍 Scan Sekarang** dulu untuk verifikasi
        3. Coba keyword lain: `restoran`, `cafe`, `toko`
        """)

st.divider()
st.caption("© 2026 Market Intel — Dony Noviandri")