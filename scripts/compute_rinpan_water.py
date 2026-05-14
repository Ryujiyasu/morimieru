#!/usr/bin/env python3
"""
Per-林班 water yield (and bare-land comparison) computation for Shizuoka.

For each forest stand:
- Take its centroid lat/lon
- Pull climate from NASA POWER (cached per 0.5° grid to avoid redundant calls)
- Pull elevation from 国土地理院 API
- Pull geology from 産総研 シームレス地質図
- Apply 林野庁 simplified water yield formula (Tier 2)
- Compute bare-land scenario (降水量×0.1)
- Compute the森林効果: yield - bare-land

Output: enriched GeoJSON with water yield + bare-land comparison per stand.
"""
import json
import time
from pathlib import Path

import requests
from shapely.geometry import shape

import sys
sys.path.insert(0, str(Path(__file__).parent))
from estimate_water_himi import (
    elev_correct_precip_monthly,
    elev_correct_temp,
    annual_runoff,
    evergreen_needleleaf_evapo_monthly,
    GEOLOGY_MAP,
    FOREST_PARAMS,
)
from estimate_co2_himi import co2_per_ha_per_year

ROOT = Path(__file__).parent.parent
INPUT = ROOT / "data" / "rinpan" / "shizuoka_rinpan.geojson"
OUTPUT = ROOT / "data" / "rinpan" / "shizuoka_rinpan_water.geojson"

# Caches (per-grid cell, keyed by rounded lat/lon)
_climate_cache = {}
_elev_cache = {}
_geo_cache = {}


