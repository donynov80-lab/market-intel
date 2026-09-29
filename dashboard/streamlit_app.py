"""
streamlit_app.py — Dashboard Market Intel
Enhanced: filter subgolongan KBLI + density-based analysis
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

from backend.db.snapshot_db import (
    save_snapshot, get_snapshots, get_tren,
    compare_snapshots, stats_snapshot, list_kombinasi,
)
from backend.db.master_db import (
    upsert_master_batch, get_master, get_master_stats,
)



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

for key in ['hasil_scan', 'hasil_analisis', 'info_scan', 'info_analisis', 'hasil_trending', 'master_baru_scan_terakhir']:
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

tab_lokasi, tab_maps, tab1, tab2, tab3, tab4, tab5, tab6, tab_tren = st.tabs([
    "📍 Trending per Lokasi", "🗺️ Peta Kompetitor", "📊 Trends",
    "🔍 Keyword", "🗺️ Campaign", "👥 Leads", "📱 WA Analyzer", "📖 Panduan",
    "📈 Tren & Master"
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
        prov = st.selectbox("🏙️ Provinsi (WAJIB)", prov_list,
                            format_func=lambda x: x['name'], index=9, key="lp")
    with c2:
        kota_list = load_kota(prov['id']) if prov else []
        opsi_kota = [{'id': '', 'name': '-- Semua Kota (opsional) --'}] + kota_list
        kota = st.selectbox("🏘️ Kota (opsional)", opsi_kota,
                            format_func=lambda x: x['name'], key="lk")
    with c3:
        kec_list = load_kecamatan(kota['id']) if kota and kota.get('id') else []
        opsi_kec = [{'id': '', 'name': '-- Semua Kecamatan (opsional) --'}] + kec_list
        kec = st.selectbox("🏡 Kecamatan (opsional)", opsi_kec,
                           format_func=lambda x: x['name'], key="lkc")
    with c4:
        kel_list = load_kelurahan(kec['id']) if kec and kec.get('id') else []
        opsi_kel = [{'id': '', 'name': '-- Semua Kelurahan (opsional) --'}] + kel_list
        kel = st.selectbox("🏠 Kelurahan (opsional)", opsi_kel,
                           format_func=lambda x: x['name'], key="lkl")

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
        st.info(f"🔍 Query analisis: **{hasil.get('keyword_lokal', '')}**")

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
# TAB 2 — PETA KOMPETITOR & PELUANG  (ENHANCED)
# =========================================================
with tab_maps:
    st.header("🗺️ Peta Kompetitor & Peluang Pasar")
    st.caption("Scan pesaing + analisis peluang buka outlet")

    st.info("""
    **ℹ️ Alur Pakai:**
    1. Ketik nama kota → **pilih KOTA (bukan KABUPATEN)**
    2. Klik **🔍 Scan Sekarang** → lihat daftar toko
    3. Filter **Subgolongan KBLI** kalau perlu
    4. Klik **🎯 Analisis Peluang** → hitung skor
    """)

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

        if kota_data.get('penduduk'):
            pend = kota_data['penduduk']
            luas = kota_data.get('luas') or 0
            info = f"👥 **Penduduk**: {pend:,} orang"
            if luas:
                info += f" | 📐 **Luas**: {luas:.1f} km² | 📊 **Kepadatan**: {pend/luas:.0f} org/km²"
            st.caption(info)

        if kota_data and not kota_data.get('geocoded', False):
            st.warning(f"⚠️ **{kota_data.get('kota', 'Kota ini')}** belum punya koordinat.")

    c1, c2 = st.columns([3, 1])
    with c1:
        keyword_scan = st.text_input("Keyword Usaha", value="kue", key="mk_kw")
    with c2:
        radius_scan = st.number_input("Radius (km)", 1, 30, 5, key="mk_rad")

    if radius_scan > 10:
        st.warning("⚠️ Radius > 10 km bisa gagal. Saran: 3-8 km.")

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
            st.error("Kota tidak punya koordinat. Pilih kota lain.")
        else:
            nama_kota = kota_data.get('kota', '')
            if 'KABUPATEN' in nama_kota.upper():
                st.info(f"💡 **{nama_kota}** adalah KABUPATEN (rural). "
                        "Coba pilih **KOTA** untuk hasil lebih baik.")

            with st.spinner(f"Scan {keyword_scan} di {nama_kota}..."):
                try:
                    scan_result = scan_sekitar(lat, lon,
                                                radius_m=int(radius_scan * 1000),
                                                keyword=keyword_scan, maks=100)
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
                    scan_result = {'success': False, 'data': [], 'error': str(e)}

            if not scan_result.get('success'):
                st.error(f"❌ Gagal: {scan_result.get('error', 'Unknown')}")
                st.warning("""
                **Coba salah satu:**
                1. Ganti **KABUPATEN** → **KOTA** (misal: "Kota Bandung")
                2. Tunggu 60 detik → scan lagi
                3. Ganti keyword: `restoran`, `cafe`, `toko`
                4. Perkecil radius jadi 3 km
                """)
            else:
                hasil_data = scan_result.get('data', [])
                from_cache = scan_result.get('from_cache', False)
                query_used = scan_result.get('query_used', '')

                if not hasil_data:
                    st.warning(f"⚠️ 0 hasil untuk '{keyword_scan}'")
                    st.info("Coba keyword lebih umum: `restoran`, `toko`, `cafe`")
                else:
                    status = "dari cache" if from_cache else f"query: {query_used}"
                    st.success(f"✅ {len(hasil_data)} toko ditemukan ({status})")

                st.session_state.hasil_scan = hasil_data
                st.session_state.info_scan = {
                    'kota': kota_pilih, 'keyword': keyword_scan,
                    'radius': radius_scan, 'lat': lat, 'lon': lon,
                    'penduduk': kota_data.get('penduduk'),
                    'luas': kota_data.get('luas'),
                }
                st.session_state.hasil_analisis = None

                  # === BARU: Auto-upsert ke master katalog ===
                try:
                    stat_master = upsert_master_batch(
                        hasil_data or [],
                        keyword=keyword_scan,
                        kota=kota_pilih,
                    )
                    st.session_state.master_baru_scan_terakhir = stat_master
                except Exception as e:
                    st.warning(f"Master upsert gagal: {e}")
                    st.session_state.master_baru_scan_terakhir = None              

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
                        st.info(f"♻️ Reuse {len(reuse)} toko dari scan.")

            with st.spinner("Menganalisis..."):
                peluang = analisis_peluang(lat, lon, keyword_scan,
                                            radius_km=radius_scan,
                                            kompetitor_list=reuse)
            st.session_state.hasil_analisis = peluang
            st.session_state.info_analisis = {
                'kota': kota_pilih, 'keyword': keyword_scan,
                'radius': radius_scan, 'lat': lat, 'lon': lon,
                'penduduk': kota_data.get('penduduk'),
                'luas': kota_data.get('luas'),
            }

    if btn_reset:
        st.session_state.hasil_scan = None
        st.session_state.hasil_analisis = None
        st.session_state.info_scan = None
        st.session_state.info_analisis = None
        st.rerun()

    # ============================================
    # TAMPILKAN HASIL SCAN (dengan FILTER SUBGOLONGAN)
    # ============================================
    if st.session_state.get('hasil_scan') is not None:
        hasil = st.session_state.hasil_scan
        info = st.session_state.info_scan

        # === BARU: Info master + tombol Simpan Snapshot ===
        _m = st.session_state.get('master_baru_scan_terakhir')
        if _m and (_m.get('baru', 0) > 0 or _m.get('update', 0) > 0):
            st.info(
                f"📚 **Master katalog**: {_m['baru']} toko **BARU** "
                f"| {_m['update']} toko sudah dikenal sebelumnya"
            )

        with st.expander("💾 Simpan sebagai Snapshot (untuk tracking bulanan)"):
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                label_snap = st.text_input(
                    "Label snapshot (opsional)",
                    placeholder="mis. Akhir Sep 2026",
                    key="snap_label",
                )
                catatan_snap = st.text_area(
                    "Catatan (opsional)", height=68, key="snap_catatan",
                )
            with col_s2:
                st.write("")
                st.write("")
                if st.button("💾 Simpan Snapshot", key="btn_snap",
                             type="primary", use_container_width=True):
                    try:
                        sid = save_snapshot(
                            kota=info.get('kota', '-'),
                            keyword=info.get('keyword', '-'),
                            radius_km=info.get('radius', 0),
                            data=st.session_state.hasil_scan or [],
                            lat=info.get('lat'),
                            lon=info.get('lon'),
                            label=label_snap.strip() or None,
                            catatan=catatan_snap.strip() or None,
                        )
                        if sid:
                            st.success(f"✅ Snapshot #{sid} tersimpan!")
                        else:
                            st.error("Gagal simpan snapshot.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()

        if not hasil:
            st.warning("Tidak ada toko ditemukan.")
        else:
            st.success(f"✅ **{len(hasil)}** lokasi di **{info['kota']}** (radius {info['radius']} km)")

            # =====================================================
            # ⭐ FILTER SUBGOLONGAN (BARU) ⭐
            # =====================================================
            subgol_codes = sorted({
                h.get('code_4digit') for h in hasil if h.get('code_4digit')
            })
            subgol_title_map = {}
            subgol_count = {}
            for h in hasil:
                c = h.get('code_4digit')
                if not c:
                    continue
                subgol_count[c] = subgol_count.get(c, 0) + 1
                if c not in subgol_title_map:
                    subgol_title_map[c] = h.get('subgolongan_title') or '-'

            def _fmt_subgol(code):
                t = subgol_title_map.get(code, '-')
                n = subgol_count.get(code, 0)
                return f"{code} — {t[:60]}  ({n})"

            if subgol_codes:
                with st.expander("🎚️ Filter Subgolongan (KBLI 4-digit)", expanded=True):
                    pilihan = st.multiselect(
                        "Pilih subgolongan yang ingin ditampilkan:",
                        options=subgol_codes,
                        default=subgol_codes,
                        format_func=_fmt_subgol,
                        key="filter_subgol",
                    )
                    search_text = st.text_input(
                        "🔎 Cari nama toko (opsional):",
                        placeholder="contoh: kue, outlet, bengkel",
                        key="filter_name",
                    )
            else:
                pilihan = []
                search_text = ""

            # Apply filter
            hasil_filtered = list(hasil)
            if pilihan:
                hasil_filtered = [h for h in hasil_filtered
                                  if h.get('code_4digit') in pilihan]
            if search_text:
                s_low = search_text.lower()
                hasil_filtered = [h for h in hasil_filtered
                                  if s_low in (h.get('nama', '') or '').lower()]

            st.write(f"**Menampilkan {len(hasil_filtered)} dari {len(hasil)} toko.**")

            # ---- Ringkasan per subgolongan (jika ada) ----
            if subgol_codes:
                with st.expander("📊 Breakdown per subgolongan", expanded=False):
                    summary_rows = []
                    for c in subgol_codes:
                        n_total = subgol_count.get(c, 0)
                        n_filtered = sum(1 for h in hasil_filtered
                                         if h.get('code_4digit') == c)
                        summary_rows.append({
                            'Kode 4d': c,
                            'Subgolongan': subgol_title_map.get(c, '-'),
                            'Total': n_total,
                            'Ditampilkan': n_filtered,
                        })
                    summary_df = pd.DataFrame(summary_rows).sort_values(
                        'Total', ascending=False)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # ---- Tabel bisnis ----
            df = pd.DataFrame([{
                'No': i + 1,
                'Nama': h['nama'],
                'Kode 4d': h.get('code_4digit') or '-',
                'Subgolongan': h.get('subgolongan_title') or '-',
                'Jarak (km)': h['jarak_km'],
                'Kategori OSM': h['kategori'],
                'Skor Match': h.get('_skor', '-'),
                'Alasan': h.get('_alasan', '-'),
                'Alamat': h['alamat'],
                'Kontak': h['kontak'],
            } for i, h in enumerate(hasil_filtered)])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("🗺️ Peta")
            try:
                import folium
                from streamlit_folium import st_folium
                m = folium.Map(location=[info['lat'], info['lon']], zoom_start=13)
                folium.Marker([info['lat'], info['lon']], popup="Pusat",
                              icon=folium.Icon(color='red', icon='star', prefix='fa')).add_to(m)
                folium.Circle([info['lat'], info['lon']], radius=info['radius']*1000,
                              color='red', fill=True, fill_opacity=0.05).add_to(m)
                for h in hasil_filtered:
                    tooltip = f"{h['nama']} ({h.get('code_4digit') or '-'})"
                    folium.Marker([h['lat'], h['lon']],
                                  popup=f"<b>{h['nama']}</b><br>{h['jarak_km']} km<br>"
                                        f"{h.get('subgolongan_title') or '-'}",
                                  tooltip=tooltip,
                                  icon=folium.Icon(color='purple', icon='store', prefix='fa')).add_to(m)
                st_folium(m, width=None, height=450, key="map_scan")
            except Exception as e:
                st.warning(f"Peta error: {e}")

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv,
                               file_name=f"kompetitor_{info['keyword']}.csv",
                               mime="text/csv", key="dl_scan")

    # ============================================
    # TAMPILKAN HASIL ANALISIS (dengan density)
    # ============================================
    if st.session_state.get('hasil_analisis'):
        peluang = st.session_state.hasil_analisis
        info = st.session_state.info_analisis

        st.divider()
        st.success(f"✅ Analisis untuk **{info['kota']}** (`{info['keyword']}`)")

        status = peluang.get('status_data', '')
        if status:
            st.caption(f"📊 **Sumber data**: {status}")

        skor = peluang.get('skor_peluang')
        jumlah_kompetitor = peluang.get('jumlah_kompetitor', 0)

        # ============ METRICS (ENHANCED: density) ============
        penduduk = info.get('penduduk')
        if penduduk:
            c1, c2, c3, c4 = st.columns(4)
        else:
            c1, c2, c3 = st.columns(3)

        with c1:
            if skor is None:
                st.metric("⚠️ Skor Peluang", "N/A")
            else:
                warna = "🟢" if skor >= 7 else ("🟡" if skor >= 4 else "🔴")
                st.metric(f"{warna} Skor Peluang", f"{skor}/10")
        with c2:
            st.metric("🏪 Total Pesaing", jumlah_kompetitor)
        with c3:
            st.metric("📏 Radius", f"{info['radius']} km")

        # ---- BARU: Density per 10rb penduduk ----
        if penduduk and penduduk > 0:
            density = jumlah_kompetitor / penduduk * 10000
            with c4:
                st.metric("📊 Density /10rb org", f"{density:.2f}")

            # Verdict density
            if density < 0.5:
                st.success(f"🟢 **Density {density:.2f} per 10rb** — peluang sangat besar, "
                           f"kompetitor sangat sedikit untuk {penduduk:,} penduduk.")
            elif density < 1.0:
                st.info(f"🟡 **Density {density:.2f} per 10rb** — peluang sedang, "
                        f"masih di bawah benchmark.")
            elif density < 3.0:
                st.warning(f"🟠 **Density {density:.2f} per 10rb** — kompetitif, "
                           f"perlu diferensiasi.")
            else:
                st.error(f"🔴 **Density {density:.2f} per 10rb** — pasar jenuh.")

        # ============ END METRICS ============

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
            st.subheader(f"🏪 Daftar {len(kompetitor)} Pesaing")
            df_pesaing = pd.DataFrame([{
                'No': i + 1,
                'Nama Toko': k['nama'],
                'Kode 4d': k.get('code_4digit') or '-',
                'Subgolongan': k.get('subgolongan_title') or '-',
                'Jarak (km)': k['jarak_km'],
                'Kategori': k['kategori'],
                'Alamat': k['alamat'],
                'Kontak': k['kontak'],
            } for i, k in enumerate(kompetitor)])
            st.dataframe(df_pesaing, use_container_width=True, hide_index=True)

            # Ringkasan per subgolongan pesaing
            pesaing_subgol = {}
            for k in kompetitor:
                c = k.get('code_4digit')
                if not c:
                    continue
                if c not in pesaing_subgol:
                    pesaing_subgol[c] = {
                        'Kode 4d': c,
                        'Subgolongan': k.get('subgolongan_title') or '-',
                        'Jumlah': 0,
                    }
                pesaing_subgol[c]['Jumlah'] += 1
            if pesaing_subgol:
                with st.expander("📊 Pesaing per subgolongan", expanded=False):
                    st.dataframe(
                        pd.DataFrame(list(pesaing_subgol.values()))
                          .sort_values('Jumlah', ascending=False),
                        use_container_width=True, hide_index=True)

            csv2 = df_pesaing.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Daftar Pesaing", data=csv2,
                               file_name=f"pesaing_{info['keyword']}.csv",
                               mime="text/csv", key="dl_pesaing")
        elif skor is None:
            st.info("💡 Klik **🔍 Scan Sekarang** dulu untuk verifikasi.")
        else:
            st.success("🎉 **Tidak ada pesaing!** Peluang EMAS.")

        st.divider()
        st.subheader("📊 Interpretasi Skor")
        st.markdown("""
        | Skor | Arti |
        |---|---|
        | **9-10** | 🟢 Peluang Emas |
        | **7-8** | 🟢 Peluang Baik |
        | **5-6** | 🟡 Sedang |
        | **3-4** | 🔴 Sulit |
        | **1-2** | 🔴 Jenuh |
        | **N/A** | ⚠️ Data tidak tersedia |

        **Density per 10rb penduduk**: angka ini menunjukkan berapa pesaing
        per 10.000 penduduk. Semakin kecil, semakin besar peluang.
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
    kws = st.text_input("Bandingkan (koma)", value="kue, bolu, lapis, pastry", key="t_cmp")
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
        ### Tips Penting
        - Pilih **KOTA** (bukan KABUPATEN) — lebih padat
        - Radius **3-8 km** untuk kota besar
        - Kalau error, tunggu **60 detik** lalu coba lagi

        ### Filter Subgolongan (BARU)
        - Setelah scan, muncul **panel filter** di atas tabel
        - Pilih subgolongan KBLI 4-digit yang ingin ditampilkan
        - Contoh: `4722` = Perdagangan Eceran Minuman (termasuk miras)
        - Berguna untuk memisah "kue" vs "roti" vs "catering"

        ### Density per 10rb Penduduk (BARU)
        - Muncul di bawah metrik skor peluang
        - Semakin kecil density → semakin besar peluang
        - Aturan cepat: `< 0.5` = peluang emas, `> 3` = jenuh

        ### Skor Peluang
        | Skor | Arti |
        |---|---|
        | **9-10** | 🟢 Peluang Emas |
        | **7-8** | 🟢 Baik |
        | **5-6** | 🟡 Sedang |
        | **3-4** | 🔴 Sulit |
        | **1-2** | 🔴 Jenuh |
        """)

    with st.expander("🔬 Sumber Data"):
        st.markdown("""
        - **Google Trends** — skor relatif keyword
        - **Google Autocomplete** — real query
        - **OpenStreetMap (Overpass)** — toko gratis
        - **KBLI Badan Pusat Statistik** — klasifikasi baku
        - **EMSIFA API** — wilayah Indonesia
        """)

    with st.expander("⚠️ Kenapa Skor N/A?"):
        st.markdown("""
        - Server Overpass rate limit
        - Data OSM kurang lengkap di area
        - Koneksi terputus

        **Solusi:** tunggu 60 detik, ganti keyword, atau pilih KOTA bukan KABUPATEN.
        """)

# =========================================================
# TAB 9 — TREN & MASTER
# =========================================================
with tab_tren:
    st.header("📈 Tren Kompetitor & Katalog Master")
    st.caption("Riwayat snapshot bulanan + semua toko yang pernah terlihat")

    sub_tren, sub_master = st.tabs(["📊 Grafik Tren", "📚 Katalog Master"])

    # -------- SUB 1: TREN --------
    with sub_tren:
        st.subheader("📊 Tren Jumlah Kompetitor")
        kombinasi = list_kombinasi()

        if not kombinasi:
            st.info(
                "Belum ada snapshot. Lakukan scan di Tab Peta Kompetitor, "
                "lalu klik **💾 Simpan Snapshot** untuk mulai tracking."
            )
        else:
            kota_unik = sorted(set(k['kota'] for k in kombinasi))
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                pilihan_kota = st.selectbox("Pilih kota", kota_unik, key="tren_kota")
            with col_t2:
                opsi_kw = sorted(set(
                    k['keyword'] for k in kombinasi if k['kota'] == pilihan_kota
                ))
                pilihan_kw = st.selectbox("Pilih keyword", opsi_kw, key="tren_kw")

            tren = get_tren(pilihan_kota, pilihan_kw)
            if tren:
                df_tren = pd.DataFrame(tren)
                df_tren['label_display'] = df_tren['label'].fillna('').replace('', pd.NA)
                df_tren['label_display'] = df_tren['label_display'].fillna(
                    df_tren['snapshot_at'].str[:10]
                )
                df_tren = df_tren.set_index('label_display')
                st.line_chart(df_tren['jumlah'], height=320)
                st.dataframe(
                    df_tren[['jumlah']].rename(columns={'jumlah': 'Jumlah Toko'}),
                    use_container_width=True,
                )
            else:
                st.info("Belum ada data tren untuk kombinasi ini.")

    # -------- SUB 2: MASTER --------
    with sub_master:
        st.subheader("📚 Katalog Master Kompetitor")

        stats_m = get_master_stats()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Toko Unik", stats_m['total'])
        c2.metric("🔴 Baru 30 Hari", stats_m['baru_30_hari'])
        c3.metric(
            "KBLI Terbanyak",
            stats_m['top_kbli'][0]['code'] if stats_m['top_kbli'] else '-'
        )

        st.divider()
        with st.expander("🔍 Filter & Pencarian", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                kw_filter = st.text_input("Keyword", placeholder="mis. miras", key="mst_kw")
            with col_f2:
                kota_filter = st.text_input("Kota (contains)", placeholder="mis. Denpasar", key="mst_kota")
            with col_f3:
                nama_filter = st.text_input("Nama toko (contains)", key="mst_nama")

            col_f4, col_f5 = st.columns(2)
            with col_f4:
                kode_filter = st.text_input("Kode KBLI 4-digit", placeholder="mis. 4722", key="mst_kode")
            with col_f5:
                baru_filter = st.checkbox("🔴 Hanya toko baru 30 hari", key="mst_baru")

        daftar = get_master(
            keyword=kw_filter.strip() or None,
            kota=kota_filter.strip() or None,
            code_4digit=kode_filter.strip() or None,
            cari_nama=nama_filter.strip() or None,
            baru_dalam_hari=30 if baru_filter else None,
            limit=500,
        )

        if not daftar:
            st.info("Belum ada data master. Lakukan scan dulu di Tab Peta Kompetitor.")
        else:
            st.success(f"📊 {len(daftar)} toko ditemukan")
            df_master = pd.DataFrame([{
                'Nama': m['nama'],
                'Obs': m['observation_count'],
                'First Seen': (m['first_seen'] or '')[:10],
                'Last Seen': (m['last_seen'] or '')[:10],
                'KBLI': m['code_4digit'] or '-',
                'Subgolongan': m['subgolongan_title'] or '-',
                'Keywords': ', '.join(m.get('keywords', [])),
                'Kota': ', '.join(m.get('kotas', [])),
            } for m in daftar])
            st.dataframe(df_master, use_container_width=True, hide_index=True)


st.divider()
st.caption("© 2026 Market Intel — Dony Noviandri")