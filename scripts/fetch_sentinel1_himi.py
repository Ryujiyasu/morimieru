#!/usr/bin/env python3
"""
Fetch Sentinel-1 SAR (C-band) imagery for the Himi AOI via CDSE.
Sentinel-1 advantages over Sentinel-2:
- Penetrates clouds (no observation gap from weather)
- VH cross-polarization correlates with forest biomass / canopy structure
- Detects forest disturbance (clear-cuts visible immediately)
- 6-12 day revisit, all-weather all-season

Output:
- data/sentinel/himi_sar.png (colorized VH backscatter map)
- data/sentinel/himi_sar_meta.json
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sh_client as sh

HIMI_LAT = 36.857
HIMI_LON = 136.987
LAT_PAD = 0.07
LON_PAD = 0.09
BBOX = (HIMI_LON - LON_PAD, HIMI_LAT - LAT_PAD, HIMI_LON + LON_PAD, HIMI_LAT + LAT_PAD)

OUT_DIR = Path(__file__).parent.parent / "data" / "sentinel"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Evalscript: colorize VH backscatter (dB) for biomass indication
# VH is more sensitive to forest biomass / canopy structure than VV
EVALSCRIPT_SAR = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["VV", "VH"] }],
    output: { bands: 4, sampleType: "UINT8" }
  };
}
function evaluatePixel(s) {
  if (s.VV === 0 && s.VH === 0) return [0, 0, 0, 0];
  // dB conversion
  const vh_db = 10 * Math.log10(s.VH);
  // VH ranges typically:
  //   bare ground / urban / water: < -18 dB
  //   sparse vegetation / cleared:  -18 to -14 dB
  //   moderate forest:              -14 to -11 dB
  //   dense forest / closed canopy: > -11 dB
  if (vh_db < -22) return [0, 0, 0, 0];               // no data
  if (vh_db < -18) return [230, 200, 160, 230];       // earth/bare (mori-mieru palette)
  if (vh_db < -14) return [167, 196, 152, 235];       // sparse
  if (vh_db < -11) return [ 90, 138,  58, 245];       // moderate
  return                  [ 45,  90,  61, 250];        // dense forest
}
"""


def find_best_sar_scene():
    """Find a recent Sentinel-1 GRD scene over Himi."""
    token = sh.get_token()
    import requests
    today = datetime.now(timezone.utc).date()
    date_to = today.isoformat()
    date_from = (today - timedelta(days=60)).isoformat()
    r = requests.post(
        "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "collections": ["sentinel-1-grd"],
            "bbox": list(BBOX),
            "datetime": f"{date_from}T00:00:00Z/{date_to}T23:59:59Z",
            "limit": 5,
        },
        timeout=60,
    )
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        return None
    # Prefer most recent
    feats.sort(key=lambda f: f["properties"].get("datetime", ""), reverse=True)
    return feats[0]


def fetch_sar_png():
    """Process API: VH-based colorized biomass map of Himi."""
    today = datetime.now(timezone.utc).date()
    date_to = today.isoformat()
    date_from = (today - timedelta(days=60)).isoformat()

    payload = {
        "input": {
            "bounds": {
                "bbox": list(BBOX),
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-1-grd",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{date_from}T00:00:00Z",
                        "to": f"{date_to}T23:59:59Z",
                    },
                    "mosaickingOrder": "mostRecent",
                    "polarization": "DV",  # VV + VH
                },
                "processing": {
                    "backCoeff": "GAMMA0_TERRAIN",
                    "demInstance": "COPERNICUS_30",
                    "orthorectify": True,
                },
            }],
        },
        "output": {
            "width": 1600,
            "height": 1400,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/png"},
            }],
        },
        "evalscript": EVALSCRIPT_SAR,
    }
    png = sh.process(payload, accept="image/png")
    out = OUT_DIR / "himi_sar.png"
    out.write_bytes(png)
    print(f"  wrote {out}  ({len(png)//1024} KB)")
    return out


def main():
    print("===== Sentinel-1 SAR for Himi =====")
    scene = find_best_sar_scene()
    if scene:
        props = scene["properties"]
        print(f"Latest scene: {scene.get('id')}")
        print(f"  Datetime: {props.get('datetime')}")
        print(f"  Platform: {props.get('platform')}")
        print(f"  Orbit direction: {props.get('sat:orbit_state')}")

    fetch_sar_png()

    meta = {
        "source": "Sentinel-1 GRD (C-band SAR) via CDSE Sentinel Hub Process API",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "bbox_wgs84": list(BBOX),
        "leaflet_bounds": [
            [BBOX[1], BBOX[0]],
            [BBOX[3], BBOX[2]],
        ],
        "scene": {
            "id": scene.get("id") if scene else None,
            "datetime": scene["properties"].get("datetime") if scene else None,
            "platform": scene["properties"].get("platform") if scene else None,
            "orbit_state": scene["properties"].get("sat:orbit_state") if scene else None,
        } if scene else None,
        "polarization": "VH (cross-pol, sensitive to forest biomass)",
        "processing": "Gamma0 terrain-corrected, orthorectified to Copernicus DEM 30m",
        "color_classes": [
            {"class": "bare/水", "vh_db_range": "< -18", "color": "#e6c8a0"},
            {"class": "疎な植生", "vh_db_range": "-18 to -14", "color": "#a7c498"},
            {"class": "中程度の森林", "vh_db_range": "-14 to -11", "color": "#5a8a3a"},
            {"class": "密な森林", "vh_db_range": "> -11", "color": "#2d5a3d"},
        ],
    }
    (OUT_DIR / "himi_sar_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\n  wrote {OUT_DIR / 'himi_sar_meta.json'}")


if __name__ == "__main__":
    main()
