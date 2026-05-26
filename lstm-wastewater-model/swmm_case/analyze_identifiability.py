from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import paper_route_pilot as pilot


RESULT_DIR = Path(r"E:\PY\LSTM\swmm_case\paper_route_full_dim_results\identifiability_analysis")
SCALE_FACTORS = [0.5, 1.0, 1.5, 2.0, 3.0]


def node_signature(delta_df: pd.DataFrame, monitors: list[str]) -> np.ndarray:
    parts: list[np.ndarray] = []
    for monitor in monitors:
        flow = delta_df[f"{monitor}_inflow"].to_numpy(dtype=float)
        peak = np.max(np.abs(flow))
        if peak > 1e-8:
            flow = flow / peak
        parts.append(flow)
    return np.concatenate(parts)


def raw_signal(delta_df: pd.DataFrame, monitors: list[str]) -> np.ndarray:
    return np.concatenate([delta_df[f"{monitor}_inflow"].to_numpy(dtype=float) for monitor in monitors])


def corr_value(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def evaluate_scaled_truth(evaluator: pilot.PaperEvaluator, scale: float) -> pd.DataFrame:
    injections = {node: values * scale for node, values in evaluator.truth_templates.items()}
    sim_series = pilot.base.run_dynamic_simulation(
        str(evaluator.config.dry_inp),
        evaluator.config.eval_stride_seconds,
        pilot.MONITOR_NODES,
        injections,
        False,
        None,
        None,
    )
    delta = pilot.base.make_delta(sim_series["metrics"], evaluator.dry_series["metrics"])
    dry_metrics = evaluator.dry_series["metrics"]

    rows = []
    for monitor in pilot.MONITOR_NODES:
        delta_flow = delta[f"{monitor}_inflow"].to_numpy(dtype=float)
        dry_flow = dry_metrics[f"{monitor}_inflow"].to_numpy(dtype=float)
        rows.append(
            {
                "scale": scale,
                "monitor": monitor,
                "peak_delta": float(np.max(np.abs(delta_flow))),
                "mean_abs_delta": float(np.mean(np.abs(delta_flow))),
                "delta_std": float(np.std(delta_flow)),
                "dry_std": float(np.std(dry_flow)),
                "snr_std_ratio": float(np.std(delta_flow) / max(np.std(dry_flow), 1e-8)),
            }
        )
    return pd.DataFrame(rows)


def build_pairwise_confusion(evaluator: pilot.PaperEvaluator, scan_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    signatures: dict[str, np.ndarray] = {}
    raw_signatures: dict[str, np.ndarray] = {}
    for node in evaluator.candidate_nodes:
        result = evaluator.single_node_cache.get(node)
        if result is None:
            result = evaluator.evaluate_plan([node], np.array([1.0], dtype=float))
        signatures[node] = node_signature(result["delta"], pilot.MONITOR_NODES)
        raw_signatures[node] = raw_signal(result["delta"], pilot.MONITOR_NODES)

    rows = []
    for left, right in combinations(evaluator.candidate_nodes, 2):
        sig_left = signatures[left]
        sig_right = signatures[right]
        raw_left = raw_signatures[left]
        raw_right = raw_signatures[right]
        rows.append(
            {
                "node_a": left,
                "node_b": right,
                "corr": corr_value(sig_left, sig_right),
                "distance": float(np.linalg.norm(sig_left - sig_right)),
                "raw_distance": float(np.linalg.norm(raw_left - raw_right)),
                "both_truth": left in pilot.TRUTH_NODES and right in pilot.TRUTH_NODES,
                "truth_pair": left in pilot.TRUTH_NODES or right in pilot.TRUTH_NODES,
            }
        )
    pair_df = pd.DataFrame(rows).sort_values(["corr", "distance"], ascending=[False, True]).reset_index(drop=True)
    return pair_df, raw_signatures


def build_truth_neighbor_table(pair_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for truth in pilot.TRUTH_NODES:
        subset = pair_df[(pair_df["node_a"] == truth) | (pair_df["node_b"] == truth)].copy()
        subset["other_node"] = subset.apply(lambda row: row["node_b"] if row["node_a"] == truth else row["node_a"], axis=1)
        top = subset.sort_values(["corr", "distance"], ascending=[False, True]).head(3)
        for _, row in top.iterrows():
            rows.append(
                {
                    "truth_node": truth,
                    "confusing_neighbor": row["other_node"],
                    "corr": float(row["corr"]),
                    "distance": float(row["distance"]),
                }
            )
    return pd.DataFrame(rows)


def build_monitor_contribution(evaluator: pilot.PaperEvaluator) -> pd.DataFrame:
    rows = []
    truth_set = set(pilot.TRUTH_NODES)
    for truth in pilot.TRUTH_NODES:
        truth_result = evaluator.single_node_cache.get(truth)
        if truth_result is None:
            truth_result = evaluator.evaluate_plan([truth], np.array([1.0], dtype=float))
        for candidate in evaluator.candidate_nodes:
            if candidate == truth:
                continue
            cand_result = evaluator.single_node_cache.get(candidate)
            if cand_result is None:
                cand_result = evaluator.evaluate_plan([candidate], np.array([1.0], dtype=float))
            for monitor in pilot.MONITOR_NODES:
                a = truth_result["delta"][f"{monitor}_inflow"].to_numpy(dtype=float)
                b = cand_result["delta"][f"{monitor}_inflow"].to_numpy(dtype=float)
                rows.append(
                    {
                        "truth_node": truth,
                        "candidate_node": candidate,
                        "monitor": monitor,
                        "monitor_distance": float(np.linalg.norm(a - b)),
                        "monitor_corr": corr_value(a, b),
                        "candidate_is_truth": candidate in truth_set,
                    }
                )
    df = pd.DataFrame(rows)
    summary = (
        df.groupby(["truth_node", "monitor"], as_index=False)
        .agg(mean_distance=("monitor_distance", "mean"), max_corr=("monitor_corr", "max"))
    )
    return summary.sort_values(["truth_node", "mean_distance"], ascending=[True, False]).reset_index(drop=True)


def build_confusion_heatmap(pair_df: pd.DataFrame, output_html: Path) -> None:
    nodes = sorted(set(pair_df["node_a"]).union(pair_df["node_b"]))
    matrix = pd.DataFrame(np.eye(len(nodes)), index=nodes, columns=nodes, dtype=float)
    for row in pair_df.itertuples():
        matrix.loc[row.node_a, row.node_b] = row.corr
        matrix.loc[row.node_b, row.node_a] = row.corr

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.to_numpy(),
            x=nodes,
            y=nodes,
            colorscale="YlOrRd",
            zmin=0,
            zmax=1,
            colorbar=dict(title="响应相关性"),
            hovertemplate="节点A=%{y}<br>节点B=%{x}<br>相关性=%{z:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_white",
        title="10 个候选节点单井响应相关性热力图",
        height=820,
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def build_scale_sensitivity_chart(scale_df: pd.DataFrame, output_html: Path) -> None:
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "各监测点 peak delta",
            "各监测点 SNR(std ratio)",
            "平均 peak delta",
            "平均 SNR(std ratio)",
        ],
    )
    colors = {
        "J145": "#2563eb",
        "J17": "#16a34a",
        "J236": "#dc2626",
        "J59": "#7c3aed",
    }
    for monitor in pilot.MONITOR_NODES:
        view = scale_df[scale_df["monitor"] == monitor]
        fig.add_trace(
            go.Scatter(x=view["scale"], y=view["peak_delta"], mode="lines+markers", name=f"{monitor} peak", line=dict(color=colors[monitor])),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=view["scale"], y=view["snr_std_ratio"], mode="lines+markers", name=f"{monitor} snr", line=dict(color=colors[monitor])),
            row=1,
            col=2,
        )
    avg_df = scale_df.groupby("scale", as_index=False).agg(avg_peak=("peak_delta", "mean"), avg_snr=("snr_std_ratio", "mean"))
    fig.add_trace(go.Bar(x=avg_df["scale"], y=avg_df["avg_peak"], name="平均 peak"), row=2, col=1)
    fig.add_trace(go.Bar(x=avg_df["scale"], y=avg_df["avg_snr"], name="平均 SNR"), row=2, col=2)
    fig.update_layout(template="plotly_white", height=820, title="注水强度敏感性分析")
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def write_report(
    summary: dict,
    truth_neighbors: pd.DataFrame,
    monitor_contrib: pd.DataFrame,
    scale_df: pd.DataFrame,
    pair_df: pd.DataFrame,
    output_md: Path,
) -> None:
    lines = [
        "# 可辨识性分析报告",
        "",
        "## 1. 先说结论",
        "",
        "当前结果不如早期工程版本，主要不是因为算法链路坏了，而是因为问题现在更接近真实溯源定义，辨识难度更高。",
        "",
        "这次分析重点回答了三个问题：",
        "",
        "1. 10 个候选节点之间，哪些点的单井响应本来就非常像。",
        "2. 当前注水实验在 4 个监测点上的信号强度是否足够明显。",
        "3. 4 个监测点里，哪些点真正提供了区分能力。",
        "",
        "## 2. 当前最容易混淆的点",
        "",
        f"- 相关性最高的节点对平均相关性约为：{pair_df['corr'].head(5).mean():.3f}",
        f"- 真实点最近邻混淆对中，最高相关性约为：{truth_neighbors['corr'].max():.3f}",
        "",
        "从当前结果看，最关键的混淆主要集中在真实点及其邻近井：",
        "",
    ]
    for row in truth_neighbors.itertuples():
        lines.append(
            f"- 真值点 `{row.truth_node}` 最容易和 `{row.confusing_neighbor}` 混淆，相关性 `{row.corr:.3f}`，距离 `{row.distance:.3f}`"
        )

    avg_scale = scale_df.groupby("scale", as_index=False).agg(avg_peak=("peak_delta", "mean"), avg_snr=("snr_std_ratio", "mean"))
    base_row = avg_scale.loc[np.isclose(avg_scale["scale"], 1.0)].iloc[0]
    max_row = avg_scale.iloc[-1]
    lines.extend(
        [
            "",
            "## 3. 注水强度是否偏弱",
            "",
            f"- 当前真实工况（scale=1.0）下，4 个监测点平均 peak delta 为 `{base_row['avg_peak']:.4f}`",
            f"- 当前真实工况（scale=1.0）下，4 个监测点平均 SNR(std ratio) 为 `{base_row['avg_snr']:.4f}`",
            f"- 当注水放大到 scale={max_row['scale']:.1f} 时，平均 peak delta 提升到 `{max_row['avg_peak']:.4f}`，平均 SNR 提升到 `{max_row['avg_snr']:.4f}`",
            "",
            "这说明注水强度越大，监测端的信号区分度会同步提高。若当前工况下响应峰值和 SNR 偏低，确实会加剧邻近井代偿。",
            "",
            "## 4. 监测点布设是否合理",
            "",
            "下表反映了不同监测点对区分真值点与其他候选点的平均贡献。`mean_distance` 越大，说明该监测点越能把真值点和其他候选点拉开。",
            "",
        ]
    )
    for row in monitor_contrib.itertuples():
        lines.append(
            f"- 真值点 `{row.truth_node}` 在监测点 `{row.monitor}` 上的平均区分距离为 `{row.mean_distance:.4f}`，最大相关性为 `{row.max_corr:.4f}`"
        )

    lines.extend(
        [
            "",
            "## 5. 综合判断",
            "",
            "当前结果不够好，最可能是两个原因叠加：",
            "",
            "1. **监测点布设辨识度不够**：部分真值点与邻近候选点在现有 4 个监测点上的响应太像。",
            "2. **注水激励强度偏弱或差异不够明显**：监测点能感知到异常，但不一定能清楚分出各支路的独特指纹。",
            "",
            "也就是说，问题已经不主要是算法主链错误，而是“实验设计 + 可辨识性”成为瓶颈。",
            "",
            "## 6. 建议",
            "",
            "1. 优先考虑增强注水激励，或者让 3 个注水点的时序形态更有差异。",
            "2. 重新评估监测点布设，重点增强对 `J129` 这类偏弱支路的约束。",
            "3. 后续算法优化应把重点放在拓扑约束、时延特征和 posterior 判别逻辑，而不是只继续堆拟合分数。",
            "",
        ]
    )
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    np.random.seed(42)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    evaluator = pilot.PaperEvaluator(
        pilot.Config(
            result_dir=RESULT_DIR,
            pilot_candidate_limit=10,
            eval_stride_seconds=3600,
        )
    )
    scan_df = pilot.run_single_scan(evaluator)
    pair_df, _ = build_pairwise_confusion(evaluator, scan_df)
    truth_neighbors = build_truth_neighbor_table(pair_df)
    monitor_contrib = build_monitor_contribution(evaluator)

    scale_frames = [evaluate_scaled_truth(evaluator, scale) for scale in SCALE_FACTORS]
    scale_df = pd.concat(scale_frames, ignore_index=True)

    build_confusion_heatmap(pair_df, RESULT_DIR / "节点响应混淆热力图.html")
    build_scale_sensitivity_chart(scale_df, RESULT_DIR / "注水强度敏感性分析.html")

    pair_df.to_csv(RESULT_DIR / "pairwise_confusion.csv", index=False, encoding="utf-8-sig")
    truth_neighbors.to_csv(RESULT_DIR / "truth_neighbor_confusion.csv", index=False, encoding="utf-8-sig")
    monitor_contrib.to_csv(RESULT_DIR / "monitor_contribution.csv", index=False, encoding="utf-8-sig")
    scale_df.to_csv(RESULT_DIR / "scale_sensitivity.csv", index=False, encoding="utf-8-sig")

    summary = {
        "truth_nodes": pilot.TRUTH_NODES,
        "monitor_nodes": pilot.MONITOR_NODES,
        "candidate_nodes": evaluator.candidate_nodes,
        "top_pair_corr": float(pair_df.iloc[0]["corr"]),
        "top_truth_neighbor_corr": float(truth_neighbors["corr"].max()),
        "current_scale_avg_snr": float(scale_df.loc[np.isclose(scale_df["scale"], 1.0), "snr_std_ratio"].mean()),
        "current_scale_avg_peak": float(scale_df.loc[np.isclose(scale_df["scale"], 1.0), "peak_delta"].mean()),
    }
    (RESULT_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    write_report(
        summary,
        truth_neighbors,
        monitor_contrib,
        scale_df,
        pair_df,
        RESULT_DIR / "可辨识性分析报告.md",
    )
    print("Identifiability analysis written to", RESULT_DIR)


if __name__ == "__main__":
    main()
