"""
peta_dual.py — v2
Peta interaktif untuk memilih 2 lokasi (A & B) untuk Bandingkan Kota.

Fitur baru v2:
  - Tombol 🔄 Reset Peta & ↩️ Undo
  - Reverse geocoding (nama kota/kecamatan) via Nominatim
  - Info penduduk & density dari wilayah_lengkap
  - Status langkah jelas (Langkah 1 / 2 / Siap)
"""
import folium
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2
import requests
from pathlib import Path

# Cache reverse geocoding (Nominatim rate limit 1 req/detik)
_GEO_CACHE = {}


def reverse_geocode(lat, lon, timeout=6):
    """Reverse geocoding via Nominatim. Return dict info atau None."""
    key = f"{lat:.3f},{lon:.3f}"  # cache 3 desimal (~100m)
    if key in _GEO_CACHE:
        return _GEO_CACHE[key]
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat, "lon": lon, "format": "json",
                "zoom": 10, "accept-language": "id",
            },
            headers={"User-Agent": "MarketIntel/1.0 (contact: donynov80@gmail.com)"},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            addr = data.get("address", {})
            nama = (addr.get("city") or addr.get("town")
                    or addr.get("county") or addr.get("municipality")
                    or addr.get("state") or "-")
            hasil = {
                "nama": nama,
                "kota": addr.get("city") or addr.get("town") or "",
                "kecamatan": addr.get("suburb") or addr.get("village") or addr.get("town") or "",
                "provinsi": addr.get("state") or "",
                "display": data.get("display_name", "")[:200],
            }
            _GEO_CACHE[key] = hasil
            return hasil
    except Exception as e:
        print(f"[Geo] Error: {e}")
    _GEO_CACHE[key] = None
    return None


def info_penduduk_dari_nama(nama):
    """Cari penduduk & luas dari wilayah_lengkap by nama."""
    if not nama or nama == "-":
        return None
    try:
        import sys
        _ROOT = Path(__file__).parent.parent.parent
        if str(_ROOT) not in sys.path:
            sys.path.insert(0, str(_ROOT))
        from backend.modules.wilayah_bertingkat import get_lokasi_by_nama
        lok = get_lokasi_by_nama(nama)
        if lok:
            penduduk = lok.get("penduduk") or 0
            luas = lok.get("luas") or 0
            return {
                "penduduk": penduduk,
                "luas": luas,
                "density": (penduduk / luas) if luas else 0,
                "nama_resmi": lok.get("nama"),
                "level": lok.get("level"),
            }
    except Exception as e:
        print(f"[Penduduk] Error: {e}")
    return None


def _hitung_jarak(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))


