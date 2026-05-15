#!/usr/bin/env python3
"""
HydroBASINS Lvl 10 (7,941 流域) に「公益機能スコア」を付与する事前計算。

入力:
- data/watersheds/japan_lev10.geojson (HydroBASINS polygons)
- data/co2/japan_prefectures_timeseries.geojson (都道府県 CO2/forest_pct)
- data/protected/japan_natural_parks.geojson (自然公園ポリゴン)
- data/mountains/japan_peaks.geojson (スコア付き山頂)

スコア:
  total = round((co2 + water + bio)/3, 1)  # 0-100

  co2_score   = area-weighted prefecture CO2/ha → 全国 min-max
  water_score = area-weighted prefecture forest_pct × 100
  bio_score   = (park_overlap_pct × 60) + (peak_count_norm × 40)

出力: data/watersheds/japan_lev10_scored.geojson
   - 簡略化ジオメトリ (tolerance 0.005)
   - properties: scores, contained_peak_ids (max 10), main_pref, peak_count, max_elev_m
"""
import json
import math
from pathlib import Path

from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union

ROOT = Path(__file__).parent.parent
WS_FILE = ROOT / "data" / "watersheds" / "japan_lev10.geojson"
PREF_FILE = ROOT / "data" / "co2" / "japan_prefectures_timeseries.geojson"
PARKS_FILE = ROOT / "data" / "protected" / "japan_natural_parks.geojson"
PEAKS_FILE = ROOT / "data" / "mountains" / "japan_peaks.geojson"
OUT = ROOT / "data" / "watersheds" / "japan_lev10_scored.geojson"


def load_prefs():
    src = json.loads(PREF_FILE.read_text())
    prefs = []
    for f in src["features"]:
        p = f["properties"]
        yearly = p.get("yearly", {})
        if not yearly:
            continue
        co2_per_ha = sum(v["co2_t"] for v in yearly.values() if v.get("co2_t")) / len(yearly) / p["pref_area_ha"]
        forest_pct = sum(v["forest_pct"] for v in yearly.values() if v.get("forest_pct") is not None) / len(yearly)
        prefs.append({
            "pref_id": p["pref_id"],
            "name": p["name_ja"],
            "co2_per_ha_yr": co2_per_ha,
            "forest_pct": forest_pct,
            "geom": shape(f["geometry"]),
        })
    return prefs


