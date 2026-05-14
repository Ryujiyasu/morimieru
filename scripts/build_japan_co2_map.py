#!/usr/bin/env python3
"""
Build a nationwide CO2 absorption heatmap from Sentinel-2 NDVI.

For each prefecture polygon (47 prefs):
- Query CDSE Sentinel Hub Statistical API with NDVI evalscript
- Use peak summer 2024 window for stable forest mask
- Compute forest pixel ratio (NDVI > 0.5)
- Compute forest area = polygon_area × forest_pct
- Compute CO2 = forest area × 9.62 t-CO2/ha/yr (IPCC Tier 2)

Output: data/co2/japan_prefectures_co2.geojson

This is the "今すぐできる版"。後で LiDAR や林班単位データで精度向上 (Tier 3) させていく。
"""
import json
import math
import time
from pathlib import Path

import requests
from shapely.geometry import shape, mapping, Polygon
from shapely.ops import transform as shapely_transform
import sh_client as sh

ROOT = Path(__file__).parent.parent
INPUT = Path("/tmp/japan-pref.geojson")
OUT = ROOT / "data" / "co2" / "japan_prefectures_co2.geojson"
OUT.parent.mkdir(parents=True, exist_ok=True)

CO2_PER_HA = 9.62  # IPCC AFOLU Tier 2 / 林野庁収穫予想表
SUMMER_WINDOW = ("2024-07-01T00:00:00Z", "2024-09-30T23:59:59Z")

