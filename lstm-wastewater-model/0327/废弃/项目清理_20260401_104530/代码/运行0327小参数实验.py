from __future__ import annotations

import json
import multiprocessing

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from 公共配置与数据 import (
    CANDIDATE_NODES,
    DRY_BASE_COPY,
    MONITOR_NODES,
    OUTFALL_NODE,
    RESULT_DIR,
    TRUTH_INJECTION_NODES,
    ExperimentConfig,
    build_structure_data,
    ensure_directories,
    load_generated_data,
    runtime_model_path,
    validate_generated_data_exists,
    write_data_manifest,
)
from 模型仿真与评估 import build_dataset, evaluate_shares
from 遗传搜索与后验 import (
    extract_ppd,
    posterior_predictive_validation,
    roulette_initial_ppd,
    run_am,
    run_ga,
)


def save_structure_html() -> None:
    nodes_df, links_df = build_structure_data(DRY_BASE_COPY)
    fig = go.Figure()
    node_map = {row["node"]: (row["x"], row["y"]) for _, row in nodes_df.iterrows()}
    for _, row in links_df.iterrows():
        if row["from_node"] not in node_map or row["to_node"] not in node_map:
            continue
        x0, y0 = node_map[row["from_node"]]
        x1, y1 = node_map[row["to_node"]]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color="#c7cedb", width=1.2),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    groups = [
        ("全网节点", nodes_df, "#9aa5b1", 5, "circle"),
        ("候选节点", nodes_df[nodes_df["node"].isin(CANDIDATE_NODES)], "#2563eb", 9, "square"),
        ("真值注入点", nodes_df[nodes_df["node"].isin(TRUTH_INJECTION_NODES)], "#dc2626", 11, "diamond"),
        ("监测点", nodes_df[nodes_df["node"].isin(MONITOR_NODES)], "#16a34a", 11, "star"),
        ("唯一排口", nodes_df[nodes_df["node"] == OUTFALL_NODE], "#7c3aed", 13, "x"),
    ]
    for name, subset, color, size, symbol in groups:
        fig.add_trace(
            go.Scatter(
                x=subset["x"],
                y=subset["y"],
                mode="markers+text",
                text=subset["node"],
                textposition="top center",
                name=name,
                marker=dict(color=color, size=size, symbol=symbol),
            )
        )
    fig.update_layout(title="0327 原始全网选点方案", template="plotly_white")
    (RESULT_DIR / "0327_原始全网选点方案.html").write_text(
        pio.to_html(fig, include_plotlyjs="cdn", full_html=True),
        encoding="utf-8",
    )


def save_monitor_fit_html(observed_delta, sim_delta) -> None:
    fig = go.Figure()
    for node in MONITOR_NODES:
        fig.add_trace(go.Scatter(x=observed_delta["相对小时"], y=observed_delta[node], mode="lines", name=f"{node} 观测", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=sim_delta["相对小时"], y=sim_delta[node], mode="lines", name=f"{node} 模拟", line=dict(width=1, dash="dash")))
    fig.update_layout(title="0327 监测拟合", template="plotly_white", xaxis_title="相对小时", yaxis_title="增量流量")
    (RESULT_DIR / "0327_监测拟合.html").write_text(pio.to_html(fig, include_plotlyjs="cdn", full_html=True), encoding="utf-8")


def save_ppd_validation_html(bands_df) -> None:
    monitor = MONITOR_NODES[0]
    df = bands_df[bands_df["监测点"] == monitor].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["相对小时"], y=df["P95"], mode="lines", line=dict(color="#cce3ff"), name="P95"))
    fig.add_trace(go.Scatter(x=df["相对小时"], y=df["P05"], mode="lines", fill="tonexty", line=dict(color="#cce3ff"), name="P05-P95"))
    fig.add_trace(go.Scatter(x=df["相对小时"], y=df["P50"], mode="lines", line=dict(color="#2563eb"), name="P50"))
    fig.add_trace(go.Scatter(x=df["相对小时"], y=df["观测值"], mode="lines", line=dict(color="#dc2626"), name="观测"))
    fig.update_layout(title=f"0327 PPD 置信区间验证（示例监测点 {monitor}）", template="plotly_white")
    (RESULT_DIR / "0327_PPD置信区间验证.html").write_text(pio.to_html(fig, include_plotlyjs="cdn", full_html=True), encoding="utf-8")