def render_peta_dual(default_a=None, default_b=None, radius_km=7,
                     key="peta_dual", height=450, zoom_start=8):
    """
    Peta 2 marker dengan tombol kontrol & reverse geocoding.
    Return: {a, b, next_mode, geo_a, geo_b}
    """
    import streamlit as st

    ss_alat = f"{key}_a_lat"
    ss_alon = f"{key}_a_lon"
    ss_blat = f"{key}_b_lat"
    ss_blon = f"{key}_b_lon"
    ss_next = f"{key}_next"

    for k in [ss_alat, ss_alon, ss_blat, ss_blon]:
        if k not in st.session_state:
            st.session_state[k] = None
    if ss_next not in st.session_state:
        st.session_state[ss_next] = 'a'

    if st.session_state[ss_alat] is None and default_a and default_a.get('lat'):
        st.session_state[ss_alat] = default_a.get('lat')
        st.session_state[ss_alon] = default_a.get('lon')
    if st.session_state[ss_blat] is None and default_b and default_b.get('lat'):
        st.session_state[ss_blat] = default_b.get('lat')
        st.session_state[ss_blon] = default_b.get('lon')

    a_lat = st.session_state[ss_alat]
    a_lon = st.session_state[ss_alon]
    b_lat = st.session_state[ss_blat]
    b_lon = st.session_state[ss_blon]
    next_mode = st.session_state[ss_next]

    # === TOMBOL KONTROL ===
    col_b1, col_b2, col_b3 = st.columns([1, 1, 4])
    with col_b1:
        if st.button("🔄 Reset Peta", key=f"{key}_reset",
                     help="Kosongkan A & B, mulai dari awal"):
            st.session_state[ss_alat] = None
            st.session_state[ss_alon] = None
            st.session_state[ss_blat] = None
            st.session_state[ss_blon] = None
            st.session_state[ss_next] = 'a'
            st.rerun()
    with col_b2:
        if st.button("↩️ Undo", key=f"{key}_undo",
                     help="Batalkan langkah terakhir",
                     disabled=(next_mode == 'a')):
            if next_mode == 'b':
                st.session_state[ss_alat] = None
                st.session_state[ss_alon] = None
                st.session_state[ss_next] = 'a'
            elif next_mode == 'done':
                st.session_state[ss_blat] = None
                st.session_state[ss_blon] = None
                st.session_state[ss_next] = 'b'
            st.rerun()
    with col_b3:
        status_map = {
            'a': "🔵 **Langkah 1**: klik peta untuk set titik **A**",
            'b': "🔴 **Langkah 2**: klik peta untuk set titik **B**",
            'done': "✅ **Siap!** Scroll ke bawah → klik **Bandingkan Sekarang**",
        }
        st.info(status_map.get(next_mode, "-"))

    # === PETA ===
    centers = []
    if a_lat is not None: centers.append((a_lat, a_lon))
    if b_lat is not None: centers.append((b_lat, b_lon))
    if centers:
        c_lat = sum(c[0] for c in centers) / len(centers)
        c_lon = sum(c[1] for c in centers) / len(centers)
    else:
        c_lat, c_lon = -6.2088, 106.8456

    m = folium.Map(location=[c_lat, c_lon], zoom_start=zoom_start,
                   tiles='OpenStreetMap')

    css = """
    <style>
        .leaflet-container { cursor: crosshair !important; }
        .leaflet-interactive { cursor: crosshair !important; }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))

    if a_lat is not None:
        folium.Marker([a_lat, a_lon], tooltip="Lokasi A",
                      icon=folium.Icon(color='blue', icon='star', prefix='fa')
                      ).add_to(m)
        folium.Circle([a_lat, a_lon], radius=radius_km*1000,
                      color='blue', fill=True, fill_opacity=0.1,
                      interactive=False).add_to(m)
    if b_lat is not None:
        folium.Marker([b_lat, b_lon], tooltip="Lokasi B",
                      icon=folium.Icon(color='red', icon='star', prefix='fa')
                      ).add_to(m)
        folium.Circle([b_lat, b_lon], radius=radius_km*1000,
                      color='red', fill=True, fill_opacity=0.1,
                      interactive=False).add_to(m)
    if a_lat is not None and b_lat is not None:
        folium.PolyLine([(a_lat, a_lon), (b_lat, b_lon)],
                        color='purple', weight=2, dash_array='8 5').add_to(m)
        jarak_ab = _hitung_jarak(a_lat, a_lon, b_lat, b_lon)
        mid_lat, mid_lon = (a_lat+b_lat)/2, (a_lon+b_lon)/2
        folium.Marker([mid_lat, mid_lon],
                      icon=folium.DivIcon(html=(
                          f'<div style="color:purple;font-weight:bold;'
                          f'background:white;padding:2px 6px;border-radius:3px;'
                          f'font-size:11px;border:1px solid purple;'
                          f'white-space:nowrap">↔ {jarak_ab:.1f} km</div>'
                      ))).add_to(m)

    output = st_folium(m, width=None, height=height, key=key,
                       returned_objects=["last_clicked"],
                       use_container_width=True)

    if output and output.get("last_clicked"):
        lc = output["last_clicked"]
        new_lat = float(lc["lat"])
        new_lng = float(lc["lng"])
        if next_mode == 'a':
            st.session_state[ss_alat] = new_lat
            st.session_state[ss_alon] = new_lng
            st.session_state[ss_next] = 'b'
            st.rerun()
        elif next_mode == 'b':
            st.session_state[ss_blat] = new_lat
            st.session_state[ss_blon] = new_lng
            st.session_state[ss_next] = 'done'
            st.rerun()
        else:
            # done → klik berikutnya reset otomatis ke A baru
            st.session_state[ss_alat] = new_lat
            st.session_state[ss_alon] = new_lng
            st.session_state[ss_blat] = None
            st.session_state[ss_blon] = None
            st.session_state[ss_next] = 'b'
            st.rerun()

    # === INFO LOKASI (reverse geocoding + penduduk) ===
    col_a, col_b = st.columns(2)

    with col_a:
        if a_lat is not None:
            geo_a = reverse_geocode(a_lat, a_lon)
            if geo_a:
                st.success(f"🔵 **A** — {geo_a['nama']}")
                if geo_a.get('kecamatan'):
                    st.caption(
                        f"📍 {geo_a['kecamatan']} | {geo_a.get('provinsi', '-')}"
                    )
                pend_a = info_penduduk_dari_nama(geo_a['nama'])
                if pend_a and pend_a['penduduk'] > 0:
                    st.caption(
                        f"👥 {pend_a['penduduk']:,} org | "
                        f"📐 {pend_a['luas']:,.0f} km² | "
                        f"📊 {pend_a['density']:,.0f} org/km²"
                    )
                st.caption(f"🛰️ `{a_lat:.4f}, {a_lon:.4f}`")
            else:
                st.info(f"🔵 **A**: `{a_lat:.4f}, {a_lon:.4f}`")
        else:
            st.info("🔵 **A**: belum dipilih")

    with col_b:
        if b_lat is not None:
            geo_b = reverse_geocode(b_lat, b_lon)
            if geo_b:
                st.success(f"🔴 **B** — {geo_b['nama']}")
                if geo_b.get('kecamatan'):
                    st.caption(
                        f"📍 {geo_b['kecamatan']} | {geo_b.get('provinsi', '-')}"
                    )
                pend_b = info_penduduk_dari_nama(geo_b['nama'])
                if pend_b and pend_b['penduduk'] > 0:
                    st.caption(
                        f"👥 {pend_b['penduduk']:,} org | "
                        f"📐 {pend_b['luas']:,.0f} km² | "
                        f"📊 {pend_b['density']:,.0f} org/km²"
                    )
                st.caption(f"🛰️ `{b_lat:.4f}, {b_lon:.4f}`")
            else:
                st.info(f"🔴 **B**: `{b_lat:.4f}, {b_lon:.4f}`")
        else:
            st.info("🔴 **B**: belum dipilih")

    return {
        'a': {'lat': a_lat, 'lon': a_lon} if a_lat is not None else None,
        'b': {'lat': b_lat, 'lon': b_lon} if b_lat is not None else None,
        'next_mode': next_mode,
    }