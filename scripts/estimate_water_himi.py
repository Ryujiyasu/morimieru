#!/usr/bin/env python3
"""
Compute the annual water yield (水資源涵養量) for the Himi-shi AOI forest,
using the formula published by 林野庁 (suigen tool Ver.1.0, 2025-11).

Inputs (all from open data):
- 月別気温・降水量: NASA POWER monthly API (free, global)
- 標高: 国土地理院 elevation API
- 地質区分: 産総研 シームレス地質図 API
- 林分情報: from our Sentinel-2 forest area + 林野庁 standard plantation defaults
  - 林地タイプ: 常緑針葉樹 (sugi/hinoki dominant in this AOI - confirmed by stable NDVI in winter)
  - 平均胸高直径: 32 cm (林野庁収穫予想表 中位 sugi 60yr)
  - 立木密度: 783 本/ha (林野庁マニュアル既定値)
  - 平均樹高: 18 m (Sentinel-2 + geological prior)

Output: data/sentinel/himi_water.json
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import requests

# ----- AOI center & forest parameters -----
HIMI_LAT = 36.857
HIMI_LON = 136.987
# Inland forest sample for geology/elevation. (36.79, 137.02) ≈ 朝日山系 east side, ~170 m.
FOREST_POINT = (36.79, 137.02)
FOREST_AREA_HA = 12398          # from data/sentinel/himi_co2.json (Sentinel-2 NDVI > 0.5)

# 林野庁マニュアル既定値 (sugi/hinoki plantation, typical 中老齢林)
FOREST_PARAMS = {
    "type": "常緑針葉樹",
    "density_per_ha": 783,
    "dbh_cm": 32,
    "height_m": 18,
    "source": "林野庁収穫予想表 中位（スギ・ヒノキ 50-70年生）+ Sentinel-2 forest mask",
}

# Interception coefficients (Komatsu et al. 2015) for 針葉樹
# r = k1 * (1 - exp(-k2 * N)), where N = density
INTERCEPTION_NEEDLE = {
    "leaf_on":  {"rain": (0.263, 1.24e-3), "snow": (0.406, 2.11e-3)},
    "leaf_off": {"rain_snow": (0.346, 1.46e-3)},  # for evergreen, this is rarely used
}

GEOLOGY_MAP = {
    # Map seamless-geology age strings → 林野庁 4-class
    "新生代 第四紀": "第四紀",
    "新生代 第三紀": "第三紀",
    "新生代 古第三紀": "第三紀",
    "新生代 新第三紀": "第三紀",
    "中生代": "中古生代",
    "古生代": "中古生代",
    "深成岩": "花崗岩類",
    "花崗岩": "花崗岩類",
}
RUNOFF_BY_GEOLOGY = {
    "第三紀": [(1306, 0.4377, -80.17), (float("inf"), 0.6433, -348.65)],
    "第四紀": [(1346, 0.2609, -56.98), (float("inf"), 0.4249, -277.72)],
    "花崗岩類": [(1343, 0.3768, -58.83), (float("inf"), 0.5443, -283.80)],
    "中古生代": [(1323, 0.3501, -75.01), (float("inf"), 0.5524, -342.65)],
}

OUT_DIR = Path(__file__).parent.parent / "data" / "sentinel"


# ----- Data fetchers -----

def fetch_climate(lat, lon, start_year=2020, end_year=2024):
    """NASA POWER monthly climate. Returns dict month → {t_c, p_mm_per_day}."""
    r = requests.get(
        "https://power.larc.nasa.gov/api/temporal/monthly/point",
        params={
            "parameters": "T2M,PRECTOTCORR",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "format": "JSON",
            "start": start_year,
            "end": end_year,
        },
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    t2m = d["properties"]["parameter"]["T2M"]
    pre = d["properties"]["parameter"]["PRECTOTCORR"]

    # Aggregate to per-month averages across years
    months = {}
    for k, t in t2m.items():
        if k.endswith("13"):  # annual mean key
            continue
        m = int(k[4:])
        months.setdefault(m, {"t": [], "p_day": []})["t"].append(t)
        months[m]["p_day"].append(pre[k])

    monthly = {}
    for m in range(1, 13):
        rec = months.get(m)
        if not rec:
            continue
        # Mean across years; convert mm/day → mm/month
        from calendar import monthrange
        days = monthrange(2023, m)[1]  # typical year
        monthly[m] = {
            "t_c": round(sum(rec["t"]) / len(rec["t"]), 2),
            "p_mm": round(sum(rec["p_day"]) / len(rec["p_day"]) * days, 1),
        }
    return monthly


def fetch_elevation(lat, lon):
    r = requests.get(
        "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php",
        params={"lon": lon, "lat": lat, "outtype": "JSON"},
        timeout=20,
    )
    r.raise_for_status()
    el = r.json().get("elevation")
    if el in (None, "-----", "----"):
        return None
    return float(el)


def fetch_geology(lat, lon):
    r = requests.get(
        "https://gbank.gsj.jp/seamless/v2/api/1.2.1/legend.json",
        params={"point": f"{lat},{lon}"},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    age = j.get("formationAge_ja", "")
    group = j.get("group_ja", "")
    # Map to 林野庁 4-class
    cls = None
    for key, val in GEOLOGY_MAP.items():
        if key in age or key in group:
            cls = val
            break
    if cls is None:
        cls = "中古生代"  # conservative default (lowest water yield)
    return {"age": age, "group": group, "class": cls, "raw": j}


# ----- Formulas -----

def elev_correct_precip(p_a_mm_per_yr, h_m, h_a_m):
    """1-6 — elevation correction (annual scale)."""
    alpha = 4.7e-4 * p_a_mm_per_yr
    return alpha * (h_m - h_a_m) + p_a_mm_per_yr


def elev_correct_precip_monthly(p_a_mm, h_m, h_a_m):
    """Elevation correction for a single month. α = C × P_a where P_a is the monthly value
    at the station (per the 林野庁 manual)."""
    alpha = 4.7e-4 * p_a_mm
    return alpha * (h_m - h_a_m) + p_a_mm


def elev_correct_temp(t_a_c, h_m, h_a_m):
    return t_a_c - 0.0065 * (h_m - h_a_m)


def annual_runoff(p_annual_corrected, geology_class):
    """1-7 / 1-8 — annual direct runoff [mm/year]."""
    p_eve = 0.6473 * p_annual_corrected - 138.67
    coeffs = RUNOFF_BY_GEOLOGY.get(geology_class, RUNOFF_BY_GEOLOGY["中古生代"])
    for thresh, a, b in coeffs:
        if p_eve <= thresh:
            return max(a * p_eve + b, 0), p_eve
    a, b = coeffs[-1][1], coeffs[-1][2]
    return max(a * p_eve + b, 0), p_eve


def evergreen_needleleaf_evapo_monthly(monthly_climate, density_per_ha, dbh_cm,
                                       p_corr_monthly, t_corr_monthly):
    """
    Compute per-ha monthly evapotranspiration for evergreen-needleleaf forest.
    Returns (transpiration_mm, interception_mm) per month.
    """
    # Per-tree transpiration reference value [cm³/day]
    q_tref = 849 * dbh_cm - 7350

    out = {}
    for m in range(1, 13):
        clim = monthly_climate.get(m)
        if not clim:
            continue
        t = t_corr_monthly[m]
        p = p_corr_monthly[m]

        # Transpiration
        f_t = 0.0244 * t + 0.4361
        q_t_per_tree_cm3_per_day = q_tref * f_t
        if q_t_per_tree_cm3_per_day < 0:
            q_t_per_tree_cm3_per_day = 0
        # cm³/day × density (trees/ha) × days = cm³/(ha·month)
        from calendar import monthrange
        days = monthrange(2023, m)[1]
        cm3_per_ha_per_month = q_t_per_tree_cm3_per_day * density_per_ha * days
        # Convert cm³/ha → mm of depth over 1 ha
        # 1 ha = 1e4 m² = 1e8 cm². 1 mm × 1 ha = 1e8 cm³ × 1e-1 = 1e7 cm³
        # 1 cm³/ha = 1e-7 cm/ha = 1e-7 × 10 mm = 1e-6 mm... wait
        # Better: 1 mm depth over 1 ha = 0.001 m × 10000 m² = 10 m³ = 10,000 L = 1e7 cm³
        transp_mm = cm3_per_ha_per_month / 1e7

        # Interception (evergreen needleleaf, simplify: always leaf-on rain)
        # For evergreen, use leaf-on year-round
        # Snow vs rain split: if T <= -2, all snow; if T >= 5, all rain; linear between
        if t <= -2:
            snow_frac = 1.0
        elif t >= 5:
            snow_frac = 0.0
        else:
            # Approximate from PDF chart (太田1989)
            snow_frac = max(0.0, min(1.0, (5 - t) / 7))
        rain_p = p * (1 - snow_frac)
        snow_p = p * snow_frac
        k1_r, k2_r = INTERCEPTION_NEEDLE["leaf_on"]["rain"]
        k1_s, k2_s = INTERCEPTION_NEEDLE["leaf_on"]["snow"]
        r_rain = k1_r * (1 - math.exp(-k2_r * density_per_ha))
        r_snow = k1_s * (1 - math.exp(-k2_s * density_per_ha))
        intercept_mm = r_rain * rain_p + r_snow * snow_p

        out[m] = {"transp": transp_mm, "intercept": intercept_mm,
                  "evapo_total": transp_mm + intercept_mm,
                  "rain_p_mm": rain_p, "snow_p_mm": snow_p}
    return out


def main():
    print("===== 水資源涵養量推定 (氷見市 forest AOI) =====\n")

    # Climate at AOI center
    monthly_raw = fetch_climate(HIMI_LAT, HIMI_LON)
    p_total_raw = sum(m["p_mm"] for m in monthly_raw.values())
    print(f"Raw climate from NASA POWER:")
    print(f"  Annual P (raw): {p_total_raw:.0f} mm")
    print(f"  Annual T mean: {sum(m['t_c'] for m in monthly_raw.values()) / 12:.1f} °C")

    # Elevation
    h_a = fetch_elevation(HIMI_LAT, HIMI_LON)
    h_forest = fetch_elevation(*FOREST_POINT)
    print(f"\nElevation:")
    print(f"  AOI center: {h_a} m   ←観測点(降水量)")
    print(f"  Forest sample point: {h_forest} m   ←対象林地")

    # Elevation correction
    p_corr_monthly = {m: elev_correct_precip_monthly(monthly_raw[m]["p_mm"], h_forest, h_a)
                      for m in monthly_raw}
    t_corr_monthly = {m: elev_correct_temp(monthly_raw[m]["t_c"], h_forest, h_a)
                      for m in monthly_raw}
    p_corr_annual = sum(p_corr_monthly.values())
    print(f"\nAfter elevation correction:")
    print(f"  Annual P: {p_corr_annual:.0f} mm")
    print(f"  Annual T mean: {sum(t_corr_monthly.values())/12:.1f} °C")

    # Geology
    geo = fetch_geology(*FOREST_POINT)
    print(f"\nGeology (at forest sample point):")
    print(f"  {geo['age']} / {geo['group']} / {geo['raw'].get('lithology_ja','')}")
    print(f"  → 林野庁分類: {geo['class']}")

    # Direct runoff
    runoff_mm, p_eve = annual_runoff(p_corr_annual, geo["class"])
    print(f"\nDirect runoff:")
    print(f"  P_eve (event-integrated): {p_eve:.0f} mm/yr")
    print(f"  Q (annual direct runoff): {runoff_mm:.0f} mm/yr")

    # Evapotranspiration
    monthly_evapo = evergreen_needleleaf_evapo_monthly(
        monthly_raw,
        FOREST_PARAMS["density_per_ha"],
        FOREST_PARAMS["dbh_cm"],
        p_corr_monthly, t_corr_monthly,
    )
    annual_evapo = sum(m["evapo_total"] for m in monthly_evapo.values())
    annual_transp = sum(m["transp"] for m in monthly_evapo.values())
    annual_intercept = sum(m["intercept"] for m in monthly_evapo.values())
    print(f"\nEvapotranspiration:")
    print(f"  Transpiration: {annual_transp:.0f} mm/yr")
    print(f"  Interception:  {annual_intercept:.0f} mm/yr")
    print(f"  Total evapo:   {annual_evapo:.0f} mm/yr")

    # Water yield
    water_yield_mm = p_corr_annual - runoff_mm - annual_evapo
    water_yield_pct = water_yield_mm / p_corr_annual * 100
    runoff_pct = runoff_mm / p_corr_annual * 100
    evapo_pct = annual_evapo / p_corr_annual * 100

    # AOI total
    water_yield_m3 = water_yield_mm * 0.001 * FOREST_AREA_HA * 10000  # mm → m, ha → m²

    print(f"\n========== Annual water budget per ha ==========")
    print(f"  Precipitation:  {p_corr_annual:6.0f} mm/yr  (100%)")
    print(f"  Direct runoff:  {runoff_mm:6.0f} mm/yr  ({runoff_pct:.1f}%)")
    print(f"  Evapotrans.:    {annual_evapo:6.0f} mm/yr  ({evapo_pct:.1f}%)")
    print(f"  Water yield:    {water_yield_mm:6.0f} mm/yr  ({water_yield_pct:.1f}%)  ← 水資源涵養量")
    print(f"")
    print(f"AOI forest area: {FOREST_AREA_HA:,} ha")
    print(f"Total water yield: {water_yield_m3:,.0f} m³/yr  ≈ {water_yield_m3/1e6:.1f} 百万トン/年")

    # Save report
    report = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "method": "林野庁「林地における水資源涵養量（貯留機能）の簡易評価法」Ver.1.0 (2025-11)",
        "method_source_url": "https://www.rinya.maff.go.jp/j/suigen/suigen/260311.html",
        "aoi": {
            "name": "氷見市 朝日山系周辺",
            "center_lat": HIMI_LAT, "center_lon": HIMI_LON,
            "forest_area_ha": FOREST_AREA_HA,
        },
        "inputs": {
            "climate": {
                "source": "NASA POWER monthly (2020-2024 mean)",
                "annual_precip_mm_raw": round(p_total_raw, 0),
                "annual_temp_c": round(sum(m['t_c'] for m in monthly_raw.values())/12, 1),
                "monthly": monthly_raw,
            },
            "elevation": {
                "source": "国土地理院 標高API",
                "weather_station_m": h_a,
                "forest_point_m": h_forest,
            },
            "geology": {
                "source": "産総研 シームレス地質図 v2 API",
                "raw_age": geo["age"],
                "lithology": geo["raw"].get("lithology_ja", ""),
                "rinya_class": geo["class"],
            },
            "forest": FOREST_PARAMS,
        },
        "intermediates": {
            "annual_precip_corrected_mm": round(p_corr_annual, 1),
            "p_event_integrated_mm": round(p_eve, 1),
        },
        "results_mm_per_yr": {
            "precipitation": round(p_corr_annual, 0),
            "direct_runoff": round(runoff_mm, 0),
            "evapotranspiration": round(annual_evapo, 0),
            "transpiration": round(annual_transp, 0),
            "interception": round(annual_intercept, 0),
            "water_yield": round(water_yield_mm, 0),
        },
        "results_pct": {
            "direct_runoff_pct": round(runoff_pct, 1),
            "evapotranspiration_pct": round(evapo_pct, 1),
            "water_yield_pct": round(water_yield_pct, 1),
        },
        "aoi_total": {
            "water_yield_m3_per_yr": round(water_yield_m3),
            "water_yield_million_tons_per_yr": round(water_yield_m3 / 1e6, 1),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "himi_water.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
