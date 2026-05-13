#!/usr/bin/env python3
"""
Fetch a recent low-cloud Sentinel-2 L2A scene covering Himi-shi (氷見市),
compute NDVI for a ~20km window, output a PNG overlay + metadata JSON
ready for Leaflet L.imageOverlay.

Data: AWS public sentinel-cogs bucket via Earth Search STAC API.
"""
import json
import os
from pathlib import Path
from datetime import datetime

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from pystac_client import Client
from PIL import Image

# ----- Config -----
HIMI_LAT = 36.857
HIMI_LON = 136.987
# bbox ~ ±0.08 deg ≈ ±8km, sized to fit within one MGRS tile
BBOX_WGS84 = (HIMI_LON - 0.08, HIMI_LAT - 0.07, HIMI_LON + 0.08, HIMI_LAT + 0.07)

STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"

OUT_DIR = Path(__file__).parent.parent / "data" / "sentinel"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_best_scene():
    """Find a recent low-cloud scene that fully contains Himi's bbox."""
    print(f"Querying STAC: {STAC_URL}")
    catalog = Client.open(STAC_URL)

    # Search by intersects=point so we only get scenes that contain Himi
    point = {"type": "Point", "coordinates": [HIMI_LON, HIMI_LAT]}
    search = catalog.search(
        collections=[COLLECTION],
        intersects=point,
        datetime="2025-11-01/2026-05-13",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=50,
    )
    items = list(search.items())
    print(f"Found {len(items)} scenes containing Himi with cloud<30%")
    if not items:
        search = catalog.search(
            collections=[COLLECTION],
            intersects=point,
            datetime="2025-01-01/2026-05-13",
            query={"eo:cloud_cover": {"lt": 60}},
            limit=50,
        )
        items = list(search.items())
        print(f"Relaxed: found {len(items)} scenes with cloud<60%")

    # Pick lowest cloud cover (most recent as tiebreaker)
    items.sort(key=lambda x: (x.properties.get("eo:cloud_cover", 100), -x.datetime.timestamp()))
    return items[0] if items else None


def read_window(href, bbox_wgs84):
    """Read a windowed slice of a COG covering the WGS84 bbox.
    Clips the window to the COG's bounds so we report the actual covered area."""
    with rasterio.open(href) as src:
        # transform bbox from WGS84 to source CRS
        bbox_src = transform_bounds("EPSG:4326", src.crs, *bbox_wgs84, densify_pts=21)
        # Intersect with the source's bounds
        src_bounds = src.bounds  # left, bottom, right, top in src CRS
        clipped = (
            max(bbox_src[0], src_bounds.left),
            max(bbox_src[1], src_bounds.bottom),
            min(bbox_src[2], src_bounds.right),
            min(bbox_src[3], src_bounds.top),
        )
        window = from_bounds(*clipped, transform=src.transform)
        data = src.read(1, window=window, boundless=False)
        win_transform = src.window_transform(window)
        return data, src.crs, win_transform, clipped


