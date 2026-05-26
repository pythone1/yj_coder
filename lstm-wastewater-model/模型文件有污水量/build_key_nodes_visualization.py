from pathlib import Path
import re
import pandas as pd
import plotly.graph_objects as go


WORKDIR = Path(r"E:\PY\LSTM\模型文件有污水量")
INP = WORKDIR / "盱眙污水管3（入渗点有雨水量）.inp"
OUTPUT_HTML = WORKDIR / "关键节点可视化.html"

INJECTION_NODES = ["J61", "J129", "J195", "J106"]
STORAGE_NODES = ["J231", "J232", "J41"]
REFERENCE_NODES = ["J1"]
KEY_NODES = INJECTION_NODES + STORAGE_NODES + REFERENCE_NODES


def read_sections(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    sections = {}
    current = None
    buf = []
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            if current is not None:
                sections[current] = buf
            current = s.strip("[]")
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = buf
    return sections


def clean_lines(lines):
    return [x.strip() for x in lines if x.strip() and not x.strip().startswith(";")]


def parse_junctions(lines):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        rows.append(
            {
                "节点名称": parts[0],
                "节点类别": "Junction",
                "井底高程": float(parts[1]),
                "最大水深": float(parts[2]),
                "初始水深": float(parts[3]),
                "地表积水深": float(parts[4]),
                "积水面积": float(parts[5]),
            }
        )
    return pd.DataFrame(rows)


def parse_storage(lines):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        rows.append(
            {
                "节点名称": parts[0],
                "节点类别": "Storage",
                "井底高程": float(parts[1]),
                "最大水深": float(parts[2]),
                "初始水深": float(parts[3]),
                "形状类型": parts[4],
                "库容曲线": parts[5] if len(parts) > 5 else "",
                "地表积水深": float(parts[6]) if len(parts) > 6 else 0.0,
                "蒸发系数": float(parts[7]) if len(parts) > 7 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def parse_coordinates(lines):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        rows.append({"节点名称": parts[0], "X坐标": float(parts[1]), "Y坐标": float(parts[2])})
    return pd.DataFrame(rows)


def parse_tags(lines):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        if len(parts) >= 3 and parts[0] == "Node":
            rows.append({"节点名称": parts[1], "标签值": parts[2]})
    return pd.DataFrame(rows)


def parse_inflows(lines):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        if len(parts) >= 4:
            rows.append(
                {
                    "节点名称": parts[0],
                    "注水时间序列": parts[2],
                    "注水类型": parts[3],
                    "Mfactor": parts[4] if len(parts) > 4 else "",
                    "Sfactor": parts[5] if len(parts) > 5 else "",
                    "Baseline": parts[6] if len(parts) > 6 else "",
                    "Pattern": parts[7] if len(parts) > 7 else "",
                }
            )
    return pd.DataFrame(rows)


def parse_links(lines, kind):
    rows = []
    for line in clean_lines(lines):
        parts = re.split(r"\s+", line)
        if len(parts) >= 3:
            rows.append({"连接名称": parts[0], "起点": parts[1], "终点": parts[2], "连接类别": kind})
    return pd.DataFrame(rows)


def build_node_table(sections):
    junctions = parse_junctions(sections.get("JUNCTIONS", []))
    storage = parse_storage(sections.get("STORAGE", []))
    coords = parse_coordinates(sections.get("COORDINATES", []))
    tags = parse_tags(sections.get("TAGS", []))
    inflows = parse_inflows(sections.get("INFLOWS", []))

    nodes = pd.concat([junctions, storage], ignore_index=True, sort=False)
    nodes = nodes.merge(coords, on="节点名称", how="left")
    nodes = nodes.merge(tags, on="节点名称", how="left")
    nodes = nodes.merge(inflows, on="节点名称", how="left")

    nodes["角色分组"] = "普通节点"
    nodes.loc[nodes["节点名称"].isin(INJECTION_NODES), "角色分组"] = "注水节点"
    nodes.loc[nodes["节点名称"].isin(STORAGE_NODES), "角色分组"] = "调蓄节点"
    nodes.loc[nodes["节点名称"].isin(REFERENCE_NODES), "角色分组"] = "参考节点"
    return nodes


def add_connection_info(nodes, links):
    upstream = links.groupby("终点")["连接名称"].apply(lambda s: ",".join(sorted(set(s)))).to_dict()
    downstream = links.groupby("起点")["连接名称"].apply(lambda s: ",".join(sorted(set(s)))).to_dict()
    upstream_n = links.groupby("终点")["连接名称"].count().to_dict()
    downstream_n = links.groupby("起点")["连接名称"].count().to_dict()
    nodes["上游连接"] = nodes["节点名称"].map(upstream).fillna("")
    nodes["下游连接"] = nodes["节点名称"].map(downstream).fillna("")
    nodes["上游连接数量"] = nodes["节点名称"].map(upstream_n).fillna(0).astype(int)
    nodes["下游连接数量"] = nodes["节点名称"].map(downstream_n).fillna(0).astype(int)
    return nodes


def format_hover(row):
    lines = [
        f"节点: {row['节点名称']}",
        f"角色: {row['角色分组']}",
        f"类型: {row.get('节点类别', '')}",
        f"井底高程: {row.get('井底高程', '')}",
        f"最大水深: {row.get('最大水深', '')}",
        f"X/Y: {row.get('X坐标', '')}, {row.get('Y坐标', '')}",
        f"标签: {row.get('标签值', '')}",
        f"上游连接: {row.get('上游连接', '')}",
        f"下游连接: {row.get('下游连接', '')}",
    ]
    if pd.notna(row.get("注水时间序列")):
        lines.extend(
            [
                f"注水时间序列: {row.get('注水时间序列', '')}",
                f"注水类型: {row.get('注水类型', '')}",
                f"Sfactor: {row.get('Sfactor', '')}",
            ]
        )
    if pd.notna(row.get("库容曲线")):
        lines.extend(
            [
                f"形状类型: {row.get('形状类型', '')}",
                f"库容曲线: {row.get('库容曲线', '')}",
            ]
        )
    return "<br>".join(lines)


def main():
    sections = read_sections(INP)
    conduits = parse_links(sections.get("CONDUITS", []), "Conduit")
    pumps = parse_links(sections.get("PUMPS", []), "Pump")
    links = pd.concat([conduits, pumps], ignore_index=True)
    nodes = build_node_table(sections)
    nodes = add_connection_info(nodes, links)
    nodes["悬浮信息"] = nodes.apply(format_hover, axis=1)

    fig = go.Figure()

    bg_links = []
    node_map = nodes.set_index("节点名称")[["X坐标", "Y坐标"]].to_dict("index")
    for _, row in links.iterrows():
        p1 = node_map.get(row["起点"])
        p2 = node_map.get(row["终点"])
        if p1 and p2:
            bg_links.extend([(p1["X坐标"], p1["Y坐标"]), (p2["X坐标"], p2["Y坐标"]), (None, None)])
    if bg_links:
        fig.add_trace(
            go.Scatter(
                x=[p[0] for p in bg_links],
                y=[p[1] for p in bg_links],
                mode="lines",
                line=dict(color="rgba(140,140,140,0.35)", width=1),
                hoverinfo="skip",
                name="管网背景",
            )
        )

    bg_nodes = nodes[~nodes["节点名称"].isin(KEY_NODES)]
    fig.add_trace(
        go.Scatter(
            x=bg_nodes["X坐标"],
            y=bg_nodes["Y坐标"],
            mode="markers",
            marker=dict(size=5, color="rgba(160,160,160,0.45)"),
            hoverinfo="skip",
            name="普通节点",
        )
    )

    groups = [
        ("参考节点", REFERENCE_NODES, "#1f77b4", "circle", 14),
        ("注水节点", INJECTION_NODES, "#d62728", "diamond", 15),
        ("调蓄节点", STORAGE_NODES, "#2ca02c", "square", 15),
    ]
    for group_name, names, color, symbol, size in groups:
        subset = nodes[nodes["节点名称"].isin(names)]
        fig.add_trace(
            go.Scatter(
                x=subset["X坐标"],
                y=subset["Y坐标"],
                mode="markers+text",
                text=subset["节点名称"],
                textposition="top center",
                marker=dict(size=size, color=color, symbol=symbol, line=dict(color="white", width=1)),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=subset["悬浮信息"],
                name=group_name,
            )
        )

    fig.update_layout(
        title="关键节点可视化（注水点、调蓄点、参考点）",
        xaxis_title="X 坐标",
        yaxis_title="Y 坐标",
        template="plotly_white",
        width=1300,
        height=850,
        legend_title="节点分组",
    )

    summary_html = """
    <div style="padding:12px 16px;margin:8px 0 14px 0;border:1px solid #ddd;border-radius:8px;background:#fafafa;font-family:Arial,Microsoft YaHei,sans-serif;">
      <b>图例说明</b><br>
      蓝色圆点：参考节点 J1<br>
      红色菱形：注水节点 J61、J129、J195、J106<br>
      绿色方块：调蓄节点 J231、J232、J41<br>
      灰色背景：全网其他节点与连接<br>
      鼠标悬停可查看节点详细信息
    </div>
    """

    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    html = html.replace("<body>", "<body>\n" + summary_html, 1)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
