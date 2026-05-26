from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_0520"
RESULT_DIR = ROOT / "results_0520" / "medium_run"
OUT_DIR = RESULT_DIR / "analysis_report_0520_medium" / "ga_am_identification_visuals_clean"
FIG_DIR = OUT_DIR / "figures"

CANDIDATE_NODES = [
    "10", "62", "124", "42", "178", "63", "103", "241", "273", "215",
    "216", "60", "308", "310", "312", "118", "304", "64", "91", "85",
]
MONITOR_NODES = ["286", "223", "239", "267", "8", "251", "252", "189", "37"]
TRUTH_NODES = ["103", "304", "10", "178", "42"]
THRESHOLD = 0.05

COLORS = {
    "pipe": "#C9D6E8",
    "node": "#B7C9E2",
    "candidate": "#F2C94C",
    "truth": "#D7191C",
    "monitor": "#2563EB",
    "ga_hit": "#7E57C2",
    "ga_comp": "#F97316",
    "am_hit": "#16A34A",
    "am_comp": "#06B6D4",
    "miss": "#FFFFFF",
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


def get_xy(nodes: pd.DataFrame) -> pd.DataFrame:
    return nodes.dropna(subset=["x", "y"]).set_index("node")[["x", "y"]]


def get_weights(shares: pd.DataFrame, solution: str) -> pd.Series:
    row = shares.loc[shares["solution"] == solution].iloc[0]
    return row[CANDIDATE_NODES].astype(float)


def classify(weights: pd.Series) -> dict[str, list[str]]:
    active = [node for node, value in weights.items() if float(value) >= THRESHOLD]
    hit = [node for node in TRUTH_NODES if node in active]
    comp = sorted([node for node in active if node not in TRUTH_NODES], key=lambda n: float(weights[n]), reverse=True)
    miss = [node for node in TRUTH_NODES if node not in active]
    return {"active": active, "hit": hit, "comp": comp, "miss": miss}


def draw_network(ax, nodes: pd.DataFrame, links: pd.DataFrame) -> pd.DataFrame:
    xy = get_xy(nodes)
    for _, link in links.iterrows():
        f, t = link["from_node"], link["to_node"]
        if f in xy.index and t in xy.index:
            ax.plot(
                [xy.loc[f, "x"], xy.loc[t, "x"]],
                [xy.loc[f, "y"], xy.loc[t, "y"]],
                color=COLORS["pipe"],
                linewidth=0.65,
                zorder=1,
            )
    ax.scatter(xy["x"], xy["y"], s=7, color=COLORS["node"], alpha=0.68, zorder=2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    return xy


def scatter_plain(ax, xy: pd.DataFrame, nodes: list[str], color: str, label: str, marker: str, size: int, label_nodes: bool = False) -> None:
    first = True
    for node in nodes:
        if node not in xy.index:
            continue
        ax.scatter(
            xy.loc[node, "x"], xy.loc[node, "y"],
            s=size,
            color=color,
            marker=marker,
            edgecolor="#111827",
            linewidth=0.45,
            zorder=4,
            label=label if first else None,
        )
        if label_nodes:
            ax.text(
                xy.loc[node, "x"], xy.loc[node, "y"], node,
                fontsize=7,
                ha="left",
                va="bottom",
                color="#111827",
                zorder=7,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.55, pad=0.15),
            )
        first = False


def scatter_weighted(ax, xy: pd.DataFrame, nodes: list[str], weights: pd.Series, color: str, label: str, marker: str) -> None:
    if not nodes:
        return
    max_w = max(float(weights[n]) for n in nodes)
    first = True
    for node in nodes:
        if node not in xy.index:
            continue
        value = float(weights[node])
        size = 80 + 320 * value / max(max_w, 0.001)
        ax.scatter(
            xy.loc[node, "x"], xy.loc[node, "y"],
            s=size,
            color=color,
            marker=marker,
            alpha=0.78,
            edgecolor="#111827",
            linewidth=0.6,
            zorder=6,
            label=label if first else None,
        )
        ax.text(
            xy.loc[node, "x"], xy.loc[node, "y"], f"{node}\n{value * 100:.1f}%",
            fontsize=7,
            ha="center",
            va="center",
            color="#111827",
            zorder=8,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.18),
        )
        first = False