def main():
    print("Loading inputs...")
    ws = json.loads(WS_FILE.read_text())
    prefs = load_prefs()
    print(f"  Watersheds: {len(ws['features'])}, prefectures: {len(prefs)}")

    parks_src = json.loads(PARKS_FILE.read_text())
    park_geoms = []
    for f in parks_src["features"]:
        try:
            g = shape(f["geometry"])
            if not g.is_valid:
                g = g.buffer(0)
            park_geoms.append(g)
        except Exception:
            continue
    park_tree = STRtree(park_geoms)
    print(f"  Parks: {len(park_geoms)}")

    peaks_src = json.loads(PEAKS_FILE.read_text())
    peak_pts = []
    peak_props = []
    for f in peaks_src["features"]:
        lon, lat = f["geometry"]["coordinates"]
        peak_pts.append(Point(lon, lat))
        peak_props.append(f["properties"])
    peak_tree = STRtree(peak_pts)
    print(f"  Peaks: {len(peak_pts)}")

    # CO2 min/max for scaling
    co2_vals = [p["co2_per_ha_yr"] for p in prefs]
    co2_min, co2_max = min(co2_vals), max(co2_vals)
    pref_tree = STRtree([p["geom"] for p in prefs])

    out_feats = []
    for i, f in enumerate(ws["features"]):
        if i % 500 == 0:
            print(f"  scoring {i}/{len(ws['features'])}...")
        wsh = shape(f["geometry"])
        if not wsh.is_valid:
            wsh = wsh.buffer(0)
        area = wsh.area  # in degrees² — used only as weight
        if area == 0:
            continue

        # ----- area-weighted prefecture CO2/water -----
        co2_acc, water_acc, area_acc = 0.0, 0.0, 0.0
        for pidx in pref_tree.query(wsh):
            pgeom = prefs[pidx]["geom"]
            inter = wsh.intersection(pgeom).area
            if inter <= 0:
                continue
            co2_acc += prefs[pidx]["co2_per_ha_yr"] * inter
            water_acc += prefs[pidx]["forest_pct"] * inter
            area_acc += inter
        if area_acc > 0:
            co2_per_ha = co2_acc / area_acc
            forest_pct = water_acc / area_acc
        else:
            co2_per_ha = (co2_min + co2_max) / 2
            forest_pct = 0
        co2_score = (co2_per_ha - co2_min) / (co2_max - co2_min) * 100 if co2_max > co2_min else 50
        water_score = forest_pct * 100

        # ----- main prefecture (largest intersection) -----
        main_pref_name = None
        main_pref_id = None
        biggest = 0
        for pidx in pref_tree.query(wsh):
            inter = wsh.intersection(prefs[pidx]["geom"]).area
            if inter > biggest:
                biggest = inter
                main_pref_name = prefs[pidx]["name"]
                main_pref_id = prefs[pidx]["pref_id"]

        # ----- park overlap pct -----
        park_inter_area = 0
        for park_idx in park_tree.query(wsh):
            try:
                pi = wsh.intersection(park_geoms[park_idx]).area
                park_inter_area += pi
            except Exception:
                continue
        park_overlap_pct = min(1.0, park_inter_area / area)

        # ----- peaks inside -----
        peaks_inside = []
        max_elev = None
        for peak_idx in peak_tree.query(wsh):
            if wsh.contains(peak_pts[peak_idx]):
                pp = peak_props[peak_idx]
                ele = pp.get("elevation_m")
                if ele is not None and (max_elev is None or ele > max_elev):
                    max_elev = ele
                peaks_inside.append({
                    "name": pp["name"],
                    "elevation_m": ele,
                    "score": pp["scores"]["total"],
                    "lat": peak_pts[peak_idx].y,
                    "lon": peak_pts[peak_idx].x,
                })
        peaks_inside.sort(key=lambda p: (p["score"] or 0), reverse=True)
        peak_count = len(peaks_inside)
        peak_count_norm = min(1.0, peak_count / 5)  # 5+ peaks → full marks

        bio_score = park_overlap_pct * 60 + peak_count_norm * 40
        bio_score = max(0, min(100, bio_score))

        total = round((co2_score + water_score + bio_score) / 3, 1)

        # Simplify geometry for web
        simp = wsh.simplify(0.005, preserve_topology=True)
        if simp.is_empty:
            simp = wsh

        props = {
            **f["properties"],
            "scores": {
                "total": total,
                "co2": round(co2_score, 1),
                "water": round(water_score, 1),
                "bio": round(bio_score, 1),
            },
            "co2_per_ha_yr": round(co2_per_ha, 2),
            "forest_pct": round(forest_pct, 3),
            "park_overlap_pct": round(park_overlap_pct * 100, 1),
            "main_pref_id": main_pref_id,
            "main_pref_name": main_pref_name,
            "peak_count": peak_count,
            "max_elev_m": max_elev,
            "top_peaks": peaks_inside[:8],
        }
        out_feats.append({
            "type": "Feature",
            "geometry": mapping(simp),
            "properties": props,
        })

    print("Writing output...")
    out = {
        "type": "FeatureCollection",
        "source": "HydroBASINS Lvl 10 × もりみえる 公益機能スコア",
        "score_method": "total = mean(co2 area-weighted pref, water forest_pct×100, bio (park%×60+peaks×40))",
        "computed_at": "2026-05-15",
        "count": len(out_feats),
        "features": out_feats,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"Wrote: {OUT} ({OUT.stat().st_size // 1024} KB, {len(out_feats)} basins)")


if __name__ == "__main__":
    main()
