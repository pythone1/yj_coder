from __future__ import annotations

from html import escape
from pathlib import Path
import json
import math

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_0520"
OUT_HTML = ANALYSIS_DIR / "0520_interactive_network_visualization.html"


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except Exception:
        return default


def load_data() -> dict[str, object]:
    return {
        "nodes": pd.read_csv(ANALYSIS_DIR / "0520_nodes_classified.csv", encoding="utf-8-sig"),
        "links": pd.read_csv(ANALYSIS_DIR / "0520_links_classified.csv", encoding="utf-8-sig"),
        "subcatchments": pd.read_csv(ANALYSIS_DIR / "0520_subcatchments.csv", encoding="utf-8-sig"),
        "flooding": pd.read_csv(ANALYSIS_DIR / "0520_node_flooding.csv", encoding="utf-8-sig"),
        "inflows": pd.read_csv(ANALYSIS_DIR / "0520_inflows.csv", encoding="utf-8-sig"),
        "timeseries": pd.read_csv(ANALYSIS_DIR / "0520_timeseries_summary.csv", encoding="utf-8-sig"),
        "summary": json.loads((ANALYSIS_DIR / "0520_model_data_summary.json").read_text(encoding="utf-8")),
    }


def normalize_series(values: list[float], size: int = 256) -> list[float]:
    if not values:
        return []
    if len(values) == size:
        return values
    result = []
    for i in range(size):
        pos = i * (len(values) - 1) / max(size - 1, 1)
        lo = int(math.floor(pos))
        hi = min(lo + 1, len(values) - 1)
        ratio = pos - lo
        result.append(values[lo] * (1 - ratio) + values[hi] * ratio)
    return result


