# backend/modules/business_classifier.py
"""
Business Classifier - SMART FILTER dengan integrasi KBLI lengkap.
Filter bisnis sampai level subgolongan (4 digit) dan kelompok (5 digit).

Analoginya seperti "kamus pintar":
- Kamus manual (KAMUS_BISNIS)  = kata kunci cepat yang kita tulis sendiri
- KBLI pemerintah              = kamus resmi lengkap berjenjang
Digabung => filter yang paham konteks DAN punya rujukan resmi.
"""

import os
import json
import re
from typing import Optional, Dict, List, Any
from difflib import SequenceMatcher

# =========================================================
# 1. LOKASI FILE KBLI
# =========================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KBLI_DIR = os.path.join(BASE_DIR, "db_eksternal")

KBLI_FILES = {
    "golpok":   "kbli_golpok.json",     # 2 digit
    "gol":      "kbli_gol.json",        # 3 digit
    "subgol":   "kbli_subgol.json",     # 4 digit
    "kelompok": "kbli_kelompok.json",   # 5 digit
    "lengkap":  "kbli_lengkap.json",    # semua level (backup)
}

# =========================================================
# 2. SINGLETON INDEX KBLI
# =========================================================
class KBLIIndex:
    """Index KBLI - load sekali, pakai terus (biar cepat)."""
    _instance = None
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self.by_code: Dict[str, dict] = {}
        self.by_level: Dict[int, List[str]] = {2: [], 3: [], 4: [], 5: []}
        self.by_title: Dict[str, str] = {}
        self.loaded_files: List[str] = []
        self._load_all()
        KBLIIndex._loaded = True

    def _load_all(self):
        for key, fname in KBLI_FILES.items():
            path = os.path.join(KBLI_DIR, fname)
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._ingest(data, source=fname)
                self.loaded_files.append(fname)
            except Exception as e:
                print(f"[KBLIIndex] Gagal load {fname}: {e}")

    def _ingest(self, data, source=""):
        if not isinstance(data, list):
            return
        for item in data:
            code = str(item.get("code", "")).strip()
            title = str(item.get("title", "")).strip()
            if not code or not title:
                continue
            level = len(code)
            if level not in (2, 3, 4, 5):
                continue
            if code in self.by_code:
                existing = self.by_code[code]
                if not existing.get("title"):
                    existing["title"] = title
                continue
            self.by_code[code] = {
                "code": code,
                "title": title,
                "desc": item.get("desc", ""),
                "level": level,
                "source": source,
            }
            self.by_level[level].append(code)
            norm = self._normalize(title)
            if norm and norm not in self.by_title:
                self.by_title[norm] = code

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ---------------- Public API ----------------
    def get(self, code: str) -> Optional[dict]:
        return self.by_code.get(code)

    def get_hierarchy(self, code: str) -> Dict[str, Optional[dict]]:
        """Ambil semua level induk dari suatu code.
        Misal 01111 -> golpok=01, gol=011, subgol=0111, kelompok=01111.
        """
        code = str(code)
        return {
            "golpok":   self.by_code.get(code[:2]),
            "gol":      self.by_code.get(code[:3]),
            "subgol":   self.by_code.get(code[:4]),
            "kelompok": self.by_code.get(code[:5]),
            "full_code": code,
        }

    def search_title(self, query: str, limit: int = 10, min_score: float = 0.4) -> List[dict]:
        q = self._normalize(query)
        if not q:
            return []
        results = []
        for norm_title, code in self.by_title.items():
            score = SequenceMatcher(None, q, norm_title).ratio()
            if q in norm_title:
                score = max(score, 0.75)
            if score >= min_score:
                entry = self.by_code.get(code, {}).copy()
                entry["score"] = round(score, 3)
                results.append(entry)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def stats(self) -> dict:
        return {
            "total": len(self.by_code),
            "golpok": len(self.by_level[2]),
            "gol": len(self.by_level[3]),
            "subgol": len(self.by_level[4]),
            "kelompok": len(self.by_level[5]),
            "files": self.loaded_files,
        }


