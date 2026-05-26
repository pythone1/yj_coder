from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

import full_network_source_tracing as base


WORK_DIR = Path(r"E:\PY\LSTM\swmm_case")
RESULT_DIR = WORK_DIR / "paper_route_full_dim_results" / "midscale_ppd"


def build_truth_prediction_map(summary: dict, output_html: Path) -> None:
    """绘制真实异常点与当前识别结果的对比图。"""
    nodes_df, links_df = base.parse_network(WORK_DIR / "case_dry.inp")
    candidate_nodes = set(summary["candidate_nodes"])
    truth_nodes = set(summary["truth_nodes"])
    predicted_nodes = set(summary["predicted_nodes"])
    monitor_nodes = set(base.MONITOR_NODES)

    fig = go.Figure()
    for row in links_df.itertuples():
        fig.add_trace(
            go.Scatter(
                x=[row.x1, row.x2],
                y=[row.y1, row.y2],
                mode="lines",
                line=dict(color="rgba(100,116,139,0.35)", width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    def add_group(name: str, node_list: list[str], color: str, symbol: str, size: int) -> None:
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

    overlap = sorted(truth_nodes & predicted_nodes)
    truth_only = sorted(truth_nodes - predicted_nodes)
    predicted_only = sorted(predicted_nodes - truth_nodes)
    candidate_only = sorted(candidate_nodes - truth_nodes - predicted_nodes)

    add_group("监测点", sorted(monitor_nodes), "#2563eb", "square", 13)
    add_group("真值且识别到", overlap, "#f59e0b", "diamond", 15)
    add_group("真值但未识别", truth_only, "#dc2626", "circle", 14)
    add_group("识别到但非真值", predicted_only, "#16a34a", "star", 16)
    add_group("其他候选点", candidate_only, "#94a3b8", "circle-open", 10)

    fig.update_layout(
        template="plotly_white",
        title="真实异常点与识别结果对比图",
        xaxis_title="X 坐标",
        yaxis_title="Y 坐标",
        height=860,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def build_leadership_overview(summary: dict, output_html: Path) -> None:
    """生成给领导直接查看的总览 HTML。"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>污水管网入渗溯源项目总览</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --ink: #10233c;
      --muted: #58708a;
      --accent: #0f766e;
      --accent2: #2563eb;
      --warn: #b45309;
      --danger: #b91c1c;
      --border: #d9e2ec;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      background:
        radial-gradient(circle at top right, rgba(37,99,235,0.08), transparent 28%),
        radial-gradient(circle at left center, rgba(15,118,110,0.08), transparent 24%),
        var(--bg);
      color: var(--ink);
    }}
    .wrap {{
      width: min(1380px, calc(100% - 40px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, #ffffff, #eef6ff 48%, #eefbf8);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px 30px;
      box-shadow: 0 18px 44px rgba(16,35,60,0.08);
    }}
    h1, h2, h3 {{ margin: 0; }}
    .subtitle {{
      margin-top: 10px;
      color: var(--muted);
      line-height: 1.7;
      font-size: 16px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 22px;
    }}
    .metric {{
      background: rgba(255,255,255,0.9);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px 16px;
    }}
    .metric .label {{
      color: var(--muted);
      font-size: 13px;
    }}
    .metric .value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
      color: var(--ink);
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      margin-top: 20px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 22px;
      box-shadow: 0 12px 28px rgba(16,35,60,0.06);
    }}
    .card p, .card li {{
      color: var(--muted);
      line-height: 1.75;
      margin: 0;
      font-size: 15px;
    }}
    ul {{
      margin: 12px 0 0;
      padding-left: 20px;
    }}
    .two {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-top: 18px;
    }}
    iframe {{
      width: 100%;
      min-height: 560px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: #fff;
    }}
    .tag {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      margin-right: 8px;
      margin-top: 10px;
      font-size: 13px;
      background: #e8f4ff;
      color: var(--accent2);
    }}
    .truth {{ color: var(--danger); font-weight: 700; }}
    .pred {{ color: var(--accent); font-weight: 700; }}
    .warn {{ color: var(--warn); font-weight: 700; }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>污水管网入渗溯源项目总览</h1>
      <p class="subtitle">
        这套系统的目标，是在只掌握少量监测点流量数据的情况下，
        通过 <strong>SWMM 物理仿真 + 遗传算法 + 贝叶斯后验采样</strong>，
        反推出最可能存在异常入渗的节点位置与贡献大小。
        当前阶段采用 10 个候选节点、4 个监测点的受控盲测版本，用于验证算法链路与可解释性。
      </p>
      <div class="metrics">
        <div class="metric"><div class="label">真实异常点</div><div class="value">{", ".join(summary["truth_nodes"])}</div></div>
        <div class="metric"><div class="label">当前识别结果</div><div class="value">{", ".join(summary["predicted_nodes"])}</div></div>
        <div class="metric"><div class="label">注水放大系数</div><div class="value">{summary.get("truth_scale_factor", 1.0):.2f}</div></div>
        <div class="metric"><div class="label">Mean NSE</div><div class="value">{summary["final_mean_nse"]:.4f}</div></div>
        <div class="metric"><div class="label">ACC</div><div class="value">{summary["acc"]:.4f}</div></div>
        <div class="metric"><div class="label">MCC</div><div class="value">{summary["mcc"]:.4f}</div></div>
        <div class="metric"><div class="label">AM 平均接受率</div><div class="value">{summary['am_accept_rate_mean']:.4f}</div></div>
      </div>
    </section>

    <section class="grid">
      <article class="card">
        <h2>一、这套算法在干什么</h2>
        <ul>
          <li>先用 <strong>晴天基线模型</strong> 给出没有异常入流时的正常响应。</li>
          <li>再用受控注水构造 <strong>观测增量</strong>，也就是异常带来的额外流量变化。</li>
          <li>遗传算法在 10 个候选节点上同时分配总入流量，反复调用 SWMM，寻找与监测曲线最接近的区域。</li>
          <li>随后用自适应 Metropolis 对高相关区域做贝叶斯采样，输出 posterior PPD 和收敛诊断。</li>
          <li>最终不仅给出“怀疑哪些点有问题”，还给出每个点贡献大小以及不确定性。</li>
        </ul>
      </article>
      <article class="card">
        <h2>二、领导最需要看的结论</h2>
        <ul>
          <li>当前链路已经从“试验脚本”升级为“<strong>可解释的数值反演系统</strong>”。</li>
          <li>本轮采用了 <strong>{summary.get("truth_scale_factor", 1.0):.2f} 倍注水放大系数</strong>，让受控实验激励更明显。</li>
          <li>算法已能稳定给出 posterior 结果，但当前仍存在 <span class="warn">邻近井代偿</span> 问题。</li>
          <li>项目现在的重点已经转为“提高辨识精度”，而不是“从零搭建链路”。</li>
        </ul>
        <div>
          <span class="tag">受控盲测</span>
          <span class="tag">10 节点候选池</span>
          <span class="tag">4 个监测点</span>
          <span class="tag">GA + AM</span>
        </div>
      </article>
    </section>

    <section class="two">
      <article class="card">
        <h2>三、真实结果 vs 识别结果</h2>
        <p>下图直接对比了真实注水点与算法识别点。红色是真值未识别，绿色是识别但非真值，金色表示真值与识别重合。</p>
        <iframe src="truth_vs_prediction_map.html"></iframe>
      </article>
      <article class="card">
        <h2>四、监测点拟合效果</h2>
        <p>下图展示 4 个监测点上，算法反演结果与真实观测增量的曲线贴合情况。Mean NSE 越高，说明整体拟合越好。</p>
        <iframe src="full_dim_monitor_fit.html"></iframe>
      </article>
    </section>

    <section class="two">
      <article class="card">
        <h2>五、后验概率分布 PPD</h2>
        <p>这一步展示算法最后认为“每个候选节点有多大概率应当保留较高入流份额”，它比单个点解更适合用来解释不确定性。</p>
        <iframe src="paper_posterior_ppd.html"></iframe>
      </article>
      <article class="card">
        <h2>六、收敛与采样诊断</h2>
        <p>这一步展示 posterior 链是否稳定、是否收敛、接受率是否健康，是判断结果是否可信的重要依据。</p>
        <iframe src="paper_convergence_diagnostics.html"></iframe>
      </article>
    </section>
  </div>
</body>
</html>
"""
    output_html.write_text(html, encoding="utf-8")


def write_report(summary: dict, output_md: Path) -> None:
    """写一份面向汇报的 Markdown 结论稿。"""
    lines = [
        "# 项目最终汇报",
        "",
        "## 1. 项目目标",
        "",
        "本项目旨在利用少量监测点流量数据，对污水管网中的异常入渗位置进行数值化定位。",
        "当前阶段采用 10 个候选节点、4 个监测点的受控盲测版本，验证整套 `SWMM + GA + AM` 技术链路是否成立。",
        "",
        "## 2. 当前实验设置",
        "",
        f"- 真实异常点：{', '.join(summary['truth_nodes'])}",
        f"- 当前识别结果：{', '.join(summary['predicted_nodes'])}",
        f"- 注水放大系数：{summary.get('truth_scale_factor', 1.0):.2f}",
        "",
        "## 3. 总体技术架构",
        "",
        "1. 用 `case_dry.inp` 作为晴天基线模型，得到正常工况响应。",
        "2. 用已知真值注水模板构造受控观测，形成监测点流量增量。",
        "3. 在总入流量守恒约束下，用遗传算法在 10 个候选节点中做全局粗筛。",
        "4. 将 GA 末代种群合并，并通过轮盘赌构造 `initial PPD`。",
        "5. 用自适应 Metropolis 在 `initial PPD` 基础上做 posterior 采样。",
        "6. 输出节点后验分布、收敛诊断、监测拟合图和真值对比图。",
        "",
        "## 4. 当前结果",
        "",
        f"- Mean NSE：{summary['final_mean_nse']:.4f}",
        f"- ACC：{summary['acc']:.4f}",
        f"- MCC：{summary['mcc']:.4f}",
        f"- MAE(all nodes)：{summary['mae_all_nodes']:.4f}",
        f"- MAE(truth nodes)：{summary['mae_truth_nodes']:.4f}",
        f"- AM 平均接受率：{summary['am_accept_rate_mean']:.4f}",
        "",
        "## 5. 结论",
        "",
        "当前系统已经具备完整、可运行、可解释的数值反演链路。",
        "如果后续继续优化，重点应放在 posterior 辨识能力、监测布设与时序激励设计，而不是重新搭主框架。",
        "",
        "## 6. 配套文件",
        "",
        "- `领导汇报总览.html`：领导可直接查看的图文总览",
        "- `truth_vs_prediction_map.html`：真实异常点与识别结果对比图",
        "- `paper_posterior_ppd.html`：后验分布图",
        "- `paper_convergence_diagnostics.html`：收敛诊断图",
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def write_node_summary(summary: dict, output_csv: Path) -> None:
    """把真值点、识别点和后验权重放进一张表，方便你在 Excel 中查看。"""
    weights = pd.read_csv(RESULT_DIR / "full_dim_weights.csv")
    weights["is_truth"] = weights["node"].isin(summary["truth_nodes"])
    weights["is_predicted"] = weights["node"].isin(summary["predicted_nodes"])
    weights.to_csv(output_csv, index=False, encoding="utf-8-sig")


def main() -> None:
    summary = json.loads((RESULT_DIR / "full_dim_summary.json").read_text(encoding="utf-8"))
    build_truth_prediction_map(summary, RESULT_DIR / "truth_vs_prediction_map.html")
    build_leadership_overview(summary, RESULT_DIR / "领导汇报总览.html")
    write_report(summary, RESULT_DIR / "项目最终汇报.md")
    write_node_summary(summary, RESULT_DIR / "节点识别对比表.csv")
    print("Wrote final leadership report artifacts to", RESULT_DIR)


if __name__ == "__main__":
    main()
