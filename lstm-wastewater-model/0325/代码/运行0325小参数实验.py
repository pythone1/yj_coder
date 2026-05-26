from __future__ import annotations

import json
import multiprocessing

import numpy as np

from 公共配置与数据 import 实验配置, 保存基础数据, 结果目录
from 模型仿真与评估 import 保存实验数据, 构造实验数据, 目标函数评估器
from 遗传搜索与后验 import 后验预测验证, 提取后验结果, 运行AM, 运行GA
from 生成结构可视化 import 生成全网结构图, 生成监测拟合图


def main() -> None:
    """0325 小参数验证入口。

    目的：
    1. 保持当前结构、候选点、真值点、监测点和主算法逻辑不变；
    2. 将 GA 和 AM 都缩回小参数；
    3. 先验证整条链能稳定跑通，不再出现长时间卡住的情况。
    """

    config = 实验配置(
        ga_种群数=3,
        ga_单群规模=12,
        ga_迭代代数=8,
        ga_精英比例=0.25,
        ga_变异强度=0.12,
        ga_迁移间隔代数=2,
        ga_跨代topk保留数=36,
        initial_ppd最小保留数=10,
        initial_ppd最大保留数=20,
        initial_ppd相对最优容差=0.10,
        initial_ppd分位数阈值=0.70,
        initial_ppd权重温度=0.05,
        am_链数=3,
        am_每链样本=120,
        am_预热=30,
        am_自适应起点=30,
        并行工作进程数=3,
    )
    结果目录.mkdir(parents=True, exist_ok=True)

    保存基础数据(config)
    dataset = 构造实验数据(config)
    保存实验数据(dataset)

    evaluator = 目标函数评估器(dataset, config)
    _, ga_hist, initial_ppd, ga_best_shares = 运行GA(evaluator, config)
    am_df = 运行AM(evaluator, initial_ppd, config)
    posterior = 提取后验结果(am_df, config)
    _, coverage_df = 后验预测验证(
        evaluator,
        am_df,
        config,
        sample_count=config.posterior_validation_sample_count,
    )

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
        "运行模式": "小参数验证",
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
        "posterior_validation_sample_count": int(config.posterior_validation_sample_count),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "posterior_coverage_min": float(coverage_df["coverage_90"].min()),
        "posterior_coverage_max": float(coverage_df["coverage_90"].max()),
        "am_accept_rate_by_chain": {
            str(int(k)): float(v) for k, v in am_df.groupby("链号")["accepted"].mean().items()
        },
    }
    (结果目录 / "0325_结果汇总.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    生成全网结构图(config)
    生成监测拟合图(dataset.观测增量, final_eval["sim_delta"], config)

    print("0325 小参数实验已完成")
    print(f"唯一排口 = {config.唯一排口}")
    print(f"Q_R = {dataset.Qr_m3:.2f} m3")
    print("当前识别前 3 节点：", "、".join(summary["predicted_top3"]))
    print(f"最终采用解 = {summary['final_solution_name']}")
    print(f"最终 Mean NSE = {summary['final_mean_nse']:.4f}")
    print("AM 接受率：", summary["am_accept_rate_by_chain"])


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
