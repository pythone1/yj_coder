"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: build_0520_plan_interactive_map.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import json
import math

import pandas as pd

from config_0416 import CANDIDATE_NODES, MONITOR_NODES, TRUTH_INJECTION_NODES


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_0520"
OUT_HTML = ANALYSIS_DIR / "0520_动态布点可视化.html"

NODES_CSV = ANALYSIS_DIR / "0520_all_nodes_full_fields.csv"
LINKS_CSV = ANALYSIS_DIR / "0520_links_classified.csv"
PLAN_JSON = ANALYSIS_DIR / "0520_monitor_candidate_injection_plan.json"


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except Exception:
        return default


def load_plan_notes() -> dict[str, str]:
    if not PLAN_JSON.exists():
        return {}
    data = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    notes: dict[str, str] = {}
    for row in data.get("plan", []):
        node = str(row.get("node", ""))
        notes[node] = str(row.get("selection_reason", ""))
    return notes


def node_role(node: str, node_type: str, pump_nodes: set[str]) -> tuple[str, str, int]:
    roles: list[str] = []
    if node in MONITOR_NODES:
        roles.append("监测点")
    if node in CANDIDATE_NODES:
        roles.append("候选点")
    if node in TRUTH_INJECTION_NODES:
        roles.append("注入点")
    if node_type == "outfall":
        roles.append("排口")
    if node_type == "storage":
        roles.append("调蓄/存储节点")
    if node in pump_nodes:
        roles.append("泵站相关节点")
    if not roles:
        roles.append("普通节点")

    if node in TRUTH_INJECTION_NODES:
        return "+".join(roles), "#dc2626", 6
    if node in MONITOR_NODES:
        return "+".join(roles), "#2563eb", 5.5
    if node in CANDIDATE_NODES:
        return "+".join(roles), "#f59e0b", 5
    if node_type == "outfall":
        return "+".join(roles), "#111827", 6
    if node in pump_nodes:
        return "+".join(roles), "#7c3aed", 5.5
    if node_type == "storage":
        return "+".join(roles), "#14b8a6", 5.5
    return "+".join(roles), "#cbd5e1", 2.2


def build_data() -> dict[str, object]:
    nodes = pd.read_csv(NODES_CSV, encoding="utf-8-sig")
    links = pd.read_csv(LINKS_CSV, encoding="utf-8-sig")
    notes = load_plan_notes()

    pump_links = links[links["type"].astype(str).str.lower().eq("pump")]
    pump_nodes = set(pump_links["from_node"].astype(str)) | set(pump_links["to_node"].astype(str))

    node_rows = []
    for _, row in nodes.iterrows():
        node = str(row["node"])
        node_type = str(row.get("inp_node_type", "junction"))
        x = safe_float(row.get("coord_x"), math.nan)
        y = safe_float(row.get("coord_y"), math.nan)
        if math.isnan(x) or math.isnan(y):
            continue
        role, color, radius = node_role(node, node_type, pump_nodes)
        node_rows.append(
            {
                "id": node,
                "x": x,
                "y": y,
                "type": node_type,
                "role": role,
                "color": color,
                "radius": radius,
                "invert": safe_float(row.get("junction_invert_elev_m", row.get("storage_invert_elev_m", row.get("outfall_invert_elev_m")))),
                "max_depth": safe_float(row.get("junction_max_depth_m", row.get("storage_max_depth_m"))),
                "ponded_area": safe_float(row.get("junction_ponded_area_m2")),
                "direct_area": safe_float(row.get("direct_subcatchment_area_ha")),
                "avg_depth": safe_float(row.get("rpt_avg_depth_m")),
                "max_rpt_depth": safe_float(row.get("rpt_max_depth_m")),
                "note": notes.get(node, ""),
            }
        )

    node_set = {row["id"] for row in node_rows}
    link_rows = []
    for _, row in links.iterrows():
        from_node = str(row["from_node"])
        to_node = str(row["to_node"])
        if from_node not in node_set or to_node not in node_set:
            continue
        link_rows.append(
            {
                "id": str(row["link"]),
                "from": from_node,
                "to": to_node,
                "type": str(row["type"]),
                "length": safe_float(row.get("length_m")),
                "max_depth_ratio": safe_float(row.get("max_full_depth_ratio")),
            }
        )

    return {
        "nodes": node_rows,
        "links": link_rows,
        "monitors": list(MONITOR_NODES),
        "candidates": list(CANDIDATE_NODES),
        "injections": list(TRUTH_INJECTION_NODES),
    }


