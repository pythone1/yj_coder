from __future__ import annotations

import csv
import json
import re
from collections import OrderedDict

from config_0401 import (
    BASELINE_MODEL_INP,
    CANDIDATE_NODES,
    LAYOUT_HTML,
    LAYOUT_LINK_CSV,
    LAYOUT_NODE_CSV,
    LAYOUT_SUMMARY_JSON,
    MONITOR_NODES,
    TERMINAL_NODE,
    TRUTH_INJECTION_NODES,
)

OUTFALL_NODE = "J132"
PUMP_NODES = ("J232", "J41")
SENSITIVE_NODES = ("J56", "J218")

ROLE_ORDER = [
    "真值注水点",
    "监测点",
    "候选布设点",
    "泵站链路节点",
    "末端关键节点",
    "结构排口",
    "敏感节点",
    "关联节点",
]

ROLE_STYLES = {
    "真值注水点": {"color": "#dc2626", "size": 18},
    "监测点": {"color": "#2563eb", "size": 15},
    "候选布设点": {"color": "#f59e0b", "size": 13},
    "泵站链路节点": {"color": "#0f766e", "size": 16},
    "末端关键节点": {"color": "#1d4ed8", "size": 16},
    "结构排口": {"color": "#111827", "size": 18},
    "敏感节点": {"color": "#7c3aed", "size": 14},
    "关联节点": {"color": "#94a3b8", "size": 8},
}


def read_text(path):
    return path.read_text(encoding="gbk", errors="ignore")


def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped.strip("[]").upper()
            sections[current] = []
        elif current is not None:
            sections[current].append(raw)
    return sections


def clean_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith(";")]


def parts(line: str) -> list[str]:
    return re.split(r"\s+", line.strip())


def parse_nodes(sections: dict[str, list[str]]) -> dict[str, dict[str, object]]:
    nodes: dict[str, dict[str, object]] = {}
    for line in clean_lines(sections.get("JUNCTIONS", [])):
        p = parts(line)
        if len(p) >= 6:
            nodes[p[0]] = {"name": p[0], "type": "Junction", "invert": float(p[1]), "depth": float(p[2])}
    for line in clean_lines(sections.get("STORAGE", [])):
        p = parts(line)
        if len(p) >= 3:
            nodes[p[0]] = {"name": p[0], "type": "Storage", "invert": float(p[1]), "depth": float(p[2])}
    for line in clean_lines(sections.get("OUTFALLS", [])):
        p = parts(line)
        if len(p) >= 4:
            nodes[p[0]] = {"name": p[0], "type": "Outfall", "invert": float(p[1]), "depth": "", "stage": p[3]}
    for line in clean_lines(sections.get("COORDINATES", [])):
        p = parts(line)
        if len(p) >= 3:
            node = nodes.setdefault(p[0], {"name": p[0], "type": "Unknown"})
            node["x"] = float(p[1])
            node["y"] = float(p[2])
    return nodes


def parse_links(sections: dict[str, list[str]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for line in clean_lines(sections.get("CONDUITS", [])):
        p = parts(line)
        if len(p) >= 3:
            links.append({"name": p[0], "type": "Conduit", "from": p[1], "to": p[2]})
    for line in clean_lines(sections.get("PUMPS", [])):
        p = parts(line)
        if len(p) >= 3:
            links.append({"name": p[0], "type": "Pump", "from": p[1], "to": p[2]})
    return links


def classify(name: str, info: dict[str, object]) -> str:
    if name in TRUTH_INJECTION_NODES:
        return "真值注水点"
    if name in MONITOR_NODES:
        return "监测点"
    if name in CANDIDATE_NODES:
        return "候选布设点"
    if name in PUMP_NODES:
        return "泵站链路节点"
    if name == TERMINAL_NODE:
        return "末端关键节点"
    if name == OUTFALL_NODE or info.get("type") == "Outfall":
        return "结构排口"
    if name in SENSITIVE_NODES:
        return "敏感节点"
    return "关联节点"


def export_tables(nodes: dict[str, dict[str, object]], links: list[dict[str, str]]) -> None:
    with LAYOUT_NODE_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["节点名称", "节点角色", "节点类型", "底高程", "最大水深", "X", "Y"],
        )
        writer.writeheader()
        for name in sorted(nodes):
            info = nodes[name]
            writer.writerow(
                {
                    "节点名称": name,
                    "节点角色": classify(name, info),
                    "节点类型": info.get("type", ""),
                    "底高程": info.get("invert", ""),
                    "最大水深": info.get("depth", ""),
                    "X": info.get("x", ""),
                    "Y": info.get("y", ""),
                }
            )

    with LAYOUT_LINK_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["连接名称", "连接类型", "起点", "终点", "备注"],
        )
        writer.writeheader()
        for link in links:
            note = ""
            if link["name"] == "C228_2":
                note = "关键泵站"
            elif link["name"] == "C89":
                note = "末端关键连接 J231 -> J132"
            writer.writerow(
                {
                    "连接名称": link["name"],
                    "连接类型": link["type"],
                    "起点": link["from"],
                    "终点": link["to"],
                    "备注": note,
                }
            )


