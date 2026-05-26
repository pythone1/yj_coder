"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: visualize_0520_ga_am_results.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_0520"
RESULT_DIR = ROOT / "results_0520" / "medium_run"
OUT_DIR = RESULT_DIR / "analysis_report_0520_medium" / "ga_am_identification_visuals"
FIG_DIR = OUT_DIR / "figures"

CANDIDATE_NODES = [
    "10", "62", "124", "42", "178", "63", "103", "241", "273", "215",
    "216", "60", "308", "310", "312", "118", "304", "64", "91", "85",
]
MONITOR_NODES = ["286", "223", "239", "267", "8", "251", "252", "189", "37"]
TRUTH_NODES = ["103", "304", "10", "178", "42"]
THRESHOLD = 0.05

COLORS = {
    "normal_node": "#B7C9E2",
    "pipe": "#CAD7E8",
    "monitor": "#2563EB",
    "candidate": "#F2C94C",
    "truth": "#DC2626",
    "ga_hit": "#7E57C2",
    "ga_comp": "#F97316",
    "am_hit": "#16A34A",
    "am_comp": "#06B6D4",
}


def setup_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nodes = pd.read_csv(ANALYSIS_DIR / "0520_nodes_classified.csv", encoding="utf-8-sig")
    links = pd.read_csv(ANALYSIS_DIR / "0520_links_classified.csv", encoding="utf-8-sig")
    shares = pd.read_csv(RESULT_DIR / "0520_solution_shares.csv", encoding="utf-8-sig")
    nodes["node"] = nodes["node"].astype(str)
    links["from_node"] = links["from_node"].astype(str)
    links["to_node"] = links["to_node"].astype(str)
    return nodes, links, shares


def node_xy(nodes: pd.DataFrame) -> pd.DataFrame:
    return nodes.dropna(subset=["x", "y"]).set_index("node")[["x", "y"]]


def shares_for(shares: pd.DataFrame, solution: str) -> pd.Series:
    row = shares.loc[shares["solution"] == solution].iloc[0]
    return row[CANDIDATE_NODES].astype(float)


def classify_solution(weights: pd.Series) -> dict[str, list[str]]:
    active = [node for node, value in weights.items() if float(value) >= THRESHOLD]
    truth_hits = [node for node in TRUTH_NODES if node in active]
    compensation = sorted(
        [node for node in active if node not in TRUTH_NODES],
        key=lambda n: float(weights[n]),
        reverse=True,
    )
    missed = [node for node in TRUTH_NODES if node not in active]
    return {"active": active, "truth_hits": truth_hits, "compensation": compensation, "missed_truth": missed}


def draw_base(ax, nodes: pd.DataFrame, links: pd.DataFrame) -> pd.DataFrame:
    xy = node_xy(nodes)
    for _, link in links.iterrows():
        f, t = link["from_node"], link["to_node"]
        if f in xy.index and t in xy.index:
            ax.plot(
                [xy.loc[f, "x"], xy.loc[t, "x"]],
                [xy.loc[f, "y"], xy.loc[t, "y"]],
                color=COLORS["pipe"],
                linewidth=0.75,
                zorder=1,
            )
    ax.scatter(xy["x"], xy["y"], s=9, color=COLORS["normal_node"], alpha=0.75, zorder=2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    return xy


def annotate_points(ax, xy: pd.DataFrame, nodes: list[str], color: str, label: str, size: int = 70, marker: str = "o") -> None:
    plotted = False
    for node in nodes:
        if node not in xy.index:
            continue
        ax.scatter(xy.loc[node, "x"], xy.loc[node, "y"], s=size, color=color, edgecolor="#111827", linewidth=0.6, marker=marker, zorder=5, label=label if not plotted else None)
        ax.text(
            xy.loc[node, "x"], xy.loc[node, "y"], node,
            fontsize=8, color="#111827", zorder=7,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.2),
        )
        plotted = True


def annotate_weighted(ax, xy: pd.DataFrame, nodes: list[str], weights: pd.Series, color: str, label: str, marker: str) -> None:
    plotted = False
    max_weight = max(float(weights[n]) for n in nodes) if nodes else 0.1
    for node in nodes:
        if node not in xy.index:
            continue
        value = float(weights[node])
        size = 120 + 650 * value / max(max_weight, 0.001)
        ax.scatter(xy.loc[node, "x"], xy.loc[node, "y"], s=size, color=color, alpha=0.72, edgecolor="#111827", linewidth=0.7, marker=marker, zorder=6, label=label if not plotted else None)
        ax.text(
            xy.loc[node, "x"], xy.loc[node, "y"], f"{node}\n{value * 100:.1f}%",
            fontsize=8, color="#111827", zorder=8,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=0.2),
        )
        plotted = True


