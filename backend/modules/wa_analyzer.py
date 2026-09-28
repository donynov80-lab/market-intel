"""
wa_analyzer.py
Analisis nomor WhatsApp:
- Deteksi operator (berdasarkan prefix)
- Validasi format nomor Indonesia
- Deteksi duplikat
- Statistik & segmentasi
"""
import re
from collections import Counter


# =========================================================
# DATABASE PREFIX OPERATOR INDONESIA
# =========================================================
OPERATOR_PREFIX = {
    # Telkomsel
    "0811": "Telkomsel", "0812": "Telkomsel", "0813": "Telkomsel",
    "0821": "Telkomsel", "0822": "Telkomsel", "0823": "Telkomsel",
    "0851": "Telkomsel", "0852": "Telkomsel", "0853": "Telkomsel",

    # Indosat (IM3 / Mentari)
    "0814": "Indosat", "0815": "Indosat", "0816": "Indosat",
    "0855": "Indosat", "0856": "Indosat", "0857": "Indosat",
    "0858": "Indosat",

    # XL Axiata
    "0817": "XL", "0818": "XL", "0819": "XL",
    "0859": "XL", "0877": "XL", "0878": "XL",

    # Axis (bagian XL)
    "0831": "Axis", "0832": "Axis", "0833": "Axis", "0838": "Axis",

    # Tri (3)
    "0895": "Tri", "0896": "Tri", "0897": "Tri",
    "0898": "Tri", "0899": "Tri",

    # Smartfren
    "0881": "Smartfren", "0882": "Smartfren", "0883": "Smartfren",
    "0884": "Smartfren", "0885": "Smartfren", "0886": "Smartfren",
    "0887": "Smartfren", "0888": "Smartfren", "0889": "Smartfren",
}


# =========================================================
# FUNGSI 1 — NORMALISASI NOMOR
# =========================================================
def normalisasi_nomor(nomor):
    """
    Bersihkan nomor dari spasi, strip, plus, dan ubah ke format 62xxx.
    
    Contoh:
        "0812-3456-7890"  → "6281234567890"
        "+62 812 3456 7890" → "6281234567890"
        "62812 3456 7890"  → "6281234567890"
    """
    if not nomor:
        return ""

    # Hapus semua karakter non-digit
    bersih = re.sub(r'\D', '', str(nomor))

    # Konversi ke format 62xxx
    if bersih.startswith('62'):
        return bersih
    elif bersih.startswith('0'):
        return '62' + bersih[1:]
    elif bersih.startswith('8'):
        return '62' + bersih
    else:
        return bersih  # Format tidak dikenal


# =========================================================
# FUNGSI 2 — DETEKSI OPERATOR
# =========================================================
def deteksi_operator(nomor):
    """
    Deteksi operator dari nomor HP Indonesia.
    Return: nama operator atau "Unknown"
    """
    bersih = normalisasi_nomor(nomor)

    # Konversi ke format 08xx
    if bersih.startswith('62'):
        lokal = '0' + bersih[2:]
    else:
        lokal = bersih

    # Ambil 4 digit pertama (08xx)
    if len(lokal) >= 4:
        prefix = lokal[:4]
        return OPERATOR_PREFIX.get(prefix, "Unknown")

    return "Invalid"


# =========================================================
# FUNGSI 3 — VALIDASI NOMOR
# =========================================================
def validasi_nomor(nomor):
    """
    Validasi format nomor HP Indonesia.
    Return: (valid: bool, pesan: str)
    """
    if not nomor or str(nomor).strip() == "":
        return False, "Nomor kosong"

    bersih = normalisasi_nomor(nomor)

    # Cek panjang (Indonesia: 10-15 digit setelah 62)
    if len(bersih) < 10:
        return False, f"Terlalu pendek ({len(bersih)} digit)"
    if len(bersih) > 15:
        return False, f"Terlalu panjang ({len(bersih)} digit)"

    # Cek harus mulai dengan 62
    if not bersih.startswith('62'):
        return False, "Format bukan Indonesia"

    # Cek digit setelah 62 harus 8
    if len(bersih) >= 3 and bersih[2] != '8':
        return False, "Bukan nomor HP (bukan 8xxx)"

    # Cek prefix operator
    operator = deteksi_operator(nomor)
    if operator == "Unknown":
        return False, "Prefix operator tidak dikenal"

    return True, f"OK ({operator})"


