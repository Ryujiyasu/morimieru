#!/usr/bin/env python3
"""
Time-series difference analysis: detect 施業効果 from Sentinel-2 NDVI over 5 years.

For Himi AOI (already in himi_timeseries.json, 71 observation points 2021-2026):
- Aggregate NDVI by year (seasonal-adjusted: use peak vegetation = summer)
- Compute year-over-year change
- Convert ΔNDVI → Δbiomass → Δwater yield + Δ CO2
- Output JSON for the frontend chart

This is the killer feature: replaces $1000s/year MRV with $0 satellite-based monitoring.
"""
import json
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).parent.parent
TS_PATH = ROOT / "data" / "sentinel" / "himi_timeseries.json"
WATER_PATH = ROOT / "data" / "sentinel" / "himi_water.json"
CO2_PATH = ROOT / "data" / "sentinel" / "himi_co2.json"
OUT_PATH = ROOT / "data" / "sentinel" / "himi_timeseries_diff.json"


def main():
    ts = json.loads(TS_PATH.read_text())
    water = json.loads(WATER_PATH.read_text())
    co2 = json.loads(CO2_PATH.read_text())

    points = ts["points"]
    print(f"Loaded {len(points)} NDVI observations")

    # Group by year, use summer mean (Jun-Sep) as the year's representative NDVI
    by_year = defaultdict(list)
    for p in points:
        dt = datetime.fromisoformat(p["date"])
        if 6 <= dt.month <= 9:  # peak vegetation
            by_year[dt.year].append(p["mean"])

    yearly = {}
    for year, vals in sorted(by_year.items()):
        if vals:
            yearly[year] = {
                "mean_ndvi_summer": round(sum(vals) / len(vals), 4),
                "count_obs": len(vals),
            }

    print("\nYearly summer NDVI averages:")
    for year, info in sorted(yearly.items()):
        print(f"  {year}: NDVI={info['mean_ndvi_summer']} (n={info['count_obs']})")

    # Year-over-year change
    years = sorted(yearly.keys())
    diffs = []
    for i in range(1, len(years)):
        y0, y1 = years[i - 1], years[i]
        ndvi0 = yearly[y0]["mean_ndvi_summer"]
        ndvi1 = yearly[y1]["mean_ndvi_summer"]
        delta = ndvi1 - ndvi0
        diffs.append({
            "from_year": y0,
            "to_year": y1,
            "ndvi_from": ndvi0,
            "ndvi_to": ndvi1,
            "delta_ndvi": round(delta, 4),
            "delta_pct": round(delta / ndvi0 * 100, 1) if ndvi0 else 0,
        })
        print(f"  {y0}→{y1}: ΔNDVI = {delta:+.4f} ({delta/ndvi0*100:+.1f}%)")

    # Multi-year aggregate (early years vs late years)
    early = [yearly[y]["mean_ndvi_summer"] for y in years[:2]]
    late = [yearly[y]["mean_ndvi_summer"] for y in years[-2:]]
    ndvi_early = sum(early) / len(early)
    ndvi_late = sum(late) / len(late)
    long_delta = ndvi_late - ndvi_early
    long_delta_pct = long_delta / ndvi_early * 100 if ndvi_early else 0

    # Translate ΔNDVI to Δbiomass / Δwater yield / Δ CO2
    # Heuristic: NDVI ↑ correlates with canopy density ↑ and thus interception ↑, transpiration ↑
    # Net effect on water yield: ambiguous (interception/transpiration up = water yield down,
    # but soil retention up = water yield up). For demo we model the conservative view:
    # forest vigor improvement → consistent or slight increase in water retention.
    # For CO2: NDVI proxy for AGB increment (per Pettorelli et al.) → translate as
    # Δbiomass ≈ Δ NDVI × 30 t-AGB/ha (typical scaling for needleleaf, peak 0.7-0.9 NDVI range)
    # then Δ CO2 = Δ biomass × 0.5 carbon fraction × 3.67

    forest_area_ha = co2["forest_area_ha"]
    delta_biomass_per_ha = long_delta * 30  # rough proxy
    delta_co2_per_ha = delta_biomass_per_ha * 0.5 * 3.67
    delta_co2_total = delta_co2_per_ha * forest_area_ha

    delta_water_pct = long_delta * 5  # 1.0 NDVI change ≈ 5% water yield change
    delta_water_total_m3 = water["aoi_total"]["water_yield_m3_per_yr"] * (delta_water_pct / 100)

    print(f"\nLong-term ({years[0]}-{years[1]} mean vs {years[-2]}-{years[-1]} mean):")
    print(f"  ΔNDVI = {long_delta:+.4f} ({long_delta_pct:+.1f}%)")
    print(f"  Δ CO2 estimate: {delta_co2_total:+,.0f} t-CO2 cumulative over the period")
    print(f"  Δ Water yield: {delta_water_pct:+.1f}% ≈ {delta_water_total_m3:+,.0f} m³/yr")

    report = {
        "method": "Sentinel-2 NDVI time-series difference (summer peak)",
        "aoi": water["aoi"],
        "observation_period": {
            "from": years[0] if years else None,
            "to": years[-1] if years else None,
            "obs_count": len(points),
        },
        "yearly_summer_ndvi": yearly,
        "year_over_year": diffs,
        "long_term": {
            "ndvi_early_mean": round(ndvi_early, 4),
            "ndvi_late_mean": round(ndvi_late, 4),
            "delta_ndvi": round(long_delta, 4),
            "delta_pct": round(long_delta_pct, 1),
            "delta_co2_cumulative_t": round(delta_co2_total),
            "delta_water_yield_pct": round(delta_water_pct, 1),
            "delta_water_yield_m3_per_yr": round(delta_water_total_m3),
        },
        "interpretation": (
            f"AOI 全体（{water['aoi']['forest_area_ha']:,.0f} ha 森林）の 5 年間 NDVI 平均が "
            f"{long_delta_pct:+.1f}% 変化。これは概ね "
            f"{delta_co2_total:+,.0f} t-CO2 の累積吸収量変化、"
            f"水資源涵養量で {delta_water_pct:+.1f}% の変動に相当する。"
            "プラスは森林整備・自然回復が進んでいる、マイナスは伐採・劣化を示唆する。"
        ),
        "notes": [
            "NDVI から AGB（地上部バイオマス）への換算は経験的近似（Pettorelli 等参照）。実測 LiDAR を組み合わせれば精度大幅向上。",
            "夏期ピーク NDVI を採用することで、季節変動の影響を最小化。",
            "本手法は林班単位・自治体単位への横展開可能。"
            "クレジット制度の MRV（モニタリング・報告・検証）に低コスト代替として適用可能。",
        ],
    }
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nWrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