def save_base_png(nodes: pd.DataFrame, links: pd.DataFrame) -> Path:
    path = FIG_DIR / "01_基础布设_真值候选监测点.png"
    fig, ax = plt.subplots(figsize=(13, 7))
    xy = draw_base(ax, nodes, links)
    annotate_points(ax, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", size=65, marker="o")
    annotate_points(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", size=95, marker="*")
    annotate_points(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", size=70, marker="s")
    ax.set_title("基础布设：真值注入点、候选点与监测点")
    ax.legend(loc="lower left", framealpha=0.92)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_result_png(nodes: pd.DataFrame, links: pd.DataFrame, weights: pd.Series, solution_name: str, title: str, filename: str) -> Path:
    path = FIG_DIR / filename
    cls = classify_solution(weights)
    fig, ax = plt.subplots(figsize=(13, 7))
    xy = draw_base(ax, nodes, links)
    annotate_points(ax, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", size=42, marker="o")
    annotate_points(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", size=95, marker="*")
    annotate_points(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", size=60, marker="s")
    if solution_name == "GA":
        annotate_weighted(ax, xy, cls["truth_hits"], weights, COLORS["ga_hit"], "GA识别到的真值点", marker="o")
        annotate_weighted(ax, xy, cls["compensation"], weights, COLORS["ga_comp"], "GA代偿点", marker="D")
    else:
        annotate_weighted(ax, xy, cls["truth_hits"], weights, COLORS["am_hit"], "AM识别到的真值点", marker="o")
        annotate_weighted(ax, xy, cls["compensation"], weights, COLORS["am_comp"], "AM代偿点", marker="D")
    annotate_points(ax, xy, cls["missed_truth"], "#FFFFFF", "漏识别真值点", size=120, marker="X")
    ax.set_title(title)
    ax.legend(loc="lower left", framealpha=0.92)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_combined_png(nodes: pd.DataFrame, links: pd.DataFrame, ga_weights: pd.Series, am_weights: pd.Series) -> Path:
    path = FIG_DIR / "04_GA_AM识别与代偿综合对比.png"
    ga_cls = classify_solution(ga_weights)
    am_cls = classify_solution(am_weights)
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    for ax, weights, cls, title, hit_color, comp_color, name in [
        (axes[0], ga_weights, ga_cls, "GA识别结果", COLORS["ga_hit"], COLORS["ga_comp"], "GA"),
        (axes[1], am_weights, am_cls, "AM识别结果", COLORS["am_hit"], COLORS["am_comp"], "AM"),
    ]:
        xy = draw_base(ax, nodes, links)
        annotate_points(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", size=46, marker="s")
        annotate_points(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", size=72, marker="*")
        annotate_weighted(ax, xy, cls["truth_hits"], weights, hit_color, f"{name}识别到的真值点", marker="o")
        annotate_weighted(ax, xy, cls["compensation"], weights, comp_color, f"{name}代偿点", marker="D")
        annotate_points(ax, xy, cls["missed_truth"], "#FFFFFF", "漏识别真值点", size=90, marker="X")
        ax.set_title(title)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.92)
    fig.suptitle("GA与AM识别结果对比：代偿点单独标色")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def add_scatter(fig: go.Figure, xy: pd.DataFrame, nodes: list[str], color: str, name: str, marker: str = "circle", size: int = 10, visible=True) -> None:
    xs, ys, text = [], [], []
    for node in nodes:
        if node in xy.index:
            xs.append(xy.loc[node, "x"])
            ys.append(xy.loc[node, "y"])
            text.append(node)
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        text=text,
        visible=visible,
        mode="markers+text",
        textposition="top center",
        marker=dict(size=size, color=color, symbol=marker, line=dict(width=1, color="#111827")),
        hovertemplate=f"{name}：%{{text}}<extra></extra>",
        name=name,
    ))


def add_weighted_scatter(fig: go.Figure, xy: pd.DataFrame, nodes: list[str], weights: pd.Series, color: str, name: str, marker: str, visible=True) -> None:
    xs, ys, text, sizes = [], [], [], []
    max_weight = max([float(weights[n]) for n in nodes], default=0.1)
    for node in nodes:
        if node in xy.index:
            value = float(weights[node])
            xs.append(xy.loc[node, "x"])
            ys.append(xy.loc[node, "y"])
            text.append(f"节点 {node}<br>比例 {value * 100:.2f}%")
            sizes.append(12 + 34 * value / max(max_weight, 0.001))
    labels = [t.split("<br>")[0].replace("节点 ", "") for t in text]
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        text=labels,
        visible=visible,
        mode="markers+text",
        textposition="top center",
        customdata=text,
        marker=dict(size=sizes, color=color, symbol=marker, line=dict(width=1, color="#111827"), opacity=0.82),
        hovertemplate="%{customdata}<extra>" + name + "</extra>",
        name=name,
    ))


def save_html(nodes: pd.DataFrame, links: pd.DataFrame, ga_weights: pd.Series, am_weights: pd.Series) -> Path:
    path = OUT_DIR / "0520_GA_AM识别与代偿综合可视化.html"
    xy = node_xy(nodes)
    edge_x, edge_y = [], []
    for _, link in links.iterrows():
        f, t = link["from_node"], link["to_node"]
        if f in xy.index and t in xy.index:
            edge_x += [xy.loc[f, "x"], xy.loc[t, "x"], None]
            edge_y += [xy.loc[f, "y"], xy.loc[t, "y"], None]

    ga_cls = classify_solution(ga_weights)
    am_cls = classify_solution(am_weights)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color=COLORS["pipe"], width=1), hoverinfo="skip", name="管线"))
    fig.add_trace(go.Scatter(x=xy["x"], y=xy["y"], mode="markers", marker=dict(size=4, color=COLORS["normal_node"]), text=xy.index, hovertemplate="节点 %{text}<extra></extra>", name="普通节点"))
    add_scatter(fig, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", marker="circle-open", size=10)
    add_scatter(fig, xy, TRUTH_NODES, COLORS["truth"], "原始真值注入点", marker="star", size=14)
    add_scatter(fig, xy, MONITOR_NODES, COLORS["monitor"], "监测点", marker="square", size=11)
    add_weighted_scatter(fig, xy, ga_cls["truth_hits"], ga_weights, COLORS["ga_hit"], "GA识别到的真值点", marker="circle")
    add_weighted_scatter(fig, xy, ga_cls["compensation"], ga_weights, COLORS["ga_comp"], "GA代偿点", marker="diamond")
    add_scatter(fig, xy, ga_cls["missed_truth"], "#FFFFFF", "GA漏识别真值点", marker="x", size=14)
    add_weighted_scatter(fig, xy, am_cls["truth_hits"], am_weights, COLORS["am_hit"], "AM识别到的真值点", marker="circle")
    add_weighted_scatter(fig, xy, am_cls["compensation"], am_weights, COLORS["am_comp"], "AM代偿点", marker="diamond")
    add_scatter(fig, xy, am_cls["missed_truth"], "#FFFFFF", "AM漏识别真值点", marker="x", size=14)

    fig.update_layout(
        title="0520中参数结果：原始注入点、候选点、GA/AM识别点与代偿点",
        template="plotly_white",
        font=dict(family="Microsoft YaHei, SimHei, Arial", size=13),
        height=820,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
        margin=dict(l=20, r=20, t=120, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
    )
    fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    setup_matplotlib()
    nodes, links, shares = load_inputs()
    ga_weights = shares_for(shares, "ga_best")
    am_weights = shares_for(shares, "posterior_best_map")
    ga_cls = classify_solution(ga_weights)
    am_cls = classify_solution(am_weights)

    outputs = {
        "base_png": str(save_base_png(nodes, links)),
        "ga_png": str(save_result_png(nodes, links, ga_weights, "GA", "GA识别结果：紫色为命中真值点，橙色为代偿点", "02_GA识别结果_含代偿点.png")),
        "am_png": str(save_result_png(nodes, links, am_weights, "AM", "AM识别结果：绿色为命中真值点，青色为代偿点", "03_AM识别结果_含代偿点.png")),
        "combined_png": str(save_combined_png(nodes, links, ga_weights, am_weights)),
        "html": str(save_html(nodes, links, ga_weights, am_weights)),
        "classification": {
            "threshold": THRESHOLD,
            "truth_nodes": TRUTH_NODES,
            "candidate_nodes": CANDIDATE_NODES,
            "monitor_nodes": MONITOR_NODES,
            "ga": ga_cls,
            "am": am_cls,
        },
    }
    (OUT_DIR / "0520_GA_AM识别与代偿分类.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