def fetch_climate(lat, lon):
    """NASA POWER monthly (2020-2024 mean), cached by ~0.5° grid."""
    key = (round(lat, 1), round(lon, 1))
    if key in _climate_cache:
        return _climate_cache[key]
    try:
        r = requests.get(
            "https://power.larc.nasa.gov/api/temporal/monthly/point",
            params={
                "parameters": "T2M,PRECTOTCORR",
                "community": "AG",
                "longitude": key[1],
                "latitude": key[0],
                "format": "JSON",
                "start": 2020,
                "end": 2024,
            },
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        t2m = d["properties"]["parameter"]["T2M"]
        pre = d["properties"]["parameter"]["PRECTOTCORR"]
        from calendar import monthrange
        months = {}
        for k, t in t2m.items():
            if k.endswith("13"):
                continue
            m = int(k[4:])
            months.setdefault(m, {"t": [], "p_day": []})["t"].append(t)
            months[m]["p_day"].append(pre[k])
        monthly = {}
        for m in range(1, 13):
            rec = months.get(m)
            if not rec:
                continue
            days = monthrange(2023, m)[1]
            monthly[m] = {
                "t_c": sum(rec["t"]) / len(rec["t"]),
                "p_mm": sum(rec["p_day"]) / len(rec["p_day"]) * days,
            }
        _climate_cache[key] = monthly
        return monthly
    except Exception as e:
        print(f"  climate fetch failed for {key}: {e}")
        return None


def fetch_elevation(lat, lon):
    key = (round(lat, 3), round(lon, 3))
    if key in _elev_cache:
        return _elev_cache[key]
    try:
        r = requests.get(
            "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php",
            params={"lon": key[1], "lat": key[0], "outtype": "JSON"},
            timeout=15,
        )
        r.raise_for_status()
        el = r.json().get("elevation")
        if el in (None, "-----", "----"):
            _elev_cache[key] = None
            return None
        _elev_cache[key] = float(el)
        return float(el)
    except Exception:
        _elev_cache[key] = None
        return None


def fetch_geology(lat, lon):
    key = (round(lat, 2), round(lon, 2))
    if key in _geo_cache:
        return _geo_cache[key]
    try:
        r = requests.get(
            "https://gbank.gsj.jp/seamless/v2/api/1.2.1/legend.json",
            params={"point": f"{key[0]},{key[1]}"},
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        age = j.get("formationAge_ja", "")
        group = j.get("group_ja", "")
        cls = None
        for k, v in GEOLOGY_MAP.items():
            if k in age or k in group:
                cls = v
                break
        if cls is None:
            cls = "中古生代"
        _geo_cache[key] = cls
        return cls
    except Exception:
        _geo_cache[key] = "中古生代"
        return "中古生代"


def compute_water_for_stand(centroid_lat, centroid_lon, area_ha):
    """Run林野庁 Tier 2 for a single stand. Returns dict of results."""
    monthly = fetch_climate(centroid_lat, centroid_lon)
    if not monthly:
        return None
    h_a = fetch_elevation(centroid_lat, centroid_lon) or 50  # fallback
    # For each stand the observation point and forest are the same point
    p_corr_monthly = {m: monthly[m]["p_mm"] for m in monthly}
    t_corr_monthly = {m: monthly[m]["t_c"] for m in monthly}
    p_annual = sum(p_corr_monthly.values())
    t_annual = sum(t_corr_monthly.values()) / 12

    geo = fetch_geology(centroid_lat, centroid_lon)
    runoff_mm, p_eve = annual_runoff(p_annual, geo)

    monthly_evapo = evergreen_needleleaf_evapo_monthly(
        monthly,
        FOREST_PARAMS["density_per_ha"],
        FOREST_PARAMS["dbh_cm"],
        p_corr_monthly,
        t_corr_monthly,
    )
    annual_evapo = sum(m["evapo_total"] for m in monthly_evapo.values())
    water_yield_mm = max(p_annual - runoff_mm - annual_evapo, 0)

    # Bare-land scenario: water yield ≈ 10% of precipitation (per 林野庁 manual)
    bare_yield_mm = p_annual * 0.10

    # CO2 per ha
    co2_per_ha = co2_per_ha_per_year()  # ~9.62 t-CO2/ha/yr

    # Stand totals
    forest_yield_m3 = water_yield_mm * 0.001 * area_ha * 10000
    bare_yield_m3 = bare_yield_mm * 0.001 * area_ha * 10000
    diff_m3 = forest_yield_m3 - bare_yield_m3

    return {
        "annual_precip_mm": round(p_annual, 0),
        "annual_temp_c": round(t_annual, 1),
        "geology": geo,
        "elevation_m": round(h_a, 1),
        "runoff_mm": round(runoff_mm, 0),
        "evapo_mm": round(annual_evapo, 0),
        "water_yield_mm": round(water_yield_mm, 0),
        "bare_yield_mm": round(bare_yield_mm, 0),
        "water_yield_m3": round(forest_yield_m3),
        "bare_yield_m3": round(bare_yield_m3),
        "forest_effect_m3": round(diff_m3),
        "co2_estimate_t_per_yr": round(co2_per_ha * area_ha),
        "forest_pct": round(water_yield_mm / p_annual * 100, 1) if p_annual else 0,
    }


def main():
    fc = json.loads(INPUT.read_text())
    feats = fc["features"]
    print(f"Computing water yield for {len(feats)} stands...")

    enriched = []
    for i, f in enumerate(feats):
        sh = shape(f["geometry"])
        c = sh.centroid
        area_ha = f["properties"].get("SHAPE_AREA", 0) / 10000
        if area_ha <= 0:
            continue
        result = compute_water_for_stand(c.y, c.x, area_ha)
        if result is None:
            continue
        new_props = dict(f["properties"])
        new_props["area_ha"] = round(area_ha, 1)
        new_props["centroid_lat"] = round(c.y, 5)
        new_props["centroid_lon"] = round(c.x, 5)
        new_props.update(result)
        enriched.append({
            "type": "Feature",
            "geometry": f["geometry"],
            "properties": new_props,
        })
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(feats)} done, climate cache: {len(_climate_cache)}, elev: {len(_elev_cache)}")
        # Throttle to be nice to public APIs
        time.sleep(0.05)

    # Summary stats
    total_forest_m3 = sum(p["properties"]["water_yield_m3"] for p in enriched)
    total_bare_m3 = sum(p["properties"]["bare_yield_m3"] for p in enriched)
    total_co2_t = sum(p["properties"]["co2_estimate_t_per_yr"] for p in enriched)
    total_ha = sum(p["properties"]["area_ha"] for p in enriched)
    print(f"\nStatic県 forest summary:")
    print(f"  Area: {total_ha:,.0f} ha")
    print(f"  Water yield (forest): {total_forest_m3:,} m³/yr")
    print(f"  Water yield (bare):   {total_bare_m3:,} m³/yr")
    print(f"  Forest effect:        {total_forest_m3 - total_bare_m3:,} m³/yr (+{(total_forest_m3/total_bare_m3 - 1)*100:.0f}%)")
    print(f"  CO2 absorption:       {total_co2_t:,} t-CO2/yr")

    out = {
        "type": "FeatureCollection",
        "source": "静岡県森林クラウド (MAGIS.RINPAN) × 林野庁簡易評価法 Tier 2",
        "stands": len(enriched),
        "total_area_ha": round(total_ha),
        "total_water_yield_m3_per_yr": total_forest_m3,
        "total_bare_yield_m3_per_yr": total_bare_m3,
        "total_co2_t_per_yr": total_co2_t,
        "features": enriched,
    }
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False))
    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"\nWrote: {OUTPUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