def build_svg(nodes: pd.DataFrame, links: pd.DataFrame, subcatchments: pd.DataFrame, flooding: pd.DataFrame) -> str:
    coords = {}
    for _, row in nodes.iterrows():
        x, y = fnum(row.get("x"), math.nan), fnum(row.get("y"), math.nan)
        if math.isnan(x) or math.isnan(y):
            continue
        coords[str(row["node"])] = {"x": x, "y": y, "type": str(row["type"])}
    xs = [v["x"] for v in coords.values()]
    ys = [v["y"] for v in coords.values()]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    width, height = 1380, 880

    def sx(x: float) -> float:
        return 45 + (x - minx) / (maxx - minx or 1) * (width - 90)

    def sy(y: float) -> float:
        return height - 45 - (y - miny) / (maxy - miny or 1) * (height - 90)

    flood_map = {
        str(row["node"]): {
            "volume_m3": fnum(row["total_flood_10^6_ltr"]) * 1000,
            "hours": fnum(row["hours_flooded"]),
            "rate": fnum(row["max_rate_cms"]),
            "time": str(row["time_of_max"]),
        }
        for _, row in flooding.iterrows()
    }
    area_by_node = subcatchments.groupby("outlet")["area_ha"].sum().to_dict() if not subcatchments.empty else {}
    pump_links = links[links["type"].astype(str).str.lower() == "pump"]
    pump_nodes = set(pump_links["from_node"].astype(str)) | set(pump_links["to_node"].astype(str))

    parts = [
        f"<svg id='networkSvg' viewBox='0 0 {width} {height}' class='network' role='img'>",
        "<defs>",
        "<filter id='softShadow'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-opacity='.18'/></filter>",
        "</defs>",
        "<g id='viewport'>",
        "<g class='layer subcatchment-layer'>",
    ]
    max_area = max(area_by_node.values()) if area_by_node else 1
    for node, area in area_by_node.items():
        node = str(node)
        if node not in coords:
            continue
        c = coords[node]
        r = 5 + 42 * math.sqrt(max(float(area), 0) / max_area)
        parts.append(
            f"<circle class='subcatchment-heat' cx='{sx(c['x']):.2f}' cy='{sy(c['y']):.2f}' r='{r:.2f}' "
            f"data-node='{escape(node)}' data-area='{float(area):.4f}' />"
        )
    parts.append("</g><g class='layer conduit-layer'>")
    for _, row in links[links["type"].astype(str).str.lower() == "conduit"].iterrows():
        a, b = str(row["from_node"]), str(row["to_node"])
        if a not in coords or b not in coords:
            continue
        ca, cb = coords[a], coords[b]
        depth_ratio = fnum(row.get("max_full_depth_ratio"))
        saturated = " saturated" if depth_ratio >= 1 else ""
        parts.append(
            f"<line class='pipe{saturated}' x1='{sx(ca['x']):.2f}' y1='{sy(ca['y']):.2f}' "
            f"x2='{sx(cb['x']):.2f}' y2='{sy(cb['y']):.2f}' data-link='{escape(str(row['link']))}' "
            f"data-from='{escape(a)}' data-to='{escape(b)}' data-depth='{depth_ratio:.3g}' />"
        )
    parts.append("</g><g class='layer pump-link-layer'>")
    for _, row in pump_links.iterrows():
        a, b = str(row["from_node"]), str(row["to_node"])
        if a not in coords or b not in coords:
            continue
        ca, cb = coords[a], coords[b]
        parts.append(
            f"<line class='pump-link' x1='{sx(ca['x']):.2f}' y1='{sy(ca['y']):.2f}' "
            f"x2='{sx(cb['x']):.2f}' y2='{sy(cb['y']):.2f}' data-link='{escape(str(row['link']))}' "
            f"data-from='{escape(a)}' data-to='{escape(b)}' />"
        )
        mx, my = (sx(ca["x"]) + sx(cb["x"])) / 2, (sy(ca["y"]) + sy(cb["y"])) / 2
        parts.append(f"<text class='pump-link-label' x='{mx:.2f}' y='{my - 8:.2f}'>{escape(str(row['link']))}</text>")
    parts.append("</g><g class='layer flood-layer'>")
    max_flood = max((v["volume_m3"] for v in flood_map.values()), default=1)
    for node, item in flood_map.items():
        if node not in coords:
            continue
        c = coords[node]
        r = 16 + 70 * math.sqrt(item["volume_m3"] / max_flood)
        parts.append(
            f"<circle class='flood-ring' cx='{sx(c['x']):.2f}' cy='{sy(c['y']):.2f}' r='{r:.2f}' "
            f"data-node='{escape(node)}' data-volume='{item['volume_m3']:.3f}' data-hours='{item['hours']:.3f}' />"
        )
    parts.append("</g><g class='layer node-layer'>")
    for _, row in nodes.iterrows():
        node = str(row["node"])
        if node not in coords:
            continue
        c = coords[node]
        node_type = str(row["type"])
        classes = ["node", node_type]
        if node in pump_nodes:
            classes.append("pump-node")
        if node in flood_map:
            classes.append("flood-node")
        cls = " ".join(classes)
        tooltip = {
            "node": node,
            "type": node_type,
            "invert": fnum(row.get("invert_elev_m")),
            "max_depth": fnum(row.get("max_depth_m_x", row.get("max_depth_m"))),
            "ponded_area": fnum(row.get("ponded_area_m2")),
            "is_pump_node": node in pump_nodes,
            "flood": flood_map.get(node),
            "subcatch_area_ha": float(area_by_node.get(node, 0)),
        }
        parts.append(
            f"<circle class='{cls}' cx='{sx(c['x']):.2f}' cy='{sy(c['y']):.2f}' r='4.2' "
            f"data-node='{escape(node)}' data-info='{escape(json.dumps(tooltip, ensure_ascii=False))}' />"
        )
    parts.append("</g><g class='layer label-layer'>")
    labeled = set(flood_map) | pump_nodes | set(nodes[nodes["type"].isin(["storage", "outfall"])]["node"].astype(str))
    for node in labeled:
        if node not in coords:
            continue
        c = coords[node]
        parts.append(f"<text class='node-label key-label' x='{sx(c['x']) + 8:.2f}' y='{sy(c['y']) - 8:.2f}'>{escape(node)}</text>")
    for _, row in nodes.iterrows():
        node = str(row["node"])
        if node in labeled or node not in coords:
            continue
        c = coords[node]
        parts.append(f"<text class='node-label all-label' x='{sx(c['x']) + 6:.2f}' y='{sy(c['y']) - 6:.2f}'>{escape(node)}</text>")
    parts.append("</g></g></svg>")
    return "\n".join(parts)


