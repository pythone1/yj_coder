from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from 公共配置与数据 import 结果目录


def 生成结果总览页() -> Path:
    summary = json.loads((结果目录 / "0327_结果汇总.json").read_text(encoding="utf-8"))
    coverage = pd.read_csv(结果目录 / "0327_posterior_predictive_coverage.csv")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=coverage["monitor"],
            y=coverage["coverage_90"],
            marker_color="#2f6fed",
            name="90%覆盖率",
        )
    )
    fig.update_layout(
        title="0327 后验预测区间覆盖率",
        xaxis_title="监测点",
        yaxis_title="覆盖率",
        yaxis_range=[0, 1.05],
        template="plotly_white",
        margin=dict(l=40, r=30, t=60, b=40),
    )

    chart_html = pio.to_html(fig, include_plotlyjs="cdn", full_html=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>0327 结果总览</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; background: #f6f8fb; color: #1f2a44; }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    .card {{ background: #fff; border: 1px solid #d9e2f2; border-radius: 16px; padding: 20px; margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
    .kpi {{ background: #f8fbff; border: 1px solid #dbe8ff; border-radius: 12px; padding: 14px; }}
    .kpi .label {{ font-size: 13px; color: #5b6b88; }}
    .kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
    iframe {{ width: 100%; height: 720px; border: none; border-radius: 12px; }}
    .small iframe {{ height: 560px; }}
    .note {{ color: #4b5565; line-height: 1.7; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>0327 论文口径小参数验证总览</h1>
      <p class="note">本页汇总 20 候选节点、10 监测点、3 真值注入点条件下的中文论文总入流量约束与英文论文 GA + AM + PPD 主链结果。</p>
      <div class="grid">
        <div class="kpi"><div class="label">唯一排口</div><div class="value">{summary['唯一排口']}</div></div>
        <div class="kpi"><div class="label">Q_R (m3)</div><div class="value">{summary['Qr_m3']:.2f}</div></div>
        <div class="kpi"><div class="label">GA best NSE</div><div class="value">{summary['ga_best_mean_nse']:.4f}</div></div>
        <div class="kpi"><div class="label">最终 Mean NSE</div><div class="value">{summary['final_mean_nse']:.4f}</div></div>
        <div class="kpi"><div class="label">posterior mean NSE</div><div class="value">{summary['posterior_mean_nse']:.4f}</div></div>
        <div class="kpi"><div class="label">posterior median NSE</div><div class="value">{summary['posterior_median_nse']:.4f}</div></div>
        <div class="kpi"><div class="label">posterior best NSE</div><div class="value">{summary['posterior_best_nse']:.4f}</div></div>
        <div class="kpi"><div class="label">PPD平均覆盖率</div><div class="value">{summary['posterior_coverage_mean']:.4f}</div></div>
      </div>
      <p class="note">当前最终采用解：<b>{summary['final_solution_name']}</b>；当前识别前 3 节点：<b>{'、'.join(summary['predicted_top3'])}</b>；initial PPD 样本数：<b>{summary['initial_ppd_count']}</b>。</p>
    </div>
    <div class="card small">{chart_html}</div>
    <div class="card">
      <h2>全网结构与选点</h2>
      <iframe src="./0327_原始全网选点方案.html"></iframe>
    </div>
    <div class="card">
      <h2>监测拟合结果</h2>
      <iframe src="./0327_监测拟合.html"></iframe>
    </div>
  </div>
</body>
</html>
"""
    out = 结果目录 / "0327_结果总览.html"
    out.write_text(html, encoding="utf-8")
    return out


def 生成详细汇报() -> Path:
    summary = json.loads((结果目录 / "0327_结果汇总.json").read_text(encoding="utf-8"))
    coverage = pd.read_csv(结果目录 / "0327_posterior_predictive_coverage.csv")
    coverage_lines = [
        f"- {row.monitor}: 90%覆盖率 = {row.coverage_90:.4f}"
        for row in coverage.itertuples(index=False)
    ]

    lines = [
        "# 0327 项目阶段汇报",
        "",
        "## 一、实验结构",
        "",
        f"- 唯一排口：`{summary['唯一排口']}`",
        f"- 20 个候选节点：{'、'.join(summary['20个候选节点'])}",
        f"- 3 个真值注入点：{'、'.join(summary['真值注入点'])}",
        f"- 10 个监测点：{'、'.join(summary['监测点'])}",
        "- 时间设置：8 小时事件窗口、10 分钟分辨率、共 48 个时间步",
        f"- 总入流量 Q_R：{summary['Qr_m3']:.2f} m3",
        f"- Q_R 口径：{summary['Qr说明']}",
        "",
        "## 二、算法口径",
        "",
        "- 中文论文部分：保留总入流量约束，将三点真值注水总量积分作为受控实验下的 Q_R。",
        "- 英文论文部分：使用多种群 GA、competition / migration、roulette wheel selection 形成 initial PPD；再用 AM 做后验采样；输出 PPD，并做 posterior predictive validation。",
        "- 工程保险丝：最终结果保留 `ga_best / posterior_mean / posterior_median / posterior_best` 择优机制，避免后验均值把好解平均坏。",
        "",
        "## 三、小参数结果",
        "",
        f"- GA best Mean NSE：{summary['ga_best_mean_nse']:.4f}",
        f"- posterior mean Mean NSE：{summary['posterior_mean_nse']:.4f}",
        f"- posterior median Mean NSE：{summary['posterior_median_nse']:.4f}",
        f"- posterior best Mean NSE：{summary['posterior_best_nse']:.4f}",
        f"- 最终采用解：`{summary['final_solution_name']}`",
        f"- 最终 Mean NSE：{summary['final_mean_nse']:.4f}",
        f"- 当前识别前 3 节点：{'、'.join(summary['predicted_top3'])}",
        f"- initial PPD 样本数：{summary['initial_ppd_count']}",
        "",
        "## 四、PPD 预测区间验证",
        "",
        f"- PPD 抽样数：{summary['posterior_validation_sample_count']}",
        f"- 平均覆盖率：{summary['posterior_coverage_mean']:.4f}",
        f"- 最小覆盖率：{summary['posterior_coverage_min']:.4f}",
        f"- 最大覆盖率：{summary['posterior_coverage_max']:.4f}",
        *coverage_lines,
        "",
        "## 五、文件索引",
        "",
        "- `0327_原始全网选点方案.html`：结构与选点图",
        "- `0327_监测拟合.html`：观测增量与模拟增量对比图",
        "- `0327_GA全部方案.csv`：GA 全部方案",
        "- `0327_initial_PPD.csv`：轮盘赌形成的 initial PPD",
        "- `0327_AM样本.csv`：AM 全部样本",
        "- `0327_PPD样本.csv`：PPD 尾部样本",
        "- `0327_posterior_predictive_bands.csv`：后验预测区间",
        "- `0327_posterior_predictive_coverage.csv`：后验覆盖率统计",
        "- `0327_结果总览.html`：结果总览页",
        "",
    ]

    out = 结果目录 / "0327_详细汇报.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    生成结果总览页()
    生成详细汇报()
    print("0327 汇报材料已生成")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
