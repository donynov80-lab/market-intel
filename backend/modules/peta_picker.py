"""
peta_picker.py — v3
Komponen peta interaktif untuk memilih titik pusat scan.

Perbaikan v3:
  - Kursor crosshair (bukan tangan) — biar terasa seperti membidik
  - Circle interactive=False — klik di dalam lingkaran tembus ke peta
"""
import folium
from streamlit_folium import st_folium


def render_peta_picker(default_lat=-6.2088, default_lon=106.8456,
                       default_radius_km=5, zoom_start=11,
                       key="peta_picker", height=500):
    """
    Render peta interaktif untuk memilih titik pusat scan.

    Return dict: { 'lat', 'lon', 'radius_km', 'is_baru' }
    """
    import streamlit as st

    ss_lat = f"{key}_lat"
    ss_lon = f"{key}_lon"

    if ss_lat not in st.session_state:
        st.session_state[ss_lat] = default_lat
        st.session_state[ss_lon] = default_lon

    lat = st.session_state[ss_lat]
    lon = st.session_state[ss_lon]

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom_start,
        tiles='OpenStreetMap',
    )

    # === FIX 1: Kursor crosshair (bukan tangan grab) ===
    css = """
    <style>
        .leaflet-container { cursor: crosshair !important; }
        .leaflet-interactive { cursor: crosshair !important; }
        .leaflet-marker-icon { cursor: move !important; }  /* marker tetap bisa digeser */
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))

    # Marker pusat
    folium.Marker(
        [lat, lon],
        popup=f"Pusat scan<br>({lat:.5f}, {lon:.5f})",
        tooltip="Klik peta untuk pindah, atau geser marker ini",
        icon=folium.Icon(color='red', icon='star', prefix='fa'),
        draggable=True,
    ).add_to(m)

    # === FIX 2: interactive=False — klik tembus ke peta ===
    folium.Circle(
        [lat, lon],
        radius=default_radius_km * 1000,
        color='blue',
        fill=True,
        fill_opacity=0.15,
        interactive=False,
    ).add_to(m)

    # Popup koordinat saat klik (feedback instan)
    folium.LatLngPopup().add_to(m)

    output = st_folium(
        m,
        width=None,
        height=height,
        key=key,
        returned_objects=["last_clicked"],
        use_container_width=True,
    )

    is_baru = False
    if output and output.get("last_clicked"):
        lc = output["last_clicked"]
        new_lat = float(lc["lat"])
        new_lng = float(lc["lng"])

        if abs(new_lat - lat) > 1e-7 or abs(new_lng - lon) > 1e-7:
            st.session_state[ss_lat] = new_lat
            st.session_state[ss_lon] = new_lng
            is_baru = True
            st.rerun()

    return {
        'lat': st.session_state[ss_lat],
        'lon': st.session_state[ss_lon],
        'radius_km': default_radius_km,
        'is_baru': is_baru,
    }