#!/usr/bin/env python3
"""
Generate inline SVG figures for the Himi water-yield report:
- NDVI 5-year time series (line chart with seasonal pattern)
- Water budget donut chart
- AOI mini-map (Japan + Himi marker)

Writes a small JSON with SVG strings so the HTML can fetch and embed them.
"""
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TS_PATH = ROOT / "data" / "sentinel" / "himi_timeseries.json"
WATER_PATH = ROOT / "data" / "sentinel" / "himi_water.json"
OUT_PATH = ROOT / "data" / "sentinel" / "himi_figures.json"


def ndvi_chart(ts):
    """SVG line chart of 5-year NDVI series."""
    points = ts["points"]
    W, H = 860, 240
    M = {"top": 24, "right": 16, "bottom": 36, "left": 44}
    plot_w = W - M["left"] - M["right"]
    plot_h = H - M["top"] - M["bottom"]

    # X axis: dates
    t0 = datetime.fromisoformat(points[0]["date"]).timestamp()
    t1 = datetime.fromisoformat(points[-1]["date"]).timestamp()
    span = t1 - t0

    # Y axis: 0.0 to 0.9
    y_min, y_max = 0.0, 0.9

    def x_for(date_str):
        t = datetime.fromisoformat(date_str).timestamp()
        return M["left"] + ((t - t0) / span) * plot_w
    def y_for(v):
        return M["top"] + (1 - (v - y_min) / (y_max - y_min)) * plot_h

    # Build path
    path_d = ""
    for i, p in enumerate(points):
        x = x_for(p["date"])
        y = y_for(p["mean"])
        path_d += f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f} "

    # Fill path (close to baseline)
    fill_d = path_d + f"L{x_for(points[-1]['date']):.1f},{M['top'] + plot_h} L{x_for(points[0]['date']):.1f},{M['top'] + plot_h} Z"

    # X axis ticks (years)
    year_ticks = []
    for year in range(2021, 2027):
        try:
            tx = datetime(year, 1, 1).timestamp()
            if t0 <= tx <= t1:
                x = M["left"] + ((tx - t0) / span) * plot_w
                year_ticks.append((x, year))
        except Exception:
            continue

    # Y axis ticks
    y_ticks = [0.0, 0.3, 0.5, 0.7, 0.9]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" style="width:100%;height:auto;display:block;">
<defs>
  <linearGradient id="ndviGrad" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0" stop-color="#5a8a3a" stop-opacity="0.5"/>
    <stop offset="1" stop-color="#5a8a3a" stop-opacity="0.05"/>
  </linearGradient>
</defs>
<!-- Forest threshold line -->
<line x1="{M['left']}" x2="{M['left']+plot_w}" y1="{y_for(0.5):.1f}" y2="{y_for(0.5):.1f}"
      stroke="#c47a4a" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.7"/>
<text x="{M['left']+plot_w-4}" y="{y_for(0.5)-4:.1f}" text-anchor="end" font-size="10" fill="#c47a4a" font-family="ui-monospace,monospace">NDVI = 0.5 (森林閾値)</text>

