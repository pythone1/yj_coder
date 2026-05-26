from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from 公共配置与数据 import 实验配置, 结果目录, 获取工作模型路径
from 模型仿真与评估 import 数据集, simplex投影, 目标函数评估器


_并行评估器: 目标函数评估器 | None = None


def _初始化GA工作进程(dataset: 数据集, config: 实验配置) -> None:
    global _并行评估器
    model_path = 获取工作模型路径(f"ga_{os.getpid()}")
    _并行评估器 = 目标函数评估器(dataset, config, model_path=model_path)


def _GA评估单个个体(shares: np.ndarray) -> dict:
    assert _并行评估器 is not None
    res = _并行评估器.评估方案(np.asarray(shares, dtype=float))
    return {
        "shares": np.asarray(res["shares"], dtype=float),
        "mean_nse": float(res["mean_nse"]),
        "loss": float(res["loss"]),
        "sse": float(res["sse"]),
    }


def _初始化AM工作进程(dataset: 数据集, config: 实验配置) -> None:
    global _并行评估器
    model_path = 获取工作模型路径(f"am_{os.getpid()}")
    _并行评估器 = 目标函数评估器(dataset, config, model_path=model_path)


def 随机稀疏种子(dim: int, rng: np.random.Generator) -> np.ndarray:
    vec = np.zeros(dim, dtype=float)
    k = int(rng.integers(1, min(4, dim) + 1))
    idx = rng.choice(dim, size=k, replace=False)
    vec[idx] = rng.random(k)
    return simplex投影(vec)


