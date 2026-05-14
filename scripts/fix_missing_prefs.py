#!/usr/bin/env python3
"""Re-run only the missing prefectures (北海道・東京・鹿児島・沖縄) with fixed bbox."""
import json
import time
from pathlib import Path
from shapely.geometry import shape, mapping

import sys
sys.path.insert(0, str(Path(__file__).parent))
from build_japan_co2_timeseries import (
    fetch_year, polygon_area_km2, CO2_PER_HA, YEARS, OUT,
)

INPUT = Path("/tmp/japan-pref.geojson")
TARGET_IDS = {1, 13, 46, 47}  # 北海道, 東京, 鹿児島, 沖縄

src = json.loads(INPUT.read_text())
current = json.loads(OUT.read_text())

# index by pref_id
by_id = {f["properties"]["pref_id"]: i for i, f in enumerate(current["features"])}

for f in src["features"]:
    pid = f["properties"]["id"]
    if pid not in TARGET_IDS:
        continue
    name = f["properties"]["nam_ja"]
    geom = shape(f["geometry"])
    pref_area_ha = round(polygon_area_km2(geom) * 100)
    print(f"\n{pid} {name} ({pref_area_ha:,} ha)")
    yearly = {}
    for year in YEARS:
        res = fetch_year(geom, year)
        if not res:
            print(f"  {year}: SKIP")
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
    # Update existing entry
    idx = by_id.get(pid)
    if idx is not None:
        current["features"][idx]["properties"]["yearly"] = yearly

OUT.write_text(json.dumps(current, ensure_ascii=False))
print(f"\nUpdated: {OUT}")
