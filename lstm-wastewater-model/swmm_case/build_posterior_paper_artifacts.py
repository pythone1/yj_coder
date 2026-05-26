from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


DEFAULT_RESULT_DIR = Path(r"E:\PY\LSTM\swmm_case\paper_route_full_dim_results")
NODE_COLUMNS = ["J129", "J195", "J61", "J128", "J130", "J194", "J72", "J60", "J62", "J127"]


def lag1_autocorr(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) < 3:
        return 0.0
    x0 = values[:-1] - values[:-1].mean()
    x1 = values[1:] - values[1:].mean()
    denom = np.sqrt(np.sum(x0**2) * np.sum(x1**2))
    if denom <= 1e-12:
        return 0.0
    return float(np.sum(x0 * x1) / denom)


def rough_ess(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    rho1 = lag1_autocorr(values)
    rho1 = min(max(rho1, -0.95), 0.95)
    return float(len(values) * (1 - rho1) / (1 + rho1))


def build_posterior_ppd(am_df: pd.DataFrame, weights_df: pd.DataFrame, output_html: Path) -> None:
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.58, 0.42],
        subplot_titles=("Posterior Probability Distribution", "Posterior Credible Interval Summary"),
        vertical_spacing=0.12,
    )
    sorted_weights = weights_df.sort_values("posterior_mean_share", ascending=False)
    for row in sorted_weights.itertuples():
        color = "#dc2626" if bool(row.is_truth) else "#64748b"
        fig.add_trace(
            go.Violin(
                x=[row.node] * len(am_df),
                y=am_df[row.node],
                name=row.node,
                line_color=color,
                fillcolor=color,
                opacity=0.28,
                points=False,
                showlegend=False,
                box_visible=True,
                meanline_visible=True,
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Bar(
            x=sorted_weights["node"],
            y=sorted_weights["posterior_mean_share"],
            marker_color=["#dc2626" if truth else "#64748b" for truth in sorted_weights["is_truth"]],
            error_y=dict(
                type="data",
                symmetric=False,
                array=sorted_weights["p95_share"] - sorted_weights["posterior_mean_share"],
                arrayminus=sorted_weights["posterior_mean_share"] - sorted_weights["p05_share"],
            ),
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    fig.add_hline(
        y=float(weights_df["tau"].iloc[0]),
        line_dash="dash",
        line_color="#c2410c",
        row=2,
        col=1,
    )
    fig.update_layout(
        template="plotly_white",
        height=900,
        title="Posterior PPD and Credible Intervals",
    )
    fig.update_yaxes(title_text="Share", row=1, col=1)
    fig.update_yaxes(title_text="Posterior mean share", row=2, col=1)
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def build_convergence_diagnostics(am_df: pd.DataFrame, weights_df: pd.DataFrame, output_html: Path) -> None:
    top_nodes = weights_df.sort_values("posterior_mean_share", ascending=False)["node"].head(4).tolist()
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Log-posterior Trace", "Acceptance and Covariance Trace", "Top-node Running Means", "Top-node Trace"),
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )
    chain_groups = [("all", am_df)] if "chain" not in am_df.columns else list(am_df.groupby("chain"))
    palette = ["#c2410c", "#2563eb", "#15803d", "#7c3aed", "#0891b2"]
    for idx, (chain_name, chain_df) in enumerate(chain_groups):
        color = palette[idx % len(palette)]
        suffix = f" chain {chain_name}" if chain_name != "all" else ""
        fig.add_trace(
            go.Scatter(x=chain_df["iteration"], y=chain_df["log_posterior"], mode="lines", line=dict(color=color, width=2), name=f"log-posterior{suffix}"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=chain_df["iteration"], y=chain_df["accepted_rate"], mode="lines", line=dict(color=color, width=2), name=f"accept rate{suffix}"),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Scatter(x=chain_df["iteration"], y=chain_df["cov_trace"], mode="lines", line=dict(color=color, width=2, dash="dot"), name=f"cov trace{suffix}"),
            row=1,
            col=2,
        )
        for node in top_nodes:
            running_mean = chain_df[node].expanding().mean()
            fig.add_trace(
                go.Scatter(x=chain_df["iteration"], y=running_mean, mode="lines", line=dict(color=color, width=2), name=f"{node} running mean{suffix}"),
                row=2,
                col=1,
            )
            fig.add_trace(
                go.Scatter(x=chain_df["iteration"], y=chain_df[node], mode="lines", line=dict(color=color, width=1.5), name=f"{node} trace{suffix}"),
                row=2,
                col=2,
            )
    fig.update_layout(template="plotly_white", height=900, title="AM Convergence Diagnostics")
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def write_posterior_report(summary: dict, weights_df: pd.DataFrame, am_df: pd.DataFrame, output_md: Path) -> None:
    tail_nodes = weights_df.sort_values("posterior_mean_share", ascending=False)["node"].tolist()
    accept_summary = (
        f"{summary['am_accept_rate_mean']:.4f} (min {summary['am_accept_rate_min']:.4f}, max {summary['am_accept_rate_max']:.4f})"
        if "am_accept_rate_mean" in summary
        else f"{summary['am_accept_rate']:.4f}"
    )
    lines = [
        "# Posterior PPD 与收敛诊断说明",
        "",
        "## 通俗总结",
        "",
        "这一组材料不再只讲“最后判出了哪些点”，而是把后验分布本身拿出来看，回答两个问题：",
        "",
        "1. 每个候选节点在后验上到底有多活跃。",
        "2. `AM` 采样过程是否已经进入相对稳定的后验区域。",
        "",
        "## 关键结论",
        "",
        f"- 当前最终 Mean NSE：{summary['final_mean_nse']:.4f}",
        f"- 当前 ACC：{summary['acc']:.4f}",
        f"- 当前 MCC：{summary['mcc']:.4f}",
        f"- 当前动态 Tau：{summary['tau']:.4f}",
        f"- 当前 AM 接受率：{accept_summary}",
        "",
        "## posterior PPD 怎么看",
        "",
        "在 PPD 图里，每个节点不是只有一个数，而是一整段分布。",
        "如果一个节点的分布整体抬得很高，而且置信区间也明显高于背景节点，说明它在后验意义上更可能是真正的异常点。",
        "",
        "## 收敛诊断怎么读",
        "",
        "收敛诊断主要看 4 件事：",
        "",
        "- `log-posterior` 是否明显进入稳定区域。",
        "- `accepted_rate` 是否不是过低也不是过高。",
        "- `cov_trace` 是否从初期探索逐渐进入较稳定尺度。",
        "- 顶部节点的 running mean 是否逐步稳定。",
        "",
        "## 重点节点统计",
        "",
        "| 节点 | 后验均值 | 5%分位 | 95%分位 | lag-1 自相关 | 粗略 ESS | 真值点 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in weights_df.sort_values("posterior_mean_share", ascending=False).itertuples():
        series = am_df[row.node].to_numpy(dtype=float)
        lines.append(
            f"| {row.node} | {row.posterior_mean_share:.4f} | {row.p05_share:.4f} | {row.p95_share:.4f} | {lag1_autocorr(series):.4f} | {rough_ess(series):.1f} | {'是' if bool(row.is_truth) else '否'} |"
        )
    lines += [
        "",
        "## 当前判断",
        "",
        "这套图的价值在于，它把“定位结果”提升成了“后验分布结果”。",
        "也就是说，我们不再只是给一个单点答案，而是能看到每个候选节点在概率意义上的活跃程度和不确定性范围。",
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RESULT_DIR
    summary = json.loads((result_dir / "full_dim_summary.json").read_text(encoding="utf-8"))
    am_df = pd.read_csv(result_dir / "full_dim_am_samples.csv")
    weights_df = pd.read_csv(result_dir / "full_dim_weights.csv")
    if "log_prior" not in am_df.columns or "log_posterior" not in am_df.columns:
        raise RuntimeError("Current full_dim_am_samples.csv does not contain posterior diagnostics columns. Re-run paper_route_full_dim.py first.")
    build_posterior_ppd(am_df, weights_df, result_dir / "paper_posterior_ppd.html")
    build_convergence_diagnostics(am_df, weights_df, result_dir / "paper_convergence_diagnostics.html")
    write_posterior_report(summary, weights_df, am_df, result_dir / "paper_posterior_report.md")
    print("Wrote posterior paper artifacts to", result_dir)


if __name__ == "__main__":
    main()
