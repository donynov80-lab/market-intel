"""
app.py
Server Flask utama — Geo-Fence Landing Page.

Jalankan: python app.py
Buka: http://localhost:5000
"""
from flask import Flask, render_template, request, jsonify
from math import radians, sin, cos, sqrt, atan2
import sys
from pathlib import Path

# Biar bisa import dari backend/
sys.path.insert(0, str(Path(__file__).parent))

from backend.db.campaign_db import ambil_campaign


# =========================================================
# INISIALISASI FLASK
# =========================================================
app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static',
    static_url_path='/static'
)


# =========================================================
# FUNGSI BANTUAN — HITUNG JARAK (HAVERSINE)
# =========================================================
def hitung_jarak_km(lat1, lon1, lat2, lon2):
    """
    Hitung jarak antara 2 koordinat (rumus Haversine).
    Return: jarak dalam km
    """
    R = 6371  # radius bumi dalam km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat/2)**2 +
         cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# =========================================================
# ROUTE 1 — HALAMAN UTAMA
# =========================================================
@app.route('/')
def index():
    """Tampilkan halaman utama geo-fence."""
    return render_template('geo_fence.html')


# =========================================================
# ROUTE 2 — API LIST CAMPAIGN (untuk peta)
# =========================================================
@app.route('/api/campaign')
def api_campaign():
    """Return list campaign aktif dalam format JSON."""
    campaigns = ambil_campaign(hanya_aktif=True)

    data = [{
        'id': c['id'],
        'nama': c['nama'],
        'lat': c['lat_toko'],
        'lon': c['lon_toko'],
        'radius_km': c['radius_km'],
    } for c in campaigns]

    return jsonify({'campaign': data, 'total': len(data)})


# =========================================================
# ROUTE 3 — API CEK LOKASI
# =========================================================
@app.route('/cek-lokasi', methods=['POST'])
def cek_lokasi():
    """
    Terima koordinat user, cek apakah dalam radius salah satu campaign.
    """
    try:
        data = request.get_json()
        user_lat = float(data['lat'])
        user_lon = float(data['lon'])
    except (KeyError, TypeError, ValueError):
        return jsonify({
            'status': 'error',
            'pesan': 'Format request salah. Butuh lat dan lon.'
        }), 400

    campaigns = ambil_campaign(hanya_aktif=True)
    if not campaigns:
        return jsonify({
            'status': 'error',
            'pesan': 'Belum ada campaign yang aktif.',
            'semua_campaign': []
        })

    cocok = None
    jarak_terdekat = float('inf')
    campaign_terdekat = None

    for c in campaigns:
        jarak = hitung_jarak_km(user_lat, user_lon, c['lat_toko'], c['lon_toko'])

        if jarak < jarak_terdekat:
            jarak_terdekat = jarak
            campaign_terdekat = c

        if jarak <= c['radius_km']:
            if cocok is None or jarak < hitung_jarak_km(
                user_lat, user_lon, cocok['lat_toko'], cocok['lon_toko']
            ):
                cocok = c
                cocok['_jarak'] = jarak

    semua = [{
        'id': c['id'],
        'nama': c['nama'],
        'lat': c['lat_toko'],
        'lon': c['lon_toko'],
        'radius_km': c['radius_km'],
    } for c in campaigns]

    if cocok:
        return jsonify({
            'status': 'in',
            'jarak_km': round(cocok['_jarak'], 2),
            'campaign': {
                'id': cocok['id'],
                'nama': cocok['nama'],
                'konten': cocok['konten'],
                'wa_link': cocok.get('wa_link', ''),
            },
            'semua_campaign': semua
        })
    else:
        return jsonify({
            'status': 'out',
            'jarak_terdekat_km': round(jarak_terdekat, 2),
            'radius_km': campaign_terdekat['radius_km'] if campaign_terdekat else 0,
            'nama_campaign_terdekat': campaign_terdekat['nama'] if campaign_terdekat else '-',
            'pesan': (
                f"Promo hanya berlaku untuk area dalam radius "
                f"{campaign_terdekat['radius_km'] if campaign_terdekat else 0} km "
                f"dari toko kami."
            ),
            'semua_campaign': semua
        })