def 初始化多种群(config: 实验配置, rng: np.random.Generator) -> list[list[np.ndarray]]:
    """真正盲测初始化：每个种群独立随机生成，不使用真值点与真值组合。"""
    dim = len(config.候选节点)
    populations: list[list[np.ndarray]] = []
    for _ in range(config.ga_种群数):
        pop: list[np.ndarray] = []
        sparse_n = max(2, config.ga_单群规模 // 2)
        for _ in range(sparse_n):
            pop.append(随机稀疏种子(dim, rng))
        while len(pop) < config.ga_单群规模:
            pop.append(simplex投影(rng.dirichlet(np.ones(dim))))
        populations.append(pop)
    return populations


def 交叉(parent_a: np.ndarray, parent_b: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    alpha = float(rng.uniform(0.25, 0.75))
    return simplex投影(alpha * parent_a + (1.0 - alpha) * parent_b)


def 变异(vector: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    mutated = np.maximum(vector + rng.normal(0.0, sigma, size=len(vector)), 0.0)
    return simplex投影(mutated)


def 轮盘赌保留(candidate_pool: pd.DataFrame, keep_ratio: float, rng: np.random.Generator) -> pd.DataFrame:
    """按英文论文口径保留高分个体：roulette wheel selection。"""
    if candidate_pool.empty:
        raise ValueError("candidate_pool 为空，无法进行轮盘赌保留。")

    values = candidate_pool["mean_nse"].to_numpy(dtype=float)
    values = values - np.max(values)
    weights = np.exp(values)
    weights = np.maximum(weights, 1e-12)
    weights /= weights.sum()

    keep_n = max(3, int(round(len(candidate_pool) * keep_ratio)))
    keep_n = min(keep_n, len(candidate_pool))

    forced_rows = candidate_pool[candidate_pool.get("forced_ga_best", 0) == 1].copy()
    forced_indices = forced_rows.index.to_numpy(dtype=int)
    forced_weights = weights[forced_indices] if len(forced_indices) else np.array([], dtype=float)

    available_mask = np.ones(len(candidate_pool), dtype=bool)
    available_mask[forced_indices] = False
    available_idx = np.arange(len(candidate_pool))[available_mask]
    available_weights = weights[available_mask]
    if available_weights.size > 0:
        available_weights = available_weights / available_weights.sum()

    remain = max(0, keep_n - len(forced_rows))
    if remain > 0 and len(available_idx) > 0:
        chosen = rng.choice(
            available_idx,
            size=min(remain, len(available_idx)),
            replace=False,
            p=available_weights,
        )
    else:
        chosen = np.array([], dtype=int)

    kept = pd.concat([forced_rows, candidate_pool.iloc[np.sort(chosen)].copy()], ignore_index=True)
    roulette_weight = list(forced_weights) + list(weights[np.sort(chosen)])
    kept["roulette_weight"] = roulette_weight
    total = float(kept["roulette_weight"].sum())
    kept["roulette_weight"] = kept["roulette_weight"] / max(total, 1e-12)
    return kept.reset_index(drop=True)


def _竞争与迁移(
    populations: list[list[np.ndarray]],
    population_scores: list[list[dict]],
    config: 实验配置,
) -> list[list[np.ndarray]]:
    """按论文描述补上多种群 competition / migration。"""
    migrate_k = max(1, min(config.ga_迁移个体数, config.ga_单群规模 // 2))
    ranked = []
    for pop_id, scored in enumerate(population_scores):
        ranked.append((pop_id, max(item["mean_nse"] for item in scored)))
    ranked.sort(key=lambda item: item[1], reverse=True)

    sorted_scored = {
        pop_id: sorted(population_scores[pop_id], key=lambda item: item["mean_nse"], reverse=True)
        for pop_id, _ in ranked
    }

    # competition：最优种群的精英替换最差种群的尾部个体
    best_pop_id = ranked[0][0]
    donor = [np.asarray(item["shares"], dtype=float).copy() for item in sorted_scored[best_pop_id][:migrate_k]]
    for loser_id, _ in ranked[1:]:
        populations[loser_id][-migrate_k:] = [vec.copy() for vec in donor]

    # migration：各群体之间做环形迁移，避免完全塌缩在单一盆地
    elite_blocks = {
        pop_id: [np.asarray(item["shares"], dtype=float).copy() for item in sorted_scored[pop_id][:migrate_k]]
        for pop_id, _ in ranked
    }
    for idx, (pop_id, _) in enumerate(ranked):
        target_id = ranked[(idx + 1) % len(ranked)][0]
        populations[target_id][-migrate_k:] = [vec.copy() for vec in elite_blocks[pop_id]]

    return populations


def 运行GA(
    evaluator: 目标函数评估器,
    config: 实验配置,
    seed: int = 20260325,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    """英文论文风格的多种群 GA：
    1. 多个 population 独立进化；
    2. 固定间隔执行 competition / migration；
    3. 末代合并后使用 roulette wheel 形成 initial PPD。
    """

    rng = np.random.default_rng(seed)
    populations = 初始化多种群(config, rng)
    population_rows: list[dict] = []
    generation_rows: list[dict] = []

    max_workers = max(1, min(config.并行工作进程数, config.ga_种群数 * config.ga_单群规模))
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_初始化GA工作进程,
        initargs=(evaluator.dataset, config),
    ) as executor:
        for generation in range(config.ga_迭代代数):
            population_scores: list[list[dict]] = []

            for pop_id, population in enumerate(populations):
                scored = list(executor.map(_GA评估单个个体, population))
                scored.sort(key=lambda item: item["mean_nse"], reverse=True)
                population_scores.append(scored)

                for idx, result in enumerate(scored):
                    row = {
                        "代数": generation + 1,
                        "种群号": pop_id + 1,
                        "个体序号": idx + 1,
                        "mean_nse": result["mean_nse"],
                        "loss": result["loss"],
                    }
                    for i, node in enumerate(config.候选节点):
                        row[node] = float(result["shares"][i])
                    population_rows.append(row)

            generation_best = max((scored[0] for scored in population_scores), key=lambda item: item["mean_nse"])
            gen_row = {
                "代数": generation + 1,
                "best_mean_nse": generation_best["mean_nse"],
                "best_loss": generation_best["loss"],
            }
            for i, node in enumerate(config.候选节点):
                gen_row[node] = float(generation_best["shares"][i])
            generation_rows.append(gen_row)

            new_populations: list[list[np.ndarray]] = []
            for scored in population_scores:
                elite_n = max(2, int(round(len(scored) * config.ga_精英比例)))
                elites = [np.asarray(item["shares"], dtype=float) for item in scored[:elite_n]]
                new_population = [vec.copy() for vec in elites]
                while len(new_population) < config.ga_单群规模:
                    a, b = rng.choice(len(elites), size=2, replace=True)
                    child = 交叉(elites[a], elites[b], rng)
                    child = 变异(child, config.ga_变异强度, rng)
                    new_population.append(child)
                new_populations.append(new_population)

            populations = new_populations
            if (
                config.ga_种群数 > 1
                and (generation + 1) % max(1, config.ga_迁移间隔代数) == 0
                and generation + 1 < config.ga_迭代代数
            ):
                populations = _竞争与迁移(populations, population_scores, config)

    all_df = pd.DataFrame(population_rows)
    hist_df = pd.DataFrame(generation_rows)
    merged_last = all_df[all_df["代数"] == config.ga_迭代代数].copy().reset_index(drop=True)

    cols = list(config.候选节点)
    merged_last["_share_key"] = merged_last[cols].round(8).astype(str).agg("|".join, axis=1)
    merged_last = merged_last.sort_values(
        ["mean_nse", "种群号", "个体序号"],
        ascending=[False, True, True],
    ).drop_duplicates("_share_key", keep="first").reset_index(drop=True)

    ga_best_row = hist_df.loc[hist_df["best_mean_nse"].idxmax()]
    ga_best = np.array([ga_best_row[node] for node in cols], dtype=float)
    ga_best_key = "|".join(f"{v:.8f}" for v in ga_best)
    merged_last["forced_ga_best"] = (merged_last["_share_key"] == ga_best_key).astype(int)

    if merged_last["forced_ga_best"].sum() == 0:
        forced_row = {
            "代数": config.ga_迭代代数,
            "种群号": 0,
            "个体序号": 0,
            "mean_nse": float(ga_best_row["best_mean_nse"]),
            "loss": float(ga_best_row["best_loss"]),
            "_share_key": ga_best_key,
            "forced_ga_best": 1,
        }
        for node in cols:
            forced_row[node] = float(ga_best_row[node])
        merged_last = pd.concat([pd.DataFrame([forced_row]), merged_last], ignore_index=True)

    merged_last = merged_last.sort_values(
        ["forced_ga_best", "mean_nse", "种群号", "个体序号"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    initial_ppd = 轮盘赌保留(merged_last, config.initial_ppd保留比例, rng)

    all_df.to_csv(结果目录 / "0325_GA全部方案.csv", index=False, encoding="utf-8-sig")
    hist_df.to_csv(结果目录 / "0325_GA每代最佳.csv", index=False, encoding="utf-8-sig")
    merged_last.to_csv(结果目录 / "0325_GA末代合并.csv", index=False, encoding="utf-8-sig")
    initial_ppd.to_csv(结果目录 / "0325_initial_PPD.csv", index=False, encoding="utf-8-sig")
    return all_df, hist_df, initial_ppd, ga_best


def 构造先验(initial_ppd: pd.DataFrame, config: 实验配置) -> dict:
    """把 initial PPD 直接表达成样本型先验，而不是单高斯近似。"""
    cols = list(config.候选节点)
    samples = initial_ppd[cols].to_numpy(dtype=float)
    weights = initial_ppd["roulette_weight"].to_numpy(dtype=float)
    weights = weights / max(float(weights.sum()), 1e-12)

    # 论文只要求“initial PPD 作为 prior information”，这里用样本型核近似，
    # 保留 PPD 的多峰特征，比单高斯更贴近“分布”本身。
    empirical_cov = np.cov(samples.T)
    if empirical_cov.ndim == 0:
        empirical_cov = np.eye(len(cols)) * config.am_基础协方差
    empirical_cov = np.atleast_2d(empirical_cov)
    empirical_cov += np.eye(len(cols)) * config.am_协方差微扰
    kernel_cov = empirical_cov * config.am_先验核协方差放大倍数
    kernel_cov += np.eye(len(cols)) * 1e-9

    return {
        "samples": samples,
        "weights": weights,
        "kernel_cov": kernel_cov,
        "kernel_cov_inv": np.linalg.pinv(kernel_cov),
        "kernel_log_det": float(np.linalg.slogdet(kernel_cov)[1]),
    }


def _logsumexp(values: np.ndarray) -> float:
    vmax = float(np.max(values))
    return float(vmax + np.log(np.sum(np.exp(values - vmax))))


def log_prior(x: np.ndarray, prior_model: dict, config: 实验配置) -> float:
    samples = prior_model["samples"]
    weights = prior_model["weights"]
    cov_inv = prior_model["kernel_cov_inv"]
    log_det = prior_model["kernel_log_det"]
    dim = len(x)
    terms = []
    for sample, weight in zip(samples, weights):
        delta = x - sample
        quad = float(delta.T @ cov_inv @ delta)
        terms.append(np.log(max(weight, 1e-12)) - 0.5 * (quad + log_det + dim * np.log(2.0 * np.pi)))
    return float(_logsumexp(np.asarray(terms, dtype=float)))


def log_likelihood(sse: float, sigma2: float) -> float:
    return float(-0.5 * sse / max(sigma2, 1e-12))


def _运行单条AM链(args: tuple[int, dict, pd.DataFrame, 实验配置, int]) -> list[dict]:
    global _并行评估器
    assert _并行评估器 is not None

    chain_id, start_row, initial_ppd, config, seed = args
    rng = np.random.default_rng(seed + chain_id)
    cols = list(config.候选节点)
    prior_model = 构造先验(initial_ppd, config)
    dim = len(cols)
    sd = 2.42 / dim
    c0 = np.eye(dim) * config.am_基础协方差

    obs_values = _并行评估器.dataset.观测增量[list(config.监测点)].to_numpy(dtype=float)
    sigma2 = max(float(np.var(obs_values)) * config.am_似然方差倍数, 1e-9)

    current = simplex投影(np.array([start_row[col] for col in cols], dtype=float))
    current_eval = _并行评估器.评估方案(current)
    current_log_like = log_likelihood(current_eval["sse"], sigma2)
    current_log_prior = log_prior(current, prior_model, config)
    current_log_post = config.am_先验强度 * current_log_prior + current_log_like

    accepted_history = [current.copy()]
    rows: list[dict] = []

    for step in range(config.am_每链样本):
        if step < config.am_自适应起点 or len(accepted_history) <= 2:
            proposal_cov = c0
        else:
            history = np.asarray(accepted_history, dtype=float)
            empirical_cov = np.cov(history.T)
            empirical_cov = np.atleast_2d(empirical_cov)
            proposal_cov = sd * empirical_cov + sd * config.am_协方差微扰 * np.eye(dim)

        proposal = rng.multivariate_normal(current, proposal_cov)
        proposal = simplex投影(proposal)
        proposal_eval = _并行评估器.评估方案(proposal)
        proposal_log_like = log_likelihood(proposal_eval["sse"], sigma2)
        proposal_log_prior = log_prior(proposal, prior_model, config)
        proposal_log_post = config.am_先验强度 * proposal_log_prior + proposal_log_like

        delta_like = float(proposal_log_like - current_log_like)
        alpha = min(1.0, float(np.exp(delta_like))) if delta_like > -50 else 0.0
        accepted = rng.random() < alpha

        if accepted:
            current = proposal
            current_eval = proposal_eval
            current_log_like = proposal_log_like
            current_log_prior = proposal_log_prior
            current_log_post = proposal_log_post
            accepted_history.append(current.copy())

        row = {
            "链号": chain_id + 1,
            "步号": step + 1,
            "accepted": int(accepted),
            "accept_prob": alpha,
            "mean_nse": current_eval["mean_nse"],
            "sse": current_eval["sse"],
            "log_like": current_log_like,
            "log_prior": current_log_prior,
            "log_posterior": current_log_post,
        }
        for idx, node in enumerate(cols):
            row[node] = float(current[idx])
        rows.append(row)

    return rows


def 运行AM(
    evaluator: 目标函数评估器,
    initial_ppd: pd.DataFrame,
    config: 实验配置,
    seed: int = 20260326,
) -> pd.DataFrame:
    chain_args: list[tuple[int, dict, pd.DataFrame, 实验配置, int]] = []
    for chain_id in range(config.am_链数):
        start_row = initial_ppd.iloc[chain_id % len(initial_ppd)].to_dict()
        chain_args.append((chain_id, start_row, initial_ppd, config, seed))

    max_workers = max(1, min(config.并行工作进程数, config.am_链数))
    rows: list[dict] = []
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_初始化AM工作进程,
        initargs=(evaluator.dataset, config),
    ) as executor:
        for chain_rows in executor.map(_运行单条AM链, chain_args):
            rows.extend(chain_rows)

    am_df = pd.DataFrame(rows)
    am_df.to_csv(结果目录 / "0325_AM样本.csv", index=False, encoding="utf-8-sig")
    return am_df


def 提取后验结果(am_df: pd.DataFrame, config: 实验配置) -> pd.DataFrame:
    cols = list(config.候选节点)
    tail = am_df.groupby("链号", group_keys=False).apply(
        lambda df: df.iloc[config.am_预热 :].reset_index(drop=True)
    )
    tail.to_csv(结果目录 / "0325_PPD样本.csv", index=False, encoding="utf-8-sig")

    rows = []
    for node in cols:
        series = tail[node].to_numpy(dtype=float)
        rows.append(
            {
                "节点": node,
                "后验均值": float(series.mean()),
                "后验中位数": float(np.median(series)),
                "P05": float(np.quantile(series, 0.05)),
                "P95": float(np.quantile(series, 0.95)),
            }
        )
    result = pd.DataFrame(rows).sort_values("后验均值", ascending=False).reset_index(drop=True)
    result.to_csv(结果目录 / "0325_后验节点权重.csv", index=False, encoding="utf-8-sig")

    ppd_summary = pd.DataFrame(
        {
            "链号": sorted(tail["链号"].unique()),
            "接受率": [float(group["accepted"].mean()) for _, group in tail.groupby("链号")],
            "尾部样本数": [int(len(group)) for _, group in tail.groupby("链号")],
            "尾部最优NSE": [float(group["mean_nse"].max()) for _, group in tail.groupby("链号")],
        }
    )
    ppd_summary.to_csv(结果目录 / "0325_PPD汇总.csv", index=False, encoding="utf-8-sig")
    return result


def 后验预测验证(
    evaluator: 目标函数评估器,
    am_df: pd.DataFrame,
    config: 实验配置,
    sample_count: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """参考论文的 PPD 验证思路：从 PPD 抽样，重新跑 SWMM，形成 90% 区间并统计覆盖率。"""
    tail = am_df.groupby("链号", group_keys=False).apply(
        lambda df: df.iloc[config.am_预热 :].reset_index(drop=True)
    )
    if tail.empty:
        raise ValueError("AM 尾部样本为空，无法进行后验预测验证。")

    pick_idx = np.linspace(0, len(tail) - 1, min(sample_count, len(tail)), dtype=int)
    simulations: list[pd.DataFrame] = []
    cols = list(config.候选节点)
    for idx in pick_idx:
        shares = tail.iloc[idx][cols].to_numpy(dtype=float)
        result = evaluator.评估方案(shares)
        sim_df = result["sim_delta"].copy()
        sim_df["sample_id"] = int(idx)
        simulations.append(sim_df)

    sim_stack = pd.concat(simulations, ignore_index=True)
    band_rows: list[dict] = []
    coverage_rows: list[dict] = []
    observed = evaluator.dataset.观测增量.copy()

    for monitor in config.监测点:
        per_monitor_rows: list[dict] = []
        for time_value, group in sim_stack.groupby("时间"):
            values = group[monitor].to_numpy(dtype=float)
            obs = float(observed.loc[observed["时间"] == time_value, monitor].iloc[0])
            row = {
                "monitor": monitor,
                "time": time_value,
                "observed": obs,
                "p05": float(np.quantile(values, 0.05)),
                "p50": float(np.quantile(values, 0.50)),
                "p95": float(np.quantile(values, 0.95)),
            }
            row["covered_90"] = bool(row["p05"] <= obs <= row["p95"])
            band_rows.append(row)
            per_monitor_rows.append(row)
        coverage_rows.append(
            {
                "monitor": monitor,
                "coverage_90": float(np.mean([row["covered_90"] for row in per_monitor_rows])),
            }
        )

    bands_df = pd.DataFrame(band_rows)
    coverage_df = pd.DataFrame(coverage_rows)
    bands_df.to_csv(结果目录 / "0325_posterior_predictive_bands.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(结果目录 / "0325_posterior_predictive_coverage.csv", index=False, encoding="utf-8-sig")
    return bands_df, coverage_df


__all__ = [
    "运行GA",
    "运行AM",
    "提取后验结果",
    "后验预测验证",
    "构造先验",
    "log_prior",
    "log_likelihood",
]