def build_html(data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>0520 动态布点可视化</title>
<style>
body {{
  margin: 0;
  background: #f5f7fb;
  color: #172033;
  font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
}}
header {{
  padding: 18px 28px;
  background: #102a43;
  color: #fff;
}}
h1 {{ margin: 0; font-size: 24px; }}
header p {{ margin: 6px 0 0; color: #dbeafe; }}
main {{
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 14px;
  padding: 14px;
}}
.panel {{
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 8px 26px rgba(16, 42, 67, .10);
}}
.side {{
  padding: 16px;
  max-height: calc(100vh - 92px);
  overflow: auto;
}}
.map-wrap {{
  height: calc(100vh - 104px);
  min-height: 680px;
  overflow: hidden;
  border: 1px solid #dbe4ef;
  position: relative;
  cursor: grab;
}}
.map-wrap:active {{
  cursor: grabbing;
}}
svg {{ width: 100%; height: 100%; background: #fff; }}
.pipe {{ stroke: #9fb0c5; stroke-width: 1.2; opacity: .55; }}
.pipe.pump {{ stroke: #7c3aed; stroke-width: 2.5; stroke-dasharray: 7 5; opacity: .75; }}
.pipe.full {{ stroke: #ef4444; stroke-width: 2.0; opacity: .75; }}
.node {{ cursor: pointer; stroke: #fff; stroke-width: 1.5; }}
.node:hover {{ stroke: #0f172a; stroke-width: 3; }}
.selected {{ stroke: #0f172a !important; stroke-width: 4 !important; }}
.label {{
  font-size: 10px;
  font-weight: 700;
  fill: #111827;
  paint-order: stroke;
  stroke: #fff;
  stroke-width: 4px;
  pointer-events: none;
}}
.all-label {{ display: none; }}
.show-all-labels .all-label {{ display: block; }}
.legend {{
  display: grid;
  gap: 8px;
  margin: 12px 0;
  font-size: 14px;
}}
.legend span {{ display: flex; align-items: center; gap: 8px; }}
.dot {{ width: 13px; height: 13px; border-radius: 50%; display: inline-block; }}
input[type="text"] {{
  width: 100%;
  box-sizing: border-box;
  padding: 9px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 9px;
  margin: 8px 0;
}}
button {{
  border: 0;
  border-radius: 9px;
  background: #2563eb;
  color: #fff;
  padding: 8px 11px;
  margin: 4px 4px 4px 0;
  cursor: pointer;
}}
label {{ display: block; margin: 8px 0; }}
.info {{
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  line-height: 1.65;
  white-space: pre-wrap;
  font-size: 13px;
}}
.tooltip {{
  position: fixed;
  z-index: 20;
  display: none;
  padding: 6px 9px;
  border-radius: 8px;
  background: rgba(15, 23, 42, .92);
  color: white;
  font-size: 13px;
  pointer-events: none;
  box-shadow: 0 8px 24px rgba(15, 23, 42, .25);
}}
.summary {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}}
.card {{
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 9px 10px;
  background: #f8fafc;
}}
.card b {{ font-size: 20px; color: #0f766e; }}
@media (max-width: 980px) {{
  main {{ grid-template-columns: 1fr; }}
  .map-wrap {{ height: 72vh; min-height: 520px; }}
}}
</style>
</head>
<body>
<header>
  <h1>0520 动态布点可视化</h1>
  <p>点击任意节点查看编号和类型；监测点、候选点、注入点用不同颜色标注。</p>
</header>
<main>
  <aside class="panel side">
    <h2>图层控制</h2>
    <label><input id="toggleLabels" type="checkbox"> 显示全部节点编号</label>
    <label><input id="togglePipes" type="checkbox" checked> 显示管段</label>
    <h2>节点搜索</h2>
    <input id="searchInput" type="text" list="nodeList" placeholder="输入节点编号，如 103、10、293">
    <datalist id="nodeList"></datalist>
    <button id="searchBtn">定位</button>
    <button id="resetBtn">重置视图</button>
    <div class="info">操作：鼠标滚轮缩放，按住左键拖动画面，鼠标悬停节点显示编号。</div>
    <div class="legend">
      <span><i class="dot" style="background:#dc2626"></i>注入点</span>
      <span><i class="dot" style="background:#2563eb"></i>监测点</span>
      <span><i class="dot" style="background:#f59e0b"></i>候选点</span>
      <span><i class="dot" style="background:#111827"></i>排口</span>
      <span><i class="dot" style="background:#7c3aed"></i>泵站相关节点</span>
      <span><i class="dot" style="background:#cbd5e1"></i>普通节点</span>
    </div>
    <div class="summary">
      <div class="card">监测点<br><b id="monitorCount"></b></div>
      <div class="card">候选点<br><b id="candidateCount"></b></div>
      <div class="card">注入点<br><b id="injectionCount"></b></div>
      <div class="card">总节点<br><b id="nodeCount"></b></div>
    </div>
    <h2>节点信息</h2>
    <div id="infoBox" class="info">点击图中的节点后，这里会显示节点编号、类型、是否为监测/候选/注入点等信息。</div>
  </aside>
  <section class="panel map-wrap">
    <svg id="networkSvg" viewBox="0 0 1400 900" role="img" aria-label="管网布点图">
      <g id="pipeLayer"></g>
      <g id="nodeLayer"></g>
      <g id="labelLayer"></g>
    </svg>
    <div id="tooltip" class="tooltip"></div>
  </section>
</main>
<script>
const DATA = {payload};
const svg = document.getElementById("networkSvg");
const pipeLayer = document.getElementById("pipeLayer");
const nodeLayer = document.getElementById("nodeLayer");
const labelLayer = document.getElementById("labelLayer");
const tooltip = document.getElementById("tooltip");
const width = 1400;
const height = 900;
const margin = 48;
const xs = DATA.nodes.map(n => n.x);
const ys = DATA.nodes.map(n => n.y);
const minX = Math.min(...xs), maxX = Math.max(...xs);
const minY = Math.min(...ys), maxY = Math.max(...ys);
const nodeMap = new Map(DATA.nodes.map(n => [n.id, n]));
let selected = null;
let viewBox = {{ x: 0, y: 0, w: width, h: height }};
let dragging = false;
let dragStart = null;

function sx(x) {{
  return margin + (x - minX) / Math.max(maxX - minX, 1) * (width - margin * 2);
}}
function sy(y) {{
  return height - margin - (y - minY) / Math.max(maxY - minY, 1) * (height - margin * 2);
}}
function addEl(name, attrs, parent) {{
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  parent.appendChild(el);
  return el;
}}
function detail(n) {{
  return [
    `节点编号：${{n.id}}`,
    `节点类型：${{n.type}}`,
    `布点类型：${{n.role}}`,
    `井底/底高程：${{n.invert.toFixed(3)}} m`,
    `最大深度：${{n.max_depth.toFixed(3)}} m`,
    `Ponding Area：${{n.ponded_area.toFixed(3)}} m²`,
    `直接汇水面积：${{n.direct_area.toFixed(4)}} ha`,
    `RPT平均水深：${{n.avg_depth.toFixed(3)}} m`,
    `RPT最大水深：${{n.max_rpt_depth.toFixed(3)}} m`,
    n.note ? `布点说明：${{n.note}}` : ""
  ].filter(Boolean).join("\\n");
}}
function selectNode(id, zoom = false) {{
  const n = nodeMap.get(id);
  if (!n) {{
    document.getElementById("infoBox").textContent = `未找到节点：${{id}}`;
    return;
  }}
  if (selected) selected.classList.remove("selected");
  selected = document.querySelector(`circle[data-node="${{CSS.escape(id)}}"]`);
  if (selected) selected.classList.add("selected");
  document.getElementById("infoBox").textContent = detail(n);
  if (zoom) {{
    const x = sx(n.x), y = sy(n.y);
    setViewBox(x - 260, y - 180, 520, 360);
  }}
}}
function setViewBox(x, y, w, h) {{
  viewBox = {{ x, y, w, h }};
  svg.setAttribute("viewBox", `${{x}} ${{y}} ${{w}} ${{h}}`);
}}
function clientToSvgPoint(evt) {{
  const rect = svg.getBoundingClientRect();
  return {{
    x: viewBox.x + (evt.clientX - rect.left) / rect.width * viewBox.w,
    y: viewBox.y + (evt.clientY - rect.top) / rect.height * viewBox.h
  }};
}}
function enableZoomPan() {{
  svg.addEventListener("wheel", evt => {{
    evt.preventDefault();
    const p = clientToSvgPoint(evt);
    const scale = evt.deltaY < 0 ? 0.82 : 1.22;
    const newW = Math.min(width * 3, Math.max(width * 0.08, viewBox.w * scale));
    const newH = Math.min(height * 3, Math.max(height * 0.08, viewBox.h * scale));
    const x = p.x - (p.x - viewBox.x) * (newW / viewBox.w);
    const y = p.y - (p.y - viewBox.y) * (newH / viewBox.h);
    setViewBox(x, y, newW, newH);
  }}, {{ passive: false }});
  svg.addEventListener("mousedown", evt => {{
    dragging = true;
    dragStart = {{ clientX: evt.clientX, clientY: evt.clientY, x: viewBox.x, y: viewBox.y }};
  }});
  window.addEventListener("mousemove", evt => {{
    if (!dragging || !dragStart) return;
    const rect = svg.getBoundingClientRect();
    const dx = (evt.clientX - dragStart.clientX) / rect.width * viewBox.w;
    const dy = (evt.clientY - dragStart.clientY) / rect.height * viewBox.h;
    setViewBox(dragStart.x - dx, dragStart.y - dy, viewBox.w, viewBox.h);
  }});
  window.addEventListener("mouseup", () => {{
    dragging = false;
    dragStart = null;
  }});
}}
function draw() {{
  DATA.links.forEach(l => {{
    const a = nodeMap.get(l.from);
    const b = nodeMap.get(l.to);
    if (!a || !b) return;
    const cls = `pipe ${{l.type === "pump" ? "pump" : ""}} ${{l.max_depth_ratio >= 1 ? "full" : ""}}`;
    addEl("line", {{
      x1: sx(a.x), y1: sy(a.y), x2: sx(b.x), y2: sy(b.y),
      class: cls, "data-link": l.id
    }}, pipeLayer);
  }});
  DATA.nodes.forEach(n => {{
    const circle = addEl("circle", {{
      cx: sx(n.x), cy: sy(n.y), r: n.radius,
      fill: n.color, class: "node", "data-node": n.id
    }}, nodeLayer);
    circle.addEventListener("click", () => selectNode(n.id));
    circle.addEventListener("mouseenter", evt => {{
      tooltip.style.display = "block";
      tooltip.textContent = `${{n.id}}｜${{n.role}}`;
    }});
    circle.addEventListener("mousemove", evt => {{
      tooltip.style.left = `${{evt.clientX + 12}}px`;
      tooltip.style.top = `${{evt.clientY + 12}}px`;
    }});
    circle.addEventListener("mouseleave", () => {{
      tooltip.style.display = "none";
    }});
    const labelClass = n.role !== "普通节点" ? "label" : "label all-label";
    addEl("text", {{
      x: sx(n.x) + n.radius + 2, y: sy(n.y) - n.radius - 2,
      class: labelClass
    }}, labelLayer).textContent = n.id;
  }});
}}
function init() {{
  draw();
  enableZoomPan();
  document.getElementById("monitorCount").textContent = DATA.monitors.length;
  document.getElementById("candidateCount").textContent = DATA.candidates.length;
  document.getElementById("injectionCount").textContent = DATA.injections.length;
  document.getElementById("nodeCount").textContent = DATA.nodes.length;
  const datalist = document.getElementById("nodeList");
  DATA.nodes.forEach(n => {{
    const opt = document.createElement("option");
    opt.value = n.id;
    datalist.appendChild(opt);
  }});
  document.getElementById("toggleLabels").addEventListener("change", e => {{
    svg.classList.toggle("show-all-labels", e.target.checked);
  }});
  document.getElementById("togglePipes").addEventListener("change", e => {{
    pipeLayer.style.display = e.target.checked ? "" : "none";
  }});
  document.getElementById("searchBtn").addEventListener("click", () => {{
    selectNode(document.getElementById("searchInput").value.trim(), true);
  }});
  document.getElementById("searchInput").addEventListener("keydown", e => {{
    if (e.key === "Enter") selectNode(e.target.value.trim(), true);
  }});
  document.getElementById("resetBtn").addEventListener("click", () => {{
    setViewBox(0, 0, width, height);
    if (selected) selected.classList.remove("selected");
    selected = null;
  }});
}}
init();
</script>
</body>
</html>
"""


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()
    OUT_HTML.write_text(build_html(data), encoding="utf-8")
    print(OUT_HTML)
    print("monitors=" + ",".join(MONITOR_NODES))
    print("candidates=" + ",".join(CANDIDATE_NODES))
    print("injections=" + ",".join(TRUTH_INJECTION_NODES))


if __name__ == "__main__":
    main()