# Evalscript: returns NDVI + valid mask (cloud-free)
EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "SCL", "dataMask"] }],
    output: [
      { id: "ndvi", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 }
    ]
  };
}
function evaluatePixel(s) {
  const cloud = (s.SCL === 3 || s.SCL === 8 || s.SCL === 9 || s.SCL === 10 || s.SCL === 11);
  const valid = (s.dataMask && !cloud) ? 1 : 0;
  const ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-7);
  return { ndvi: [ndvi], dataMask: [valid] };
}
"""


def polygon_area_km2(geom):
    """Rough area in km² using equal-area approximation."""
    # Use centroid latitude for approximate scaling
    c = geom.centroid
    lat_rad = math.radians(c.y)
    # Equal-area projection: 1 degree lat = 111 km; 1 degree lon = 111 × cos(lat) km
    def projected(coords):
        return [(x * 111 * math.cos(lat_rad), y * 111) for x, y in coords]
    if geom.geom_type == "Polygon":
        ext = projected(list(geom.exterior.coords))
        proj_geom = Polygon(ext)
        return proj_geom.area
    elif geom.geom_type == "MultiPolygon":
        total = 0
        for poly in geom.geoms:
            ext = projected(list(poly.exterior.coords))
            total += Polygon(ext).area
        return total
    return 0


def fetch_forest_pct(geom):
    """Statistical API: compute forest pixel ratio (NDVI > 0.5) within the polygon."""
    # CDSE Statistical API accepts GeoJSON geometry
    geom_dict = mapping(geom)
    # Reduce overly complex polygons
    if geom.geom_type == "MultiPolygon":
        # Keep largest part only to simplify
        largest = max(geom.geoms, key=lambda p: p.area)
        geom_dict = mapping(largest)

    bbox = geom.bounds
    width = max(100, min(500, int((bbox[2] - bbox[0]) * 111)))
    height = max(100, min(500, int((bbox[3] - bbox[1]) * 111)))

    payload = {
        "input": {
            "bounds": {
                "geometry": geom_dict,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 30},
            }],
        },
        "aggregation": {
            "timeRange": {"from": SUMMER_WINDOW[0], "to": SUMMER_WINDOW[1]},
            "aggregationInterval": {"of": "P3M"},  # single 3-month aggregate
            "evalscript": EVALSCRIPT,
            "width": width,
            "height": height,
        },
        "calculations": {
            "ndvi": {
                "histograms": {"default": {"nBins": 10, "lowEdge": -0.5, "highEdge": 1.0}},
                "statistics": {"default": {}},
            },
        },
    }

    result = sh.statistics(payload)
    for entry in result.get("data", []):
        try:
            ndvi_stats = entry["outputs"]["ndvi"]["bands"]["B0"]["stats"]
            mean = ndvi_stats.get("mean")
            sample_count = ndvi_stats.get("sampleCount", 0)
            no_data = ndvi_stats.get("noDataCount", 0)
            valid = sample_count - no_data
            if valid == 0:
                continue
            # Use histogram to count NDVI > 0.5
            hist = entry["outputs"]["ndvi"]["bands"]["B0"]["histogram"]["bins"]
            forest_count = 0
            for b in hist:
                if b.get("lowEdge", 0) >= 0.5:
                    forest_count += b.get("count", 0)
            forest_pct = forest_count / valid if valid else 0
            return {
                "mean_ndvi": round(mean, 3),
                "valid_pixels": valid,
                "forest_pixels": forest_count,
                "forest_pct": round(forest_pct, 4),
            }
        except (KeyError, TypeError):
            continue
    return None


def main():
    src = json.loads(INPUT.read_text())
    print(f"Loaded {len(src['features'])} prefecture polygons")

    enriched = []
    for i, f in enumerate(src["features"]):
        pid = f["properties"].get("id")
        name = f["properties"].get("nam_ja", "")
        geom = shape(f["geometry"])
        area_km2 = polygon_area_km2(geom)
        pref_area_ha = round(area_km2 * 100)

        print(f"  {pid:2d} {name} ({pref_area_ha:,} ha)...", end="", flush=True)

        result = fetch_forest_pct(geom)
        if result is None:
            print(" SKIP")
            continue

        forest_area_ha = round(pref_area_ha * result["forest_pct"])
        co2_t = round(forest_area_ha * CO2_PER_HA)
        co2_per_ha = co2_t / forest_area_ha if forest_area_ha else 0

        # Simplify geometry for web display
        simplified = geom.simplify(0.015, preserve_topology=True)
        if simplified.is_empty:
            simplified = geom

        enriched.append({
            "type": "Feature",
            "geometry": mapping(simplified),
            "properties": {
                "pref_id": pid,
                "name_ja": name,
                "pref_area_ha": pref_area_ha,
                "forest_pct": result["forest_pct"],
                "forest_area_ha": forest_area_ha,
                "mean_ndvi": result["mean_ndvi"],
                "valid_pixels": result["valid_pixels"],
                "co2_t_per_yr": co2_t,
                "co2_million_t_per_yr": round(co2_t / 1e6, 2),
                "co2_per_ha_t_per_yr": round(co2_per_ha, 2),
            },
        })
        print(f" NDVI={result['mean_ndvi']:.2f} forest={result['forest_pct']*100:.0f}% → {forest_area_ha:,}ha → {co2_t:,}t/yr")
        time.sleep(0.5)  # API politeness

    total_pref_ha = sum(p["properties"]["pref_area_ha"] for p in enriched)
    total_forest_ha = sum(p["properties"]["forest_area_ha"] for p in enriched)
    total_co2 = sum(p["properties"]["co2_t_per_yr"] for p in enriched)
    print(f"\nTotal pref area: {total_pref_ha:,} ha")
    print(f"Total forest area (Sentinel-2 NDVI > 0.5): {total_forest_ha:,} ha ({total_forest_ha/total_pref_ha*100:.1f}%)")
    print(f"Total CO2 absorption: {total_co2:,} t-CO2/yr ({total_co2/1e6:.0f}M t/yr)")

    out = {
        "type": "FeatureCollection",
        "source": "Sentinel-2 L2A (CDSE Statistical API, peak summer 2024) × IPCC AFOLU Tier 2",
        "method": "森林ピクセル = NDVI > 0.5 / 都道府県ポリゴン内集計 / CO2 = 森林面積 × 9.62 t-CO2/ha/年",
        "co2_per_ha_per_yr": CO2_PER_HA,
        "computed_at": "2026-05-14",
        "total_pref_area_ha": total_pref_ha,
        "total_forest_area_ha": total_forest_ha,
        "total_co2_t_per_yr": total_co2,
        "features": enriched,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"\nWrote: {OUT} ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
