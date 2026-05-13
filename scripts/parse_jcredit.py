#!/usr/bin/env python3
"""
Parse J-credit forest projects from japancredit.go.jp.
Geocode by extracting prefecture/municipality from the location string,
add slight jitter so projects don't overlap on the map.
Output: data/jcredit_projects.json
"""
import json
import re
import random
from pathlib import Path
from bs4 import BeautifulSoup

random.seed(42)

# Approximate prefecture centroids (Japanese prefectures)
PREF_CENTROIDS = {
    "北海道": (43.064, 141.347), "青森県": (40.824, 140.740), "岩手県": (39.704, 141.153),
    "宮城県": (38.269, 140.872), "秋田県": (39.719, 140.103), "山形県": (38.240, 140.364),
    "福島県": (37.750, 140.468), "茨城県": (36.342, 140.447), "栃木県": (36.566, 139.884),
    "群馬県": (36.391, 139.060), "埼玉県": (35.857, 139.649), "千葉県": (35.605, 140.123),
    "東京都": (35.690, 139.692), "神奈川県": (35.448, 139.643), "新潟県": (37.902, 139.024),
    "富山県": (36.695, 137.211), "石川県": (36.595, 136.626), "福井県": (36.065, 136.222),
    "山梨県": (35.664, 138.568), "長野県": (36.651, 138.181), "岐阜県": (35.391, 136.722),
    "静岡県": (34.977, 138.383), "愛知県": (35.180, 136.907), "三重県": (34.730, 136.509),
    "滋賀県": (35.005, 135.869), "京都府": (35.021, 135.756), "大阪府": (34.687, 135.520),
    "兵庫県": (34.691, 135.183), "奈良県": (34.685, 135.833), "和歌山県": (34.226, 135.168),
    "鳥取県": (35.504, 134.238), "島根県": (35.472, 133.051), "岡山県": (34.662, 133.935),
    "広島県": (34.397, 132.460), "山口県": (34.186, 131.471), "徳島県": (34.066, 134.560),
    "香川県": (34.340, 134.043), "愛媛県": (33.842, 132.766), "高知県": (33.560, 133.531),
    "福岡県": (33.607, 130.418), "佐賀県": (33.249, 130.299), "長崎県": (32.745, 129.874),
    "熊本県": (32.790, 130.742), "大分県": (33.238, 131.613), "宮崎県": (31.911, 131.424),
    "鹿児島県": (31.560, 130.558), "沖縄県": (26.213, 127.681),
}

PREF_RE = re.compile(r"^(北海道|東京都|京都府|大阪府|[^県]+県)")

def parse_html(html_path):
    soup = BeautifulSoup(Path(html_path).read_text(), "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        raise RuntimeError("expected 2 tables, got %d" % len(tables))

    rows = tables[1].find_all("tr")
    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]

    projects = []
    for tr in rows[1:]:
        cells = tr.find_all(["th", "td"])
        if len(cells) < len(headers):
            continue
        rec = {}
        for h, td in zip(headers, cells):
            rec[h] = td.get_text(" ", strip=True)
        projects.append(rec)
    return projects, headers


def geocode_prefecture(location):
    """Extract prefecture, return centroid lat/lon."""
    m = PREF_RE.match(location)
    if not m:
        return None, None, None
    pref = m.group(1)
    return PREF_CENTROIDS.get(pref, (None, None)), pref, location


def estimate_area_and_co2(project_summary, methodology):
    """Heuristic estimation since real area is in linked PDFs.
    Use a default range based on what's typical for J-credit forest projects."""
    # Typical FO-001 projects: 50-3000 ha, CO2 absorption 5-15 t-CO2/ha/year
    # We don't have the actual numbers but we can show a range
    return None  # leave as-is for now


def main():
    html_path = "/tmp/jcredit.html"
    out_path = Path(__file__).parent.parent / "data" / "jcredit_projects.json"

    projects, headers = parse_html(html_path)
    print(f"Parsed {len(projects)} projects")

    processed = []
    for p in projects:
        loc = p.get("プロジェクト実施場所", "")
        centroid, pref, full_loc = geocode_prefecture(loc)
        if not centroid or centroid[0] is None:
            continue

        # Add jitter so projects don't overlap visually (±0.5 degrees ≈ 50km)
        # Use project number as deterministic seed for stable positions
        proj_no = p.get("プロジェクト番号", "0")
        try:
            n = int(re.sub(r"\D", "", proj_no) or "0")
        except ValueError:
            n = 0
        rnd = random.Random(n)
        lat = centroid[0] + (rnd.random() - 0.5) * 1.0
        lon = centroid[1] + (rnd.random() - 0.5) * 1.0

        method = p.get("適用方法論", "")
        # Filter forest methodology only (FO-001, FO-003) - already filtered server-side but double-check
        if "FO-" not in method:
            continue

        processed.append({
            "no": p.get("プロジェクト番号", ""),
            "applied_at": p.get("登録申請日", ""),
            "operator": p.get("プロジェクト実施者・法人番号", ""),
            "location": loc,
            "prefecture": pref,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "credit_buyer": p.get("クレジット取得予定者・法人番号", ""),
            "summary": p.get("プロジェクト概要", ""),
            "started_at": p.get("認証期間の開始日", ""),
            "methodology": method,
        })

    print(f"Processed {len(processed)} projects with location")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "source": "J-クレジット制度 登録プロジェクト一覧",
            "source_url": "https://japancredit.go.jp/project/index.php?method=FO",
            "fetched_at": "2026-05-13",
            "total": len(processed),
            "methodology_summary": "FO-001（森林経営活動）+ FO-003（再造林活動）",
            "projects": processed,
        }, f, ensure_ascii=False, indent=2)

    print(f"Wrote: {out_path}")

    # Stats
    by_pref = {}
    by_method = {}
    for p in processed:
        by_pref[p["prefecture"]] = by_pref.get(p["prefecture"], 0) + 1
        m = p["methodology"].split(" ")[0] if p["methodology"] else "?"
        by_method[m] = by_method.get(m, 0) + 1
    print("\nBy methodology:", by_method)
    print("Top 10 prefectures:")
    for pref, cnt in sorted(by_pref.items(), key=lambda x: -x[1])[:10]:
        print(f"  {pref}: {cnt}")


if __name__ == "__main__":
    main()