def build_html(data: dict[str, object]) -> str:
    nodes: pd.DataFrame = data["nodes"]  # type: ignore[assignment]
    links: pd.DataFrame = data["links"]  # type: ignore[assignment]
    subcatchments: pd.DataFrame = data["subcatchments"]  # type: ignore[assignment]
    flooding: pd.DataFrame = data["flooding"]  # type: ignore[assignment]
    inflows: pd.DataFrame = data["inflows"]  # type: ignore[assignment]
    timeseries: pd.DataFrame = data["timeseries"]  # type: ignore[assignment]
    summary: dict[str, object] = data["summary"]  # type: ignore[assignment]
    options = summary.get("options", {})
    continuity = summary.get("continuity", {})
    outfalls = summary.get("outfall_loading", [])

    wet_inflow = fnum(continuity.get("Wet Weather Inflow") if isinstance(continuity, dict) else None)
    outflow = fnum(continuity.get("External Outflow") if isinstance(continuity, dict) else None)
    flooding_loss = fnum(continuity.get("Flooding Loss") if isinstance(continuity, dict) else None)
    final_storage = fnum(continuity.get("Final Stored Volume") if isinstance(continuity, dict) else None)
    continuity_error = fnum(continuity.get("Continuity Error (%)") if isinstance(continuity, dict) else None)

    pump_links = links[links["type"].astype(str).str.lower() == "pump"]
    storage_nodes = nodes[nodes["type"].astype(str) == "storage"]["node"].astype(str).tolist()
    outfall_nodes = nodes[nodes["type"].astype(str) == "outfall"]["node"].astype(str).tolist()
    flow_inflows = inflows[inflows["constituent"].astype(str).str.upper().eq("FLOW")] if not inflows.empty else pd.DataFrame()
    pollutant_inflows = inflows[~inflows["constituent"].astype(str).str.upper().eq("FLOW")] if not inflows.empty else pd.DataFrame()
    sewage_ts = timeseries[timeseries["series"].astype(str).eq("0519污水量")] if not timeseries.empty else pd.DataFrame()

    flood_rows = "".join(
        f"<tr><td>{escape(str(r.node))}</td><td>{fnum(r.total_flood_10_6_ltr) * 1000:.3f}</td><td>{fnum(r.hours_flooded):.2f}</td><td>{fnum(r.max_rate_cms):.3f}</td><td>{escape(str(r.time_of_max))}</td></tr>"
        for r in flooding.rename(columns={"total_flood_10^6_ltr": "total_flood_10_6_ltr"}).itertuples(index=False)
    )
    pump_rows = "".join(
        f"<tr><td>{escape(str(r.link))}</td><td>{escape(str(r.from_node))}</td><td>{escape(str(r.to_node))}</td></tr>"
        for r in pump_links.itertuples(index=False)
    )
    outfall_rows = "".join(
        f"<tr><td>{escape(str(item.get('outfall', '')))}</td><td>{fnum(item.get('avg_flow_cms')):.3f}</td><td>{fnum(item.get('max_flow_cms')):.3f}</td><td>{fnum(item.get('total_volume_10^6_ltr')) * 1000:.1f}</td></tr>"
        for item in outfalls
        if isinstance(item, dict)
    )
    ts_rows = "".join(
        f"<tr><td>{escape(str(r.series))}</td><td>{int(fnum(r.point_count))}</td><td>{fnum(r.min_value):.4f}</td><td>{fnum(r.max_value):.4f}</td><td>{fnum(r.mean_value):.4f}</td></tr>"
        for r in timeseries.itertuples(index=False)
    )
    inflow_rows = "".join(
        f"<tr><td>{escape(str(r.node))}</td><td>{escape(str(r.constituent))}</td><td>{escape(str(r.type))}</td><td>{escape(str(r.timeseries))}</td><td>{fnum(r.baseline):.3f}</td></tr>"
        for r in inflows.itertuples(index=False)
    )

    svg = build_svg(nodes, links, subcatchments, flooding)
    node_json = json.dumps(nodes["node"].astype(str).tolist(), ensure_ascii=False)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>0520 新模型动态分类可视化</title>