def main():
    item = find_best_scene()
    if not item:
        raise RuntimeError("No scene found")

    print(f"\nSelected scene: {item.id}")
    print(f"  Datetime: {item.datetime}")
    print(f"  Cloud cover: {item.properties.get('eo:cloud_cover'):.1f}%")
    print(f"  MGRS tile: {item.properties.get('mgrs:utm_zone', '?')}{item.properties.get('mgrs:latitude_band', '?')}{item.properties.get('mgrs:grid_square', '?')}")
    print(f"  Platform: {item.properties.get('platform')}")

    # Use VSI HTTP for direct read (no boto3 needed)
    os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
    os.environ["AWS_NO_SIGN_REQUEST"] = "YES"

    red_url = item.assets["red"].href
    nir_url = item.assets["nir"].href
    print(f"\nFetching red band:  {red_url}")
    print(f"Fetching NIR band:  {nir_url}")

    red, crs, transform_, bbox_src = read_window(red_url, BBOX_WGS84)
    nir, _, _, _ = read_window(nir_url, BBOX_WGS84)
    print(f"Window shape: {red.shape}, CRS: {crs}")

    # NDVI calculation
    red_f = red.astype(np.float32)
    nir_f = nir.astype(np.float32)
    # Scale: Sentinel-2 L2A reflectance is 0-10000, but Earth Search COG often already scaled
    if red_f.max() > 100:
        red_f /= 10000.0
        nir_f /= 10000.0

    denom = (nir_f + red_f)
    ndvi = np.where(denom > 0, (nir_f - red_f) / denom, np.nan)
    ndvi = np.clip(ndvi, -0.2, 1.0)

    # Stats
    valid = ~np.isnan(ndvi) & (ndvi > -0.1)
    print(f"NDVI stats — min: {np.nanmin(ndvi):.3f}, mean: {np.nanmean(ndvi[valid]):.3f}, max: {np.nanmax(ndvi):.3f}")
    print(f"Forest pixel ratio (NDVI>0.5): {(ndvi[valid] > 0.5).mean()*100:.1f}%")

    # ----- Colorize NDVI as PNG -----
    # Color ramp: -0.1 brown -> 0 cream -> 0.3 light green -> 0.7 forest green -> 1.0 dark green
    def colorize(v):
        v = np.where(np.isnan(v), -1, v)
        rgba = np.zeros((*v.shape, 4), dtype=np.uint8)
        # No data → transparent
        nodata = (v < -0.5)
        # Bare/water → light brown/cream
        bare = (v >= -0.5) & (v < 0.15)
        # Light vegetation → light green
        light = (v >= 0.15) & (v < 0.4)
        # Vegetation → green
        veg = (v >= 0.4) & (v < 0.65)
        # Dense forest → dark forest green
        forest = (v >= 0.65)

        # Bare (cream/tan)
        rgba[bare] = [230, 200, 160, 220]
        # Light vegetation (sage)
        rgba[light] = [167, 196, 152, 230]
        # Vegetation (green)
        rgba[veg] = [90, 138, 58, 240]
        # Forest (deep forest green)
        rgba[forest] = [45, 90, 61, 250]
        # No data → transparent
        rgba[nodata] = [0, 0, 0, 0]
        return rgba

    rgba = colorize(ndvi)
    img = Image.fromarray(rgba, mode="RGBA")
    png_path = OUT_DIR / "himi_ndvi.png"
    img.save(png_path, optimize=True)
    print(f"\nWrote: {png_path} ({png_path.stat().st_size // 1024} KB)")

    # Save a true-color PNG too (RGB composite)
    blue_url = item.assets["blue"].href
    green_url = item.assets["green"].href
    print(f"\nFetching RGB for true-color preview...")
    b, _, _, _ = read_window(blue_url, BBOX_WGS84)
    g, _, _, _ = read_window(green_url, BBOX_WGS84)
    rgb = np.stack([red, g, b], axis=-1).astype(np.float32)
    if rgb.max() > 100:
        rgb /= 10000.0
    # Stretch
    rgb = np.clip(rgb * 3.5, 0, 1)  # brighten
    rgb_uint8 = (rgb * 255).astype(np.uint8)
    Image.fromarray(rgb_uint8).save(OUT_DIR / "himi_rgb.png", optimize=True)
    print(f"Wrote: {OUT_DIR / 'himi_rgb.png'}")

    # ----- Metadata JSON for Leaflet -----
    # Compute the actual covered bbox in WGS84 from the source CRS clipped bounds
    actual_bbox_wgs84 = transform_bounds(crs, "EPSG:4326", *bbox_src, densify_pts=21)

    meta = {
        "scene_id": item.id,
        "datetime": item.datetime.isoformat(),
        "platform": item.properties.get("platform"),
        "cloud_cover": item.properties.get("eo:cloud_cover"),
        "mgrs_tile": f"T{item.properties.get('mgrs:utm_zone', '?')}{item.properties.get('mgrs:latitude_band', '?')}{item.properties.get('mgrs:grid_square', '?')}",
        "bbox_wgs84": list(actual_bbox_wgs84),  # [west, south, east, north]
        "leaflet_bounds": [
            [actual_bbox_wgs84[1], actual_bbox_wgs84[0]],
            [actual_bbox_wgs84[3], actual_bbox_wgs84[2]],
        ],
        "shape": list(red.shape),
        "stats": {
            "ndvi_mean": float(np.nanmean(ndvi[valid])) if valid.any() else None,
            "ndvi_max": float(np.nanmax(ndvi)) if valid.any() else None,
            "forest_pct": float((ndvi[valid] > 0.5).mean() * 100) if valid.any() else None,
        },
        "source": "Sentinel-2 L2A via AWS sentinel-cogs Open Data",
        "stac_item_url": item.self_href if hasattr(item, "self_href") else None,
    }
    with open(OUT_DIR / "himi_meta.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {OUT_DIR / 'himi_meta.json'}")
    print(f"\nDone. NDVI overlay covers: {actual_bbox_wgs84}")


if __name__ == "__main__":
    main()
