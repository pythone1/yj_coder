from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import plotly.graph_objects as go


BASE_DIR = Path(r"E:\PY\LSTM\模型文件有污水量")
INPUT_FILES = [
    BASE_DIR / "盱眙污水管3（入渗点有雨水量）.inp",
    BASE_DIR / "盱眙污水管3（入渗点无雨水量）.inp",
]


NODE_STYLE = {
    "normal": {"color": "#8a8f98", "size": 3, "label": "普通节点"},
    "tagged": {"color": "#2f7ed8", "size": 5, "label": "带 TAG 标签节点"},
    "monitor": {"color": "#00a676", "size": 7, "label": "监测点"},
    "infiltration": {"color": "#ff9f1c", "size": 8, "label": "入渗点"},
    "inflow": {"color": "#ef476f", "size": 9, "label": "外部入流节点"},
}

STYLE_PRIORITY = {
    "normal": 0,
    "tagged": 1,
    "monitor": 2,
    "infiltration": 3,
    "inflow": 4,
}


def read_lines(path: Path) -> List[str]:
    for encoding in ("utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding).splitlines()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"unable to decode {path}")


def parse_sections(lines: Iterable[str]) -> Dict[str, List[Tuple[int, str]]]:
    sections: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
    current = ""
    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped.strip("[]").upper()
            continue
        if current:
            sections[current].append((idx, line))
    return sections


def parse_named_rows(section_lines: Iterable[Tuple[int, str]]) -> List[Tuple[int, List[str]]]:
    rows: List[Tuple[int, List[str]]] = []
    for line_no, raw in section_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith(";"):
            continue
        rows.append((line_no, stripped.split()))
    return rows


def parse_junction_comments(section_lines: Iterable[Tuple[int, str]]) -> Dict[str, str]:
    marker_map: Dict[str, str] = {}
    pending_comment = ""
    for _, raw in section_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(";"):
            comment = stripped.lstrip(";").strip()
            pending_comment = comment or pending_comment
            continue
        tokens = stripped.split()
        if not tokens:
            continue
        node_name = tokens[0]
        if pending_comment in {"入渗点", "监测点"}:
            marker_map[node_name] = pending_comment
        pending_comment = ""
    return marker_map


def parse_model(path: Path) -> dict:
    lines = read_lines(path)
    sections = parse_sections(lines)

    coords = {}
    for _, tokens in parse_named_rows(sections.get("COORDINATES", [])):
        if len(tokens) >= 3:
            coords[tokens[0]] = {"x": float(tokens[1]), "y": float(tokens[2])}

    nodes = {}
    for _, tokens in parse_named_rows(sections.get("JUNCTIONS", [])):
        if len(tokens) >= 3:
            nodes[tokens[0]] = {
                "type": "JUNCTION",
                "elevation": float(tokens[1]),
                "max_depth": float(tokens[2]),
            }
    for _, tokens in parse_named_rows(sections.get("OUTFALLS", [])):
        if len(tokens) >= 2:
            nodes[tokens[0]] = {
                "type": "OUTFALL",
                "elevation": float(tokens[1]),
                "max_depth": 0.0,
            }
    for _, tokens in parse_named_rows(sections.get("STORAGE", [])):
        if len(tokens) >= 3:
            nodes[tokens[0]] = {
                "type": "STORAGE",
                "elevation": float(tokens[1]),
                "max_depth": float(tokens[2]),
            }

    for name, coord in coords.items():
        if name in nodes:
            nodes[name].update(coord)

    conduits = []
    for _, tokens in parse_named_rows(sections.get("CONDUITS", [])):
        if len(tokens) >= 5:
            conduits.append(
                {
                    "name": tokens[0],
                    "from_node": tokens[1],
                    "to_node": tokens[2],
                    "length": float(tokens[3]),
                    "roughness": float(tokens[4]),
                }
            )

    xsections = {}
    for _, tokens in parse_named_rows(sections.get("XSECTIONS", [])):
        if len(tokens) >= 3:
            xsections[tokens[0]] = {
                "shape": tokens[1],
                "geom1": float(tokens[2]),
            }

    inflow_nodes = set()
    inflow_series = {}
    for _, tokens in parse_named_rows(sections.get("INFLOWS", [])):
        if len(tokens) >= 3:
            inflow_nodes.add(tokens[0])
            inflow_series[tokens[0]] = tokens[2]

    tags = defaultdict(list)
    for _, tokens in parse_named_rows(sections.get("TAGS", [])):
        if len(tokens) >= 3:
            obj_type, obj_name = tokens[0], tokens[1]
            tag = " ".join(tokens[2:])
            tags[obj_name].append(f"{obj_type}:{tag}")

    comments = parse_junction_comments(sections.get("JUNCTIONS", []))
    infiltration_nodes = {name for name, comment in comments.items() if comment == "入渗点"}
    monitor_nodes = {name for name, comment in comments.items() if comment == "监测点"}

    return {
        "path": path,
        "nodes": nodes,
        "conduits": conduits,
        "xsections": xsections,
        "inflow_nodes": inflow_nodes,
        "inflow_series": inflow_series,
        "tags": tags,
        "infiltration_nodes": infiltration_nodes,
        "monitor_nodes": monitor_nodes,
    }


def classify_node(node_name: str, model: dict) -> str:
    category = "normal"
    if node_name in model["tags"]:
        category = "tagged"
    if node_name in model["monitor_nodes"]:
        category = "monitor"
    if node_name in model["infiltration_nodes"]:
        category = "infiltration"
    if node_name in model["inflow_nodes"]:
        category = "inflow"
    return category


def build_hover_text(node_name: str, node_data: dict, model: dict) -> str:
    categories = [NODE_STYLE[classify_node(node_name, model)]["label"]]
    if node_name in model["monitor_nodes"] and "监测点" not in categories:
        categories.append("监测点")
    if node_name in model["infiltration_nodes"] and "入渗点" not in categories:
        categories.append("入渗点")
    if node_name in model["inflow_nodes"] and "外部入流节点" not in categories:
        categories.append("外部入流节点")
    if node_name in model["tags"] and "带 TAG 标签节点" not in categories:
        categories.append("带 TAG 标签节点")

    extras = []
    if node_name in model["inflow_series"]:
        extras.append(f"入流时序: {model['inflow_series'][node_name]}")
    if node_name in model["tags"]:
        extras.append("标签: " + "; ".join(model["tags"][node_name][:4]))

    return (
        f"<b>{node_name}</b><br>"
        f"类型: {node_data['type']}<br>"
        f"分类: {' / '.join(categories)}<br>"
        f"高程: {node_data['elevation']:.3f} m<br>"
        f"最大深度: {node_data['max_depth']:.3f} m<br>"
        f"X: {node_data['x']:.3f}<br>"
        f"Y: {node_data['y']:.3f}"
        + (f"<br>{'<br>'.join(extras)}" if extras else "")
    )


def add_conduit_trace(fig: go.Figure, model: dict) -> None:
    x_lines: List[float | None] = []
    y_lines: List[float | None] = []
    z_lines: List[float | None] = []
    hover_x: List[float] = []
    hover_y: List[float] = []
    hover_z: List[float] = []
    hover_text: List[str] = []

    for conduit in model["conduits"]:
        from_node = model["nodes"].get(conduit["from_node"])
        to_node = model["nodes"].get(conduit["to_node"])
        if not from_node or not to_node:
            continue
        if any(key not in from_node for key in ("x", "y")) or any(key not in to_node for key in ("x", "y")):
            continue

        x1, y1, z1 = from_node["x"], from_node["y"], from_node["elevation"]
        x2, y2, z2 = to_node["x"], to_node["y"], to_node["elevation"]
        x_lines.extend([x1, x2, None])
        y_lines.extend([y1, y2, None])
        z_lines.extend([z1, z2, None])

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        mid_z = (z1 + z2) / 2
        hover_x.append(mid_x)
        hover_y.append(mid_y)
        hover_z.append(mid_z)
        xsec = model["xsections"].get(conduit["name"], {})
        hover_text.append(
            f"<b>{conduit['name']}</b><br>"
            f"{conduit['from_node']} -> {conduit['to_node']}<br>"
            f"长度: {conduit['length']:.3f} m<br>"
            f"糙率: {conduit['roughness']:.3f}<br>"
            f"断面: {xsec.get('shape', 'N/A')}<br>"
            f"Geom1/管径: {xsec.get('geom1', 0):.3f}"
        )

    fig.add_trace(
        go.Scatter3d(
            x=x_lines,
            y=y_lines,
            z=z_lines,
            mode="lines",
            line=dict(color="rgba(90, 105, 120, 0.45)", width=3),
            name="管道",
            hoverinfo="none",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=hover_x,
            y=hover_y,
            z=hover_z,
            mode="markers",
            marker=dict(size=2, color="rgba(0,0,0,0)"),
            text=hover_text,
            hoverinfo="text",
            name="管道信息",
            showlegend=False,
        )
    )


def add_node_traces(fig: go.Figure, model: dict) -> None:
    grouped = defaultdict(lambda: {"x": [], "y": [], "z": [], "text": []})

    for node_name, node_data in model["nodes"].items():
        if "x" not in node_data or "y" not in node_data:
            continue
        category = classify_node(node_name, model)
        grouped[category]["x"].append(node_data["x"])
        grouped[category]["y"].append(node_data["y"])
        grouped[category]["z"].append(node_data["elevation"])
        grouped[category]["text"].append(build_hover_text(node_name, node_data, model))

    for category, style in sorted(NODE_STYLE.items(), key=lambda item: STYLE_PRIORITY[item[0]]):
        data = grouped.get(category)
        if not data or not data["x"]:
            continue
        fig.add_trace(
            go.Scatter3d(
                x=data["x"],
                y=data["y"],
                z=data["z"],
                mode="markers+text" if category in {"inflow", "infiltration", "monitor"} else "markers",
                text=[
                    text.split("<br>", 1)[0].replace("<b>", "").replace("</b>", "")
                    for text in data["text"]
                ] if category in {"inflow", "infiltration", "monitor"} else None,
                textposition="top center",
                textfont=dict(size=10, color=style["color"]),
                marker=dict(size=style["size"], color=style["color"], opacity=0.95),
                hoverinfo="text",
                hovertext=data["text"],
                name=f"{style['label']} ({len(data['x'])})",
            )
        )


def build_title(model: dict) -> str:
    return (
        f"{model['path'].stem}<br>"
        f"<sup>红: 外部入流节点  橙: 入渗点  绿: 监测点  蓝: 带标签节点  灰: 普通节点</sup>"
    )


def create_figure(model: dict) -> go.Figure:
    fig = go.Figure()
    add_conduit_trace(fig, model)
    add_node_traces(fig, model)

    fig.update_layout(
        title=build_title(model),
        template="plotly_white",
        margin=dict(l=0, r=0, t=70, b=0),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        scene=dict(
            xaxis_title="X 坐标",
            yaxis_title="Y 坐标",
            zaxis_title="井底高程 (m)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.45, y=-1.55, z=0.9)),
        ),
    )
    return fig


def output_name(inp_path: Path) -> Path:
    stem = inp_path.stem
    return inp_path.with_name(f"{stem}_三维可视化_关键节点标注.html")


def main() -> None:
    for inp_path in INPUT_FILES:
        model = parse_model(inp_path)
        fig = create_figure(model)
        html_path = output_name(inp_path)
        fig.write_html(str(html_path), include_plotlyjs="cdn")
        print(f"已生成: {html_path}")


if __name__ == "__main__":
    main()
