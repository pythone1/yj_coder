from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


RESULT_DIR = Path(r"E:\PY\LSTM\0323\results")


def load_inputs() -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """读取汇报所需的核心结果文件。"""
    summary = json.loads((RESULT_DIR / "summary.json").read_text(encoding="utf-8"))
    weights = pd.read_csv(RESULT_DIR / "posterior_weights.csv")
    ga_history = pd.read_csv(RESULT_DIR / "ga_history.csv")
    coverage = pd.read_csv(RESULT_DIR / "posterior_predictive_coverage.csv")
    return summary, weights, ga_history, coverage


def build_ga_posterior_summary(
    summary: dict,
    weights: pd.DataFrame,
    ga_history: pd.DataFrame,
    coverage: pd.DataFrame,
) -> None:
    """
    生成一张“GA + posterior”汇总图。

    这张图的目的不是展示所有细节，而是让汇报时能一页看清：
    1. GA 迭代是否在持续变好；
    2. posterior 最终把权重分给了哪些节点；
    3. posterior predictive validation 在各监测点的覆盖率如何；
    4. 当前这套链路的关键指标整体表现怎样。
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "GA 各代最佳 Mean NSE",
            "Posterior Top 10 节点权重",
            "Posterior Predictive 90% 覆盖率",
            "关键指标总览",
        ),
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )

    fig.add_trace(
        go.Scatter(
            x=ga_history["generation"],
            y=ga_history["best_mean_nse"],
            mode="lines+markers",
            line=dict(color="#2563EB", width=3),
            marker=dict(size=8),
            name="GA best NSE",
        ),
        row=1,
        col=1,
    )

    top_weights = weights.head(10).copy()
    bar_colors = ["#DC2626" if bool(v) else "#64748B" for v in top_weights["is_truth"]]
    fig.add_trace(
        go.Bar(
            x=top_weights["node"],
            y=top_weights["posterior_mean_share"],
            marker_color=bar_colors,
            name="Posterior mean share",
        ),
        row=1,
        col=2,
    )

    coverage_colors = [
        "#16A34A" if value >= 0.7 else "#F59E0B" if value >= 0.5 else "#DC2626"
        for value in coverage["coverage_90"]
    ]
    fig.add_trace(
        go.Bar(
            x=coverage["monitor"],
            y=coverage["coverage_90"],
            marker_color=coverage_colors,
            name="90% 覆盖率",
        ),
        row=2,
        col=1,
    )

    metric_names = ["Mean NSE", "ACC", "MCC", "Coverage"]
    metric_values = [
        summary["final_mean_nse"],
        summary["acc"],
        summary["mcc"],
        summary["posterior_coverage_mean"],
    ]
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=metric_values,
            marker_color=["#2563EB", "#16A34A", "#7C3AED", "#EA580C"],
            name="关键指标",
        ),
        row=2,
        col=2,
    )

    fig.update_yaxes(range=[0, 1.05], row=1, col=1)
    fig.update_yaxes(
        range=[0, max(0.45, float(top_weights["posterior_mean_share"].max()) + 0.05)],
        row=1,
        col=2,
    )
    fig.update_yaxes(range=[0, 1.0], row=2, col=1)
    fig.update_yaxes(range=[-0.1, 1.05], row=2, col=2)

    fig.update_layout(
        title="0323 子网络：GA 与 Posterior 汇总图",
        template="plotly_white",
        height=860,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=50, r=30, t=80, b=40),
    )
    fig.write_html(str(RESULT_DIR / "ga_posterior_summary.html"), include_plotlyjs="cdn")


def build_overview_html(summary: dict, coverage: pd.DataFrame) -> None:
    """生成一页式总览汇报 HTML，方便直接给领导或汇报对象查看。"""
    coverage_rows = "\n".join(
        f"<tr><td>{row.monitor}</td><td>{row.coverage_90:.3f}</td></tr>"
        for row in coverage.itertuples()
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>0323 项目总览</title>
  <style>
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
      color: #10233c;
      background: linear-gradient(180deg, #f8fbff 0%, #eef5fb 100%);
    }}
    .wrap {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px 28px 36px;
    }}
    .hero {{
      background: white;
      border-radius: 18px;
      padding: 24px 28px;
      box-shadow: 0 12px 30px rgba(16, 35, 60, 0.08);
      margin-bottom: 20px;
    }}
    .hero h1 {{
      margin: 0 0 12px;
      font-size: 30px;
    }}
    .hero p {{
      margin: 0;
      line-height: 1.8;
      color: #355070;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }}
    .card {{
      background: white;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 24px rgba(16, 35, 60, 0.07);
    }}
    .card .label {{
      font-size: 13px;
      color: #64748b;
      margin-bottom: 8px;
    }}
    .card .value {{
      font-size: 28px;
      font-weight: 700;
      line-height: 1.3;
    }}
    .section {{
      background: white;
      border-radius: 18px;
      padding: 18px 20px 24px;
      box-shadow: 0 10px 24px rgba(16, 35, 60, 0.07);
      margin-bottom: 20px;
    }}
    .section h2 {{
      margin: 0 0 14px;
      font-size: 22px;
    }}
    iframe {{
      width: 100%;
      border: none;
      border-radius: 12px;
      background: #fff;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin-top: 8px;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
      padding: 10px 8px;
    }}
    th {{
      color: #334155;
    }}
    .note {{
      color: #475569;
      line-height: 1.85;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>0323 精细子网络溯源总览</h1>
      <p>
        当前链路基于 10 分钟分辨率数据、20 节点候选子网络、2 个真实注入点和 5 个关键监测点构建。
        总量约束 Q_R 来自边界监测点 <b>{", ".join(summary["boundary_monitors"])}</b> 的积分差值，
        随后进入 <b>GA -&gt; initial PPD -&gt; AM -&gt; posterior predictive validation</b> 完整链路。
        这页的目标是把“模型在做什么、结果怎么样、不确定性验证如何”放到同一个界面里讲清楚。
      </p>
    </div>

    <div class="grid">
      <div class="card"><div class="label">真实注入点</div><div class="value">{", ".join(summary["truth_nodes"])}</div></div>
      <div class="card"><div class="label">最终识别点</div><div class="value">{", ".join(summary["predicted_nodes"])}</div></div>
      <div class="card"><div class="label">Mean NSE</div><div class="value">{summary["final_mean_nse"]:.3f}</div></div>
      <div class="card"><div class="label">Q_R (m³)</div><div class="value">{summary["q_r_monitor_based"]:.1f}</div></div>
      <div class="card"><div class="label">ACC</div><div class="value">{summary["acc"]:.3f}</div></div>
      <div class="card"><div class="label">MCC</div><div class="value">{summary["mcc"]:.3f}</div></div>
      <div class="card"><div class="label">Posterior 90% 覆盖均值</div><div class="value">{summary["posterior_coverage_mean"]:.3f}</div></div>
      <div class="card"><div class="label">最终解来源</div><div class="value">{summary["final_solution_name"]}</div></div>
    </div>

    <div class="section">
      <h2>算法链说明</h2>
      <div class="note">
        第一步：运行 dry 基线与注入工况，构造 5 个监测点的流量增量。<br>
        第二步：对边界监测点 <b>{", ".join(summary["boundary_monitors"])}</b> 做积分差值，得到总额外入流量 <b>Q_R</b>。<br>
        第三步：多种群 GA 在 20 个候选节点之间分配 Q_R，按平均 NSE 粗筛，并形成 initial PPD。<br>
        第四步：AM 结合 prior 与 likelihood 做 posterior 采样，得到节点后验权重与后验样本。<br>
        第五步：对 posterior 样本重新做 SWMM 仿真，形成 90% 后验预测区间，检验真实监测曲线是否被覆盖。
      </div>
    </div>

    <div class="section">
      <h2>子网络与识别结果</h2>
      <iframe src="selected_subnetwork_overview.html" height="820"></iframe>
    </div>

    <div class="section">
      <h2>GA 与 Posterior 汇总图</h2>
      <iframe src="ga_posterior_summary.html" height="900"></iframe>
    </div>

    <div class="section">
      <h2>监测点拟合图</h2>
      <iframe src="monitor_fit_10min.html" height="1500"></iframe>
    </div>

    <div class="section">
      <h2>Posterior Predictive Validation</h2>
      <iframe src="posterior_predictive_validation.html" height="1500"></iframe>
      <table>
        <thead><tr><th>监测点</th><th>90% 覆盖率</th></tr></thead>
        <tbody>{coverage_rows}</tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
    (RESULT_DIR / "0323_总览汇报.html").write_text(html, encoding="utf-8")


def write_technical_report(summary: dict, weights: pd.DataFrame, coverage: pd.DataFrame) -> None:
    """写一份可直接阅读的技术说明，兼顾汇报口径与算法口径。"""
    top_weight_rows = []
    for row in weights.head(10).itertuples():
        truth_flag = "是" if bool(row.is_truth) else "否"
        top_weight_rows.append(
            f"| {row.node} | {row.posterior_mean_share:.4f} | {row.posterior_median_share:.4f} | {truth_flag} |"
        )

    coverage_rows = []
    for row in coverage.itertuples():
        coverage_rows.append(f"| {row.monitor} | {row.coverage_90:.4f} |")

    report = f"""# 0323 技术报告