def build_role_traces(node_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: OrderedDict[str, list[dict[str, object]]] = OrderedDict((role, []) for role in ROLE_ORDER)
    for row in node_rows:
        grouped[row["role"]].append(row)

    traces: list[dict[str, object]] = []
    for role, rows in grouped.items():
        if not rows:
            continue
        style = ROLE_STYLES[role]
        traces.append(
            {
                "type": "scatter",
                "name": role,
                "legendgroup": role,
                "x": [row["x"] for row in rows],
                "y": [row["y"] for row in rows],
                "mode": "markers+text",
                "text": [row["name"] for row in rows],
                "textposition": "top center",
                "marker": {
                    "size": [style["size"] for _ in rows],
                    "color": [style["color"] for _ in rows],
                    "line": {"color": "#ffffff", "width": 1},
                },
                "customdata": [[row["type"], row["invert"], row["depth"]] for row in rows],
                "hovertemplate": "<b>%{text}</b><br>角色="
                + role
                + "<br>类型=%{customdata[0]}<br>底高程=%{customdata[1]}<br>最大水深=%{customdata[2]}<extra></extra>",
            }
        )
    return traces


def export_html(nodes: dict[str, dict[str, object]], links: list[dict[str, str]]) -> None:
    node_rows = []
    for name, info in nodes.items():
        node_rows.append(
            {
                "name": name,
                "role": classify(name, info),
                "type": info.get("type", ""),
                "invert": info.get("invert", ""),
                "depth": info.get("depth", ""),
                "x": info.get("x", 0.0),
                "y": info.get("y", 0.0),
            }
        )

    role_traces = build_role_traces(node_rows)
    node_map = {row["name"]: row for row in node_rows}

    edge_traces: list[dict[str, object]] = []
    edge_traces.append(
        {
            "type": "scatter",
            "name": "一般连接",
            "legendgroup": "连接",
            "x": [],
            "y": [],
            "mode": "lines",
            "line": {"color": "#cbd5e1", "width": 1.1},
            "hoverinfo": "skip",
            "showlegend": True,
        }
    )
    edge_traces.append(
        {
            "type": "scatter",
            "name": "关键连接",
            "legendgroup": "连接",
            "x": [],
            "y": [],
            "mode": "lines",
            "line": {"color": "#0f172a", "width": 3.5},
            "hoverinfo": "skip",
            "showlegend": True,
        }
    )
    for link in links:
        a = node_map.get(link["from"])
        b = node_map.get(link["to"])
        if not a or not b:
            continue
        idx = 1 if link["name"] in {"C228_2", "C89"} else 0
        edge_traces[idx]["x"].extend([a["x"], b["x"], None])
        edge_traces[idx]["y"].extend([a["y"], b["y"], None])

    traces = edge_traces + role_traces

    controls_html = "\n".join(
        [
            f'<label><input type="checkbox" class="role-toggle" data-role="{role}" checked> {role}</label>'
            for role in ROLE_ORDER
        ]
    )

    html_text = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>0401 布设方案可视化</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f8fafc; margin: 0; color: #0f172a; }}
    .wrap {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
    .grid {{ display: grid; grid-template-columns: 1.8fr 0.9fr; gap: 18px; }}
    .card {{ background: #fff; border-radius: 14px; box-shadow: 0 8px 24px rgba(15,23,42,.08); padding: 16px; }}
    .toggles {{ display: grid; grid-template-columns: 1fr; gap: 8px; margin-bottom: 16px; }}
    .toggles label {{ display: flex; align-items: center; gap: 8px; font-size: 14px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 8px 6px; text-align: left; }}
    th {{ background: #f8fafc; }}
    .tip {{ font-size: 12px; color: #475569; margin-top: 8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>0401 布设方案可视化</h1>
    <p>按类型开关查看候选布设点、监测点、真值注水点、泵站链路、末端与排口。图例和右侧开关都可以控制显隐。</p>
    <div class="grid">
      <div class="card">
        <div id="plot" style="width:100%;height:900px;"></div>
      </div>
      <div class="card">
        <h3>类型开关</h3>
        <div class="toggles">
          {controls_html}
        </div>
        <div class="tip">说明：连接图层默认始终显示；如果想只看某一类节点，可以取消其它类型勾选。</div>
        <h3 style="margin-top:20px;">角色说明</h3>
        <table>
          <thead><tr><th>角色</th><th>说明</th></tr></thead>
          <tbody>
            <tr><td>真值注水点</td><td>当前事件模板里三处注水节点 J76 / J124 / J140</td></tr>
            <tr><td>监测点</td><td>用于拟合的 {len(MONITOR_NODES)} 个监测节点</td></tr>
            <tr><td>候选布设点</td><td>GA / AM 搜索的 20 个候选点</td></tr>
            <tr><td>泵站链路节点</td><td>J232 → C228_2 → J41</td></tr>
            <tr><td>末端关键节点</td><td>J231</td></tr>
            <tr><td>结构排口</td><td>J132</td></tr>
            <tr><td>敏感节点</td><td>J56 / J218</td></tr>
            <tr><td>关联节点</td><td>其余网络节点</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <script>
    const traces = {json.dumps(traces, ensure_ascii=False)};
    const plotDiv = document.getElementById('plot');
    Plotly.newPlot(plotDiv, traces, {{
      paper_bgcolor: '#fff',
      plot_bgcolor: '#fff',
      margin: {{l:20, r:20, t:20, b:20}},
      xaxis: {{title:'X', showgrid:false, zeroline:false}},
      yaxis: {{title:'Y', showgrid:false, zeroline:false, scaleanchor:'x', scaleratio:1}},
      legend: {{orientation:'h', yanchor:'bottom', y:1.02, xanchor:'left', x:0}}
    }}, {{responsive:true}});

    const roleTraceIndex = new Map();
    traces.forEach((trace, index) => {{
      if ({json.dumps(ROLE_ORDER, ensure_ascii=False)}.includes(trace.name)) {{
        roleTraceIndex.set(trace.name, index);
      }}
    }});

    document.querySelectorAll('.role-toggle').forEach((input) => {{
      input.addEventListener('change', () => {{
        const role = input.dataset.role;
        const index = roleTraceIndex.get(role);
        if (index === undefined) return;
        Plotly.restyle(plotDiv, {{visible: input.checked ? true : 'legendonly'}}, [index]);
      }});
    }});
  </script>
</body>
</html>
"""
    LAYOUT_HTML.write_text(html_text, encoding="utf-8")


def main() -> None:
    sections = split_sections(read_text(BASELINE_MODEL_INP))
    nodes = parse_nodes(sections)
    links = parse_links(sections)
    export_tables(nodes, links)
    export_html(nodes, links)
    summary = {
        "baseline_inp": str(BASELINE_MODEL_INP),
        "candidate_count": len(CANDIDATE_NODES),
        "monitor_count": len(MONITOR_NODES),
        "truth_injection_nodes": list(TRUTH_INJECTION_NODES),
        "pump_nodes": list(PUMP_NODES),
        "terminal_node": TERMINAL_NODE,
        "outfall_node": OUTFALL_NODE,
        "roles": ROLE_ORDER,
    }
    LAYOUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
