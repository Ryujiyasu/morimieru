#!/usr/bin/env python3
"""
Generate the Shizuoka prefecture per-municipality forest report
from the per-rinpan water yield data.

Input: data/rinpan/shizuoka_rinpan_water.geojson
Output: report/shizuoka-forests.html
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
INPUT = ROOT / "data" / "rinpan" / "shizuoka_rinpan_water.geojson"
OUTPUT = ROOT / "report" / "shizuoka-forests.html"

# Tentative 静岡県市町村コード mapping (forest-clouds local codes 61-76)
# Note: these are heuristic — refine when actual mapping is found.
MUNI_NAMES = {
    "61": "市町村-61",
    "62": "市町村-62",
    "63": "市町村-63",
    "65": "市町村-65",
    "66": "市町村-66",
    "67": "市町村-67",
    "68": "市町村-68",
    "69": "市町村-69",
    "70": "市町村-70",
    "73": "市町村-73",
    "74": "市町村-74",
    "75": "市町村-75",
    "76": "市町村-76",
}


def fmt_num(n):
    return f"{n:,}"


def main():
    fc = json.loads(INPUT.read_text())
    feats = fc["features"]

    # Aggregate by municipality
    by_muni = defaultdict(lambda: {
        "stands": 0,
        "area_ha": 0,
        "water_yield_m3": 0,
        "bare_yield_m3": 0,
        "co2_t": 0,
        "stand_list": [],
    })

    for f in feats:
        p = f["properties"]
        mc = p.get("市町村CD", "?")
        by_muni[mc]["stands"] += 1
        by_muni[mc]["area_ha"] += p.get("area_ha", 0)
        by_muni[mc]["water_yield_m3"] += p.get("water_yield_m3", 0)
        by_muni[mc]["bare_yield_m3"] += p.get("bare_yield_m3", 0)
        by_muni[mc]["co2_t"] += p.get("co2_estimate_t_per_yr", 0)
        by_muni[mc]["stand_list"].append(p)

    # Totals
    total_stands = sum(d["stands"] for d in by_muni.values())
    total_area_ha = sum(d["area_ha"] for d in by_muni.values())
    total_water = sum(d["water_yield_m3"] for d in by_muni.values())
    total_bare = sum(d["bare_yield_m3"] for d in by_muni.values())
    total_co2 = sum(d["co2_t"] for d in by_muni.values())
    forest_effect = total_water - total_bare

    # Sort municipalities by area
    munis_sorted = sorted(by_muni.items(), key=lambda x: -x[1]["area_ha"])

    # Build HTML
    muni_rows = ""
    for mc, d in munis_sorted:
        name = MUNI_NAMES.get(mc, mc)
        effect = d["water_yield_m3"] - d["bare_yield_m3"]
        effect_pct = (effect / d["bare_yield_m3"] * 100) if d["bare_yield_m3"] else 0
        muni_rows += f"""
        <tr>
          <td><strong>{name}</strong><br><small>コード {mc}</small></td>
          <td class="num">{d['stands']:,}</td>
          <td class="num">{d['area_ha']:,.0f}</td>
          <td class="num">{d['water_yield_m3']:,}</td>
          <td class="num bare">{d['bare_yield_m3']:,}</td>
          <td class="num effect">+{effect:,}<br><small>+{effect_pct:.0f}%</small></td>
          <td class="num">{d['co2_t']:,}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>静岡県 森林公益機能レポート｜もりみえる</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=M+PLUS+Rounded+1c:wght@400;500;700;900&family=Josefin+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --green-900: #1f3d2a; --green-700: #2d5a3d; --green-100: #e7efde;
  --blue-900: #1f4570; --blue-700: #3b6da1; --blue-100: #e7f0fa;
  --earth-500: #c47a4a; --earth-600: #8c5a3a;
  --cream: #faf6ef; --paper: #ffffff;
  --ink-900: #2a2820; --ink-700: #4a4838; --ink-500: #7a786a; --ink-300: #bcbaae;
  --font-jp: 'Noto Sans JP', system-ui, sans-serif;
  --font-display: 'M PLUS Rounded 1c', 'Noto Sans JP', sans-serif;
  --font-en: 'Josefin Sans', sans-serif;
  --font-mono: ui-monospace, 'SF Mono', Menlo, monospace;
}}
*, *::before, *::after {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font-family: var(--font-jp); color: var(--ink-900); background: var(--cream);
  line-height: 1.8; -webkit-font-smoothing: antialiased;
}}
.report {{ max-width: 960px; margin: 0 auto; padding: 56px 36px 80px; }}
.report-header {{
  border-bottom: 3px solid var(--green-700); padding-bottom: 28px; margin-bottom: 40px;
}}
.report-eyebrow {{
  font-family: var(--font-en); font-size: 13px; letter-spacing: 0.3em;
  text-transform: uppercase; color: var(--green-700); margin: 0 0 16px; font-weight: 500;
}}
.report-title {{
  font-family: var(--font-display); font-weight: 900;
  font-size: clamp(28px, 4.5vw, 42px); line-height: 1.35;
  color: var(--green-900); margin: 0 0 16px;
}}
.report-subtitle {{ font-size: 15px; color: var(--ink-700); margin: 0 0 18px; }}
h2 {{
  font-family: var(--font-display); font-weight: 700;
  font-size: 22px; color: var(--green-900);
  margin: 48px 0 14px; padding-bottom: 8px;
  border-bottom: 1px solid var(--ink-300);
}}
.hero-stats {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px; margin: 24px 0 36px;
}}
.stat {{
  background: var(--paper); padding: 22px 24px; border-radius: 12px;
  border-left: 4px solid var(--green-700);
}}
.stat.water {{ border-left-color: var(--blue-700); }}
.stat.bare {{ border-left-color: var(--earth-500); }}
.stat.effect {{ border-left-color: var(--green-700); }}
.stat-label {{
  font-size: 11px; color: var(--ink-500); margin: 0 0 6px;
  letter-spacing: 0.1em; text-transform: uppercase; font-weight: 500;
}}
.stat-value {{
  font-family: var(--font-display); font-weight: 900; font-size: 26px;
  color: var(--green-900); margin: 0; line-height: 1.1;
}}
.stat-value .unit {{ font-size: 13px; font-weight: 500; color: var(--ink-500); margin-left: 4px; }}
.stat-note {{ font-size: 11px; color: var(--ink-500); margin: 4px 0 0; }}

