#!/usr/bin/env python3
"""
Download all 47 prefecture A10 ZIPs (国土数値情報 自然公園地域 2015年度版),
combine into a single simplified GeoJSON.

Source: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A10-2015.html
License: CC-BY 4.0 (商用OK)。岡山県(33)のみ非商用なので除外。
Layer codes: 11=国立公園、12=国定公園、13=都道府県立自然公園
"""
import io
import json
import re
import zipfile
from pathlib import Path

import fiona
import requests
from shapely.geometry import shape, mapping

BASE = "https://nlftp.mlit.go.jp/ksj/gml/data/A10/A10-15"
HEADERS = {"User-Agent": "Mozilla/5.0",
           "Referer": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A10-2015.html"}

PREF_NAMES = {
    1: "北海道", 2: "青森県", 3: "岩手県", 4: "宮城県", 5: "秋田県",
    6: "山形県", 7: "福島県", 8: "茨城県", 9: "栃木県", 10: "群馬県",
    11: "埼玉県", 12: "千葉県", 13: "東京都", 14: "神奈川県", 15: "新潟県",
    16: "富山県", 17: "石川県", 18: "福井県", 19: "山梨県", 20: "長野県",
    21: "岐阜県", 22: "静岡県", 23: "愛知県", 24: "三重県", 25: "滋賀県",
    26: "京都府", 27: "大阪府", 28: "兵庫県", 29: "奈良県", 30: "和歌山県",
    31: "鳥取県", 32: "島根県", 33: "岡山県", 34: "広島県", 35: "山口県",
    36: "徳島県", 37: "香川県", 38: "愛媛県", 39: "高知県", 40: "福岡県",
    41: "佐賀県", 42: "長崎県", 43: "熊本県", 44: "大分県", 45: "宮崎県",
    46: "鹿児島県", 47: "沖縄県",
}

LAYER_NAMES = {11: "国立公園", 12: "国定公園", 13: "都道府県立自然公園"}

PARK_TYPE_RE = re.compile(r"_(\d{4})(\d{2})(\d{2})\.shp$")  # ...160211.shp → 11

OUT = Path(__file__).parent.parent / "data" / "protected" / "japan_natural_parks.geojson"
OUT.parent.mkdir(parents=True, exist_ok=True)


def fetch_pref(pref_code):
    """Download one prefecture ZIP, return (mem_zip)."""
    url = f"{BASE}/A10-15_{pref_code:02d}_GML.zip"
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code != 200 or r.headers.get("Content-Type", "").startswith("text/html"):
        return None
    return io.BytesIO(r.content)


def features_from_zip(memzip, pref_code):
    """Extract all shapefile features (combined across the 3 layer-files in a ZIP)."""
    with zipfile.ZipFile(memzip) as zf:
        # Group files by basename
        basenames = set()
        for name in zf.namelist():
            if name.endswith(".shp"):
                basenames.add(name[:-4])

        # Extract to a temp dir
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            zf.extractall(td)

            features = []
            for bn in basenames:
                shp = Path(td) / f"{bn}.shp"
                if not shp.exists():
                    continue
                # layer code from filename suffix (last 2 digits before .shp)
                m = re.search(r"(\d{2})$", bn)
                layer_code = int(m.group(1)) if m else 0
                layer_name = LAYER_NAMES.get(layer_code, f"L{layer_code}")

                try:
                    src = fiona.open(shp, encoding="shift_jis")
                except Exception:
                    src = fiona.open(shp)
                with src as features_src:
                    for f in features_src:
                        try:
                            geom = shape(f["geometry"])
                            if geom.is_empty:
                                continue
                            geom = geom.simplify(0.005, preserve_topology=True)  # ~500m, web map detail
                            if geom.is_empty:
                                continue
                            props = f["properties"]
                            features.append({
                                "type": "Feature",
                                "geometry": mapping(geom),
                                "properties": {
                                    "park_type": layer_name,
                                    "pref_code": pref_code,
                                    "prefecture": PREF_NAMES[pref_code],
                                    "name_raw": props.get("CTV_NAME", ""),
                                    "area_size": props.get("AREA_SIZE"),
                                    "obj_id": props.get("OBJECTID"),
                                },
                            })
                        except Exception:
                            continue
            return features


def main():
    all_features = []
    for code in range(1, 48):
        print(f"  pref {code:02d} {PREF_NAMES[code]}...", end="", flush=True)
        mz = fetch_pref(code)
        if not mz:
            print(" (skipped - download failed)")
            continue
        try:
            feats = features_from_zip(mz, code)
            print(f" {len(feats):4d} polygons")
            all_features.extend(feats)
        except Exception as e:
            print(f" error: {e}")

    print(f"\nTotal features: {len(all_features)}")

    # Drop tiny sub-polygons (< 50,000 m² ≈ 5 ha) — too small for web display
    # Keep large coherent park shapes. This dramatically shrinks the file.
    import math
    big = []
    for f in all_features:
        geom = shape(f["geometry"])
        # Rough area in m² (degrees → m at lat ~36)
        area_m2 = geom.area * (111000 ** 2) * math.cos(math.radians(36))
        if area_m2 >= 50000:
            big.append(f)
    print(f"After area filter (>= 5 ha): {len(big)} (was {len(all_features)})")

    out = {
        "type": "FeatureCollection",
        "source": "国土数値情報 A10 自然公園地域 2015年度版 (国土交通省)",
        "license": "CC-BY 4.0",
        "license_note": "岡山県(33)のみ非商用",
        "features": big,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    size_kb = OUT.stat().st_size / 1024
    print(f"\nWrote: {OUT} ({size_kb:.0f} KB)")

    # Per-type breakdown
    type_counts = {}
    for f in all_features:
        t = f["properties"]["park_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, n in sorted(type_counts.items()):
        print(f"  {t}: {n}")


if __name__ == "__main__":
    main()