def compact_legend(ax) -> None:
    ax.legend(
        loc="lower left",
        fontsize=8,
        framealpha=0.9,
        markerscale=0.7,
        borderpad=0.35,
        labelspacing=0.35,
        handletextpad=0.4,
    )


def save_base_png(nodes: pd.DataFrame, links: pd.DataFrame) -> Path:
    path = FIG_DIR / "01_基础布设_不压盖版.png"
    fig, ax = plt.subplots(figsize=(11, 7))
    xy = draw_network(ax, nodes, links)
    scatter_plain(ax, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", "o", 34, label_nodes=False)
    scatter_plain(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", "*", 90, label_nodes=True)
    scatter_plain(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", "s", 42, label_nodes=True)
    ax.set_title("基础布设：候选点、真值注入点与监测点")
    compact_legend(ax)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_solution_png(
    nodes: pd.DataFrame,
    links: pd.DataFrame,
    weights: pd.Series,
    title: str,
    filename: str,
    hit_color: str,
    comp_color: str,
    hit_label: str,
    comp_label: str,
) -> Path:
    path = FIG_DIR / filename
    cls = classify(weights)
    fig, ax = plt.subplots(figsize=(11, 7))
    xy = draw_network(ax, nodes, links)
    scatter_plain(ax, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", "o", 20, label_nodes=False)
    scatter_plain(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", "s", 30, label_nodes=False)
    scatter_plain(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", "*", 72, label_nodes=False)
    scatter_weighted(ax, xy, cls["hit"], weights, hit_color, hit_label, "o")
    scatter_weighted(ax, xy, cls["comp"], weights, comp_color, comp_label, "D")
    scatter_plain(ax, xy, cls["miss"], COLORS["miss"], "漏识别真值点", "X", 78, label_nodes=True)
    ax.set_title(title)
    compact_legend(ax)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_compare_png(nodes: pd.DataFrame, links: pd.DataFrame, ga: pd.Series, am: pd.Series) -> Path:
    path = FIG_DIR / "04_GA_AM综合对比_不压盖版.png"
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    for ax, weights, title, hit_color, comp_color, hit_label, comp_label in [
        (axes[0], ga, "GA识别结果", COLORS["ga_hit"], COLORS["ga_comp"], "命中真值", "GA代偿"),
        (axes[1], am, "AM识别结果", COLORS["am_hit"], COLORS["am_comp"], "命中真值", "AM代偿"),
    ]:
        cls = classify(weights)
        xy = draw_network(ax, nodes, links)
        scatter_plain(ax, xy, MONITOR_NODES, COLORS["monitor"], "监测点", "s", 24, label_nodes=False)
        scatter_plain(ax, xy, TRUTH_NODES, COLORS["truth"], "真值注入点", "*", 58, label_nodes=False)
        scatter_weighted(ax, xy, cls["hit"], weights, hit_color, hit_label, "o")
        scatter_weighted(ax, xy, cls["comp"], weights, comp_color, comp_label, "D")
        scatter_plain(ax, xy, cls["miss"], COLORS["miss"], "漏识别真值点", "X", 62, label_nodes=True)
        ax.set_title(title)
        compact_legend(ax)
    fig.suptitle("GA与AM识别结果对比：代偿点单独标色")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def add_html_points(fig: go.Figure, xy: pd.DataFrame, nodes: list[str], color: str, name: str, symbol: str, size: int) -> None:
    xs, ys, hover = [], [], []
    for node in nodes:
        if node in xy.index:
            xs.append(xy.loc[node, "x"])
            ys.append(xy.loc[node, "y"])
            hover.append(f"节点 {node}")
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        marker=dict(size=size, color=color, symbol=symbol, line=dict(width=1, color="#111827")),
        customdata=hover,
        hovertemplate="%{customdata}<extra>" + name + "</extra>",
        name=name,
    ))


def add_html_weighted(fig: go.Figure, xy: pd.DataFrame, nodes: list[str], weights: pd.Series, color: str, name: str, symbol: str) -> None:
    xs, ys, hover, sizes = [], [], [], []
    max_w = max([float(weights[n]) for n in nodes], default=0.1)
    for node in nodes:
        if node in xy.index:
            value = float(weights[node])
            xs.append(xy.loc[node, "x"])
            ys.append(xy.loc[node, "y"])
            hover.append(f"节点 {node}<br>识别比例 {value * 100:.2f}%")
            sizes.append(9 + 24 * value / max(max_w, 0.001))
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        marker=dict(size=sizes, color=color, symbol=symbol, opacity=0.82, line=dict(width=1, color="#111827")),
        customdata=hover,
        hovertemplate="%{customdata}<extra>" + name + "</extra>",
        name=name,
    ))


def save_html(nodes: pd.DataFrame, links: pd.DataFrame, ga: pd.Series, am: pd.Series) -> Path:
    path = OUT_DIR / "0520_GA_AM识别与代偿综合可视化_不压盖版.html"
    xy = get_xy(nodes)
    edge_x, edge_y = [], []
    for _, link in links.iterrows():
        f, t = link["from_node"], link["to_node"]
        if f in xy.index and t in xy.index:
            edge_x += [xy.loc[f, "x"], xy.loc[t, "x"], None]
            edge_y += [xy.loc[f, "y"], xy.loc[t, "y"], None]
    ga_cls = classify(ga)
    am_cls = classify(am)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color=COLORS["pipe"], width=1), hoverinfo="skip", name="管线"))
    fig.add_trace(go.Scatter(x=xy["x"], y=xy["y"], mode="markers", marker=dict(size=3.5, color=COLORS["node"]), text=xy.index, hovertemplate="节点 %{text}<extra>普通节点</extra>", name="普通节点"))
    add_html_points(fig, xy, CANDIDATE_NODES, COLORS["candidate"], "候选点", "circle-open", 8)
    add_html_points(fig, xy, TRUTH_NODES, COLORS["truth"], "原始真值注入点", "star", 12)
    add_html_points(fig, xy, MONITOR_NODES, COLORS["monitor"], "监测点", "square", 9)
    add_html_weighted(fig, xy, ga_cls["hit"], ga, COLORS["ga_hit"], "GA识别到的真值点", "circle")
    add_html_weighted(fig, xy, ga_cls["comp"], ga, COLORS["ga_comp"], "GA代偿点", "diamond")
    add_html_points(fig, xy, ga_cls["miss"], COLORS["miss"], "GA漏识别真值点", "x", 11)
    add_html_weighted(fig, xy, am_cls["hit"], am, COLORS["am_hit"], "AM识别到的真值点", "circle")
    add_html_weighted(fig, xy, am_cls["comp"], am, COLORS["am_comp"], "AM代偿点", "diamond")
    add_html_points(fig, xy, am_cls["miss"], COLORS["miss"], "AM漏识别真值点", "x", 11)
    fig.update_layout(
        title="0520中参数结果：真值注入点、候选点、GA/AM识别点与代偿点（悬停查看编号和比例）",
        template="plotly_white",
        font=dict(family="Microsoft YaHei, SimHei, Arial", size=13),
        height=820,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0, itemwidth=80),
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
    ga = get_weights(shares, "ga_best")
    am = get_weights(shares, "posterior_best_map")
    outputs = {
        "base_png": str(save_base_png(nodes, links)),
        "ga_png": str(save_solution_png(nodes, links, ga, "GA识别结果：紫色为命中真值点，橙色为代偿点", "02_GA识别结果_不压盖版.png", COLORS["ga_hit"], COLORS["ga_comp"], "GA命中真值", "GA代偿点")),
        "am_png": str(save_solution_png(nodes, links, am, "AM识别结果：绿色为命中真值点，青色为代偿点", "03_AM识别结果_不压盖版.png", COLORS["am_hit"], COLORS["am_comp"], "AM命中真值", "AM代偿点")),
        "combined_png": str(save_compare_png(nodes, links, ga, am)),
        "html": str(save_html(nodes, links, ga, am)),
        "ga": classify(ga),
        "am": classify(am),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