def save_summary_pages(summary: dict) -> None:
    (RESULT_DIR / "0327_结果汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    html = f"""
<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>0327 结果总览</title></head>
<body style="font-family: Microsoft YaHei, sans-serif; margin: 24px;">
<h1>0327 结果总览</h1>
<ul>
  <li>Q_R = {summary['Qr_m3']:.2f} m3</li>
  <li>ga_best_mean_nse = {summary['ga_best_mean_nse']:.4f}</li>
  <li>posterior_median_nse = {summary['posterior_median_nse']:.4f}</li>
  <li>posterior_best_nse = {summary['posterior_best_nse']:.4f}</li>
  <li>最终采用 = {summary['final_solution_name']}</li>
  <li>识别前 3 = {' / '.join(summary['predicted_top3'])}</li>
  <li>PPD 平均覆盖率 = {summary['posterior_coverage_mean']:.4f}</li>
</ul>
</body></html>
"""
    (RESULT_DIR / "0327_结果总览.html").write_text(html, encoding="utf-8")


def save_docs(summary: dict) -> None:
    file_doc = "\n".join(
        [
            "# 0327 文件说明",
            "",
            "- `数据/生成数据/0327_总入流过程_10分钟.csv`：48 小时总过程，前 24 小时有注水波形。",
            "- `数据/生成数据/0327_真值注水数据_10分钟.csv`：三处真值点按 10 分钟拆分后的注水数据。",
            "- `数据/生成数据/0327_基线监测_10分钟.csv`：原始 dry.out 提取并细分得到的基线监测。",
            "- `数据/生成数据/0327_事件监测_10分钟.csv`：clean 副本注水后的事件监测。",
            "- `数据/生成数据/0327_观测增量_10分钟.csv`：事件减基线的增量。",
            "- `数据/生成数据/0327_排口过程_10分钟.csv`：排口基线/事件/增量过程。",
            "- `结果/0327_GA全部方案.csv`：GA 全部评估方案。",
            "- `结果/0327_GA每代最佳.csv`：GA 每代每群最佳。",
            "- `结果/0327_GA末代合并.csv`：轮盘赌前的末代合并池。",
            "- `结果/0327_initial_PPD.csv`：轮盘赌后进入 initial PPD 的方案。",
            "- `结果/0327_AM样本.csv`：AM 全部样本。",
            "- `结果/0327_PPD样本.csv`：预热后保留的 PPD 样本。",
            "- `结果/0327_后验节点权重.csv`：后验均值/中位数/P05/P95。",
            "- `结果/0327_posterior_predictive_coverage.csv`：各监测点 90% 覆盖率。",
        ]
    )
    (RESULT_DIR / "0327_文件说明.md").write_text(file_doc, encoding="utf-8")

    report = "\n".join(
        [
            "# 0327 详细汇报",
            "",
            "## 方法口径",
            "",
            "- 48 小时总时长，前 24 小时注水，10 分钟分辨率。",
            "- 中文论文：保留 `Q_R` 总入流量约束。",
            "- 英文论文：多种群 GA + 轮盘赌 + initial PPD + Metropolis(AM) + 自适应协方差 + 中位数诊断 + 90% 置信区间验证。",
            "- 最终结果按论文口径取 `posterior_median`。",
            "",
            "## 结果摘要",
            "",
            f"- Q_R：{summary['Qr_m3']:.2f} m3",
            f"- ga_best_mean_nse：{summary['ga_best_mean_nse']:.4f}",
            f"- posterior_median_nse：{summary['posterior_median_nse']:.4f}",
            f"- posterior_best_nse：{summary['posterior_best_nse']:.4f}",
            f"- 最终采用：{summary['final_solution_name']}",
            f"- 最终 Mean NSE：{summary['final_mean_nse']:.4f}",
            f"- 当前识别前 3：{' / '.join(summary['predicted_top3'])}",
            f"- PPD 平均 90% 覆盖率：{summary['posterior_coverage_mean']:.4f}",
        ]
    )
    (RESULT_DIR / "0327_详细汇报.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_directories()
    config = ExperimentConfig(
        ga_population_count=2,
        ga_population_size=8,
        ga_generations=4,
        ga_migration_interval=2,
        ga_migration_count=2,
        ga_competition_replace_count=2,
        am_chain_count=2,
        am_samples_per_chain=60,
        am_warmup=15,
        am_adapt_start=15,
        posterior_validation_samples=12,
        parallel_workers=4,
    )
    validate_generated_data_exists()
    write_data_manifest(config)
    generated = load_generated_data()
    dataset = build_dataset(generated)

    ga_all_df, ga_history_df, ga_last_df, ga_best_shares = run_ga(dataset, generated, config)
    ga_all_df.to_csv(RESULT_DIR / "0327_GA全部方案.csv", index=False, encoding="utf-8-sig")
    ga_history_df.to_csv(RESULT_DIR / "0327_GA每代最佳.csv", index=False, encoding="utf-8-sig")
    ga_last_df.to_csv(RESULT_DIR / "0327_GA末代合并.csv", index=False, encoding="utf-8-sig")

    rng = np.random.default_rng(config.random_seed + 99)
    initial_ppd_df = roulette_initial_ppd(ga_last_df, ga_best_shares, config, rng)
    initial_ppd_df.to_csv(RESULT_DIR / "0327_initial_PPD.csv", index=False, encoding="utf-8-sig")

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    am_df.to_csv(RESULT_DIR / "0327_AM样本.csv", index=False, encoding="utf-8-sig")

    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    ppd_samples_df.to_csv(RESULT_DIR / "0327_PPD样本.csv", index=False, encoding="utf-8-sig")
    posterior_df.to_csv(RESULT_DIR / "0327_后验节点权重.csv", index=False, encoding="utf-8-sig")

    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)
    bands_df.to_csv(RESULT_DIR / "0327_posterior_predictive_bands.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(RESULT_DIR / "0327_posterior_predictive_coverage.csv", index=False, encoding="utf-8-sig")

    posterior_median_map = dict(zip(posterior_df["节点"], posterior_df["后验中位数"]))
    posterior_median_shares = np.array([posterior_median_map[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_median_shares = posterior_median_shares / max(float(posterior_median_shares.sum()), 1e-12)

    top_post_row = am_df.sort_values("log_posterior", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_post_row[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_best_shares = posterior_best_shares / max(float(posterior_best_shares.sum()), 1e-12)

    runtime_inp = runtime_model_path(0)
    ga_best_eval = evaluate_shares(ga_best_shares, dataset, str(runtime_inp))
    posterior_median_eval = evaluate_shares(posterior_median_shares, dataset, str(runtime_inp))
    posterior_best_eval = evaluate_shares(posterior_best_shares, dataset, str(runtime_inp))

    final_name = "posterior_median"
    final_eval = posterior_median_eval
    final_eval["sim_delta"].to_csv(RESULT_DIR / "0327_最终方案模拟增量.csv", index=False, encoding="utf-8-sig")

    observed_plot_df = dataset.observed_delta.copy().iloc[: len(final_eval["sim_delta"])].reset_index(drop=True)
    observed_plot_df["相对小时"] = dataset.total_process["相对小时"].iloc[: len(observed_plot_df)].to_numpy(dtype=float)
    sim_plot_df = final_eval["sim_delta"].copy()

    summary = {
        "run_mode": "0327 论文口径小参数实验",
        "Qr_m3": dataset.qr_m3,
        "ga_best_mean_nse": float(ga_best_eval["mean_nse"]),
        "posterior_median_nse": float(posterior_median_eval["mean_nse"]),
        "posterior_best_nse": float(posterior_best_eval["mean_nse"]),
        "final_solution_name": final_name,
        "final_mean_nse": float(final_eval["mean_nse"]),
        "predicted_top3": posterior_df.head(3)["节点"].tolist(),
        "initial_ppd_count": int(len(initial_ppd_df)),
        "posterior_validation_sample_count": int(config.posterior_validation_samples),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "am_accept_rate_by_chain": {str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()},
        "am_sd": float(2.42 / len(CANDIDATE_NODES)),
        "am_dimension_d": int(len(CANDIDATE_NODES)),
    }

    save_structure_html()
    save_monitor_fit_html(observed_plot_df, sim_plot_df)
    save_ppd_validation_html(bands_df)
    save_summary_pages(summary)
    save_docs(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