<style>
body{{margin:0;background:#f4f7fb;color:#172033;font-family:'Microsoft YaHei','SimHei',Arial,sans-serif;}}
header{{padding:24px 34px;background:#102a43;color:white;}}
header h1{{margin:0;font-size:26px;}}
header p{{margin:8px 0 0;color:#dbeafe;}}
main{{display:grid;grid-template-columns:310px 1fr;gap:16px;padding:16px;}}
.side,.panel{{background:white;border-radius:12px;box-shadow:0 8px 24px #12304a12;}}
.side{{padding:16px;align-self:start;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;}}
.panel{{padding:14px;}}
.cards{{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:12px;margin-bottom:16px;}}
.card{{background:white;border-radius:12px;padding:12px 14px;box-shadow:0 8px 24px #12304a12;}}
.card span{{font-size:12px;color:#64748b;display:block;}} .card b{{font-size:24px;color:#0f766e;}}
label{{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:14px;}}
input[type='text']{{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px 10px;margin:8px 0;}}
button{{border:0;border-radius:8px;background:#1d4ed8;color:white;padding:8px 10px;margin:4px 4px 4px 0;cursor:pointer;}}
.muted{{color:#64748b;font-size:13px;line-height:1.6;}}
.warn{{background:#fff7ed;border-left:5px solid #f97316;border-radius:8px;padding:10px 12px;margin:10px 0;line-height:1.7;}}
.ok{{background:#ecfdf5;border-left:5px solid #10b981;border-radius:8px;padding:10px 12px;margin:10px 0;line-height:1.7;}}
.network-wrap{{height:78vh;overflow:hidden;border:1px solid #dbe4ef;border-radius:10px;background:#fbfdff;}}
.network{{width:100%;height:100%;}}
.pipe{{stroke:#8aa0b4;stroke-width:1.15;opacity:.62;}}
.pipe.saturated{{stroke:#ef4444;stroke-width:2.2;opacity:.72;}}
.pump-link{{stroke:#8b5cf6;stroke-width:3.2;opacity:.9;stroke-dasharray:7 4;}}
.pump-link-label{{font-size:13px;font-weight:700;fill:#6d28d9;paint-order:stroke;stroke:white;stroke-width:4px;}}
.subcatchment-heat{{fill:#facc15;opacity:.16;stroke:#f59e0b;stroke-width:.6;}}
.flood-ring{{fill:#ef4444;stroke:#b91c1c;stroke-width:2;opacity:.30;filter:url(#softShadow);}}
.node{{stroke:white;stroke-width:1.3;cursor:pointer;}}
.junction{{fill:#3b82f6;}}
.storage{{fill:#f59e0b;r:7;}}
.outfall{{fill:#111827;r:8;}}
.pump-node{{fill:#8b5cf6;r:8;}}
.flood-node{{fill:#dc2626;r:8;}}
.node-label{{font-size:12px;font-weight:700;fill:#172033;paint-order:stroke;stroke:white;stroke-width:4px;}}
.all-label{{display:none;}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px;font-size:13px;}}
.dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:-2px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}} th,td{{border-bottom:1px solid #e5e7eb;padding:7px 8px;text-align:left;}} th{{background:#eff6ff;color:#1e3a8a;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;}}
#detailBox{{font-size:13px;line-height:1.7;white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;}}
.hide-conduits .conduit-layer,.hide-pumps .pump-link-layer,.hide-flood .flood-layer,.hide-subcatch .subcatchment-layer,.hide-labels .label-layer{{display:none;}}
.show-all-labels .all-label{{display:block;}}
.highlight-node{{stroke:#0f172a !important;stroke-width:4 !important;filter:url(#softShadow);}}
@media(max-width:1100px){{main{{grid-template-columns:1fr;}}.side{{position:static;max-height:none;}}.cards{{grid-template-columns:repeat(2,1fr);}}.grid2{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<header>
<h1>0520 新模型动态分类可视化</h1>
<p>节点、泵站、排口、溢流、汇水区接入和管段饱满风险分层展示</p>
</header>
<main>
<aside class="side">
<h2>图层控制</h2>
<label><input type="checkbox" id="ckConduits" checked> 管段</label>
<label><input type="checkbox" id="ckPumps" checked> 泵与泵站节点</label>
<label><input type="checkbox" id="ckFlood" checked> 溢流节点热区</label>
<label><input type="checkbox" id="ckSubcatch" checked> 汇水区接入面积</label>
<label><input type="checkbox" id="ckLabels" checked> 关键标签</label>
<label><input type="checkbox" id="ckAllLabels"> 显示全部节点编号</label>
<h2>节点定位</h2>
<input id="nodeSearch" type="text" list="nodeList" placeholder="输入节点号，如 110、293、J254">
<datalist id="nodeList"></datalist>
<button onclick="searchNode()">定位节点</button>
<button onclick="resetView()">重置视图</button>
<h2>选中对象</h2>
<div id="detailBox">点击图上的节点查看属性。</div>
<div class="legend">
<span><i class="dot" style="background:#3b82f6"></i>检查井</span>
<span><i class="dot" style="background:#f59e0b"></i>调蓄/存储</span>
<span><i class="dot" style="background:#8b5cf6"></i>泵站节点</span>
<span><i class="dot" style="background:#111827"></i>排口</span>
<span><i class="dot" style="background:#dc2626"></i>溢流</span>
</div>
</aside>
<section>
<div class="cards">
<div class="card"><span>检查井</span><b>{int((nodes['type'] == 'junction').sum())}</b></div>
<div class="card"><span>泵</span><b>{len(pump_links)}</b></div>
<div class="card"><span>排口</span><b>{len(outfall_nodes)}</b></div>
<div class="card"><span>溢流节点</span><b>{len(flooding)}</b></div>
<div class="card"><span>汇水区</span><b>{len(subcatchments)}</b></div>
<div class="card"><span>时间步长</span><b>{escape(str(options.get('REPORT_STEP', '')))}</b></div>
<div class="card"><span>出流体积</span><b>{outflow * 1000:.0f} m³</b></div>
<div class="card"><span>溢流损失</span><b>{flooding_loss * 1000:.0f} m³</b></div>
</div>
<div class="panel">
<div class="network-wrap">{svg}</div>
</div>
<div class="grid2">
<div class="panel"><h2>注入/入流判读</h2>
<div class="ok">未检测到节点外部 FLOW 水量注入。`INFLOWS` 中只有污染物质量输入：节点 19 的 COD，类型为 MASS，基值 216。</div>
<div class="warn">模型水量来自 `RAINGAGES + SUBCATCHMENTS`：135 个汇水区引用 `0519污水量` 时间序列进入管网，RPT 中表现为 Wet Weather Inflow = {wet_inflow:.3f} × 10^6 L。</div>
<table><tr><th>节点</th><th>污染物/对象</th><th>类型</th><th>时间序列</th><th>基值</th></tr>{inflow_rows}</table>
</div>
<div class="panel"><h2>溢流与积水设置</h2>
<div class="warn">`ALLOW_PONDING = {escape(str(options.get('ALLOW_PONDING', '')))}；所有检查井 ponded area 为 0。因此溢流不会作为地面积水留存并回流，RPT 中计为 Flooding Loss。</div>
<table><tr><th>溢流节点</th><th>溢流量 m³</th><th>持续 h</th><th>峰值 CMS</th><th>峰值时间</th></tr>{flood_rows}</table>
</div>
</div>
<div class="grid2">
<div class="panel"><h2>泵站/泵连接</h2><p class="muted">存储节点：{escape(', '.join(storage_nodes))}；泵站相关节点会在图上显示为紫色。</p><table><tr><th>泵</th><th>起点</th><th>终点</th></tr>{pump_rows}</table></div>
<div class="panel"><h2>排口结果</h2><p class="muted">排口节点：{escape(', '.join(outfall_nodes))}；Flow Routing Continuity Error = {continuity_error:.3f}%；Final Stored Volume = {final_storage * 1000:.1f} m³。</p><table><tr><th>排口</th><th>平均流量 CMS</th><th>最大流量 CMS</th><th>总出流 m³</th></tr>{outfall_rows}</table></div>
</div>
<div class="panel"><h2>时间序列摘要</h2><table><tr><th>序列名</th><th>点数</th><th>最小值</th><th>最大值</th><th>均值</th></tr>{ts_rows}</table></div>
</section>
</main>
<script>
const allNodes = {node_json};
const datalist = document.getElementById('nodeList');
allNodes.forEach(n => {{
  const opt = document.createElement('option');
  opt.value = n;
  datalist.appendChild(opt);
}});
const svg = document.getElementById('networkSvg');
const viewport = document.getElementById('viewport');
let selected = null;
function updateLayers(){{
  svg.classList.toggle('hide-conduits', !document.getElementById('ckConduits').checked);
  svg.classList.toggle('hide-pumps', !document.getElementById('ckPumps').checked);
  svg.classList.toggle('hide-flood', !document.getElementById('ckFlood').checked);
  svg.classList.toggle('hide-subcatch', !document.getElementById('ckSubcatch').checked);
  svg.classList.toggle('hide-labels', !document.getElementById('ckLabels').checked);
  svg.classList.toggle('show-all-labels', document.getElementById('ckAllLabels').checked);
}}
document.querySelectorAll('input[type=checkbox]').forEach(x => x.addEventListener('change', updateLayers));
function nodeText(info){{
  const flood = info.flood ? `\\n溢流量: ${{info.flood.volume_m3.toFixed(3)}} m³\\n溢流持续: ${{info.flood.hours.toFixed(2)}} h\\n峰值溢流率: ${{info.flood.rate.toFixed(3)}} CMS\\n峰值时间: ${{info.flood.time}}` : '\\n溢流: 无';
  return `节点: ${{info.node}}\\n类型: ${{info.type}}\\n井底/底高程: ${{info.invert.toFixed(3)}} m\\n最大深度: ${{info.max_depth.toFixed(3)}} m\\nPonded Area: ${{info.ponded_area.toFixed(3)}} m²\\n泵站相关: ${{info.is_pump_node ? '是' : '否'}}\\n接入汇水区面积: ${{info.subcatch_area_ha.toFixed(4)}} ha${{flood}}`;
}}
document.querySelectorAll('.node').forEach(el => {{
  el.addEventListener('click', () => {{
    if(selected) selected.classList.remove('highlight-node');
    selected = el;
    el.classList.add('highlight-node');
    const info = JSON.parse(el.dataset.info);
    document.getElementById('detailBox').textContent = nodeText(info);
  }});
}});
function searchNode(){{
  const val = document.getElementById('nodeSearch').value.trim();
  const el = document.querySelector(`.node[data-node="${{CSS.escape(val)}}"]`);
  if(!el){{
    document.getElementById('detailBox').textContent = `未找到节点：${{val}}`;
    return;
  }}
  el.dispatchEvent(new Event('click'));
  const cx = Number(el.getAttribute('cx')), cy = Number(el.getAttribute('cy'));
  svg.setAttribute('viewBox', `${{cx - 260}} ${{cy - 180}} 520 360`);
}}
function resetView(){{
  svg.setAttribute('viewBox', '0 0 1380 880');
  if(selected) selected.classList.remove('highlight-node');
  selected = null;
  document.getElementById('detailBox').textContent = '点击图上的节点查看属性。';
}}
updateLayers();
</script>
</body>
</html>"""


def main() -> None:
    data = load_data()
    OUT_HTML.write_text(build_html(data), encoding="utf-8")
    print(OUT_HTML)


if __name__ == "__main__":
    main()
