"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: ga_am_0416.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

﻿from __future__ import annotations

import math
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from config_0416 import CANDIDATE_NODES, MONITOR_NODES, ExperimentConfig
from simulation_0416 import ExperimentDataset, simplex_project, worker_evaluate, worker_initializer

_PARALLEL_EVAL_CACHE: dict[tuple[float, ...], dict[str, Any]] = {}
_PARALLEL_EVAL_CACHE_HITS = 0
_PARALLEL_EVAL_CACHE_MISSES = 0


def log_progress(message: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def random_sparse_individual(dim: int, rng: np.random.Generator) -> np.ndarray:
    active_count = int(rng.integers(1, min(5, dim) + 1))
    active_idx = rng.choice(dim, size=active_count, replace=False)
    values = np.zeros(dim, dtype=float)
    values[active_idx] = rng.random(active_count)
    return simplex_project(values)


def random_population_individual(dim: int, rng: np.random.Generator) -> np.ndarray:
    if bool(rng.random() < 0.5):
        return random_sparse_individual(dim, rng)
    return simplex_project(rng.dirichlet(np.ones(dim)))


def _shares_key(shares: np.ndarray, decimals: int = 5) -> tuple[float, ...]:
    arr = np.asarray(shares, dtype=float).reshape(-1)
    arr = np.round(arr, decimals=max(0, int(decimals)))
    return tuple(float(v) for v in arr)


def reset_evaluation_cache() -> None:
    global _PARALLEL_EVAL_CACHE_HITS, _PARALLEL_EVAL_CACHE_MISSES
    _PARALLEL_EVAL_CACHE.clear()
    _PARALLEL_EVAL_CACHE_HITS = 0
    _PARALLEL_EVAL_CACHE_MISSES = 0


def evaluation_cache_stats() -> dict[str, int]:
    return {
        "entries": len(_PARALLEL_EVAL_CACHE),
        "hits": int(_PARALLEL_EVAL_CACHE_HITS),
        "misses": int(_PARALLEL_EVAL_CACHE_MISSES),
    }


def _compact_eval_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "shares": np.asarray(result["shares"], dtype=float).copy(),
        "mean_nse": float(result["mean_nse"]),
        "sse": float(result["sse"]),
        "cache_hit": bool(result.get("cache_hit", False)),
    }


def _copy_eval_result(result: dict[str, Any], cache_hit: bool | None = None) -> dict[str, Any]:
    copied = dict(result)
    copied["shares"] = np.asarray(result["shares"], dtype=float).copy()
    if cache_hit is not None:
        copied["cache_hit"] = cache_hit
    return copied


