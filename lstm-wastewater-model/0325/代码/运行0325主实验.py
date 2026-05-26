from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import numpy as np

from 公共配置与数据 import 实验配置, 保存基础数据, 结果目录
from 模型仿真与评估 import 保存实验数据, 构造实验数据, 目标函数评估器
from 遗传搜索与后验 import 提取后验结果, 运行AM, 运行GA
from 生成结构可视化 import 生成全网结构图, 生成监测拟合图


def main() -> None:
    config = 实验配置()
    结果目录.mkdir(parents=True, exist_ok=True)

    保存基础数据(config)
    dataset = 构造实验数据(config)
    保存实验数据(dataset)

    evaluator = 目标函数评估器(dataset, config)
    _, ga_hist, initial_ppd, ga_best_shares = 运行GA(evaluator, config)
    am_df = 运行AM(evaluator, initial_ppd, config)
    posterior = 提取后验结果(am_df, config)

    posterior_map = dict(zip(posterior["节点"], posterior["后验均值"]))
    posterior_mean_shares = np.array([posterior_map[node] for node in config.候选节点], dtype=float)
    posterior_mean_shares = posterior_mean_shares / posterior_mean_shares.sum()

    top_post_row = am_df.sort_values("log_posterior", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_post_row[node] for node in config.候选节点], dtype=float)
    posterior_best_shares = posterior_best_shares / posterior_best_shares.sum()

    candidate_solutions = {
        "ga_best": np.asarray(ga_best_shares, dtype=float),
        "posterior_mean": posterior_mean_shares,
        "posterior_best": posterior_best_shares,
    }
    candidate_evals = {name: evaluator.评估方案(shares) for name, shares in candidate_solutions.items()}
    final_name, final_eval = max(candidate_evals.items(), key=lambda item: item[1]["mean_nse"])

    final_eval["sim_delta"].to_csv(
        结果目录 / "0325_最佳方案模拟增量.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "唯一排口": config.唯一排口,
        "20个候选节点": list(config.候选节点),
        "真值注入点": list(config.真值注入点),
        "监测点": list(config.监测点),
        "Qr_m3": dataset.Qr_m3,
        "Qr说明": "3个汇入点注入序列积分汇总",
        "ga_best_mean_nse": float(ga_hist["best_mean_nse"].max()),
        "posterior_mean_nse": float(candidate_evals["posterior_mean"]["mean_nse"]),
        "posterior_best_nse": float(candidate_evals["posterior_best"]["mean_nse"]),
        "final_solution_name": final_name,
        "final_mean_nse": float(final_eval["mean_nse"]),
        "predicted_top3": posterior.head(3)["节点"].tolist(),
    }
    (结果目录 / "0325_结果汇总.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    生成全网结构图(config)
    生成监测拟合图(dataset.观测增量, final_eval["sim_delta"], config)

    report_lines = [
        "# 0325 当前主实验汇报",
        "",
        f"- 唯一排口：`{config.唯一排口}`",
        f"- 20 个候选节点：{'、'.join(config.候选节点)}",
        f"- 3 个真值注入点：{'、'.join(config.真值注入点)}",
        f"- {len(config.监测点)} 个监测点：{'、'.join(config.监测点)}",
        f"- 事件窗口：{config.事件时长小时} 小时，{config.时间步秒数 // 60} 分钟一笔",
        f"- Q_R：{dataset.Qr_m3:.2f} m3",
        f"- Q_R 口径：{summary['Qr说明']}",
        f"- GA 最佳 Mean NSE：{summary['ga_best_mean_nse']:.4f}",
        f"- posterior mean Mean NSE：{summary['posterior_mean_nse']:.4f}",
        f"- posterior best Mean NSE：{summary['posterior_best_nse']:.4f}",
        f"- 最终采用解：{summary['final_solution_name']}",
        f"- 最终 Mean NSE：{summary['final_mean_nse']:.4f}",
        f"- 当前识别前 3 节点：{'、'.join(summary['predicted_top3'])}",
        "",
        "## 注水过程说明",
        "",
        "本次 8 小时事件采用一条共享的降雨型时间过程，将三个真值点的总量按 48 个 10 分钟时段进行等比例分配。",
        "三个点总量分别为 18000、26000、32000 m3，因此时间节奏一致，但总体强度不同。",
        "",
        "## 算法说明",
        "",
        "1. 先在 dry 基线模型上跑 8 小时基线。",
        "2. 再在同一基线模型上叠加三点真值注水，得到事件工况。",
        f"3. 用事件减基线形成 {len(config.监测点)} 个监测点的观测增量序列。",
        "4. 用 20 维份额向量表示各候选节点分到的总入流量比例。",
        f"5. GA 在 20 维空间里做全局搜索，指标是 {len(config.监测点)} 个监测点增量流量的平均 NSE。",
        "6. GA 末代高分样本经轮盘赌形成 initial PPD，再交给 AM 继续做后验采样。",
        "",
        "## 结果文件",
        "",
        "- `0325_原始全网选点方案.html`：全网结构、主干长路径和选点结果",
        "- `0325_监测拟合.html`：监测点观测增量与最终模拟增量对比",
        "- `0325_GA全部方案.csv`：GA 全部个体",
        "- `0325_AM样本.csv`：AM 全部采样链",
        "- `0325_后验节点权重.csv`：后验节点权重汇总",
    ]
    (结果目录 / "0325_成果汇报.md").write_text("\n".join(report_lines), encoding="utf-8")

    print("0325 主实验已完成")
    print(f"唯一排口 = {config.唯一排口}")
    print(f"Q_R = {dataset.Qr_m3:.2f} m3")
    print("当前识别前 3 节点：", "、".join(summary["predicted_top3"]))
    print(f"最终采用解 = {summary['final_solution_name']}")
    print(f"最终 Mean NSE = {summary['final_mean_nse']:.4f}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
