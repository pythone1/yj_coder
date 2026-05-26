from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path


MODEL_DIR = Path(r"E:\PY\LSTM\0327\export_ascii\当前确认模型_泵站0.5开0.2关_注水0.3倍调整")
INP_PATH = MODEL_DIR / "0327_由旱天基线重建_三点注水模型_0.3倍.inp"
HTML_PATH = MODEL_DIR / "0327_排口与关键节点可视化.html"
NODES_CSV_PATH = MODEL_DIR / "0327_排口与关键节点信息.csv"
LINKS_CSV_PATH = MODEL_DIR / "0327_排口与关键节点连接关系.csv"
MANIFEST_PATH = MODEL_DIR / "0327_排口与关键节点说明.json"

INJECTION_NODES = ["J76", "J124", "J140"]
PUMP_NODES = ["J232", "J41"]
TERMINAL_NODES = ["J231", "J132"]
FLOODED_NODES = ["J41"]
OUTFALL_NAMES = ["J132"]
HIGHLIGHT_LINKS = ["C228_2", "C89"]


def read_inp_sections(path: Path) -> dict[str, list[str]]:
    text = path.read_text(encoding="gbk", errors="ignore")
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped.strip("[]").upper()
            sections[current] = []
        elif current is not None:
            sections[current].append(line.rstrip("\n"))
    return sections


def clean_data_lines(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        result.append(stripped)
    return result


def split_parts(line: str) -> list[str]:
    return re.split(r"\s+", line.strip())


def parse_nodes(sections: dict[str, list[str]]) -> dict[str, dict[str, object]]:
    nodes: dict[str, dict[str, object]] = {}

    for line in clean_data_lines(sections.get("JUNCTIONS", [])):
        parts = split_parts(line)
        if len(parts) < 6:
            continue
        nodes[parts[0]] = {
            "name": parts[0],
            "kind": "Junction",
            "invert_elev": float(parts[1]),
            "max_depth": float(parts[2]),
            "init_depth": float(parts[3]),
            "surcharge_depth": float(parts[4]),
            "ponded_area": float(parts[5]),
        }

    for line in clean_data_lines(sections.get("STORAGE", [])):
        parts = split_parts(line)
        if len(parts) < 5:
            continue
        nodes[parts[0]] = {
            "name": parts[0],
            "kind": "Storage",
            "invert_elev": float(parts[1]),
            "max_depth": float(parts[2]),
            "init_depth": float(parts[3]),
            "shape": parts[4],
        }

    for line in clean_data_lines(sections.get("OUTFALLS", [])):
        parts = split_parts(line)
        if len(parts) < 4:
            continue
        nodes[parts[0]] = {
            "name": parts[0],
            "kind": "Outfall",
            "invert_elev": float(parts[1]),
            "outfall_type": parts[2],
            "stage_data": parts[3],
            "gated": parts[4] if len(parts) > 4 else "",
        }

    for line in clean_data_lines(sections.get("COORDINATES", [])):
        parts = split_parts(line)
        if len(parts) < 3:
            continue
        node = nodes.setdefault(parts[0], {"name": parts[0], "kind": "Unknown"})
        node["x"] = float(parts[1])
        node["y"] = float(parts[2])

    for line in clean_data_lines(sections.get("INFLOWS", [])):
        parts = split_parts(line)
        if len(parts) < 4:
            continue
        node = nodes.setdefault(parts[0], {"name": parts[0], "kind": "Unknown"})
        node["inflow_type"] = parts[1]
        node["timeseries"] = parts[2]
        node["constituent"] = parts[3]
    return nodes


def parse_links(sections: dict[str, list[str]]) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []

    for line in clean_data_lines(sections.get("CONDUITS", [])):
        parts = split_parts(line)
        if len(parts) < 3:
            continue
        links.append(
            {
                "name": parts[0],
                "kind": "Conduit",
                "from_node": parts[1],
                "to_node": parts[2],
            }
        )

    for line in clean_data_lines(sections.get("PUMPS", [])):
        parts = split_parts(line)
        if len(parts) < 3:
            continue
        links.append(
            {
                "name": parts[0],
                "kind": "Pump",
                "from_node": parts[1],
                "to_node": parts[2],
                "curve": parts[3] if len(parts) > 3 else "",
                "startup": parts[5] if len(parts) > 5 else "",
                "shutoff": parts[6] if len(parts) > 6 else "",
            }
        )

    return links


def classify_node(name: str, info: dict[str, object]) -> str:
    if name in OUTFALL_NAMES:
        return "结构排口"
    if name in TERMINAL_NODES:
        return "末端关键节点"
    if name in PUMP_NODES:
        return "泵站链路节点"
    if name in INJECTION_NODES:
        return "注水点"
    if name in FLOODED_NODES:
        return "事件溢流点"
    if info.get("kind") == "Outfall":
        return "结构排口"
    return "关键关联节点"


def collect_focus_nodes(nodes: dict[str, dict[str, object]], links: list[dict[str, object]]) -> list[str]:
    focus = set(INJECTION_NODES + PUMP_NODES + TERMINAL_NODES + FLOODED_NODES + OUTFALL_NAMES)
    focus.update(["J218", "J56"])
    for link in links:
        if link["name"] in HIGHLIGHT_LINKS:
            focus.add(link["from_node"])
            focus.add(link["to_node"])
    for link in links:
        if link["from_node"] in focus or link["to_node"] in focus:
            focus.add(link["from_node"])
            focus.add(link["to_node"])
    return sorted(node for node in focus if node in nodes)


def export_csvs(nodes: dict[str, dict[str, object]], links: list[dict[str, object]], focus_nodes: list[str]) -> None:
    with NODES_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "节点名称",
                "节点角色",
                "节点类型",
                "底高程",
                "最大水深",
                "X",
                "Y",
                "注水时序",
            ],
        )
        writer.writeheader()
        for name in focus_nodes:
            info = nodes[name]
            writer.writerow(
                {
                    "节点名称": name,
                    "节点角色": classify_node(name, info),
                    "节点类型": info.get("kind", ""),
                    "底高程": info.get("invert_elev", ""),
                    "最大水深": info.get("max_depth", ""),
                    "X": info.get("x", ""),
                    "Y": info.get("y", ""),
                    "注水时序": info.get("timeseries", ""),
                }
            )

    with LINKS_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["连接名称", "连接类型", "起点", "终点", "备注"],
        )
        writer.writeheader()
        for link in links:
            if link["from_node"] in focus_nodes or link["to_node"] in focus_nodes or link["name"] in HIGHLIGHT_LINKS:
                note = ""
                if link["name"] == "C89":
                    note = "J231到结构排口J132的最后一段"
                elif link["name"] == "C228_2":
                    note = "关键泵站"
                writer.writerow(
                    {
                        "连接名称": link["name"],
                        "连接类型": link["kind"],
                        "起点": link["from_node"],
                        "终点": link["to_node"],
                        "备注": note,
                    }
                )