# =========================================================
# ROUTE 4 — API SIMPAN LEAD
# =========================================================
@app.route('/api/lead', methods=['POST'])
def api_tambah_lead():
    """Simpan lead baru dari user yang klaim promo."""
    from backend.db.leads_db import tambah_lead
    from backend.db.campaign_db import ambil_campaign

    try:
        data = request.get_json()
        nama = data.get('nama', '').strip()
        no_wa = data.get('no_wa', '').strip()

        if not nama or len(nama) < 2:
            return jsonify({'status': 'error', 'pesan': 'Nama minimal 2 karakter'}), 400
        if not no_wa or len(no_wa.replace(' ', '').replace('-', '')) < 9:
            return jsonify({'status': 'error', 'pesan': 'Nomor WA tidak valid'}), 400

        no_wa_clean = no_wa.replace(' ', '').replace('-', '').replace('+', '')
        if no_wa_clean.startswith('0'):
            no_wa_clean = '62' + no_wa_clean[1:]
        elif not no_wa_clean.startswith('62'):
            no_wa_clean = '62' + no_wa_clean

        lead_id = tambah_lead(
            nama=nama,
            no_wa=no_wa_clean,
            email=data.get('email', ''),
            campaign_id=data.get('campaign_id'),
            lat=data.get('lat'),
            lon=data.get('lon'),
            catatan=data.get('catatan', '')
        )

        wa_link = ''
        cid = data.get('campaign_id')
        if cid:
            camp = ambil_campaign(id_campaign=cid)
            if camp and camp.get('wa_link'):
                wa_link = camp['wa_link']
                if 'text=' not in wa_link:
                    separator = '&' if '?' in wa_link else '?'
                    from urllib.parse import quote
                    pesan = f"Halo, saya {nama}, saya lihat promo {camp['nama']} dan tertarik!"
                    wa_link += f"{separator}text={quote(pesan)}"

        return jsonify({
            'status': 'ok',
            'lead_id': lead_id,
            'pesan': f'Terima kasih {nama}! Data kamu tersimpan.',
            'wa_link': wa_link
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'pesan': f'Gagal simpan lead: {str(e)}'
        }), 500


# =========================================================
# ROUTE ADMIN — HALAMAN KELOLA CAMPAIGN
# =========================================================
@app.route('/admin')
def admin():
    """Tampilkan halaman admin."""
    return render_template('admin.html')


# =========================================================
# API ADMIN — LIST CAMPAIGN (semua)
# =========================================================
@app.route('/api/admin/campaign')
def api_admin_list():
    """Return semua campaign (termasuk yang nonaktif)."""
    from backend.db.campaign_db import ambil_campaign
    campaigns = ambil_campaign(hanya_aktif=False)
    return jsonify({'campaign': campaigns, 'total': len(campaigns)})


# =========================================================
# API ADMIN — TAMBAH CAMPAIGN
# =========================================================
@app.route('/api/admin/campaign', methods=['POST'])
def api_admin_tambah():
    """Tambah campaign baru."""
    from backend.db.campaign_db import tambah_campaign

    try:
        data = request.get_json()
        wajib = ['nama', 'lat_toko', 'lon_toko', 'radius_km', 'konten']
        for field in wajib:
            if field not in data or data[field] == '':
                return jsonify({
                    'status': 'error',
                    'pesan': f'Field {field} wajib diisi.'
                }), 400

        new_id = tambah_campaign(
            nama=data['nama'],
            lat=float(data['lat_toko']),
            lon=float(data['lon_toko']),
            radius_km=float(data['radius_km']),
            konten=data['konten'],
            wa_link=data.get('wa_link', '')
        )

        return jsonify({
            'status': 'ok',
            'id': new_id,
            'pesan': f'Campaign #{new_id} berhasil dibuat.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'pesan': f'Gagal: {str(e)}'
        }), 500


# =========================================================
# API ADMIN — HAPUS CAMPAIGN
# =========================================================
@app.route('/api/admin/campaign/<int:id_campaign>', methods=['DELETE'])
def api_admin_hapus(id_campaign):
    """Hapus campaign berdasarkan ID."""
    from backend.db.campaign_db import hapus_campaign

    try:
        hapus_campaign(id_campaign)
        return jsonify({
            'status': 'ok',
            'pesan': f'Campaign #{id_campaign} dihapus.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'pesan': f'Gagal hapus: {str(e)}'
        }), 500


# =========================================================
# ROUTE ADMIN — HALAMAN LIHAT LEADS
# =========================================================
@app.route('/admin/leads')
def admin_leads():
    """Halaman admin untuk lihat leads."""
    return render_template('admin_leads.html')


# =========================================================
# API ADMIN — LIST LEADS
# =========================================================
@app.route('/api/admin/leads')
def api_admin_leads():
    """Return semua leads."""
    from backend.db.leads_db import ambil_leads, statistik_leads
    leads = ambil_leads()
    stat = statistik_leads()
    return jsonify({
        'leads': leads,
        'statistik': stat
    })


# =========================================================
# API ADMIN — UPDATE STATUS LEAD
# =========================================================
@app.route('/api/admin/leads/<int:id_lead>/status', methods=['POST'])
def api_update_lead_status(id_lead):
    """Update status lead."""
    from backend.db.leads_db import update_status_lead

    try:
        data = request.get_json()
        status_baru = data.get('status', '').strip()

        if status_baru not in ['baru', 'followup', 'closing', 'batal']:
            return jsonify({'status': 'error', 'pesan': 'Status tidak valid'}), 400

        update_status_lead(id_lead, status_baru)
        return jsonify({'status': 'ok', 'pesan': f'Status diubah ke {status_baru}'})

    except Exception as e:
        return jsonify({'status': 'error', 'pesan': str(e)}), 500


# =========================================================
# ROUTE HEALTH CHECK
# =========================================================
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'Market Intel Geo-Fence'})


# =========================================================
# MAIN
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MARKET INTEL GEO-FENCE SERVER")
    print("=" * 60)
    print("📡 Buka di browser: http://localhost:5000")
    print("🛑 Tekan Ctrl+C untuk stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)