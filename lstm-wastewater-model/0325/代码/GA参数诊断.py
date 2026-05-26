from __future__ import annotations

import itertools
import json
import multiprocessing
from pathlib import Path

import numpy as np
import pandas as pd

from 公共配置与数据 import 实验配置, 结果目录, 保存基础数据
from 模型仿真与评估 import 构造实验数据, 目标函数评估器, 保存实验数据
from 遗传搜索与后验 import 运行GA


def 计算真值份额(config: 实验配置) -> dict[str, float]:
    total = float(sum(config.真值总体积立方米))
    return {
        node: float(volume / total)
        for node, volume in zip(config.真值注入点, config.真值总体积立方米)
    }


def 评估接近程度(best_shares: np.ndarray, config: 实验配置) -> dict[str, float | list[str]]:
    candidate_nodes = list(config.候选节点)
    truth_share_map = 计算真值份额(config)
    best_share_map = {node: float(best_shares[idx]) for idx, node in enumerate(candidate_nodes)}

    # 真值节点上的份额恢复情况
    truth_recovered = {
        node: best_share_map.get(node, 0.0)
        for node in config.真值注入点
    }

    # top3 节点
    top3 = sorted(best_share_map.items(), key=lambda item: item[1], reverse=True)[:3]
    top3_nodes = [node for node, _ in top3]
    top3_overlap = sum(1 for node in top3_nodes if node in config.真值注入点)

    # 在当前候选走廊顺序上，计算每个 top3 到最近真值点的最小索引距离
    idx_map = {node: idx for idx, node in enumerate(candidate_nodes)}
    truth_idx = [idx_map[node] for node in config.真值注入点]
    top3_distance = float(
        np.mean([min(abs(idx_map[node] - t) for t in truth_idx) for node in top3_nodes])
    )

    # 直接看和真值份额向量的 L1 差距
    truth_vector = np.array([truth_share_map.get(node, 0.0) for node in candidate_nodes], dtype=float)
    l1_to_truth = float(np.sum(np.abs(best_shares - truth_vector)))

    return {
        "top3_nodes": top3_nodes,
        "top3_truth_overlap": int(top3_overlap),
        "top3_mean_index_distance_to_truth": top3_distance,
        "l1_to_truth": l1_to_truth,
        "truth_recovered_J76": float(truth_recovered.get("J76", 0.0)),
        "truth_recovered_J124": float(truth_recovered.get("J124", 0.0)),
        "truth_recovered_J140": float(truth_recovered.get("J140", 0.0)),
    }


def 运行单组试验(config: 实验配置) -> dict:
    保存基础数据(config)
    dataset = 构造实验数据(config)
    保存实验数据(dataset)
    evaluator = 目标函数评估器(dataset, config)
    _, ga_hist, initial_ppd, ga_best_shares = 运行GA(evaluator, config)

    ga_best_eval = evaluator.评估方案(ga_best_shares)
    closeness = 评估接近程度(np.asarray(ga_best_shares, dtype=float), config)
    return {
        "ga_种群数": config.ga_种群数,
        "ga_单群规模": config.ga_单群规模,
        "ga_迭代代数": config.ga_迭代代数,
        "ga_精英比例": config.ga_精英比例,
        "ga_变异强度": config.ga_变异强度,
        "ga_迁移间隔代数": config.ga_迁移间隔代数,
        "ga_迁移个体数": config.ga_迁移个体数,
        "ga_跨代topk保留数": config.ga_跨代topk保留数,
        "initial_ppd_size": int(len(initial_ppd)),
        "best_mean_nse": float(ga_best_eval["mean_nse"]),
        **closeness,
    }


def 主程序() -> None:
    base = 实验配置(
        am_链数=2,
        am_每链样本=40,
        am_预热=10,
        am_自适应起点=10,
        并行工作进程数=3,
    )

    # 围绕“防止第二代过早塌缩”重点扫这几个参数
    population_sizes = [8, 12, 16]
    generations = [4, 6, 8]
    elite_ratios = [0.10, 0.20, 0.25]
    mutation_sigmas = [0.08, 0.12, 0.18]
    migration_intervals = [2, 3]

    combos = []
    for pop_size, gen, elite, sigma, mig in itertools.product(
        population_sizes,
        generations,
        elite_ratios,
        mutation_sigmas,
        migration_intervals,
    ):
        combos.append(
            {
                "ga_种群数": 2,
                "ga_单群规模": pop_size,
                "ga_迭代代数": gen,
                "ga_精英比例": elite,
                "ga_变异强度": sigma,
                "ga_迁移间隔代数": mig,
                "ga_迁移个体数": 2,
                "ga_跨代topk保留数": max(24, pop_size * 2),
            }
        )

    # 先挑一批代表性组合，避免一次太夸张
    shortlist = [
        combos[0],
        combos[4],
        combos[8],
        combos[18],
        combos[26],
        combos[34],
        combos[52],
        combos[70],
        combos[88],
        combos[106],
        combos[124],
        combos[142],
    ]

    results = []
    for idx, kwargs in enumerate(shortlist, start=1):
        print(f"[GA诊断] {idx}/{len(shortlist)} -> {kwargs}", flush=True)
        config = 实验配置(**{**base.__dict__, **kwargs})
        result = 运行单组试验(config)
        results.append(result)

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values(
        ["top3_truth_overlap", "best_mean_nse", "truth_recovered_J124", "truth_recovered_J76", "truth_recovered_J140"],
        ascending=[False, False, False, False, False],
    ).reset_index(drop=True)

    out_csv = 结果目录 / "0325_GA参数诊断结果.csv"
    out_json = 结果目录 / "0325_GA参数诊断结果.json"
    result_df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out_json.write_text(
        json.dumps(result_df.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("GA 参数诊断完成")
    print(f"结果已保存: {out_csv}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    主程序()
