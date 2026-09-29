# backend/modules/opportunity_analyzer.py
"""
Analisis Peluang - bandingkan jumlah kompetitor per subgolongan KBLI
terhadap jumlah penduduk kota.

Analoginya: kalau di kota 500.000 penduduk cuma ada 2 toko kue
(density 0.04 per 10rb), itu peluang. Kalau ada 500 (density 10),
itu sudah perang.
"""

from typing import List, Dict, Optional
from backend.modules.business_classifier import get_classifier


# Benchmark kasar "kepadatan wajar" per 10rb penduduk.
# Angka ini untuk tuning — bisa diubah sesuai pengalaman.
BENCHMARK_PER_10K = {
    "default": 5.0,
}


class OpportunityAnalyzer:
    def __init__(self, prefer_level: int = 4):
        self.classifier = get_classifier(prefer_level=prefer_level)

    # ------------------------------------------------------------------
    def group_by_subgolongan(self, businesses: List[dict]) -> Dict[str, Dict]:
        groups: Dict[str, Dict] = {}
        for b in businesses:
            code4 = b.get("code_4digit")
            if not code4:
                continue
            if code4 not in groups:
                groups[code4] = {
                    "code_4digit": code4,
                    "title": b.get("subgolongan_title") or b.get("kbli_title") or "-",
                    "count": 0,
                    "items": [],
                }
            groups[code4]["count"] += 1
            groups[code4]["items"].append(b)
        return groups

    # ------------------------------------------------------------------
    def analyze(self, businesses: List[dict], population: int,
                city_name: str = "", area_km2: Optional[float] = None) -> Dict:
        """
        Return dict:
        {
          "city": str,
          "population": int,
          "area_km2": float|None,
          "total_businesses": int,
          "results": [ {subgolongan, count, density, score, verdict}, ... ]
        }
        """
        if population <= 0:
            return {
                "city": city_name, "population": population,
                "area_km2": area_km2, "total_businesses": 0,
                "results": [], "error": "Populasi tidak valid",
            }

        groups = self.group_by_subgolongan(businesses)
        results = []
        for code4, g in groups.items():
            density_10k = (g["count"] / population) * 10000
            benchmark = BENCHMARK_PER_10K.get(code4, BENCHMARK_PER_10K["default"])
            ratio = density_10k / benchmark if benchmark else 0

            score = self._score(ratio)
            verdict = self._verdict(ratio)

            entry = {
                "code_4digit": code4,
                "title": g["title"],
                "count": g["count"],
                "density_per_10k": round(density_10k, 3),
                "benchmark": benchmark,
                "ratio_vs_benchmark": round(ratio, 3),
                "score": score,
                "verdict": verdict,
                "sample_names": [x.get("name") for x in g["items"][:5]],
            }

            # Kalau luas kota tersedia -> density geografis
            if area_km2 and area_km2 > 0:
                entry["density_per_km2"] = round(g["count"] / area_km2, 3)

            results.append(entry)

        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "city": city_name,
            "population": population,
            "area_km2": area_km2,
            "total_businesses": len(businesses),
            "results": results,
            "error": None,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _score(ratio: float) -> int:
        """Skor 0-100. Semakin rendah ratio (kompetitor < benchmark) → skor tinggi."""
        if ratio == 0:      return 100
        if ratio < 0.2:     return 95
        if ratio < 0.5:     return 85
        if ratio < 0.8:     return 70
        if ratio < 1.2:     return 55
        if ratio < 2.0:     return 40
        if ratio < 4.0:     return 25
        return 10

    @staticmethod
    def _verdict(ratio: float) -> str:
        if ratio == 0:      return "🟢 Peluang Emas — belum ada kompetitor"
        if ratio < 0.5:     return "🟢 Peluang Tinggi — kompetitor sangat sedikit"
        if ratio < 1.0:     return "🟡 Peluang Sedang — masih di bawah benchmark"
        if ratio < 2.0:     return "🟠 Kompetitif — di atas benchmark nasional"
        if ratio < 4.0:     return "🔴 Sangat Kompetitif"
        return "⚫ Jenuh — hindari masuk tanpa diferensiasi kuat"

    # ------------------------------------------------------------------
    def to_dataframe(self, analysis: Dict):
        """Convert ke pandas DataFrame (opsional)."""
        try:
            import pandas as pd
        except ImportError:
            return None
        rows = []
        for r in analysis.get("results", []):
            rows.append({
                "Kode (4 digit)": r["code_4digit"],
                "Subgolongan": r["title"],
                "Jumlah Kompetitor": r["count"],
                "Density /10rb": r["density_per_10k"],
                "Rasio vs Benchmark": r["ratio_vs_benchmark"],
                "Skor": r["score"],
                "Verdict": r["verdict"],
            })
        return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Quick test
if __name__ == "__main__":
    dummy = [
        {"name": "Outlet 23", "code_4digit": "4722", "subgolongan_title": "Perdagangan Eceran Minuman"},
        {"name": "Toko Wine A", "code_4digit": "4722", "subgolongan_title": "Perdagangan Eceran Minuman"},
        {"name": "Toko Kue Sederhana", "code_4digit": "1071", "subgolongan_title": "Industri Produk Roti dan Kue"},
        {"name": "Bakery B", "code_4digit": "1071", "subgolongan_title": "Industri Produk Roti dan Kue"},
        {"name": "Bengkel X", "code_4digit": "4520", "subgolongan_title": "Reparasi Mobil"},
    ]
    analyzer = OpportunityAnalyzer()
    hasil = analyzer.analyze(dummy, population=500_000, city_name="Contoh")
    for r in hasil["results"]:
        print(f"{r['code_4digit']}  {r['title'][:40]:40}  "
              f"n={r['count']}  dens={r['density_per_10k']:.3f}  "
              f"skor={r['score']}  {r['verdict']}")