# =========================================================
# 3. KAMUS BISNIS MANUAL (keyword -> KBLI code)
# =========================================================
KAMUS_BISNIS: Dict[str, str] = {
    # Makanan & Minuman
    "kue": "1071", "bakery": "1071", "roti": "1071",
    "warung": "4711", "toko kelontong": "4711", "minimarket": "4711",
    "restoran": "5610", "rumah makan": "5610",
    "kafe": "5630", "cafe": "5630", "kedai kopi": "5630", "coffee shop": "5630",
    "catering": "5621", "katering": "5621",
    "bakso": "5610", "mie": "1074", "nasi goreng": "5610", "sate": "5610",
    "kopi": "1076", "teh": "1076", "pizza": "1075", "burger": "5610",
    "ayam goreng": "5610", "seafood": "5610", "es krim": "1053",

    # Minuman beralkohol (contoh penting)
    "miras": "4722", "minuman keras": "4722", "alkohol": "4722",
    "bar": "5630", "pub": "5630", "wine": "4722", "bir": "4722",

    # Retail
    "toko": "4711", "toko buah": "4721", "toko sayur": "4721",
    "toko baju": "4771", "butik": "4771", "toko sepatu": "4771",
    "apotek": "4772", "apotik": "4772", "toko obat": "4772", "farmasi": "4772",
    "toko kosmetik": "4772",
    "salon": "9611", "barbershop": "9611", "pangkas rambut": "9611",
    "spa": "9612", "toko emas": "4773", "toko perhiasan": "4773",
    "toko hp": "4741", "toko handphone": "4741", "toko komputer": "4741",
    "toko bangunan": "4752", "toko material": "4752", "toko cat": "4752",
    "toko mebel": "4759", "toko furniture": "4759",
    "bengkel": "4520", "bengkel mobil": "4520", "bengkel motor": "4540",
    "cuci mobil": "4520", "car wash": "4520", "tambal ban": "4520",
    "laundry": "9620", "penatu": "9620",
    "fotokopi": "8219", "percetakan": "1811", "digital printing": "1811",

    # Jasa
    "hotel": "5511", "penginapan": "5511", "guest house": "5519",
    "homestay": "5513", "villa": "5519", "hostel": "5519",
    "travel": "7911", "agen travel": "7911", "biro perjalanan": "7912", "tour": "7912",
    "ojek": "4942", "taksi": "4942", "kurir": "5320", "ekspedisi": "5320",
    "logistik": "5229", "gudang": "5210",
    "klinik": "8610", "puskesmas": "8610", "rumah sakit": "8610",
    "dokter": "8620", "dokter gigi": "8620", "bidan": "8690", "laboratorium": "8690",
    "sekolah": "8510", "kursus": "8549", "bimbel": "8549", "les": "8549",
    "paud": "8513", "taman kanak": "8513",
    "universitas": "8531", "kampus": "8531",
    "notaris": "6910", "pengacara": "6910", "konsultan": "7020",
    "akuntan": "6920", "pajak": "6920", "arsitek": "7110",
    "kontraktor": "4101", "developer": "4101",
    "gym": "9311", "fitness": "9311", "kolam renang": "9311", "stadion": "9311",
    "bioskop": "5914", "karaoke": "9329", "klub malam": "9329",
    "panti pijat": "9612", "pijat": "9612",
    "toko bunga": "4776", "florist": "4776",
    "pet shop": "4775", "petshop": "4775", "toko hewan": "4775",
    "pasar": "4711",

    # Industri & Produksi
    "pertanian": "0111", "peternakan": "0141", "perikanan": "0311",
    "perkebunan": "0121", "tambang": "0510", "konstruksi": "4101",
    "manufaktur": "1011",

    # Otomotif
    "dealer mobil": "4510", "showroom": "4510", "jual mobil": "4510",
    "jual motor": "4540", "sparepart": "4530", "suku cadang": "4530",

    # Properti
    "properti": "6811", "real estate": "6811", "kontrakan": "6811", "sewa rumah": "6811",

    # Teknologi
    "software house": "6201", "startup": "6201",
    "it consultant": "6202", "web developer": "6201",
    "digital agency": "7310", "marketing agency": "7310", "iklan": "7310",
}


