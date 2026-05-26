from pathlib import Path
import json
import importlib.util
import sys

import plotly.graph_objects as go


ROOT = Path(r"E:\PY\LSTM\0323")
RESULTS = ROOT / "results"


def load_pipeline_module():
    module_path = ROOT / "pipeline_0323.py"
    spec = importlib.util.spec_from_file_location("p0323_html_builder", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    mod = load_pipeline_module()
    cfg = mod.Config()
    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))

    nodes_df, links_df = mod.base.parse_network(cfg.dry_inp)
    chosen = set(cfg.candidate_nodes) | set(cfg.monitor_nodes) | set(cfg.truth_nodes) | {cfg.outlet_node}
    sub_nodes = nodes_df[nodes_df["node"].isin(chosen)].copy()
    sub_links = links_df[links_df["from_node"].isin(chosen) & links_df["to_node"].isin(chosen)].copy()

    fig = go.Figure()
    for row in links_df.itertuples():
        fig.add_trace(
            go.Scatter(
                x=[row.x1, row.x2],
                y=[row.y1, row.y2],
                mode="lines",
                line=dict(color="rgba(148,163,184,0.18)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=nodes_df["x"],
            y=nodes_df["y"],
            mode="markers",
            name="全网节点",
            marker=dict(color="rgba(100,116,139,0.45)", size=4),
            text=nodes_df["node"],
            hovertemplate="节点 %{text}<extra></extra>",
        )
    )

    def add_group(node_list, name, color, symbol, size):
        if not node_list:
            return
        df = nodes_df[nodes_df["node"].isin(node_list)]
        fig.add_trace(
            go.Scatter(
                x=df["x"],
                y=df["y"],
                mode="markers+text",
                text=df["node"],
                textposition="top center",
                name=name,
                marker=dict(color=color, symbol=symbol, size=size, line=dict(color="white", width=1)),
            )
        )

    truth = set(cfg.truth_nodes)
    predicted = set(summary["predicted_nodes"])
    monitors = set(cfg.monitor_nodes)
    outlet = {cfg.outlet_node}
    other = set(cfg.candidate_nodes) - truth - predicted - monitors - outlet

    add_group(sorted(other), "其他候选点", "#94A3B8", "circle-open", 8)
    add_group(sorted(monitors - outlet), "监测点", "#2563EB", "square", 12)
    add_group(sorted(truth - predicted), "真值未识别", "#DC2626", "circle", 13)
    add_group(sorted(predicted - truth), "识别非真值", "#16A34A", "star", 15)
    add_group(sorted(truth & predicted), "真值且识别到", "#F59E0B", "diamond", 14)
    add_group(sorted(outlet), "唯一汇出端", "#7C3AED", "x", 15)

    fig.update_layout(
        title="0323 当前实验全网结构图",
        template="plotly_white",
        width=1200,
        height=820,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    node_table = sub_nodes[["node", "node_type", "elevation"]].sort_values("node").to_html(index=False)
    link_table = sub_links[["link", "from_node", "to_node", "length"]].sort_values("link").to_html(index=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>0323 当前实验全网结构图</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 24px; color: #1f2937; }}
.card {{ border: 1px solid #d1d5db; border-radius: 12px; padding: 16px 20px; margin-bottom: 18px; background: #fff; }}
h1, h2 {{ margin: 0 0 12px 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; }}
th {{ background: #f8fafc; }}
.small {{ color: #475569; font-size: 14px; line-height: 1.7; }}
</style>
</head>
<body>
<div class="card">
  <h1>0323 当前实验总览</h1>
  <div class="small">
    <p>当前实验使用 <b>{cfg.dry_inp.name}</b> 作为基础干天模型，在 8 小时事件窗口内进行反演。</p>
    <p>真值点：{", ".join(cfg.truth_nodes)}；监测点：{", ".join(cfg.monitor_nodes)}；唯一汇出端：{cfg.outlet_node}。</p>
    <p>当前结果：识别为 {", ".join(summary["predicted_nodes"])}；Q_R = {summary["q_r_outlet_based"]:.2f} m³；Mean NSE = {summary["final_mean_nse"]:.4f}。</p>
    <p>说明：本页面不直接展示原始 INP 中可能存在编码问题的中文字段，只展示当前实验实际使用的节点、连边和结果标签，因此不应再出现乱码。</p>
  </div>
</div>
<div class="card">{plot_html}</div>
<div class="card">
  <h2>当前实验节点表</h2>
  {node_table}
</div>
<div class="card">
  <h2>当前实验管段表</h2>
  {link_table}
</div>
</body>
</html>
"""

    out = RESULTS / "clean_chinese_overview.html"
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