<!-- Y axis -->'''
    for v in y_ticks:
        y = y_for(v)
        svg += f'\n<line x1="{M["left"]}" x2="{M["left"]+plot_w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e0ddc8" stroke-width="0.5"/>'
        svg += f'\n<text x="{M["left"]-6}" y="{y+3:.1f}" text-anchor="end" font-size="11" fill="#7a786a" font-family="ui-monospace,monospace">{v:.1f}</text>'

    svg += f'\n<!-- Data area -->\n<path d="{fill_d}" fill="url(#ndviGrad)"/>\n<path d="{path_d}" fill="none" stroke="#2d5a3d" stroke-width="1.7"/>'

    # X axis ticks
    for x, year in year_ticks:
        svg += f'\n<line x1="{x:.1f}" x2="{x:.1f}" y1="{M["top"]+plot_h}" y2="{M["top"]+plot_h+4}" stroke="#7a786a" stroke-width="0.6"/>'
        svg += f'\n<text x="{x:.1f}" y="{M["top"]+plot_h+18}" text-anchor="middle" font-size="11" fill="#4a4838" font-family="ui-monospace,monospace">{year}</text>'

    # Axis labels
    svg += f'\n<text x="{M["left"]-32}" y="{M["top"]+plot_h/2}" font-size="11" fill="#4a4838" text-anchor="middle" transform="rotate(-90 {M["left"]-32} {M["top"]+plot_h/2})">NDVI 平均</text>'
    svg += f'\n<text x="{W/2}" y="{H-4}" font-size="11" fill="#4a4838" text-anchor="middle">観測年（{len(points)} 観測点・Sentinel-2 / CDSE 実測）</text>'

    svg += '\n</svg>'
    return svg


def water_donut(water):
    """SVG donut chart of water budget."""
    r = water["results_pct"]
    runoff = r["direct_runoff_pct"]
    evapo = r["evapotranspiration_pct"]
    yield_pct = r["water_yield_pct"]
    # Normalize to 100
    total = runoff + evapo + yield_pct
    runoff_norm = runoff / total * 100
    evapo_norm = evapo / total * 100
    yield_norm = yield_pct / total * 100

    W = 360
    cx, cy = W / 2, W / 2
    R = 130  # outer radius
    r_inner = 80

    def arc_path(start_deg, end_deg):
        start_rad = math.radians(start_deg - 90)
        end_rad = math.radians(end_deg - 90)
        x1, y1 = cx + R * math.cos(start_rad), cy + R * math.sin(start_rad)
        x2, y2 = cx + R * math.cos(end_rad), cy + R * math.sin(end_rad)
        x3, y3 = cx + r_inner * math.cos(end_rad), cy + r_inner * math.sin(end_rad)
        x4, y4 = cx + r_inner * math.cos(start_rad), cy + r_inner * math.sin(start_rad)
        large = 1 if (end_deg - start_deg) > 180 else 0
        return f"M{x1:.1f},{y1:.1f} A{R},{R} 0 {large},1 {x2:.1f},{y2:.1f} L{x3:.1f},{y3:.1f} A{r_inner},{r_inner} 0 {large},0 {x4:.1f},{y4:.1f} Z"

    a = 0
    a_runoff_end = a + (runoff_norm * 3.6)
    a_evapo_end = a_runoff_end + (evapo_norm * 3.6)
    a_yield_end = 360

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" style="width:100%;height:auto;max-width:340px;display:block;margin:0 auto;">
  <path d="{arc_path(a, a_runoff_end)}" fill="#c47a4a"/>
  <path d="{arc_path(a_runoff_end, a_evapo_end)}" fill="#7ba56f"/>
  <path d="{arc_path(a_evapo_end, a_yield_end)}" fill="#3b6da1"/>

  <text x="{cx}" y="{cy-6}" text-anchor="middle" font-family="'M PLUS Rounded 1c',sans-serif" font-weight="700" font-size="36" fill="#1f4570">{yield_pct:.0f}%</text>
  <text x="{cx}" y="{cy+18}" text-anchor="middle" font-family="'Noto Sans JP',sans-serif" font-size="11" fill="#7a786a">が水資源涵養に</text>

  <!-- Outer labels -->
  <text x="{cx+R*math.cos(math.radians(-90+runoff_norm*1.8))+4}" y="{cy+R*math.sin(math.radians(-90+runoff_norm*1.8))+4}" font-size="11" fill="#8c5a3a" font-weight="600">直接流出 {runoff:.0f}%</text>
  <text x="{cx+R*math.cos(math.radians(-90+runoff_norm*3.6+evapo_norm*1.8))-30}" y="{cy+R*math.sin(math.radians(-90+runoff_norm*3.6+evapo_norm*1.8))-8}" font-size="11" fill="#3a5a30" font-weight="600">蒸発散 {evapo:.0f}%</text>
  <text x="{cx-90}" y="{cy-R-4}" font-size="11" fill="#1f4570" font-weight="600">水資源涵養 {yield_pct:.0f}%</text>
</svg>'''
    return svg


def japan_map():
    """Simple Japan outline with Himi marker."""
    # Use a stylized representation - Honshu coastline approximation
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="120 24 35 23" style="width:100%;height:auto;max-width:420px;display:block;margin:0 auto;">
  <!-- Simplified Japan outline -->
  <path d="M141.5,45 L143.5,43 L143,42 L144.5,41 L145.5,40.5 L145,38.5 L143,37 L141,35.5 L139.5,34 L139,32 L137.5,31 L136,30 L135.5,28 L134,27 L132,26 L130,26.5 L128.5,28 L127,30 L127.5,32 L129,33.5 L131,34 L131.5,36 L133,37 L131.5,38.5 L130,40 L128,41 L127,42.5 L128.5,43 L130,43 L131.5,42 L133,41 L134.5,42 L136,42.5 L137.5,43.5 L139,44 L140,45 L141.5,45 Z"
        fill="#a7c498" stroke="#5a8a3a" stroke-width="0.3" opacity="0.7"/>
  <!-- Hokkaido -->
  <path d="M141,43 L142,42 L143.5,41.5 L144,41 L145,42.5 L145,44 L143.5,44.5 L142,44 Z"
        fill="#a7c498" stroke="#5a8a3a" stroke-width="0.3" opacity="0.7"/>
  <!-- Himi marker (36.857N, 136.987E) -->
  <circle cx="136.987" cy="36.857" r="0.7" fill="#c47a4a" stroke="white" stroke-width="0.18"/>
  <circle cx="136.987" cy="36.857" r="0.3" fill="white"/>
  <text x="136.5" y="35.7" font-size="0.9" fill="#1f4570" font-weight="700" text-anchor="end">氷見市</text>
</svg>'''
    return svg


def main():
    ts = json.loads(TS_PATH.read_text())
    water = json.loads(WATER_PATH.read_text())

    out = {
        "ndvi_chart_svg": ndvi_chart(ts),
        "water_donut_svg": water_donut(water),
        "japan_map_svg": japan_map(),
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False))
    print(f"Wrote: {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