## 1. 场景概述
本轮实验在原始 SWMM 管网基础上，选取了 20 个候选节点组成一个精细子网络。
目标是验证：在 10 分钟分辨率数据条件下，是否能够通过监测点流量响应，将两个真实注入点从候选节点中识别出来。

- 真实注入点：{", ".join(summary["truth_nodes"])}
- 监测点：{", ".join(summary["monitor_nodes"])}
- 边界监测点：{", ".join(summary["boundary_monitors"])}
- 候选节点数：{summary["candidate_count"]}
- 分析时间步长：{summary["analysis_step_seconds"]} 秒

## 2. 核心链路
这套链路保持论文主逻辑不变：

1. 先用 dry 工况和注入工况构造监测点流量增量。
2. 由边界监测点积分差值反算总额外入流量 Q_R。
3. 用多种群 GA 在 20 个候选节点之间分配 Q_R，并形成 initial PPD。
4. 用 AM 在 initial PPD 基础上继续进行 posterior 采样。
5. 通过 posterior predictive validation 评估真实监测曲线是否落在后验预测区间内。

## 3. 当前结果
- 最终识别点：{", ".join(summary["predicted_nodes"])}
- 最终解来源：{summary["final_solution_name"]}
- Mean NSE：{summary["final_mean_nse"]:.4f}
- ACC：{summary["acc"]:.4f}
- MCC：{summary["mcc"]:.4f}
- Q_R：{summary["q_r_monitor_based"]:.2f} m³
- Posterior 90% 覆盖均值：{summary["posterior_coverage_mean"]:.4f}