# =========================================================
# 4. KAMUS OSM TAG -> KBLI (untuk data peta/Overpass)
# =========================================================
KAMUS_OSM: Dict[str, str] = {
    # shop=*
    "shop=bakery": "1071", "shop=butcher": "4721", "shop=seafood": "4721",
    "shop=greengrocer": "4721", "shop=convenience": "4711",
    "shop=supermarket": "4711", "shop=department_store": "4719",
    "shop=clothes": "4771", "shop=shoes": "4771", "shop=bags": "4771",
    "shop=jewelry": "4773", "shop=pharmacy": "4772", "shop=chemist": "4772",
    "shop=cosmetics": "4772", "shop=hairdresser": "9611", "shop=beauty": "9611",
    "shop=car": "4510", "shop=car_repair": "4520", "shop=car_parts": "4530",
    "shop=motorcycle": "4540", "shop=motorcycle_repair": "4540",
    "shop=hardware": "4752", "shop=doityourself": "4752", "shop=paint": "4752",
    "shop=furniture": "4759", "shop=electronics": "4741",
    "shop=computer": "4741", "shop=mobile_phone": "4741",
    "shop=florist": "4776", "shop=pet": "4775",
    "shop=alcohol": "4722", "shop=wine": "4722", "shop=beverages": "4722",
    "shop=tobacco": "4723",
    "shop=books": "4761", "shop=stationery": "4761",
    "shop=toys": "4764", "shop=sports": "4763",
    "shop=laundry": "9620", "shop=travel_agency": "7911",
    "shop=optician": "4773", "shop=watchmaker": "4773", "shop=photo": "7420",
    "shop=tailor": "1412", "shop=massage": "9612",
    "shop=mall": "4719", "shop=variety_store": "4719", "shop=wholesale": "4690",

    # amenity=*
    "amenity=restaurant": "5610", "amenity=fast_food": "5610",
    "amenity=cafe": "5630", "amenity=bar": "5630", "amenity=pub": "5630",
    "amenity=nightclub": "9329", "amenity=biergarten": "5630",
    "amenity=bank": "6412", "amenity=atm": "6412",
    "amenity=pharmacy": "4772", "amenity=hospital": "8610", "amenity=clinic": "8610",
    "amenity=doctors": "8620", "amenity=dentist": "8620", "amenity=veterinary": "7500",
    "amenity=school": "8510", "amenity=kindergarten": "8513",
    "amenity=college": "8531", "amenity=university": "8531",
    "amenity=cinema": "5914", "amenity=theatre": "9001",
    "amenity=marketplace": "4711",
    "amenity=police": "8423", "amenity=fire_station": "8423",
    "amenity=post_office": "5310", "amenity=place_of_worship": "9491",
    "amenity=fuel": "4730", "amenity=car_wash": "4520", "amenity=car_rental": "7710",
    "amenity=driving_school": "8549", "amenity=internet_cafe": "6199",
    "amenity=brothel": "9329",

    # office=*
    "office=lawyer": "6910", "office=accountant": "6920",
    "office=estate_agent": "6820", "office=insurance": "6512",
    "office=it": "6202", "office=consulting": "7020", "office=architect": "7110",
    "office=travel_agent": "7911", "office=advertising_agency": "7310",
    "office=company": "7010", "office=government": "8411",

    # tourism=*
    "tourism=hotel": "5511", "tourism=motel": "5519", "tourism=hostel": "5519",
    "tourism=guest_house": "5519", "tourism=bed_and_breakfast": "5519",
    "tourism=camp_site": "5519", "tourism=chalet": "5519", "tourism=apartment": "5519",
    "tourism=museum": "9102", "tourism=attraction": "9321",
    "tourism=zoo": "9103", "tourism=theme_park": "9321",

    # leisure=*
    "leisure=fitness_centre": "9311", "leisure=sports_centre": "9311",
    "leisure=stadium": "9311", "leisure=swimming_pool": "9311",
    "leisure=golf_course": "9311", "leisure=park": "8130",
    "leisure=playground": "9329", "leisure=dance": "9329",
    "leisure=bowling_alley": "9311",

    # craft=*
    "craft=carpenter": "1629", "craft=tailor": "1412", "craft=brewery": "1103",
    "craft=bakery": "1071", "craft=photographer": "7420", "craft=plumber": "4322",
    "craft=electrician": "4321", "craft=painter": "4330", "craft=shoemaker": "1520",
    "craft=blacksmith": "2593", "craft=joiner": "1622", "craft=jeweller": "3212",
    "craft=stonemason": "2396", "craft=car_repair": "4520",
    "craft=distillery": "1101", "craft=window_construction": "4330",
}


