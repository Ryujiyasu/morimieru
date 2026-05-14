#!/usr/bin/env python3
"""
Extract Japan watersheds from HydroBASINS level 8 Asia shapefile.
- License: HydroSHEDS CC-BY, commercial use OK
- Level 8 ≈ ~1000-3000 km² basins (one major river → one polygon)
- Output: data/watersheds/japan_lev08.geojson (simplified)
"""
import json
from pathlib import Path

import fiona
from shapely.geometry import shape, mapping, box
from shapely.ops import transform as shapely_transform

SHP_PATH = Path("/tmp/hybas_as/hybas_as_lev08_v1c.shp")
OUT_PATH = Path(__file__).parent.parent / "data" / "watersheds" / "japan_lev08.geojson"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Japan bounding box (with some margin for offshore islands)
JAPAN_BBOX = box(122.0, 24.0, 154.0, 46.0)


def main():
    with fiona.open(SHP_PATH) as src:
        print(f"Source CRS: {src.crs}")
        print(f"Total features: {len(src)}")
        print(f"Schema fields: {list(src.schema['properties'].keys())}")

        features = []
        for f in src:
            geom = shape(f["geometry"])
            if not JAPAN_BBOX.intersects(geom):
                continue
            # Clip to Japan bbox (drop offshore extensions)
            clipped = geom.intersection(JAPAN_BBOX)
            if clipped.is_empty:
                continue
            # Simplify ~0.01 deg (~1km) for compact GeoJSON — enough for Leaflet zoom 7-10
            simplified = clipped.simplify(0.01, preserve_topology=True)
            if simplified.is_empty:
                continue
            features.append({
                "type": "Feature",
                "geometry": mapping(simplified),
                "properties": {
                    "hybas_id": int(f["properties"]["HYBAS_ID"]),
                    "next_down": int(f["properties"]["NEXT_DOWN"]),
                    "next_sink": int(f["properties"]["NEXT_SINK"]),
                    "area_sqkm": round(f["properties"]["SUB_AREA"], 2),
                    "up_area_sqkm": round(f["properties"]["UP_AREA"], 2),
                },
            })
    print(f"Japan basins: {len(features)}")

    out = {
        "type": "FeatureCollection",
        "source": "HydroSHEDS HydroBASINS v1c level 8 (CC-BY)",
        "features": features,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False))
    print(f"Wrote: {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