def color_for_role(role: str) -> str:
    return {
        "结构排口": "#111827",
        "末端关键节点": "#2563eb",
        "泵站链路节点": "#f59e0b",
        "注水点": "#dc2626",
        "事件溢流点": "#7c3aed",
        "关键关联节点": "#6b7280",
    }.get(role, "#6b7280")


def size_for_role(role: str) -> int:
    return {
        "结构排口": 18,
        "末端关键节点": 16,
        "泵站链路节点": 15,
        "注水点": 16,
        "事件溢流点": 15,
        "关键关联节点": 11,
    }.get(role, 10)


def render_html(nodes: dict[str, dict[str, object]], links: list[dict[str, object]], focus_nodes: list[str]) -> None:
    focus_node_rows = []
    for name in focus_nodes:
        info = nodes[name]
        role = classify_node(name, info)
        focus_node_rows.append(
            {
                "name": name,
                "role": role,
                "kind": info.get("kind", ""),
                "x": info.get("x", 0.0),
                "y": info.get("y", 0.0),
                "invert": info.get("invert_elev", ""),
                "depth": info.get("max_depth", ""),
                "timeseries": info.get("timeseries", ""),
                "color": color_for_role(role),
                "size": size_for_role(role),
            }
        )

    focus_links = []
    for link in links:
        if link["from_node"] in focus_nodes and link["to_node"] in focus_nodes:
            focus_links.append(link)
        elif link["name"] in HIGHLIGHT_LINKS:
            focus_links.append(link)

    html_text = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>0327 排口与关键节点可视化</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    .wrap {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
    .title {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
    .subtitle {{ color: #475569; margin-bottom: 18px; }}
    .grid {{ display: grid; grid-template-columns: 1.7fr 1fr; gap: 18px; }}
    .card {{ background: white; border-radius: 14px; box-shadow: 0 8px 30px rgba(15,23,42,0.08); padding: 16px; }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
    .dot {{ width: 12px; height: 12px; border-radius: 999px; display: inline-block; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 8px 6px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #f8fafc; position: sticky; top: 0; }}
    .small {{ color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">0327 排口与关键节点可视化</div>
    <div class="subtitle">当前模型：泵站 0.5 开 / 0.2 关，注水 0.3 倍调整版。结构排口是 J132，工程重点末端链路是 J231 → C89 → J132。</div>
    <div class="grid">
      <div class="card">
        <div id="plot" style="width:100%;height:820px;"></div>
      </div>
      <div class="card">
        <h3>角色说明</h3>
        <div class="legend-item"><span class="dot" style="background:#111827"></span>结构排口：J132</div>
        <div class="legend-item"><span class="dot" style="background:#2563eb"></span>末端关键节点：J231 等</div>
        <div class="legend-item"><span class="dot" style="background:#f59e0b"></span>泵站链路节点：J232 / J41</div>
        <div class="legend-item"><span class="dot" style="background:#dc2626"></span>注水点：J76 / J124 / J140</div>
        <div class="legend-item"><span class="dot" style="background:#7c3aed"></span>事件溢流关注点</div>
        <p class="small">注：J41 是当前调整后 0.3 倍事件下仍有溢流的节点；J56、J218 是上一版中较敏感的节点，这里也保留观察。</p>
        <h3>关键节点表</h3>
        <div style="max-height:520px; overflow:auto;">
          <table>
            <thead>
              <tr><th>节点</th><th>角色</th><th>类型</th><th>底高程</th><th>最大水深</th><th>注水时序</th></tr>
            </thead>
            <tbody>
              {"".join(
                  f"<tr><td>{html.escape(str(row['name']))}</td><td>{html.escape(str(row['role']))}</td><td>{html.escape(str(row['kind']))}</td><td>{html.escape(str(row['invert']))}</td><td>{html.escape(str(row['depth']))}</td><td>{html.escape(str(row['timeseries']))}</td></tr>"
                  for row in focus_node_rows
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <script>
    const nodes = {json.dumps(focus_node_rows, ensure_ascii=False)};
    const links = {json.dumps(focus_links, ensure_ascii=False)};
    const nodeMap = Object.fromEntries(nodes.map(n => [n.name, n]));

    const traces = [];

    for (const link of links) {{
      const a = nodeMap[link.from_node];
      const b = nodeMap[link.to_node];
      if (!a || !b) continue;
      const isHighlight = ['C89', 'C228_2'].includes(link.name);
      traces.push({{
        x: [a.x, b.x],
        y: [a.y, b.y],
        mode: 'lines',
        line: {{
          color: isHighlight ? '#0f172a' : '#94a3b8',
          width: isHighlight ? 4 : 2,
          dash: link.kind === 'Pump' ? 'dot' : 'solid'
        }},
        hovertemplate: `${{link.name}}<br>${{link.kind}}<br>${{link.from_node}} → ${{link.to_node}}<extra></extra>`,
        showlegend: false
      }});
    }}

    const roleGroups = [...new Set(nodes.map(n => n.role))];
    for (const role of roleGroups) {{
      const subset = nodes.filter(n => n.role === role);
      traces.push({{
        x: subset.map(n => n.x),
        y: subset.map(n => n.y),
        text: subset.map(n => n.name),
        customdata: subset.map(n => [n.role, n.kind, n.invert, n.depth, n.timeseries]),
        mode: 'markers+text',
        textposition: 'top center',
        marker: {{
          size: subset.map(n => n.size),
          color: subset.map(n => n.color),
          line: {{color: 'white', width: 1.5}}
        }},
        name: role,
        hovertemplate: '节点=%{{text}}<br>角色=%{{customdata[0]}}<br>类型=%{{customdata[1]}}<br>底高程=%{{customdata[2]}}<br>最大水深=%{{customdata[3]}}<br>注水时序=%{{customdata[4]}}<extra></extra>'
      }});
    }}

    Plotly.newPlot('plot', traces, {{
      title: '排口与关键节点网络位置图',
      xaxis: {{title: 'X 坐标'}},
      yaxis: {{title: 'Y 坐标', scaleanchor: 'x', scaleratio: 1}},
      paper_bgcolor: 'white',
      plot_bgcolor: 'white',
      legend: {{orientation: 'h', y: 1.08}}
    }}, {{responsive: true}});
  </script>
</body>
</html>"""
    HTML_PATH.write_text(html_text, encoding="utf-8")


def write_manifest(focus_nodes: list[str]) -> None:
    manifest = {
        "model_inp": str(INP_PATH),
        "html": str(HTML_PATH),
        "nodes_csv": str(NODES_CSV_PATH),
        "links_csv": str(LINKS_CSV_PATH),
        "focus_nodes": focus_nodes,
        "injection_nodes": INJECTION_NODES,
        "pump_nodes": PUMP_NODES,
        "terminal_nodes": TERMINAL_NODES,
        "outfall": OUTFALL_NAMES,
        "highlight_links": HIGHLIGHT_LINKS,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    sections = read_inp_sections(INP_PATH)
    nodes = parse_nodes(sections)
    links = parse_links(sections)
    focus_nodes = collect_focus_nodes(nodes, links)
    export_csvs(nodes, links, focus_nodes)
    render_html(nodes, links, focus_nodes)
    write_manifest(focus_nodes)
    print(str(HTML_PATH))
    print(str(NODES_CSV_PATH))
    print(str(LINKS_CSV_PATH))


if __name__ == "__main__":
    main()
