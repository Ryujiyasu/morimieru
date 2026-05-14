#!/usr/bin/env python3
"""
Build a 10-year Sentinel-2 NDVI timeseries × CO2 absorption per prefecture.

For each (prefecture, year) in 47 × 11 = 517 cells:
- Call CDSE Statistical API with NDVI evalscript for that summer
- Compute forest pixel ratio (NDVI > 0.5) within prefecture polygon
- Forest area = polygon_area × forest_pct
- CO2 = forest area × 9.62

Output: data/co2/japan_prefectures_timeseries.geojson
  features: 47 prefectures
  each properties has yearly: { "2015": {...}, ..., "2025": {...} }
"""
import json
import math
import time
from pathlib import Path

from shapely.geometry import shape, mapping, Polygon
import sh_client as sh

ROOT = Path(__file__).parent.parent
INPUT = Path("/tmp/japan-pref.geojson")
OUT = ROOT / "data" / "co2" / "japan_prefectures_timeseries.geojson"
OUT.parent.mkdir(parents=True, exist_ok=True)

CO2_PER_HA = 9.62
YEARS = list(range(2015, 2026))  # 2015 - 2025

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
    c = geom.centroid
    lat_rad = math.radians(c.y)
    def projected(coords):
        return [(x * 111 * math.cos(lat_rad), y * 111) for x, y in coords]
    if geom.geom_type == "Polygon":
        return Polygon(projected(list(geom.exterior.coords))).area
    elif geom.geom_type == "MultiPolygon":
        total = 0
        for poly in geom.geoms:
            total += Polygon(projected(list(poly.exterior.coords))).area
        return total
    return 0


def fetch_year(geom, year, retries=3):
    if geom.geom_type == "MultiPolygon":
        largest = max(geom.geoms, key=lambda p: p.area)
        geom_dict = mapping(largest)
    else:
        geom_dict = mapping(geom)

    bbox = geom.bounds
    width = max(80, min(300, int((bbox[2] - bbox[0]) * 80)))
    height = max(80, min(300, int((bbox[3] - bbox[1]) * 80)))

    payload = {
        "input": {
            "bounds": {
                "bbox": list(geom.bounds),
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 30},
            }],
        },
        "aggregation": {
            "timeRange": {
                "from": f"{year}-07-01T00:00:00Z",
                "to": f"{year}-09-30T23:59:59Z",
            },
            "aggregationInterval": {"of": "P1M"},
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
    backoff = 2
    for attempt in range(retries):
        try:
            result = sh.statistics(payload)
            break
        except Exception as e:
            err = str(e)
            if "429" in err or "RATE_LIMIT" in err:
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
    else:
        return None
    # Aggregate across all monthly entries — pick the one with highest valid count
    best = None
    for entry in result.get("data", []):
        try:
            b0 = entry["outputs"]["ndvi"]["bands"]["B0"]
            stats = b0["stats"]
            sc = stats.get("sampleCount", 0)
            nd = stats.get("noDataCount", 0)
            valid = sc - nd
            if valid == 0:
                continue
            hist = b0["histogram"]["bins"]
            forest_count = sum(b.get("count", 0) for b in hist if b.get("lowEdge", 0) >= 0.5)
            rec = {
                "mean_ndvi": round(stats.get("mean", 0), 3),
                "forest_pct": round(forest_count / valid, 4),
                "valid_pixels": valid,
            }
            if best is None or valid > best["valid_pixels"]:
                best = rec
        except (KeyError, TypeError):
            continue
    return best


def main():
    src = json.loads(INPUT.read_text())
    print(f"Prefectures: {len(src['features'])}, years: {YEARS[0]}-{YEARS[-1]}")
    print(f"Total API calls: {len(src['features']) * len(YEARS)}")

    enriched = []
    for i, f in enumerate(src["features"]):
        pid = f["properties"].get("id")
        name = f["properties"].get("nam_ja", "")
        geom = shape(f["geometry"])
        pref_area_ha = round(polygon_area_km2(geom) * 100)
        print(f"\n[{i+1}/{len(src['features'])}] {pid} {name} ({pref_area_ha:,} ha)")

        yearly = {}
        for year in YEARS:
            res = fetch_year(geom, year)
            if not res:
                continue
            forest_ha = round(pref_area_ha * res["forest_pct"])
            co2 = round(forest_ha * CO2_PER_HA)
            yearly[year] = {
                "ndvi": res["mean_ndvi"],
                "forest_pct": res["forest_pct"],
                "forest_ha": forest_ha,
                "co2_t": co2,
            }
            print(f"  {year}: NDVI={res['mean_ndvi']:.2f} fc={res['forest_pct']*100:.0f}% → {forest_ha:,}ha {co2:,}t/yr")
            time.sleep(0.6)

        # Simplify geometry
        simplified = geom.simplify(0.02, preserve_topology=True)
        if simplified.is_empty:
            simplified = geom

        enriched.append({
            "type": "Feature",
            "geometry": mapping(simplified),
            "properties": {
                "pref_id": pid,
                "name_ja": name,
                "pref_area_ha": pref_area_ha,
                "yearly": yearly,
            },
        })

        # Save partial result every 10 prefectures
        if (i + 1) % 10 == 0:
            partial = {
                "type": "FeatureCollection",
                "source": "Sentinel-2 L2A × IPCC Tier 2",
                "method": "森林ピクセル NDVI > 0.5 × 9.62 t-CO2/ha/yr",
                "years": YEARS,
                "features": enriched,
            }
            OUT.write_text(json.dumps(partial, ensure_ascii=False))
            print(f"  [snapshot saved: {i+1} prefectures]")

    out = {
        "type": "FeatureCollection",
        "source": "Sentinel-2 L2A (CDSE Statistical API, dynamics 2015-2025) × IPCC AFOLU Tier 2",
        "method": "森林ピクセル = NDVI > 0.5 / 都道府県ポリゴン内集計 / CO2 = 森林面積 × 9.62 t-CO2/ha/年",
        "co2_per_ha_per_yr": CO2_PER_HA,
        "years": YEARS,
        "computed_at": "2026-05-14",
        "features": enriched,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"\nWrote: {OUT} ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