# =========================================================
# 5. KELAS UTAMA BUSINESS CLASSIFIER
# =========================================================
class BusinessClassifier:
    """
    Filter cerdas untuk klasifikasi bisnis.
    Analogi: resepsionis hotel yang:
    - punya buku catatan cepat (KAMUS_BISNIS) untuk tamu umum
    - punya buku besar resmi (KBLI) untuk kasus detail
    - kalau ditanya soal tidak jelas, cek dua-duanya
    """

    def __init__(self, prefer_level: int = 4):
        """
        prefer_level: level KBLI yang diutamakan saat mengembalikan hasil.
                      2=golpok, 3=gol, 4=subgol, 5=kelompok. Default 4.
        """
        self.kbli = KBLIIndex()
        self.prefer_level = prefer_level
        self.kamus = KAMUS_BISNIS
        self.kamus_osm = KAMUS_OSM

    # ----------------- Utility -----------------
    @staticmethod
    def _norm(text: str) -> str:
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r"[^a-z0-9\s=]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _match_kamus(self, text: str) -> Optional[dict]:
        t = self._norm(text)
        if not t:
            return None
        best_kw = None
        for kw in self.kamus.keys():
            kw_n = self._norm(kw)
            if kw_n and kw_n in t:
                if best_kw is None or len(kw_n) > len(self._norm(best_kw)):
                    best_kw = kw
        if not best_kw:
            return None
        return {
            "matched_keyword": best_kw,
            "code": self.kamus[best_kw],
            "source": "KAMUS_BISNIS",
            "confidence": 0.9,
        }

    def _match_osm(self, tags: List[str]) -> Optional[dict]:
        if not tags:
            return None
        for tag in tags:
            tag_n = self._norm(tag).replace(" ", "_")
            for osm_key, code in self.kamus_osm.items():
                if self._norm(osm_key).replace(" ", "_") == tag_n:
                    return {
                        "matched_keyword": osm_key,
                        "code": code,
                        "source": "KAMUS_OSM",
                        "confidence": 0.95,
                    }
        for tag in tags:
            for osm_key, code in self.kamus_osm.items():
                if osm_key.split("=")[-1] in tag.lower():
                    return {
                        "matched_keyword": osm_key,
                        "code": code,
                        "source": "KAMUS_OSM",
                        "confidence": 0.7,
                    }
        return None

    def _match_title(self, text: str, min_score: float = 0.45) -> Optional[dict]:
        results = self.kbli.search_title(text, limit=1, min_score=min_score)
        if results:
            r = results[0]
            return {
                "matched_keyword": r.get("title", ""),
                "code": r.get("code", ""),
                "source": "KBLI_TITLE",
                "confidence": r.get("score", 0.5),
            }
        return None

    def _resolve_code(self, code: str) -> dict:
        if not code:
            return {}
        hierarchy = self.kbli.get_hierarchy(code)
        prefer = str(code)[: self.prefer_level]
        chosen = self.kbli.get(prefer) or self.kbli.get(code) or {}
        return {
            "code": code,
            "code_preferred": prefer,
            "preferred_level": self.prefer_level,
            "preferred_entry": chosen,
            "hierarchy": {
                "golpok":   hierarchy.get("golpok"),
                "gol":      hierarchy.get("gol"),
                "subgol":   hierarchy.get("subgol"),
                "kelompok": hierarchy.get("kelompok"),
            },
        }

    @staticmethod
    def _fmt(entry) -> Optional[dict]:
        if not entry:
            return None
        return {
            "code": entry.get("code"),
            "title": entry.get("title"),
            "level": entry.get("level"),
        }

    def _find_title(self, code: str) -> Optional[str]:
        for length in (5, 4, 3, 2):
            c = str(code)[:length]
            entry = self.kbli.get(c)
            if entry:
                return entry.get("title")
        return None

    # ----------------- Public API -----------------
    def classify(self, name: str = "", tags: Optional[List[str]] = None,
                 category: str = "") -> dict:
        """
        Klasifikasi satu bisnis.
        Return dict dengan code, code_4digit, code_5digit, title, confidence,
        source, hierarchy.
        """
        osm_match = self._match_osm(tags or [])
        text_blob = " ".join([name, category, " ".join(tags or [])])
        kamus_match = self._match_kamus(text_blob)
        title_match = self._match_title(text_blob)

        candidates = [m for m in (osm_match, kamus_match, title_match) if m]
        if not candidates:
            return {
                "code": None, "code_4digit": None, "code_5digit": None,
                "title": None, "confidence": 0.0, "source": "NONE",
                "hierarchy": {},
                "note": "Tidak ada kecocokan - tambahkan keyword ke KAMUS_BISNIS",
            }

        best = max(candidates, key=lambda x: x["confidence"])
        resolved = self._resolve_code(best["code"])
        pref = resolved.get("preferred_entry") or {}
        full_code = best["code"]
        code_4 = str(full_code)[:4] if len(str(full_code)) >= 4 else None
        code_5 = str(full_code)[:5] if len(str(full_code)) >= 5 else None

        return {
            "code": full_code,
            "code_2digit": str(full_code)[:2],
            "code_3digit": str(full_code)[:3],
            "code_4digit": code_4,
            "code_5digit": code_5,
            "title": pref.get("title") or self._find_title(full_code),
            "confidence": round(best["confidence"], 3),
            "source": best["source"],
            "matched_keyword": best.get("matched_keyword"),
            "hierarchy": {
                "golpok":   self._fmt(resolved["hierarchy"].get("golpok")),
                "gol":      self._fmt(resolved["hierarchy"].get("gol")),
                "subgol":   self._fmt(resolved["hierarchy"].get("subgol")),
                "kelompok": self._fmt(resolved["hierarchy"].get("kelompok")),
            },
        }

    def classify_batch(self, items: List[dict]) -> List[dict]:
        return [self.classify(**it) for it in items]

    def filter_by_subgolongan(self, items: List[dict],
                              subgol_codes: List[str]) -> List[dict]:
        """
        Filter hasil klasifikasi yang subgolongannya (4 digit) ada di list.
        Berguna untuk memfilter "hanya tampilkan toko miras (4722)".
        """
        wanted = {str(s).strip()[:4] for s in subgol_codes}
        out = []
        for it in items:
            cls = self.classify(**it) if "code" not in it else it
            if cls.get("code_4digit") in wanted:
                out.append(cls)
        return out

    def stats(self) -> dict:
        s = self.kbli.stats()
        s["kamus_bisnis"] = len(self.kamus)
        s["kamus_osm"] = len(self.kamus_osm)
        return s