## 4. Posterior Top 10 节点
| 节点 | posterior mean share | posterior median share | 是否真值 |
|---|---:|---:|---|
{chr(10).join(top_weight_rows)}

## 5. Posterior Predictive 覆盖率
| 监测点 | 90% 覆盖率 |
|---|---:|
{chr(10).join(coverage_rows)}

## 6. 结果解读
从当前结果看，这一版 20 节点精细子网络已经能够稳定识别两个真实注入点，说明：

- 监测积分反算 Q_R 这条链路是可行的；
- GA 可以把搜索收缩到正确的高概率区域；
- AM 与 posterior 结果已经足够支撑最终识别；
- posterior predictive validation 也已经接回主链。

当前仍然可以继续提升的方向，主要集中在 posterior predictive coverage 的进一步提高，尤其是对较弱监测点的覆盖表现。
"""
    (RESULT_DIR / "0323_技术报告.md").write_text(report, encoding="utf-8")


def main() -> None:
    summary, weights, ga_history, coverage = load_inputs()
    build_ga_posterior_summary(summary, weights, ga_history, coverage)
    build_overview_html(summary, coverage)
    write_technical_report(summary, weights, coverage)
    print(f"Wrote 0323 report artifacts: {RESULT_DIR}")


if __name__ == "__main__":
    main()
