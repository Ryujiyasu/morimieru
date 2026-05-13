#!/usr/bin/env python3
"""
Fetch Himi-shi NDVI via CDSE Sentinel Hub Process API and Statistical API.
Outputs:
  data/sentinel/himi_ndvi.png      - colored NDVI raster for Leaflet imageOverlay
  data/sentinel/himi_meta.json     - scene metadata + Leaflet bounds
  data/sentinel/himi_timeseries.json - NDVI 5-year time series for the chart
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import sh_client as sh

# Himi-shi target AOI: ~16km × 14km centered on the city
HIMI_LAT = 36.857
HIMI_LON = 136.987
LAT_PAD = 0.07   # ~7.7 km north/south
LON_PAD = 0.09   # ~8.0 km east/west at this latitude
BBOX_WGS84 = (HIMI_LON - LON_PAD, HIMI_LAT - LAT_PAD, HIMI_LON + LON_PAD, HIMI_LAT + LAT_PAD)

OUT_DIR = Path(__file__).parent.parent / "data" / "sentinel"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_latest_ndvi_png():
    today = datetime.utcnow().date()
    date_to = today.isoformat()
    date_from = (today - timedelta(days=60)).isoformat()  # 60-day window
    print(f"Fetching latest cloud-low NDVI for {date_from} → {date_to}")

    payload = sh.build_process_payload_png(
        bbox_wgs84=BBOX_WGS84,
        date_from=date_from,
        date_to=date_to,
        width=1600,
        height=1400,
        mosaicking_order="leastCC",
    )
    png = sh.process(payload, accept="image/png")
    out = OUT_DIR / "himi_ndvi.png"
    out.write_bytes(png)
    print(f"  wrote {out}  ({len(png)//1024} KB)")
    return out


def fetch_scene_metadata():
    """Use catalog API to find the actual scene used (most recent low-cloud one)."""
    today = datetime.utcnow().date()
    date_to = today.isoformat()
    date_from = (today - timedelta(days=60)).isoformat()
    token = sh.get_token()
    import requests
    r = requests.post(
        "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "collections": ["sentinel-2-l2a"],
            "bbox": list(BBOX_WGS84),
            "datetime": f"{date_from}T00:00:00Z/{date_to}T23:59:59Z",
            "filter": "eo:cloud_cover < 30",
            "filter-lang": "cql2-text",
            "limit": 10,
        },
        timeout=60,
    )
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        return None
    # Pick lowest cloud
    feats.sort(key=lambda f: f["properties"].get("eo:cloud_cover", 100))
    return feats[0]


def fetch_timeseries():
    """Pull 5-year NDVI time series via Statistical API."""
    today = datetime.utcnow().date()
    date_to = today.isoformat()
    date_from = (today.replace(year=today.year - 5)).isoformat()
    print(f"Fetching NDVI time series {date_from} → {date_to}")

    payload = sh.build_statistics_payload(
        bbox_wgs84=BBOX_WGS84,
        date_from=date_from,
        date_to=date_to,
        aggregation_interval_days=10,  # roughly every 10 days
    )
    result = sh.statistics(payload)

    # Result format: { "data": [ { "interval": {...}, "outputs": { "ndvi": { "bands": { "B0": { "stats": {...}, "histogram": {...} } } } } }, ...] }
    points = []
    for entry in result.get("data", []):
        try:
            iv = entry["interval"]
            day = iv["from"][:10]
            stats = entry["outputs"]["ndvi"]["bands"]["B0"]["stats"]
            mean = stats.get("mean")
            if mean is None or (isinstance(mean, float) and (mean != mean)):  # NaN check
                continue
            p5 = stats.get("percentiles", {}).get("5.0")
            p50 = stats.get("percentiles", {}).get("50.0")
            p95 = stats.get("percentiles", {}).get("95.0")
            sample_count = stats.get("sampleCount", 0)
            no_data = stats.get("noDataCount", 0)
            valid_ratio = (sample_count - no_data) / sample_count if sample_count else 0
            if valid_ratio < 0.3:  # skip mostly-cloud periods
                continue
            points.append({
                "date": day,
                "mean": round(mean, 4),
                "p5": round(p5, 4) if p5 is not None else None,
                "p50": round(p50, 4) if p50 is not None else None,
                "p95": round(p95, 4) if p95 is not None else None,
                "valid_ratio": round(valid_ratio, 3),
            })
        except (KeyError, TypeError):
            continue

    points.sort(key=lambda p: p["date"])
    print(f"  {len(points)} valid time points")
    return points


def main():
    # 1. Process API: get colored NDVI PNG (latest low-cloud composite)
    fetch_latest_ndvi_png()

    # 2. Catalog API: identify which scene we got, for the on-map metadata stamp
    scene = fetch_scene_metadata()
    scene_info = None
    if scene:
        props = scene.get("properties", {})
        scene_info = {
            "scene_id": scene.get("id"),
            "datetime": props.get("datetime"),
            "platform": props.get("platform"),
            "cloud_cover": props.get("eo:cloud_cover"),
            "mgrs_tile": props.get("mgrs:tile") or props.get("s2:mgrs_tile"),
        }
        print(f"  scene picked: {scene_info['scene_id']}  cloud={scene_info['cloud_cover']:.1f}%")

    # 3. Statistical API: time series for the chart
    series = fetch_timeseries()

    # 4. Assemble metadata
    meta = {
        "source": "CDSE Sentinel Hub Process API",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "bbox_wgs84": list(BBOX_WGS84),
        "leaflet_bounds": [
            [BBOX_WGS84[1], BBOX_WGS84[0]],
            [BBOX_WGS84[3], BBOX_WGS84[2]],
        ],
        "scene": scene_info,
        "timeseries_points": len(series),
        "evalscript": "NDVI with SCL cloud mask + brand palette",
    }
    (OUT_DIR / "himi_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (OUT_DIR / "himi_timeseries.json").write_text(json.dumps({
        "source": "CDSE Sentinel Hub Statistical API",
        "aoi": "氷見市 朝日山系周辺 16km × 14km",
        "interval_days": 10,
        "points": series,
    }, ensure_ascii=False, indent=2))
    print(f"\nWrote meta + time series ({len(series)} points)")


if __name__ == "__main__":
    main()
