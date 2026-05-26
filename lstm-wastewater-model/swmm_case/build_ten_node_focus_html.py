from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path

import plotly.graph_objects as go

import full_network_source_tracing as base


WORK_DIR = Path(r"E:\PY\LSTM\swmm_case")
RESULT_DIR = WORK_DIR / "paper_route_full_dim_results" / "midscale_ppd"


def build_graph(links_df):
    graph = defaultdict(set)
    edge_map = {}
    for row in links_df.itertuples():
        graph[row.from_node].add(row.to_node)
        graph[row.to_node].add(row.from_node)
        edge_map[(row.from_node, row.to_node)] = row.link
        edge_map[(row.to_node, row.from_node)] = row.link
    return graph, edge_map


def shortest_path_nodes(graph, start: str, end: str) -> list[str]:
    if start == end:
        return [start]
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        for nxt in sorted(graph[node]):
            if nxt in visited:
                continue
            if nxt == end:
                return path + [nxt]
            visited.add(nxt)
            queue.append((nxt, path + [nxt]))
    return [start, end]


def collect_focus_links(graph, edge_map, focus_nodes: list[str]) -> set[str]:
    chosen = set()
    for i, left in enumerate(focus_nodes):
        for right in focus_nodes[i + 1 :]:
            path = shortest_path_nodes(graph, left, right)
            for a, b in zip(path[:-1], path[1:]):
                link = edge_map.get((a, b))
                if link:
                    chosen.add(link)
    return chosen


def add_node_group(fig, nodes_df, node_list, name, color, symbol, size):
    if not node_list:
        return
    view = nodes_df.loc[nodes_df["node"].isin(node_list)].copy()
    fig.add_trace(
        go.Scatter(
            x=view["x"],
            y=view["y"],
            mode="markers+text",
            name=name,
            text=view["node"],
            textposition="top center",
            marker=dict(color=color, size=size, symbol=symbol, line=dict(color="white", width=1.5)),
            hovertemplate="节点=%{text}<extra></extra>",
        )
    )


def build_html() -> Path:
    summary = json.loads((RESULT_DIR / "full_dim_summary.json").read_text(encoding="utf-8"))
    nodes_df, links_df = base.parse_network(WORK_DIR / "case_dry.inp")
    graph, edge_map = build_graph(links_df)

    candidate_nodes = summary["candidate_nodes"]
    truth_nodes = set(summary["truth_nodes"])
    predicted_nodes = set(summary["predicted_nodes"])
    monitor_nodes = list(base.MONITOR_NODES)
    focus_nodes = candidate_nodes + monitor_nodes
    chosen_links = collect_focus_links(graph, edge_map, focus_nodes)

    fig = go.Figure()

    bg_links = links_df.loc[~links_df["link"].isin(chosen_links)]
    for row in bg_links.itertuples():
        fig.add_trace(
            go.Scatter(
                x=[row.x1, row.x2],
                y=[row.y1, row.y2],
                mode="lines",
                line=dict(color="rgba(148,163,184,0.18)", width=1.3),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    focus_links_df = links_df.loc[links_df["link"].isin(chosen_links)]
    for row in focus_links_df.itertuples():
        fig.add_trace(
            go.Scatter(
                x=[row.x1, row.x2],
                y=[row.y1, row.y2],
                mode="lines",
                line=dict(color="rgba(37,99,235,0.65)", width=3.0),
                hovertemplate=f"管段={row.link}<br>{row.from_node} -> {row.to_node}<extra></extra>",
                showlegend=False,
            )
        )

    overlap = sorted(truth_nodes & predicted_nodes)
    truth_only = sorted(truth_nodes - predicted_nodes)
    predicted_only = sorted(predicted_nodes - truth_nodes)
    candidate_only = sorted(set(candidate_nodes) - truth_nodes - predicted_nodes)

    add_node_group(fig, nodes_df, monitor_nodes, "监测点", "#2563eb", "square", 14)
    add_node_group(fig, nodes_df, overlap, "真值且识别到", "#f59e0b", "diamond", 17)
    add_node_group(fig, nodes_df, truth_only, "真值但未识别", "#dc2626", "circle", 15)
    add_node_group(fig, nodes_df, predicted_only, "识别到但非真值", "#16a34a", "star", 18)
    add_node_group(fig, nodes_df, candidate_only, "其余候选点", "#7c3aed", "circle-open", 12)

    fig.update_layout(
        template="plotly_white",
        title="10 节点候选池专题图",
        xaxis_title="X 坐标",
        yaxis_title="Y 坐标",
        height=920,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=30, r=30, t=80, b=30),
    )

    summary_text = f"""
    <div style="font-family:Microsoft YaHei, sans-serif;padding:14px 16px;border:1px solid #d9e2ec;border-radius:16px;background:#ffffff;margin-bottom:14px;">
      <div style="font-size:22px;font-weight:700;color:#10233c;">10 节点专题说明</div>
      <div style="margin-top:10px;color:#58708a;line-height:1.8;">
        原始管网共有 <b>242</b> 个节点、<b>237</b> 条管段。当前先在下面这 <b>10</b> 个候选节点上做受控盲测反演：
        <br><b>{", ".join(candidate_nodes)}</b>
        <br><br>监测点：<b>{", ".join(monitor_nodes)}</b>
        <br>真实异常点：<b>{", ".join(summary["truth_nodes"])}</b>
        <br>当前识别结果：<b>{", ".join(summary["predicted_nodes"])}</b>
        <br>注水放大系数：<b>{summary.get("truth_scale_factor", 1.0):.2f}</b>
        <br>Mean NSE：<b>{summary["final_mean_nse"]:.4f}</b>
        <br>ACC：<b>{summary["acc"]:.4f}</b>
        <br>MCC：<b>{summary["mcc"]:.4f}</b>
      </div>
    </div>
    """

    output_html = RESULT_DIR / "10节点专题图.html"
    inner_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>10 节点专题图</title>
  <style>
    body {{
      margin: 0;
      background: linear-gradient(180deg, #f5f8fc 0%, #eef4fb 100%);
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      color: #10233c;
    }}
    .wrap {{
      width: min(1400px, calc(100% - 36px));
      margin: 0 auto;
      padding: 24px 0 28px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    {summary_text}
    {inner_html}
  </div>
</body>
</html>
"""
    output_html.write_text(page, encoding="utf-8")
    return output_html


def main() -> None:
    output = build_html()
    print("Wrote", output)


if __name__ == "__main__":
    main()
