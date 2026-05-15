#!/usr/bin/env python3
"""
日本全国の山頂を OSM (Overpass) から取得し、各山に「公益機能トータルスコア」を付与する。

入力:
- /tmp/osm_peaks_japan.json (Overpass API の出力: natural=peak + name フィルタ)
- data/co2/japan_prefectures_timeseries.geojson (都道府県 CO2/forest_pct)
- data/protected/japan_natural_parks.geojson (自然公園ポリゴン)

スコア設計:
  total = round( (co2_score + water_score + bio_score) / 3, 1 )

  co2_score   : 所属都道府県の (CO2/ha)/年 を全国 min-max で 0-100 にスケール
  water_score : 所属都道府県の forest_pct × 100  (森林率が水源涵養の最大代理指標)
  bio_score   : 自然公園内なら +30 / 隣接 5km 以内 +15 / それ以外 0
                さらに 標高 (1500m 以上はピーク無人化代理で +20、1000-1500m +10)
                クリップ 0-100

出力: data/mountains/japan_peaks.geojson (Point feature collection)
"""
import json
import math
from pathlib import Path

from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = Path(__file__).parent.parent
INPUT = Path("/tmp/osm_peaks_japan.json")
PREF_FILE = ROOT / "data" / "co2" / "japan_prefectures_timeseries.geojson"
PARKS_FILE = ROOT / "data" / "protected" / "japan_natural_parks.geojson"
OUT = ROOT / "data" / "mountains" / "japan_peaks.geojson"
OUT.parent.mkdir(parents=True, exist_ok=True)


def load_prefs():
    """{pref_id: {name_ja, co2_per_ha_yr, forest_pct, geom}}"""
    src = json.loads(PREF_FILE.read_text())
    prefs = {}
    for f in src["features"]:
        p = f["properties"]
        yearly = p.get("yearly", {})
        if not yearly:
            continue
        co2_per_ha_list = [(v["co2_t"] / p["pref_area_ha"]) for v in yearly.values() if v.get("co2_t")]
        fc_list = [v["forest_pct"] for v in yearly.values() if v.get("forest_pct") is not None]
        if not co2_per_ha_list:
            continue
        co2_per_ha = sum(co2_per_ha_list) / len(co2_per_ha_list)
        forest_pct = sum(fc_list) / len(fc_list) if fc_list else 0
        prefs[p["pref_id"]] = {
            "name": p["name_ja"],
            "pref_id": p["pref_id"],
            "co2_per_ha_yr": co2_per_ha,
            "forest_pct": forest_pct,
            "geom": shape(f["geometry"]),
        }
    return prefs


def load_parks():
    src = json.loads(PARKS_FILE.read_text())
    feats = []
    for f in src["features"]:
        try:
            g = shape(f["geometry"])
            if not g.is_valid:
                g = g.buffer(0)
            feats.append((g, f["properties"]))
        except Exception:
            continue
    return feats


def main():
    raw = json.loads(INPUT.read_text())
    nodes = raw["elements"]
    print(f"OSM peaks (raw): {len(nodes)}")

    prefs = load_prefs()
    print(f"Prefectures with data: {len(prefs)}")

    pref_geoms = [p["geom"] for p in prefs.values()]
    pref_ids = list(prefs.keys())
    pref_tree = STRtree(pref_geoms)

    parks = load_parks()
    print(f"Natural park polygons: {len(parks)}")
    park_geoms = [g for g, _ in parks]
    park_tree = STRtree(park_geoms)

    # Compute min/max CO2 for scaling
    co2_vals = [p["co2_per_ha_yr"] for p in prefs.values()]
    co2_min, co2_max = min(co2_vals), max(co2_vals)

    def lookup_pref(lon, lat):
        pt = Point(lon, lat)
        for idx in pref_tree.query(pt):
            geom = pref_geoms[idx]
            if geom.contains(pt) or geom.intersects(pt):
                return prefs[pref_ids[idx]]
        # If not in polygon (off-shore peak?), pick nearest
        if not pref_geoms:
            return None
        idx = min(range(len(pref_geoms)), key=lambda i: pref_geoms[i].distance(pt))
        return prefs[pref_ids[idx]]

    def park_info(lon, lat):
        pt = Point(lon, lat)
        # Inside?
        for idx in park_tree.query(pt):
            g = park_geoms[idx]
            if g.contains(pt) or g.intersects(pt):
                return parks[idx][1], 0
        # Within ~5km?
        buf = pt.buffer(0.05)  # ~5km at lat 35
        for idx in park_tree.query(buf):
            g = park_geoms[idx]
            d_deg = g.distance(pt)
            if d_deg < 0.05:
                return parks[idx][1], round(d_deg * 111, 1)
        return None, None

    out_features = []
    counted = 0
    skipped_no_pref = 0
    for el in nodes:
        tags = el.get("tags", {})
        name_ja = tags.get("name:ja") or tags.get("name") or ""
        if not name_ja:
            continue
        ele_raw = tags.get("ele")
        try:
            ele = float(ele_raw) if ele_raw is not None else None
        except (ValueError, TypeError):
            ele = None
        lon, lat = el.get("lon"), el.get("lat")
        if lon is None or lat is None:
            continue

        pref = lookup_pref(lon, lat)
        if pref is None:
            skipped_no_pref += 1
            continue

        # ---- score components ----
        # CO2 (min-max scaled)
        co2_score = (pref["co2_per_ha_yr"] - co2_min) / (co2_max - co2_min) * 100 if co2_max > co2_min else 50

        # Water = forest_pct as %
        water_score = pref["forest_pct"] * 100

        # Bio: park + elevation
        park_p, park_d = park_info(lon, lat)
        bio = 0
        if park_p is not None:
            bio = 30 if park_d == 0 else 15
        if ele is not None:
            if ele >= 1500:
                bio += 20
            elif ele >= 1000:
                bio += 10
            elif ele >= 500:
                bio += 5
        bio_score = max(0, min(100, bio + 30))  # base 30 for being a named peak

        total = round((co2_score + water_score + bio_score) / 3, 1)

        props = {
            "name": name_ja,
            "name_en": tags.get("name:en") or "",
            "name_kana": tags.get("name:ja_kana") or tags.get("name:ja_rm") or "",
            "elevation_m": round(ele, 1) if ele is not None else None,
            "pref_id": pref["pref_id"],
            "pref_name": pref["name"],
            "scores": {
                "total": total,
                "co2": round(co2_score, 1),
                "water": round(water_score, 1),
                "bio": round(bio_score, 1),
            },
            "co2_per_ha_yr": round(pref["co2_per_ha_yr"], 2),
            "forest_pct": round(pref["forest_pct"], 3),
            "in_park": park_p.get("park_type") if park_p and park_d == 0 else None,
            "nearby_park": park_p.get("park_type") if park_p and park_d and park_d > 0 else None,
            "park_distance_km": park_d if park_d and park_d > 0 else None,
            "wikipedia": tags.get("wikipedia") or "",
        }

        out_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })
        counted += 1

    print(f"Output peaks: {counted} (skipped no-pref: {skipped_no_pref})")

    out = {
        "type": "FeatureCollection",
        "source": "OSM (natural=peak, name required) × もりみえる 公益機能スコア",
        "score_method": "total = mean(co2_score, water_score, bio_score) — 0-100 scale",
        "scaling": {
            "co2_min_t_per_ha_yr": round(co2_min, 2),
            "co2_max_t_per_ha_yr": round(co2_max, 2),
        },
        "computed_at": "2026-05-15",
        "count": counted,
        "features": out_features,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"Wrote: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