# =========================================================
# 6. SINGLETON INSTANCE
# =========================================================
_classifier_instance: Optional[BusinessClassifier] = None


def get_classifier(prefer_level: int = 4) -> BusinessClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = BusinessClassifier(prefer_level=prefer_level)
    return _classifier_instance


def classify(name: str = "", tags=None, category: str = "") -> dict:
    return get_classifier().classify(name=name, tags=tags or [], category=category)


def filter_miras(items):
    """Shortcut: filter hanya toko miras (subgolongan 4722)."""
    return get_classifier().filter_by_subgolongan(items, ["4722"])


# =========================================================
# 7. SELF-TEST
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("BUSINESS CLASSIFIER - SELF TEST")
    print("=" * 60)

    c = get_classifier(prefer_level=4)
    print("\n[Stats KBLI]")
    for k, v in c.stats().items():
        print(f"  {k}: {v}")

    print("\n[Test 1: Outlet 23 dengan tag shop=alcohol]")
    print(json.dumps(c.classify(name="Outlet 23", tags=["shop=alcohol"]),
                     indent=2, ensure_ascii=False))

    print("\n[Test 2: Toko Kue Sederhana]")
    print(json.dumps(c.classify(name="Toko Kue Sederhana"),
                     indent=2, ensure_ascii=False))

    print("\n[Test 3: Bengkel Motor Jaya]")
    print(json.dumps(c.classify(name="Bengkel Motor Jaya",
                                tags=["shop=motorcycle_repair"]),
                     indent=2, ensure_ascii=False))

    print("\n[Test 4: Filter miras dari batch]")
    items = [
        {"name": "Outlet 23", "tags": ["shop=alcohol"]},
        {"name": "Toko Kue Sederhana", "tags": []},
        {"name": "Warung Bu Ani", "tags": ["shop=convenience"]},
        {"name": "Toko Minuman Keras", "tags": ["shop=wine"]},
    ]
    hasil = c.filter_by_subgolongan(items, ["4722"])
    print(f"  Ditemukan {len(hasil)} dari {len(items)} yang subgolongan 4722")
    for h in hasil:
        print(f"   - {h.get('title')} ({h.get('code_4digit')})")