table.muni-table {{
  width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13.5px;
  background: var(--paper); border-radius: 10px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.muni-table th, .muni-table td {{
  text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--ink-300);
}}
.muni-table th {{
  background: var(--green-700); color: white; font-weight: 500;
  font-size: 12px; letter-spacing: 0.05em;
}}
.muni-table td.num {{
  text-align: right; font-family: var(--font-mono); font-size: 13px;
}}
.muni-table td.num.bare {{ color: var(--earth-600); }}
.muni-table td.num.effect {{
  color: var(--green-700); font-weight: 600;
  background: rgba(45, 90, 61, 0.05);
}}
.muni-table tr:hover {{ background: var(--cream); }}
.muni-table small {{ color: var(--ink-500); font-size: 10px; font-family: var(--font-jp); }}

.callout {{
  background: var(--blue-100); border-left: 4px solid var(--blue-700);
  padding: 18px 22px; border-radius: 0 8px 8px 0;
  margin: 24px 0; font-size: 14px;
}}
.callout strong {{ color: var(--blue-900); }}

.disclaimer {{
  font-size: 12px; color: var(--ink-500); line-height: 1.85;
  border-top: 1px dashed var(--ink-300); padding-top: 20px; margin-top: 36px;
}}
.report-footer {{
  margin-top: 56px; padding-top: 24px;
  border-top: 1px solid var(--ink-300);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px;
}}
.report-footer p {{ margin: 0; font-size: 12px; color: var(--ink-500); }}

@media print {{ body {{ background: white; }} .report {{ padding: 24px; }} }}
@media (max-width: 640px) {{
  .report {{ padding: 32px 18px 56px; }}
  .muni-table {{ font-size: 11.5px; }}
  .muni-table th, .muni-table td {{ padding: 8px 6px; }}
}}
</style>
</head>
<body>
<div class="report">

<div class="report-header">
  <p class="report-eyebrow">Shizuoka Prefecture Forest Public Function Report</p>
  <h1 class="report-title">静岡県 森林公益機能<br>市町村別レポート</h1>
  <p class="report-subtitle">
    静岡県森林クラウド公開システム（{total_stands:,} 林班）× 林野庁簡易評価法による
    市町村別の森林公益機能（水資源涵養 + CO₂吸収 + 裸地比較）の定量評価
  </p>
</div>

<h2>1. 静岡県全体サマリ</h2>

<div class="hero-stats">
  <div class="stat">
    <p class="stat-label">対象 林班数</p>
    <p class="stat-value">{total_stands:,}<span class="unit">林班</span></p>
  </div>
  <div class="stat">
    <p class="stat-label">対象 森林面積</p>
    <p class="stat-value">{total_area_ha:,.0f}<span class="unit">ha</span></p>
  </div>
  <div class="stat water">
    <p class="stat-label">水資源涵養量</p>
    <p class="stat-value">{total_water/1e6:,.1f}<span class="unit">百万m³/年</span></p>
  </div>
  <div class="stat bare">
    <p class="stat-label">裸地仮定の場合</p>
    <p class="stat-value">{total_bare/1e6:,.1f}<span class="unit">百万m³/年</span></p>
  </div>
  <div class="stat effect">
    <p class="stat-label">森林維持効果</p>
    <p class="stat-value">+{forest_effect/1e6:,.1f}<span class="unit">百万m³/年</span></p>
    <p class="stat-note">+{(forest_effect/total_bare*100) if total_bare else 0:.0f}% 増</p>
  </div>
  <div class="stat">
    <p class="stat-label">CO₂吸収量</p>
    <p class="stat-value">{total_co2:,}<span class="unit">t-CO₂/年</span></p>
  </div>
</div>

<div class="callout">
  <strong>このレポートが意味すること：</strong>
  もし静岡県の本対象森林 {total_area_ha:,.0f} ha が裸地化（伐採後植栽せず・はげ山化）した場合、
  年間の水資源涵養量は <strong>{total_water/1e6:.1f} 百万 m³ → {total_bare/1e6:.1f} 百万 m³</strong> に
  落ち込み、<strong>{forest_effect/1e6:.1f} 百万 m³（家庭約 {int(forest_effect/73):,} 世帯分相当）</strong>
  の水資源が失われる。森林を維持することの公益機能は、この差分として定量化できる。
</div>

<h2>2. 市町村別 内訳</h2>

<p>面積の大きい順。市町村コードは静岡県森林クラウドの内部コード（61-76）。</p>

<table class="muni-table">
  <thead>
    <tr>
      <th>市町村</th>
      <th>林班数</th>
      <th>森林面積 (ha)</th>
      <th>水源涵養 (m³/年)</th>
      <th>裸地仮定 (m³/年)</th>
      <th>森林維持効果</th>
      <th>CO₂ (t/年)</th>
    </tr>
  </thead>
  <tbody>{muni_rows}
  </tbody>
</table>

<h2>3. 計算手法</h2>

<p>
各林班ごとに：
</p>

<ul>
  <li>林班ポリゴンの面積（SHAPE_AREA）を Sentinel-2 で抽出した森林ピクセルと突合</li>
  <li>林班重心の座標で気象（NASA POWER）・標高（国土地理院）・地質（産総研シームレス地質図）を取得</li>
  <li>林野庁簡易評価法 Ver.1.0 で水資源涵養量を算定（針葉樹常緑として）</li>
  <li>裸地仮定：水資源涵養量＝降水量 × 10%（マニュアル準拠）</li>
  <li>CO₂ 吸収量：IPCC AFOLU Tier 2（9.62 t-CO₂/ha/年）× 林班面積</li>
</ul>

<div class="callout">
  <strong>次のステップ（精度向上）</strong>：
  栃木県・兵庫県・高知県では既に LiDAR の高精度森林資源データ
  （20m メッシュ × 樹種・本数・樹高・材積）が「らしんばん」（MIERUNE×日本森林技術協会）
  経由で公開されており、商用利用可能。静岡県でも同等データが公開されれば、林野庁標準値
  ではなく実測 DBH・密度・樹高で計算でき、Tier 3 相当の精度（不確実性 ±10〜15%）に到達できる。
</div>

<h2>4. データソース</h2>

<ul>
  <li><strong>林班ポリゴン</strong>：静岡県森林クラウド公開システム（MAGIS.RINPAN ベクトルタイル）</li>
  <li><strong>気象</strong>：NASA POWER monthly API（2020-2024 mean）</li>
  <li><strong>標高</strong>：国土地理院 5m DEM API</li>
  <li><strong>地質</strong>：産総研 シームレス地質図 v2 API</li>
  <li><strong>水源涵養計算式</strong>：林野庁「林地における水資源涵養量簡易評価法」Ver.1.0（令和8年3月）</li>
  <li><strong>CO₂ 換算</strong>：IPCC AFOLU 2006 Tier 2 + 林野庁収穫予想表</li>
</ul>

<p class="disclaimer">
※ 本レポートは林野庁の公式評価式に準拠した第三者試算であり、公式認証データではありません。
林野庁簡易評価法 Ver.1.0 は本来 100ha 未満の小規模林分を対象としており、本レポートでは
林班単位（中央値約 100ha 程度）で適用しているが、林分内の樹高・密度・DBH のばらつきを
標準値で平均化している点に注意。LiDAR 等の実測データ統合で Tier 3 への移行が可能。
</p>

<div class="report-footer">
  <p>© 2026 もりみえる｜<a href="https://mori-mieru.jp/">mori-mieru.jp</a></p>
</div>

</div>
</body>
</html>
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html)
    print(f"Wrote: {OUTPUT}")
    print(f"Summary: {total_stands} stands, {total_area_ha:,.0f} ha, {total_water:,} m³/yr water, {total_co2:,} t-CO2/yr")


if __name__ == "__main__":
    main()
