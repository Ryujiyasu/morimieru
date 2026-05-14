#!/usr/bin/env python3
"""
Fetch Shizuoka prefecture forest stand (林班) polygons from the prefecture's
公開システム vector tile endpoint.

Endpoint: https://fcloud.pref.shizuoka.jp/MAP/MVT/MAGIS.RINPAN/{z}/{x}/{y}.pbf
Tile format: Mapbox Vector Tile (protobuf)
Attributes per feature: ID, KEYRIN, 市町村CD, 林班, SHAPE_AREA (m²), SHAPE_LEN (m)

Strategy:
- Iterate tiles at z=12 covering Shizuoka prefecture (34.6-35.5°N, 137.4-139.2°E)
- Decode each tile, convert local tile coords → WGS84 lon/lat
- Deduplicate features by ID
- Output single GeoJSON with all 林班 polygons
"""
import json
import math
from pathlib import Path

import requests
import mapbox_vector_tile
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

OUT_PATH = Path(__file__).parent.parent / "data" / "rinpan" / "shizuoka_rinpan.geojson"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

TILE_URL = "https://fcloud.pref.shizuoka.jp/MAP/MVT/MAGIS.RINPAN/{z}/{x}/{y}.pbf"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fcloud.pref.shizuoka.jp/fgis/",
}

# Shizuoka bbox (approximate)
SHIZUOKA_BBOX = (137.40, 34.60, 139.20, 35.65)
ZOOM = 12  # at z=12, ~4 km/tile - good balance of detail vs request count


def lon_to_tile_x(lon, z):
    return int((lon + 180.0) / 360.0 * (1 << z))


def lat_to_tile_y(lat, z):
    lat_rad = math.radians(lat)
    return int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * (1 << z))


def tile_x_to_lon(x, z):
    return x / (1 << z) * 360.0 - 180.0


def tile_y_to_lat(y, z):
    n = math.pi - 2.0 * math.pi * y / (1 << z)
    return math.degrees(math.atan(math.sinh(n)))


def local_coords_to_lonlat(coords, x_tile, y_tile, z, extent):
    """Convert MVT local coords (origin top-left, y down, range 0..extent) to lon/lat."""
    lon_w = tile_x_to_lon(x_tile, z)
    lon_e = tile_x_to_lon(x_tile + 1, z)
    lat_n = tile_y_to_lat(y_tile, z)
    lat_s = tile_y_to_lat(y_tile + 1, z)

    def transform_point(pt):
        px, py = pt
        # Note: MVT default y axis is top-down (y=0 at top)
        # mapbox-vector-tile lib already flips y, so y=0 at bottom
        lon = lon_w + (px / extent) * (lon_e - lon_w)
        lat = lat_s + (py / extent) * (lat_n - lat_s)
        return [lon, lat]

    def walk(c):
        if not c:
            return c
        if isinstance(c[0], (int, float)):
            return transform_point(c)
        return [walk(sub) for sub in c]

    return walk(coords)


def fetch_tile(z, x, y):
    url = TILE_URL.format(z=z, x=x, y=y)
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200 or not r.content or r.content[:5] == b"<!DOC":
        return None
    return r.content


def features_from_tile(pbf, x, y, z):
    """Decode tile, return list of GeoJSON features in WGS84."""
    try:
        decoded = mapbox_vector_tile.decode(pbf)
    except Exception:
        return []
    out = []
    for layer_name, layer in decoded.items():
        if not layer_name.endswith("RINPAN"):
            continue
        extent = layer.get("extent", 4096)
        for feat in layer.get("features", []):
            geom = feat.get("geometry") or {}
            gtype = geom.get("type")
            coords = geom.get("coordinates")
            if not gtype or not coords:
                continue
            transformed = local_coords_to_lonlat(coords, x, y, z, extent)
            new_geom = {"type": gtype, "coordinates": transformed}
            try:
                sh = shape(new_geom)
                if sh.is_empty:
                    continue
            except Exception:
                continue
            out.append({
                "type": "Feature",
                "geometry": mapping(sh),
                "properties": feat.get("properties", {}),
            })
    return out


def main():
    x_min = lon_to_tile_x(SHIZUOKA_BBOX[0], ZOOM)
    x_max = lon_to_tile_x(SHIZUOKA_BBOX[2], ZOOM)
    y_min = lat_to_tile_y(SHIZUOKA_BBOX[3], ZOOM)  # top
    y_max = lat_to_tile_y(SHIZUOKA_BBOX[1], ZOOM)  # bottom
    print(f"Tile grid at z={ZOOM}: x [{x_min}, {x_max}], y [{y_min}, {y_max}]")
    print(f"Total tiles to fetch: {(x_max - x_min + 1) * (y_max - y_min + 1)}")

    seen_ids = set()
    all_features = []
    empty_tiles = 0
    nonempty_tiles = 0
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            pbf = fetch_tile(ZOOM, x, y)
            if pbf is None:
                continue
            feats = features_from_tile(pbf, x, y, ZOOM)
            if not feats:
                empty_tiles += 1
                continue
            nonempty_tiles += 1
            for f in feats:
                fid = f["properties"].get("ID")
                if fid and fid in seen_ids:
                    continue
                if fid:
                    seen_ids.add(fid)
                all_features.append(f)
        print(f"  x={x}: total features so far: {len(all_features)}")

    print(f"\nNon-empty tiles: {nonempty_tiles}, empty: {empty_tiles}")
    print(f"Total unique 林班 polygons: {len(all_features)}")

    # Area stats
    if all_features:
        areas = [f["properties"].get("SHAPE_AREA", 0) / 10000 for f in all_features]
        areas_valid = [a for a in areas if a > 0]
        if areas_valid:
            print(f"Stand area stats (ha):")
            print(f"  Total: {sum(areas_valid):,.0f}")
            print(f"  Mean: {sum(areas_valid)/len(areas_valid):.1f}")
            print(f"  Min: {min(areas_valid):.1f}, Max: {max(areas_valid):.1f}")
            big = [a for a in areas_valid if a > 100]
            print(f"  > 100 ha: {len(big)} stands")
            small = [a for a in areas_valid if a < 100]
            print(f"  < 100 ha: {len(small)} stands")

    out = {
        "type": "FeatureCollection",
        "source": "静岡県森林クラウド公開システム (MAGIS.RINPAN ベクトルタイル)",
        "endpoint": TILE_URL,
        "fetched_at": "2026-05-14",
        "license": "静岡県オープンデータ（公開システム経由）",
        "features": all_features,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False))
    size_mb = OUT_PATH.stat().st_size / 1024 / 1024
    print(f"\nWrote: {OUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
