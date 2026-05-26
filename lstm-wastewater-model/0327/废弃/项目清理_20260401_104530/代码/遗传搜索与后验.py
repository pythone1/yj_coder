from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd

from 公共配置与数据 import CANDIDATE_NODES, MONITOR_NODES, ExperimentConfig
from 模型仿真与评估 import ExperimentDataset, simplex_project, worker_evaluate, worker_initializer


def random_sparse_individual(dim: int, rng: np.random.Generator) -> np.ndarray:
    active_count = int(rng.integers(1, min(5, dim) + 1))
    active_idx = rng.choice(dim, size=active_count, replace=False)
    values = np.zeros(dim, dtype=float)
    values[active_idx] = rng.random(active_count)
    return simplex_project(values)


def initialize_populations(config: ExperimentConfig, rng: np.random.Generator) -> list[np.ndarray]:
    dim = len(CANDIDATE_NODES)
    populations: list[np.ndarray] = []
    for _ in range(config.ga_population_count):
        members = []
        for index in range(config.ga_population_size):
            if index < config.ga_population_size // 2:
                members.append(random_sparse_individual(dim, rng))
            else:
                members.append(simplex_project(rng.dirichlet(np.ones(dim))))
        populations.append(np.vstack(members))
    return populations


def parallel_evaluate(tasks: list[tuple[int, np.ndarray]], generated_data: dict[str, pd.DataFrame], worker_count: int) -> list[dict[str, Any]]:
    if worker_count <= 1:
        worker_initializer(generated_data)
        return [worker_evaluate(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=worker_count, initializer=worker_initializer, initargs=(generated_data,)) as executor:
        return list(executor.map(worker_evaluate, tasks))


def population_competition(populations: list[np.ndarray], evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[np.ndarray]:
    """Paper-like competition: stronger populations replace weakest individuals in weaker populations."""
    if len(populations) <= 1:
        return populations

    elite_count = max(1, config.ga_competition_replace_count)
    population_scores = []
    for pop_idx, rows in enumerate(evaluated_populations):
        top_scores = [row["mean_nse"] for row in rows[:elite_count]]
        population_scores.append((pop_idx, float(np.mean(top_scores))))
    ranked = sorted(population_scores, key=lambda item: item[1], reverse=True)

    updated = [pop.copy() for pop in populations]
    half = len(ranked) // 2
    for offset in range(half):
        strong_idx = ranked[offset][0]
        weak_idx = ranked[-(offset + 1)][0]
        if strong_idx == weak_idx:
            continue
        strong_elites = np.vstack([row["shares"] for row in evaluated_populations[strong_idx][:elite_count]])
        weak_sorted = evaluated_populations[weak_idx]
        survivor_count = max(0, config.ga_population_size - elite_count)
        survivors = [row["shares"] for row in weak_sorted[:survivor_count]]
        updated[weak_idx] = np.vstack(survivors + list(strong_elites))[: config.ga_population_size]
    return updated


def population_migration(populations: list[np.ndarray], evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[np.ndarray]:
    if len(populations) <= 1:
        return populations
    migrant_count = max(1, min(config.ga_migration_count, config.ga_population_size - 1))
    migrants = [np.vstack([row["shares"] for row in rows[:migrant_count]]) for rows in evaluated_populations]
    updated = [pop.copy() for pop in populations]
    for pop_idx in range(len(populations)):
        target_idx = (pop_idx + 1) % len(populations)
        target_rows = evaluated_populations[target_idx]
        survivor_count = config.ga_population_size - migrant_count
        survivors = [row["shares"] for row in target_rows[:survivor_count]]
        updated[target_idx] = np.vstack(survivors + list(migrants[pop_idx]))
    return updated


def evolve_population(rows: list[dict[str, Any]], config: ExperimentConfig, rng: np.random.Generator) -> np.ndarray:
    dim = len(CANDIDATE_NODES)
    elite_count = max(1, int(math.ceil(config.ga_population_size * config.ga_elite_ratio)))
    elites = [row["shares"] for row in rows[:elite_count]]
    offspring = elites.copy()
    while len(offspring) < config.ga_population_size:
        p1_idx, p2_idx = rng.choice(elite_count, size=2, replace=True)
        p1 = elites[int(p1_idx)]
        p2 = elites[int(p2_idx)]
        alpha = float(rng.uniform(0.25, 0.75))
        child = alpha * p1 + (1.0 - alpha) * p2
        child = child + rng.normal(0.0, config.ga_mutation_strength, size=dim)
        offspring.append(simplex_project(child))
    return np.vstack(offspring[: config.ga_population_size])


def run_ga(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(config.random_seed)
    populations = initialize_populations(config, rng)
    history_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    best_global: dict[str, Any] | None = None

    for generation in range(config.ga_generations):
        print(f"[GA] generation {generation + 1}/{config.ga_generations}", flush=True)
        evaluated_populations: list[list[dict[str, Any]]] = []
        for pop_idx, pop in enumerate(populations):
            tasks = [(i % max(1, config.parallel_workers), ind) for i, ind in enumerate(pop)]
            evaluated = parallel_evaluate(tasks, generated_data, config.parallel_workers)
            for row in evaluated:
                row["population"] = pop_idx
                row["generation"] = generation + 1
                if best_global is None or row["mean_nse"] > best_global["mean_nse"]:
                    best_global = row
            evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
            evaluated_populations.append(evaluated)

            best = evaluated[0]
            history_rows.append(
                {
                    "generation": generation + 1,
                    "population": pop_idx,
                    "best_mean_nse": float(best["mean_nse"]),
                    "best_sse": float(best["sse"]),
                }
            )

            for rank, row in enumerate(evaluated, start=1):
                record = {
                    "generation": generation + 1,
                    "population": pop_idx,
                    "rank": rank,
                    "mean_nse": float(row["mean_nse"]),
                    "sse": float(row["sse"]),
                }
                for node_idx, node in enumerate(CANDIDATE_NODES):
                    record[node] = float(row["shares"][node_idx])
                all_rows.append(record)

        if (generation + 1) % max(1, config.ga_migration_interval) == 0 and config.ga_population_count > 1:
            populations = population_competition(populations, evaluated_populations, config)
            # Re-evaluate after competition to get current survivors, then migrate.
            reevaluated_populations: list[list[dict[str, Any]]] = []
            for pop_idx, pop in enumerate(populations):
                tasks = [(i % max(1, config.parallel_workers), ind) for i, ind in enumerate(pop)]
                evaluated = parallel_evaluate(tasks, generated_data, config.parallel_workers)
                evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
                reevaluated_populations.append(evaluated)
            populations = population_migration(populations, reevaluated_populations, config)

        new_populations: list[np.ndarray] = []
        # Evaluate populations used for breeding after competition/migration if it happened.
        if (generation + 1) % max(1, config.ga_migration_interval) == 0 and config.ga_population_count > 1:
            breeding_rows: list[list[dict[str, Any]]] = []
            for pop_idx, pop in enumerate(populations):
                tasks = [(i % max(1, config.parallel_workers), ind) for i, ind in enumerate(pop)]
                evaluated = parallel_evaluate(tasks, generated_data, config.parallel_workers)
                evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
                breeding_rows.append(evaluated)
        else:
            breeding_rows = evaluated_populations

        for rows in breeding_rows:
            new_populations.append(evolve_population(rows, config, rng))
        populations = new_populations

    if best_global is None:
        raise RuntimeError("GA 未产生任何有效个体")

    all_df = pd.DataFrame(all_rows)
    history_df = pd.DataFrame(history_rows)
    merged_last_df = (
        all_df[all_df["generation"] == config.ga_generations]
        .copy()
        .sort_values("mean_nse", ascending=False)
        .reset_index(drop=True)
    )
    return all_df, history_df, merged_last_df, best_global["shares"]


def roulette_initial_ppd(merged_last: pd.DataFrame, ga_best_shares: np.ndarray, config: ExperimentConfig, rng: np.random.Generator) -> pd.DataFrame:
    """Closer to the paper: merge final populations then remove inferior individuals by roulette selection."""
    if merged_last.empty:
        raise ValueError("GA 末代结果为空，无法进行轮盘赌")

    pool = merged_last.copy().reset_index(drop=True)
    fitness = pool["mean_nse"].to_numpy(dtype=float)
    shifted = fitness - fitness.min() + 1e-12
    roulette_prob = shifted / shifted.sum()

    keep_count = min(config.ga_population_size, len(pool))
    chosen = rng.choice(len(pool), size=keep_count, replace=False, p=roulette_prob)
    initial = pool.iloc[np.sort(chosen)].copy().reset_index(drop=True)

    initial_array = initial[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    has_best = bool(np.any(np.all(np.isclose(initial_array, ga_best_shares[None, :], atol=1e-10, rtol=0.0), axis=1)))
    if not has_best:
        best_match_idx = int(np.argmax(fitness))
        best_row = pool.iloc[[best_match_idx]].copy()
        if len(initial) >= keep_count:
            initial = pd.concat([best_row, initial.iloc[:-1]], ignore_index=True)
        else:
            initial = pd.concat([best_row, initial], ignore_index=True)

    selected_fitness = initial["mean_nse"].to_numpy(dtype=float)
    selected_shifted = selected_fitness - selected_fitness.min() + 1e-12
    initial["roulette_weight"] = selected_shifted / selected_shifted.sum()
    return initial.reset_index(drop=True)


def sample_based_log_prior(x: np.ndarray, initial_ppd: pd.DataFrame, kernel_scale: float) -> float:
    samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    weights = initial_ppd["roulette_weight"].to_numpy(dtype=float)
    diffs = samples - x[None, :]
    sq = np.sum(diffs * diffs, axis=1)
    logs = np.log(np.maximum(weights, 1e-300)) - 0.5 * sq / max(kernel_scale, 1e-12)
    max_log = float(np.max(logs))
    return float(max_log + np.log(np.sum(np.exp(logs - max_log))))


def adaptive_covariance(history: list[np.ndarray], config: ExperimentConfig) -> np.ndarray:
    d = len(CANDIDATE_NODES)
    sd = 2.42 / d
    if len(history) <= config.am_adapt_start:
        return np.eye(d) * config.am_initial_covariance
    arr = np.vstack(history)
    cov = np.cov(arr.T, bias=False)
    if np.ndim(cov) == 0:
        cov = np.eye(d) * float(cov)
    return sd * cov + sd * config.am_eps * np.eye(d)


def run_am(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], initial_ppd: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    rng = np.random.default_rng(config.random_seed + 1)
    initial_samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    obs = dataset.observed_delta[list(MONITOR_NODES)].to_numpy(dtype=float)
    sigma = max(float(np.std(obs)), 1e-6)
    kernel_scale = 0.01
    rows: list[dict[str, Any]] = []

    for chain_id in range(config.am_chain_count):
        print(f"[AM] chain {chain_id + 1}/{config.am_chain_count} start", flush=True)
        current = simplex_project(initial_samples[chain_id % len(initial_samples)])
        history = [current.copy()]
        current_eval = parallel_evaluate([(0, current)], generated_data, 1)[0]
        current_log_like = -0.5 * current_eval["sse"] / (sigma**2)
        current_log_prior = sample_based_log_prior(current, initial_ppd, kernel_scale)

        for step in range(config.am_samples_per_chain):
            if step == 0 or (step + 1) % 100 == 0 or step + 1 == config.am_samples_per_chain:
                print(f"[AM] chain {chain_id + 1}/{config.am_chain_count} step {step + 1}/{config.am_samples_per_chain}", flush=True)
            cov = adaptive_covariance(history, config)
            proposal = rng.multivariate_normal(mean=current, cov=cov)
            proposal = simplex_project(proposal)

            proposal_eval = parallel_evaluate([(0, proposal)], generated_data, 1)[0]
            proposal_log_like = -0.5 * proposal_eval["sse"] / (sigma**2)
            proposal_log_prior = sample_based_log_prior(proposal, initial_ppd, kernel_scale)

            # Paper equation (8): acceptance by likelihood ratio.
            accept_prob = min(1.0, float(np.exp(proposal_log_like - current_log_like)))
            accepted = bool(rng.random() < accept_prob)
            if accepted:
                current = proposal
                current_eval = proposal_eval
                current_log_like = proposal_log_like
                current_log_prior = proposal_log_prior
                history.append(current.copy())

            row = {
                "chain": chain_id,
                "step": step + 1,
                "accepted": int(accepted),
                "mean_nse": float(current_eval["mean_nse"]),
                "sse": float(current_eval["sse"]),
                "log_like": float(current_log_like),
                "log_prior": float(current_log_prior),
                "log_posterior": float(current_log_like + current_log_prior),
            }
            for idx, node in enumerate(CANDIDATE_NODES):
                row[node] = float(current[idx])
            rows.append(row)

    return pd.DataFrame(rows)


def extract_ppd(am_samples: pd.DataFrame, config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    tail = am_samples[am_samples["step"] > config.am_warmup].copy()
    if tail.empty:
        raise ValueError("AM 尾部样本为空，无法提取 PPD")
    summary_rows = []
    for node in CANDIDATE_NODES:
        values = tail[node].to_numpy(dtype=float)
        summary_rows.append(
            {
                "节点": node,
                "后验均值": float(np.mean(values)),
                "后验中位数": float(np.median(values)),
                "P05": float(np.quantile(values, 0.05)),
                "P95": float(np.quantile(values, 0.95)),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("后验中位数", ascending=False).reset_index(drop=True)
    return tail.reset_index(drop=True), summary_df


def posterior_predictive_validation(
    dataset: ExperimentDataset,
    generated_data: dict[str, pd.DataFrame],
    ppd_samples: pd.DataFrame,
    config: ExperimentConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_count = min(config.posterior_validation_samples, len(ppd_samples))
    draws = ppd_samples.sample(n=sample_count, random_state=config.random_seed)
    band_rows = []
    monitor_predictions = {node: [] for node in MONITOR_NODES}

    for _, draw in draws.iterrows():
        shares = draw[list(CANDIDATE_NODES)].to_numpy(dtype=float)
        eval_result = parallel_evaluate([(0, shares)], generated_data, 1)[0]
        sim_delta = eval_result["sim_delta"]
        for node in MONITOR_NODES:
            monitor_predictions[node].append(sim_delta[node].to_numpy(dtype=float))

    for node in MONITOR_NODES:
        pred = np.vstack(monitor_predictions[node])
        p05 = np.quantile(pred, 0.05, axis=0)
        p50 = np.quantile(pred, 0.50, axis=0)
        p95 = np.quantile(pred, 0.95, axis=0)
        obs = dataset.observed_delta[node].to_numpy(dtype=float)[: pred.shape[1]]
        coverage = float(np.mean((obs >= p05) & (obs <= p95)))
        for step_idx in range(pred.shape[1]):
            band_rows.append(
                {
                    "监测点": node,
                    "步号": step_idx,
                    "相对小时": float(dataset.total_process.iloc[step_idx]["相对小时"]),
                    "P05": float(p05[step_idx]),
                    "P50": float(p50[step_idx]),
                    "P95": float(p95[step_idx]),
                    "观测值": float(obs[step_idx]),
                    "coverage_90": coverage,
                }
            )
    bands_df = pd.DataFrame(band_rows)
    coverage_df = bands_df.groupby("监测点", as_index=False)["coverage_90"].first()
    return bands_df, coverage_df


# Chinese aliases for compatibility.
运行GA = run_ga
轮盘赌生成initial_ppd = roulette_initial_ppd
运行AM = run_am
提取PPD = extract_ppd
后验预测验证 = posterior_predictive_validation
