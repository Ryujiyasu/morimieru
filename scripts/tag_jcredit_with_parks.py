#!/usr/bin/env python3
"""
For each J-credit forest project, check if its location is inside / near a
natural park, and tag the JSON.

Inputs:
  - data/jcredit_projects.json (264 projects)
  - data/protected/japan_natural_parks.geojson (5065 polygons)

Output: updates data/jcredit_projects.json in-place with `park` field.
"""
import json
from pathlib import Path

from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = Path(__file__).parent.parent
JC_PATH = ROOT / "data" / "jcredit_projects.json"
PARKS_PATH = ROOT / "data" / "protected" / "japan_natural_parks.geojson"

# Park-type priority for the badge (国立公園 > 国定公園 > 都道府県立)
PARK_PRIORITY = {"国立公園": 3, "国定公園": 2, "都道府県立自然公園": 1}


def main():
    jc = json.loads(JC_PATH.read_text())
    parks_fc = json.loads(PARKS_PATH.read_text())

    geoms = []
    park_info = []
    for f in parks_fc["features"]:
        try:
            g = shape(f["geometry"])
            geoms.append(g)
            park_info.append(f["properties"])
        except Exception:
            continue
    print(f"Indexed {len(geoms)} park polygons")

    tree = STRtree(geoms)

    inside_count = 0
    nearby_count = 0
    for proj in jc["projects"]:
        pt = Point(proj["lon"], proj["lat"])
        # Direct containment
        candidates = tree.query(pt)
        in_park = None
        best_priority = -1
        for idx in candidates:
            g = geoms[idx]
            if g.contains(pt):
                p = park_info[idx]
                pri = PARK_PRIORITY.get(p["park_type"], 0)
                if pri > best_priority:
                    in_park = {
                        "park_type": p["park_type"],
                        "prefecture": p["prefecture"],
                    }
                    best_priority = pri

        if in_park:
            proj["park"] = in_park
            inside_count += 1
            continue

        # Nearby: within ~5km (0.05 deg) of a park boundary
        buffered = pt.buffer(0.05)
        candidates = tree.query(buffered)
        nearest_dist = None
        nearest_park = None
        for idx in candidates:
            g = geoms[idx]
            d = g.distance(pt)
            if nearest_dist is None or d < nearest_dist:
                nearest_dist = d
                nearest_park = park_info[idx]
        if nearest_park and nearest_dist is not None and nearest_dist <= 0.05:
            proj["park"] = {
                "park_type": nearest_park["park_type"],
                "prefecture": nearest_park["prefecture"],
                "nearby_km": round(nearest_dist * 111, 1),  # approx degrees → km
            }
            nearby_count += 1

    print(f"\nResults:")
    print(f"  Inside a park:      {inside_count} projects")
    print(f"  Near (<5km):        {nearby_count} projects")
    print(f"  No park association: {len(jc['projects']) - inside_count - nearby_count}")

    # Breakdown by park type
    by_type = {}
    for proj in jc["projects"]:
        if "park" in proj:
            t = proj["park"]["park_type"]
            by_type[t] = by_type.get(t, 0) + 1
    print(f"\nBy park type (inside + near):")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")

    # Re-write
    JC_PATH.write_text(json.dumps(jc, ensure_ascii=False, indent=2))
    print(f"\nUpdated: {JC_PATH}")


if __name__ == "__main__":
    main()