def deduplicate_and_refill_population(
    members: list[np.ndarray] | np.ndarray,
    config: ExperimentConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    dim = len(CANDIDATE_NODES)
    unique_members: list[np.ndarray] = []
    seen: set[tuple[float, ...]] = set()
    for member in members:
        projected = simplex_project(np.asarray(member, dtype=float))
        key = _shares_key(projected, config.ga_dedup_decimals)
        if key in seen:
            continue
        unique_members.append(projected)
        seen.add(key)

    elite_pool = unique_members[: max(1, min(len(unique_members), int(math.ceil(config.ga_population_size * config.ga_elite_ratio))))]
    attempts = 0
    max_attempts = max(100, config.ga_population_size * 50)
    while len(unique_members) < config.ga_population_size and attempts < max_attempts:
        attempts += 1
        if elite_pool and bool(rng.random() < 0.65):
            parent = elite_pool[int(rng.integers(0, len(elite_pool)))]
            candidate = simplex_project(parent + rng.normal(0.0, config.ga_mutation_strength, size=dim))
        else:
            candidate = random_population_individual(dim, rng)
        key = _shares_key(candidate, config.ga_dedup_decimals)
        if key in seen:
            continue
        unique_members.append(candidate)
        seen.add(key)

    while len(unique_members) < config.ga_population_size:
        candidate = simplex_project(rng.random(dim))
        key = _shares_key(candidate, config.ga_dedup_decimals)
        if key in seen:
            continue
        unique_members.append(candidate)
        seen.add(key)

    return np.vstack(unique_members[: config.ga_population_size])


def deduplicate_evaluated_rows(rows: list[dict[str, Any]], config: ExperimentConfig) -> list[dict[str, Any]]:
    unique_rows: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    for row in rows:
        key = _shares_key(row["shares"], config.ga_dedup_decimals)
        if key in seen:
            continue
        unique_rows.append(row)
        seen.add(key)
    return unique_rows


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
        populations.append(deduplicate_and_refill_population(members, config, rng))
    return populations


def parallel_evaluate(
    tasks: list[tuple[int, np.ndarray]],
    generated_data: dict[str, pd.DataFrame],
    worker_count: int,
    include_series: bool = False,
    use_cache: bool = True,
    cache_decimals: int = 4,
) -> list[dict[str, Any]]:
    global _PARALLEL_EVAL_CACHE_HITS, _PARALLEL_EVAL_CACHE_MISSES
    if not tasks:
        return []

    if include_series or not use_cache:
        worker_tasks = [(worker_id, shares, include_series, cache_decimals) for worker_id, shares in tasks]
        if worker_count <= 1:
            worker_initializer(generated_data)
            return [worker_evaluate(task) for task in worker_tasks]
        with ProcessPoolExecutor(max_workers=worker_count, initializer=worker_initializer, initargs=(generated_data,)) as executor:
            return list(executor.map(worker_evaluate, worker_tasks))

    output: list[dict[str, Any] | None] = [None] * len(tasks)
    pending_by_key: dict[tuple[float, ...], tuple[int, np.ndarray]] = {}
    pending_positions: dict[tuple[float, ...], list[int]] = {}
    for pos, (_, shares) in enumerate(tasks):
        key = _shares_key(simplex_project(shares), cache_decimals)
        cached = _PARALLEL_EVAL_CACHE.get(key)
        if cached is not None:
            _PARALLEL_EVAL_CACHE_HITS += 1
            output[pos] = _copy_eval_result(cached, cache_hit=True)
            continue
        pending_positions.setdefault(key, []).append(pos)
        if key not in pending_by_key:
            pending_by_key[key] = (len(pending_by_key) % max(1, worker_count), shares)

    unique_tasks = [
        (worker_id, shares, False, cache_decimals)
        for worker_id, shares in pending_by_key.values()
    ]
    _PARALLEL_EVAL_CACHE_MISSES += len(unique_tasks)
    if unique_tasks:
        if worker_count <= 1:
            worker_initializer(generated_data)
            unique_results = [worker_evaluate(task) for task in unique_tasks]
        else:
            with ProcessPoolExecutor(max_workers=worker_count, initializer=worker_initializer, initargs=(generated_data,)) as executor:
                unique_results = list(executor.map(worker_evaluate, unique_tasks))
        for key, result in zip(pending_by_key.keys(), unique_results):
            compact = _compact_eval_result(result)
            _PARALLEL_EVAL_CACHE[key] = compact
            positions = pending_positions[key]
            if len(positions) > 1:
                _PARALLEL_EVAL_CACHE_HITS += len(positions) - 1
            for idx, pos in enumerate(positions):
                output[pos] = _copy_eval_result(compact, cache_hit=idx > 0)

    return [item for item in output if item is not None]


def _clone_evaluated_row(row: dict[str, Any]) -> dict[str, Any]:
    cloned = dict(row)
    cloned["shares"] = np.asarray(row["shares"], dtype=float).copy()
    return cloned


def population_competition_rows(evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[list[dict[str, Any]]]:
    if len(evaluated_populations) <= 1:
        return [[_clone_evaluated_row(row) for row in rows] for rows in evaluated_populations]
    elite_count = max(1, config.ga_competition_replace_count)
    population_scores = []
    for pop_idx, rows in enumerate(evaluated_populations):
        if not rows:
            population_scores.append((pop_idx, -1.0e12))
            continue
        top_scores = [row["mean_nse"] for row in rows[:elite_count]]
        population_scores.append((pop_idx, float(np.mean(top_scores))))
    ranked = sorted(population_scores, key=lambda item: item[1], reverse=True)
    updated = [[_clone_evaluated_row(row) for row in rows] for rows in evaluated_populations]
    half = len(ranked) // 2
    for offset in range(half):
        strong_idx = ranked[offset][0]
        weak_idx = ranked[-(offset + 1)][0]
        if strong_idx == weak_idx or not updated[strong_idx] or not updated[weak_idx]:
            continue
        actual_elite_count = min(elite_count, len(updated[strong_idx]))
        strong_elites = [_clone_evaluated_row(row) for row in updated[strong_idx][:actual_elite_count]]
        survivor_count = max(0, config.ga_population_size - actual_elite_count)
        survivors = [_clone_evaluated_row(row) for row in updated[weak_idx][:survivor_count]]
        updated[weak_idx] = deduplicate_evaluated_rows(survivors + strong_elites, config)
    return updated


def population_migration_rows(evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[list[dict[str, Any]]]:
    if len(evaluated_populations) <= 1:
        return [[_clone_evaluated_row(row) for row in rows] for rows in evaluated_populations]
    migrant_count = max(1, min(config.ga_migration_count, config.ga_population_size - 1))
    migrants: list[list[dict[str, Any]]] = []
    for rows in evaluated_populations:
        migrants.append([_clone_evaluated_row(row) for row in rows[: min(migrant_count, len(rows))]])
    updated = [[_clone_evaluated_row(row) for row in rows] for rows in evaluated_populations]
    for pop_idx in range(len(evaluated_populations)):
        target_idx = (pop_idx + 1) % len(evaluated_populations)
        actual_migrant_count = len(migrants[pop_idx])
        survivor_count = max(0, config.ga_population_size - actual_migrant_count)
        survivors = [_clone_evaluated_row(row) for row in updated[target_idx][:survivor_count]]
        updated[target_idx] = deduplicate_evaluated_rows(survivors + migrants[pop_idx], config)
    return updated


def _cache_hit_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if bool(row.get("cache_hit", False)))


def population_competition(populations: list[np.ndarray], evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[np.ndarray]:
    if len(populations) <= 1:
        return populations
    elite_count = max(1, config.ga_competition_replace_count)
    population_scores = []
    for pop_idx, rows in enumerate(evaluated_populations):
        if not rows:
            population_scores.append((pop_idx, -1.0e12))
            continue
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
        if not evaluated_populations[strong_idx] or not evaluated_populations[weak_idx]:
            continue
        actual_elite_count = min(elite_count, len(evaluated_populations[strong_idx]))
        strong_elites = np.vstack([row["shares"] for row in evaluated_populations[strong_idx][:actual_elite_count]])
        weak_sorted = evaluated_populations[weak_idx]
        survivor_count = max(0, config.ga_population_size - actual_elite_count)
        survivors = [row["shares"] for row in weak_sorted[:survivor_count]]
        updated[weak_idx] = np.vstack(survivors + list(strong_elites))[: config.ga_population_size]
    return updated


def population_migration(populations: list[np.ndarray], evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[np.ndarray]:
    if len(populations) <= 1:
        return populations
    migrant_count = max(1, min(config.ga_migration_count, config.ga_population_size - 1))
    migrants = []
    for pop, rows in zip(populations, evaluated_populations):
        if rows:
            migrants.append(np.vstack([row["shares"] for row in rows[: min(migrant_count, len(rows))]]))
        else:
            migrants.append(pop[:migrant_count])
    updated = [pop.copy() for pop in populations]
    for pop_idx in range(len(populations)):
        target_idx = (pop_idx + 1) % len(populations)
        target_rows = evaluated_populations[target_idx]
        actual_migrant_count = len(migrants[pop_idx])
        survivor_count = config.ga_population_size - actual_migrant_count
        survivors = [row["shares"] for row in target_rows[:survivor_count]]
        updated[target_idx] = np.vstack(survivors + list(migrants[pop_idx]))
    return updated


def evolve_population(rows: list[dict[str, Any]], config: ExperimentConfig, rng: np.random.Generator) -> np.ndarray:
    dim = len(CANDIDATE_NODES)
    if not rows:
        return deduplicate_and_refill_population([], config, rng)
    elite_count = min(len(rows), max(1, int(math.ceil(config.ga_population_size * config.ga_elite_ratio))))
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
    return deduplicate_and_refill_population(offspring, config, rng)


def run_ga(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    reset_evaluation_cache()
    rng = np.random.default_rng(config.random_seed)
    populations = initialize_populations(config, rng)
    history_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    best_global: dict[str, Any] | None = None

    log_progress(
        f"GA start: populations={config.ga_population_count}, size={config.ga_population_size}, "
        f"generations={config.ga_generations}, workers={config.parallel_workers}"
    )

    for generation in tqdm(range(config.ga_generations), desc="GA generations", leave=True):
        log_progress(f"GA generation {generation + 1}/{config.ga_generations}")
        evaluated_populations: list[list[dict[str, Any]]] = []
        for pop_idx, pop in enumerate(populations):
            log_progress(f"GA generation {generation + 1}: evaluating population {pop_idx + 1}/{len(populations)}")
            tasks = [(i % max(1, config.parallel_workers), ind) for i, ind in enumerate(pop)]
            evaluated = parallel_evaluate(
                tasks,
                generated_data,
                config.parallel_workers,
                include_series=False,
                use_cache=True,
                cache_decimals=config.ga_dedup_decimals,
            )
            cache_hits = _cache_hit_count(evaluated)
            for row in evaluated:
                row["population"] = pop_idx
                row["generation"] = generation + 1
                if best_global is None or row["mean_nse"] > best_global["mean_nse"]:
                    best_global = row
            evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
            unique_evaluated = deduplicate_evaluated_rows(evaluated, config)
            removed_count = len(evaluated) - len(unique_evaluated)
            if removed_count > 0:
                log_progress(
                    f"GA generation {generation + 1}: population {pop_idx + 1} deduplicated "
                    f"{removed_count} repeated individuals before breeding"
                )
            evaluated = unique_evaluated
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
            log_progress(
                f"GA generation {generation + 1}: population {pop_idx + 1} "
                f"ga_metric_mean_nse={best['mean_nse']:.4f}, sse_record={best['sse']:.6g}, "
                f"top3={format_top_nodes(best['shares'])}, cache_hits={cache_hits}"
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
            log_progress(f"GA generation {generation + 1}: competition + migration using carried evaluated rows")
            competition_rows = population_competition_rows(evaluated_populations, config)
            migrated_rows = population_migration_rows(competition_rows, config)
            breeding_rows = [deduplicate_evaluated_rows(rows, config) for rows in migrated_rows]
        else:
            breeding_rows = evaluated_populations

        populations = [evolve_population(rows, config, rng) for rows in breeding_rows]

    if best_global is None:
        raise RuntimeError("GA produced no valid individual")

    all_df = pd.DataFrame(all_rows)
    history_df = pd.DataFrame(history_rows)
    merged_last_df = all_df[all_df["generation"] == config.ga_generations].copy().sort_values("mean_nse", ascending=False).reset_index(drop=True)
    log_progress(
        f"GA done: global_best_ga_metric_mean_nse={best_global['mean_nse']:.4f}, "
        f"sse_record={best_global['sse']:.6g}, top3={format_top_nodes(best_global['shares'])}, "
        f"cache={evaluation_cache_stats()}"
    )
    return all_df, history_df, merged_last_df, best_global["shares"]


def _deduplicate_share_dataframe(df: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    rounded = df.loc[:, list(CANDIDATE_NODES)].round(config.ga_dedup_decimals)
    dedup_key = rounded.astype(str).agg("|".join, axis=1)
    return df.assign(_dedup_key=dedup_key).drop_duplicates(subset="_dedup_key", keep="first").drop(columns="_dedup_key")


def _rank_selection_weights(count: int, pressure: float) -> np.ndarray:
    if count <= 0:
        return np.array([], dtype=float)
    ranks = np.arange(count, 0, -1, dtype=float)
    weights = ranks ** max(0.0, float(pressure))
    return weights / float(weights.sum())


def roulette_initial_ppd(
    merged_last: pd.DataFrame,
    ga_best_shares: np.ndarray,
    config: ExperimentConfig,
    rng: np.random.Generator,
    ga_best_row: pd.Series | dict[str, Any] | None = None,
) -> pd.DataFrame:
    pool = (
        merged_last.copy()
        .sort_values(["mean_nse", "sse"], ascending=[False, True])
        .reset_index(drop=True)
    )
    pool = pool[np.isfinite(pool["mean_nse"].to_numpy(dtype=float))].copy()
    quality_pool = pool[pool["mean_nse"] > config.initial_ppd_min_mean_nse].copy()
    if not quality_pool.empty:
        pool = quality_pool
    pool = _deduplicate_share_dataframe(pool, config).reset_index(drop=True)
    if pool.empty:
        raise RuntimeError("GA last generation produced no unique individual for initial PPD")

    best_nse = float(pool["mean_nse"].max())
    relative_cutoff = best_nse - max(0.0, float(config.initial_ppd_max_nse_drop))
    quality_cutoff = max(float(config.initial_ppd_min_mean_nse), relative_cutoff)
    quality_pool = pool[pool["mean_nse"] >= quality_cutoff].copy().reset_index(drop=True)
    min_required = max(1, min(config.initial_ppd_min_count, len(pool)))
    if len(quality_pool) >= min_required:
        pool = quality_pool
    else:
        pool = pool.head(min_required).copy().reset_index(drop=True)

    roulette_prob = _rank_selection_weights(len(pool), config.initial_ppd_rank_pressure)
    keep_fraction = min(1.0, max(0.0, config.initial_ppd_keep_fraction))
    fraction_count = int(math.ceil(len(pool) * keep_fraction))
    keep_count = min(len(pool), max(1, config.initial_ppd_min_count, fraction_count))
    chosen = rng.choice(len(pool), size=keep_count, replace=False, p=roulette_prob)
    initial = pool.iloc[np.sort(chosen)].copy().reset_index(drop=True)

    if ga_best_row is not None:
        best_row = pd.DataFrame([dict(ga_best_row)]).copy()
        for node_idx, node in enumerate(CANDIDATE_NODES):
            best_row[node] = float(ga_best_shares[node_idx])
        for col in pool.columns:
            if col not in best_row.columns:
                best_row[col] = np.nan
        best_row = best_row[pool.columns]
    else:
        pool_array = pool[list(CANDIDATE_NODES)].to_numpy(dtype=float)
        best_mask = np.all(np.isclose(pool_array, ga_best_shares[None, :], atol=1e-10, rtol=0.0), axis=1)
        best_row = pool.loc[best_mask].head(1).copy()
        if best_row.empty:
            best_row = pool.iloc[[0]].copy()

    initial = (
        pd.concat([best_row, initial], ignore_index=True)
        .pipe(_deduplicate_share_dataframe, config)
        .sort_values(["mean_nse", "sse"], ascending=[False, True])
        .head(keep_count)
        .reset_index(drop=True)
    )

    initial["roulette_weight"] = _rank_selection_weights(len(initial), config.initial_ppd_rank_pressure)
    log_progress(
        f"Initial PPD built: quality_pool={len(pool)}, keep_count={len(initial)}, "
        f"ga_metric_best_mean_nse={best_nse:.4f}, cutoff={quality_cutoff:.4f}, "
        f"min_mean_nse={float(initial['mean_nse'].min()):.4f}, "
        f"best_sse_record={float(initial['sse'].min()):.6g}"
    )
    return initial.reset_index(drop=True)


def sample_based_log_prior(x: np.ndarray, initial_ppd: pd.DataFrame, kernel_scale: float) -> float:
    # Step 1 (GA) only provides a sample-based prior diagnostic by default.
    # It enters AM acceptance only when config.am_use_prior_in_acceptance is true.
    samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    weights = initial_ppd["roulette_weight"].to_numpy(dtype=float)
    diffs = samples - x[None, :]
    sq = np.sum(diffs * diffs, axis=1)
    logs = np.log(np.maximum(weights, 1e-300)) - 0.5 * sq / max(kernel_scale, 1e-12)
    max_log = float(np.max(logs))
    return float(max_log + np.log(np.sum(np.exp(logs - max_log))))


def initial_ppd_weighted_covariance(initial_ppd: pd.DataFrame, config: ExperimentConfig) -> np.ndarray:
    d = len(CANDIDATE_NODES)
    sd = (2.4**2) / d
    samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    if len(samples) < 2:
        return np.eye(d) * config.am_initial_covariance

    weights = initial_ppd.get("roulette_weight", pd.Series(np.ones(len(samples), dtype=float))).to_numpy(dtype=float)
    weights = np.maximum(weights, 0.0)
    if float(weights.sum()) <= 0.0:
        weights = np.ones(len(samples), dtype=float)
    weights = weights / float(weights.sum())

    mean = np.sum(samples * weights[:, None], axis=0)
    diffs = samples - mean[None, :]
    cov = (diffs * weights[:, None]).T @ diffs
    cov_floor = max(config.am_initial_covariance * 0.10, config.am_eps)
    return sd * cov + cov_floor * np.eye(d)


def adaptive_covariance(history: list[np.ndarray], config: ExperimentConfig, initial_covariance: np.ndarray | None = None) -> np.ndarray:
    d = len(CANDIDATE_NODES)
    # Follow the AM scaling stated in the English paper: s_d = 2.4^2 / d.
    sd = (2.4**2) / d
    if len(history) <= config.am_adapt_start:
        if initial_covariance is not None:
            return initial_covariance
        return np.eye(d) * config.am_initial_covariance
    arr = np.vstack(history)
    cov = np.cov(arr.T, bias=False)
    if np.ndim(cov) == 0:
        cov = np.eye(d) * float(cov)
    return sd * cov + sd * config.am_eps * np.eye(d)


def propose_simplex_candidate(
    current: np.ndarray,
    covariance: np.ndarray,
    rng: np.random.Generator,
    config: ExperimentConfig,
) -> np.ndarray:
    if config.am_proposal_method == "tangent_projected_gaussian":
        perturb = rng.multivariate_normal(mean=np.zeros_like(current), cov=covariance)
        # Keep proposals on the fixed-total tangent plane first; projection is then only for non-negative bounds.
        perturb = perturb - float(np.mean(perturb))
        return simplex_project(current + perturb)
    proposal = rng.multivariate_normal(mean=current, cov=covariance)
    return simplex_project(proposal)


def select_am_start_indices(initial_ppd: pd.DataFrame, config: ExperimentConfig, rng: np.random.Generator) -> np.ndarray:
    sample_count = len(initial_ppd)
    if sample_count == 0:
        raise RuntimeError("Initial PPD is empty; AM has no starting points")
    if not config.am_start_weighted:
        return np.arange(config.am_chain_count, dtype=int) % sample_count

    start_indices = [0]
    if config.am_chain_count <= 1:
        return np.asarray(start_indices, dtype=int)

    available = np.arange(1, sample_count, dtype=int)
    if len(available) == 0:
        return np.zeros(config.am_chain_count, dtype=int)

    weights = initial_ppd["roulette_weight"].to_numpy(dtype=float)[available]
    weights = np.maximum(weights, 0.0)
    if float(weights.sum()) <= 0.0:
        weights = np.ones(len(available), dtype=float)
    weights = weights / float(weights.sum())
    needed = config.am_chain_count - 1
    replace = needed > len(available)
    sampled = rng.choice(available, size=needed, replace=replace, p=weights)
    start_indices.extend(int(idx) for idx in sampled)
    return np.asarray(start_indices, dtype=int)


def format_top_nodes(shares: np.ndarray, top_k: int = 3) -> str:
    ranked = np.argsort(np.asarray(shares, dtype=float))[::-1][:top_k]
    return ", ".join(f"{CANDIDATE_NODES[idx]}={float(shares[idx]):.4f}" for idx in ranked)


def _run_am_chain(
    chain_id: int,
    generated_data: dict[str, pd.DataFrame],
    initial_ppd: pd.DataFrame,
    config: ExperimentConfig,
    sigma: float,
    kernel_scale: float,
    chain_seed: int,
    start_index: int,
    initial_covariance: np.ndarray | None,
) -> tuple[int, list[dict[str, Any]], float]:
    rng = np.random.default_rng(chain_seed)
    initial_samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    worker_initializer(generated_data)

    log_progress(f"AM chain {chain_id + 1}/{config.am_chain_count} start: initial_ppd_index={start_index}")
    current = simplex_project(initial_samples[start_index % len(initial_samples)])
    history = [current.copy()]
    current_eval = worker_evaluate((0, current, False, config.ga_dedup_decimals))
    current_log_like = -0.5 * current_eval["sse"] / (sigma**2)
    current_log_ga_prior = sample_based_log_prior(current, initial_ppd, kernel_scale)
    current_log_target = current_log_like + current_log_ga_prior if config.am_use_prior_in_acceptance else current_log_like

    accepted_count = 0
    rows: list[dict[str, Any]] = []
    for step in range(config.am_samples_per_chain):
        if step == 0 or (step + 1) % config.progress_step_interval == 0 or step + 1 == config.am_samples_per_chain:
            current_accept_rate = accepted_count / max(1, step)
            log_progress(
                f"AM chain {chain_id + 1}: step {step + 1}/{config.am_samples_per_chain}, "
                f"accepted={accepted_count}, accept_rate={current_accept_rate:.4f}, "
                f"am_metric_raw_sse={current_eval['sse']:.6g}, log_like={current_log_like:.4f}, "
                f"acceptance_log_target={current_log_target:.4f}, "
                f"mean_nse_record={current_eval['mean_nse']:.4f}, top3={format_top_nodes(current)}"
            )

        cov = adaptive_covariance(history, config, initial_covariance)
        proposal = propose_simplex_candidate(current, cov, rng, config)
        proposal_eval = worker_evaluate((0, proposal, False, config.ga_dedup_decimals))
        proposal_log_like = -0.5 * proposal_eval["sse"] / (sigma**2)
        proposal_log_ga_prior = sample_based_log_prior(proposal, initial_ppd, kernel_scale)
        proposal_log_target = (
            proposal_log_like + proposal_log_ga_prior
            if config.am_use_prior_in_acceptance
            else proposal_log_like
        )
        log_accept_ratio = proposal_log_target - current_log_target
        accept_prob = 1.0 if log_accept_ratio >= 0 else float(np.exp(log_accept_ratio))
        accepted = bool(rng.random() < accept_prob)
        if accepted:
            current = proposal
            current_eval = proposal_eval
            current_log_like = proposal_log_like
            current_log_ga_prior = proposal_log_ga_prior
            current_log_target = proposal_log_target
            accepted_count += 1

        row = {
            "chain": chain_id,
            "step": step + 1,
            "accepted": int(accepted),
            "mean_nse": float(current_eval["mean_nse"]),
            "sse": float(current_eval["sse"]),
            "log_like": float(current_log_like),
            "log_ga_prior_diagnostic": float(current_log_ga_prior),
            "acceptance_log_target": float(current_log_target),
            "log_like_plus_ga_prior_diagnostic": float(current_log_like + current_log_ga_prior),
        }
        for idx, node in enumerate(CANDIDATE_NODES):
            row[node] = float(current[idx])
        rows.append(row)
        history.append(current.copy())

    accept_rate = accepted_count / max(1, config.am_samples_per_chain)
    log_progress(f"AM chain {chain_id + 1} done: accept_rate={accept_rate:.4f}")
    return chain_id, rows, float(accept_rate)


def _run_am_chain_entry(args: tuple[int, dict[str, pd.DataFrame], pd.DataFrame, ExperimentConfig, float, float, int, int, np.ndarray | None]) -> tuple[int, list[dict[str, Any]], float]:
    return _run_am_chain(*args)


def run_am(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], initial_ppd: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    obs = dataset.observed_delta[list(MONITOR_NODES)].to_numpy(dtype=float)
    sigma = max(float(np.std(obs)), 1e-6)
    kernel_scale = config.am_prior_kernel_scale
    chain_workers = min(max(1, config.parallel_workers), config.am_chain_count)
    seed_rng = np.random.default_rng(config.random_seed + 1)
    chain_seeds = seed_rng.integers(0, np.iinfo(np.int64).max, size=config.am_chain_count, dtype=np.int64)
    start_rng = np.random.default_rng(config.random_seed + 2)
    start_indices = select_am_start_indices(initial_ppd, config, start_rng)
    initial_covariance = initial_ppd_weighted_covariance(initial_ppd, config) if config.am_use_initial_ppd_covariance else None

    log_progress(
        f"AM start: chains={config.am_chain_count}, samples_per_chain={config.am_samples_per_chain}, "
        f"warmup={config.am_warmup}, adapt_start={config.am_adapt_start}, init_cov={config.am_initial_covariance}, "
        f"initial_ppd={len(initial_ppd)}, prior_acceptance={config.am_use_prior_in_acceptance}, "
        f"ppd_covariance={config.am_use_initial_ppd_covariance}, chain_workers={chain_workers}"
    )

    chain_args = [
        (
            chain_id,
            generated_data,
            initial_ppd,
            config,
            sigma,
            kernel_scale,
            int(chain_seeds[chain_id]),
            int(start_indices[chain_id]),
            initial_covariance,
        )
        for chain_id in range(config.am_chain_count)
    ]
    if chain_workers <= 1:
        chain_results = [_run_am_chain(*args) for args in chain_args]
    else:
        with ProcessPoolExecutor(max_workers=chain_workers) as executor:
            chain_results = list(executor.map(_run_am_chain_entry, chain_args))

    chain_results.sort(key=lambda item: item[0])
    rows: list[dict[str, Any]] = []
    for _, chain_rows, _ in chain_results:
        rows.extend(chain_rows)
    return pd.DataFrame(rows).sort_values(["chain", "step"]).reset_index(drop=True)


def extract_ppd(am_samples: pd.DataFrame, config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    tail = am_samples[am_samples["step"] > config.am_warmup].copy()
    summary_rows = []
    for node in CANDIDATE_NODES:
        values = tail[node].to_numpy(dtype=float)
        summary_rows.append(
            {
                "node": node,
                "posterior_mean": float(np.mean(values)),
                "posterior_median": float(np.median(values)),
                "p05": float(np.quantile(values, 0.05)),
                "p95": float(np.quantile(values, 0.95)),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("posterior_median", ascending=False).reset_index(drop=True)
    return tail.reset_index(drop=True), summary_df


def posterior_predictive_validation(
    dataset: ExperimentDataset,
    generated_data: dict[str, pd.DataFrame],
    ppd_samples: pd.DataFrame,
    config: ExperimentConfig,
    validation_dataset: ExperimentDataset | None = None,
    validation_generated_data: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # The English paper validates PPD by driving the model with a different observed
    # rainfall event and checking whether observed outlet flow falls inside the 90%
    # probabilistic simulation interval. If no independent validation event is passed,
    # this function still produces the same outlet-flow diagnostic, but labels it as
    # same-event diagnostic instead of paper-strength validation.
    validation_dataset = validation_dataset if validation_dataset is not None else dataset
    validation_generated_data = validation_generated_data if validation_generated_data is not None else generated_data
    validation_mode = "independent_event" if validation_dataset is not dataset else "same_event_outlet_diagnostic"
    sample_count = min(config.posterior_validation_samples, len(ppd_samples))
    if sample_count <= 0:
        raise RuntimeError("No PPD samples available for posterior predictive validation")
    draws = ppd_samples.sample(n=sample_count, random_state=config.random_seed)
    band_rows = []
    outlet_predictions: list[np.ndarray] = []

    log_progress(f"Posterior predictive validation start: target=outlet_flow, mode={validation_mode}, samples={sample_count}")
    for draw_idx, (_, draw) in enumerate(tqdm(draws.iterrows(), total=sample_count, desc="Posterior validation", leave=True), start=1):
        if draw_idx == 1 or draw_idx % max(1, config.progress_step_interval // 2) == 0 or draw_idx == sample_count:
            log_progress(f"Posterior predictive validation sample {draw_idx}/{sample_count}")
        shares = draw[list(CANDIDATE_NODES)].to_numpy(dtype=float)
        eval_result = parallel_evaluate(
            [(0, shares)],
            validation_generated_data,
            1,
            include_series=True,
            use_cache=False,
            cache_decimals=config.ga_dedup_decimals,
        )[0]
        outlet_predictions.append(eval_result["event_outlet"]["outfall_link_flow_cms"].to_numpy(dtype=float))

    pred = np.vstack(outlet_predictions)
    obs = validation_dataset.outlet["outfall_link_flow_cms"].to_numpy(dtype=float)[: pred.shape[1]]
    p05 = np.quantile(pred, 0.05, axis=0)
    p50 = np.quantile(pred, 0.50, axis=0)
    p95 = np.quantile(pred, 0.95, axis=0)
    coverage_tol = np.maximum(1e-9, np.maximum(np.abs(p05), np.abs(p95)) * 1e-8)
    covered = (obs >= p05 - coverage_tol) & (obs <= p95 + coverage_tol)
    covered_count = int(np.sum(covered))
    total_count = int(len(covered))
    uncovered_count = total_count - covered_count
    coverage = float(covered_count / max(1, total_count))
    coverage_rows = [
        {
            "target": "outlet_flow",
            "validation_mode": validation_mode,
            "coverage_90": coverage,
            "covered_count": covered_count,
            "uncovered_count": uncovered_count,
            "total_count": total_count,
            "coverage_to_noncoverage": f"{covered_count}:{uncovered_count}",
        }
    ]
    for step_idx in range(pred.shape[1]):
        band_rows.append(
            {
                "target": "outlet_flow",
                "validation_mode": validation_mode,
                "step": step_idx,
                "relative_hour": float(validation_dataset.total_process["relative_hour"].iloc[step_idx]),
                "p05": float(p05[step_idx]),
                "p50": float(p50[step_idx]),
                "p95": float(p95[step_idx]),
                "observed": float(obs[step_idx]),
                "covered_90": int(covered[step_idx]),
            }
        )
    log_progress("Posterior predictive validation done")
    return pd.DataFrame(band_rows), pd.DataFrame(coverage_rows)