# =========================================================
# FUNGSI 4 — ANALISIS BANYAK NOMOR
# =========================================================
def analisis_daftar_nomor(daftar_nomor):
    """
    Analisis list nomor. Return dict lengkap.
    
    Args:
        daftar_nomor (list): list of str nomor
    
    Returns:
        dict: {
            'total': int,
            'valid': int,
            'invalid': int,
            'duplikat': int,
            'per_operator': {operator: count},
            'detail': [{nomor_asli, nomor_bersih, valid, pesan, operator, duplikat}, ...]
        }
    """
    hasil = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'duplikat': 0,
        'per_operator': {},
        'detail': []
    }

    seen = set()
    operator_counter = Counter()

    for nomor_mentah in daftar_nomor:
        nomor_str = str(nomor_mentah).strip()
        if not nomor_str:
            continue

        hasil['total'] += 1

        bersih = normalisasi_nomor(nomor_str)
        valid, pesan = validasi_nomor(nomor_str)
        operator = deteksi_operator(nomor_str) if valid else "-"

        # Cek duplikat
        is_duplikat = bersih in seen
        if is_duplikat:
            hasil['duplikat'] += 1
        else:
            seen.add(bersih)

        # Statistik
        if valid and not is_duplikat:
            hasil['valid'] += 1
            operator_counter[operator] += 1
        elif not valid:
            hasil['invalid'] += 1

        hasil['detail'].append({
            'nomor_asli': nomor_str,
            'nomor_bersih': bersih,
            'valid': valid,
            'pesan': pesan,
            'operator': operator,
            'duplikat': is_duplikat,
        })

    hasil['per_operator'] = dict(operator_counter)
    return hasil


# =========================================================
# FUNGSI 5 — GENERATE LAPORAN TEKS
# =========================================================
def buat_laporan_teks(hasil):
    """Buat laporan format teks (untuk print/tampil)."""
    lines = []
    lines.append("=" * 55)
    lines.append("📱 LAPORAN ANALISIS NOMOR WA")
    lines.append("=" * 55)
    lines.append(f"Total input    : {hasil['total']}")
    lines.append(f"Valid          : {hasil['valid']}")
    lines.append(f"Invalid        : {hasil['invalid']}")
    lines.append(f"Duplikat       : {hasil['duplikat']}")
    lines.append("")

    if hasil['per_operator']:
        lines.append("📊 Distribusi Operator:")
        total_valid = sum(hasil['per_operator'].values())
        for op, count in sorted(hasil['per_operator'].items(),
                                 key=lambda x: -x[1]):
            persen = (count / total_valid * 100) if total_valid > 0 else 0
            lines.append(f"   {op:12} : {count:4} ({persen:.1f}%)")

    lines.append("")
    return "\n".join(lines)


# =========================================================
# MAIN — TEST
# =========================================================
if __name__ == "__main__":
    print("=" * 55)
    print("📱 TEST WA ANALYZER")
    print("=" * 55)

    # Test data
    sample = [
        "6282114188277",       # Telkomsel (dari lead kamu)
        "08123456789",         # Telkomsel
        "0812-3456-7890",      # Telkomsel (dengan strip)
        "+62 813 1234 5678",   # Telkomsel (dengan + dan spasi)
        "6281234567890",       # Duplikat
        "08987654321",         # Tri
        "08175555555",         # XL
        "1234",                # Invalid (pendek)
        "abc",                 # Invalid (bukan angka)
        "085612345678",        # Indosat
    ]

    hasil = analisis_daftar_nomor(sample)
    print(buat_laporan_teks(hasil))

    print("\n📋 Detail per nomor:")
    print("-" * 55)
    for d in hasil['detail']:
        status = "✅" if d['valid'] else "❌"
        dup = " (DUPLIKAT)" if d['duplikat'] else ""
        print(f"{status} {d['nomor_asli']:25} → {d['pesan']}{dup}")