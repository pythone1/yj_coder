from __future__ import annotations

import math
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from config_0401 import CANDIDATE_NODES, MONITOR_NODES, ExperimentConfig
from simulation_0401 import ExperimentDataset, simplex_project, worker_evaluate, worker_initializer


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


def _shares_key(shares: np.ndarray) -> tuple[float, ...]:
    arr = np.asarray(shares, dtype=float).reshape(-1)
    return tuple(float(v) for v in arr)


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
        key = _shares_key(projected)
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
        key = _shares_key(candidate)
        if key in seen:
            continue
        unique_members.append(candidate)
        seen.add(key)

    while len(unique_members) < config.ga_population_size:
        candidate = simplex_project(rng.random(dim))
        key = _shares_key(candidate)
        if key in seen:
            continue
        unique_members.append(candidate)
        seen.add(key)

    return np.vstack(unique_members[: config.ga_population_size])


def deduplicate_evaluated_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_rows: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    for row in rows:
        key = _shares_key(row["shares"])
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


def parallel_evaluate(tasks: list[tuple[int, np.ndarray]], generated_data: dict[str, pd.DataFrame], worker_count: int) -> list[dict[str, Any]]:
    if worker_count <= 1:
        worker_initializer(generated_data)
        return [worker_evaluate(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=worker_count, initializer=worker_initializer, initargs=(generated_data,)) as executor:
        return list(executor.map(worker_evaluate, tasks))


def population_competition(populations: list[np.ndarray], evaluated_populations: list[list[dict[str, Any]]], config: ExperimentConfig) -> list[np.ndarray]:
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
    return deduplicate_and_refill_population(offspring, config, rng)


def run_ga(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
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
            evaluated = parallel_evaluate(tasks, generated_data, config.parallel_workers)
            for row in evaluated:
                row["population"] = pop_idx
                row["generation"] = generation + 1
                if best_global is None or row["mean_nse"] > best_global["mean_nse"]:
                    best_global = row
            evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
            unique_evaluated = deduplicate_evaluated_rows(evaluated)
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
            log_progress(f"GA generation {generation + 1}: population {pop_idx + 1} best_nse={best['mean_nse']:.4f}")

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
            log_progress(f"GA generation {generation + 1}: competition + migration")
            populations = population_competition(populations, evaluated_populations, config)
            populations = [deduplicate_and_refill_population(pop, config, rng) for pop in populations]
            reevaluated_populations: list[list[dict[str, Any]]] = []
            for pop in populations:
                tasks = [(i % max(1, config.parallel_workers), ind) for i, ind in enumerate(pop)]
                evaluated = parallel_evaluate(tasks, generated_data, config.parallel_workers)
                evaluated.sort(key=lambda item: item["mean_nse"], reverse=True)
                evaluated = deduplicate_evaluated_rows(evaluated)
                reevaluated_populations.append(evaluated)
            populations = population_migration(populations, reevaluated_populations, config)
            populations = [deduplicate_and_refill_population(pop, config, rng) for pop in populations]
            breeding_rows = reevaluated_populations
        else:
            breeding_rows = evaluated_populations

        populations = [evolve_population(rows, config, rng) for rows in breeding_rows]

    if best_global is None:
        raise RuntimeError("GA produced no valid individual")

    all_df = pd.DataFrame(all_rows)
    history_df = pd.DataFrame(history_rows)
    merged_last_df = all_df[all_df["generation"] == config.ga_generations].copy().sort_values("mean_nse", ascending=False).reset_index(drop=True)
    log_progress(f"GA done: global_best_nse={best_global['mean_nse']:.4f}")
    return all_df, history_df, merged_last_df, best_global["shares"]


def roulette_initial_ppd(merged_last: pd.DataFrame, ga_best_shares: np.ndarray, config: ExperimentConfig, rng: np.random.Generator) -> pd.DataFrame:
    pool = (
        merged_last.copy()
        .sort_values(["mean_nse", "sse"], ascending=[False, True])
        .drop_duplicates(subset=CANDIDATE_NODES, keep="first")
        .reset_index(drop=True)
    )
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
        initial = pd.concat([best_row, initial.iloc[:-1]], ignore_index=True)

    selected_fitness = initial["mean_nse"].to_numpy(dtype=float)
    selected_shifted = selected_fitness - selected_fitness.min() + 1e-12
    initial["roulette_weight"] = selected_shifted / selected_shifted.sum()
    log_progress(f"Initial PPD built: unique_pool={len(pool)}, keep_count={len(initial)}")
    return initial.reset_index(drop=True)


def sample_based_log_prior(x: np.ndarray, initial_ppd: pd.DataFrame, kernel_scale: float) -> float:
    # Align with the English paper's description:
    # p(X) is prior information generated by Step 1 (initial PPD from GA).
    # We keep the paper's likelihood-ratio acceptance rule in run_am, while
    # recording this sample-based prior for posterior diagnostics.
    samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    weights = initial_ppd["roulette_weight"].to_numpy(dtype=float)
    diffs = samples - x[None, :]
    sq = np.sum(diffs * diffs, axis=1)
    logs = np.log(np.maximum(weights, 1e-300)) - 0.5 * sq / max(kernel_scale, 1e-12)
    max_log = float(np.max(logs))
    return float(max_log + np.log(np.sum(np.exp(logs - max_log))))


def adaptive_covariance(history: list[np.ndarray], config: ExperimentConfig) -> np.ndarray:
    d = len(CANDIDATE_NODES)
    # Follow the AM scaling stated in the English paper: s_d = 2.4^2 / d.
    sd = (2.4**2) / d
    if len(history) <= config.am_adapt_start:
        return np.eye(d) * config.am_initial_covariance
    arr = np.vstack(history)
    cov = np.cov(arr.T, bias=False)
    if np.ndim(cov) == 0:
        cov = np.eye(d) * float(cov)
    return sd * cov + sd * config.am_eps * np.eye(d)


def _run_am_chain(
    chain_id: int,
    generated_data: dict[str, pd.DataFrame],
    initial_ppd: pd.DataFrame,
    config: ExperimentConfig,
    sigma: float,
    kernel_scale: float,
    chain_seed: int,
) -> tuple[int, list[dict[str, Any]], float]:
    rng = np.random.default_rng(chain_seed)
    initial_samples = initial_ppd[list(CANDIDATE_NODES)].to_numpy(dtype=float)
    worker_initializer(generated_data)

    log_progress(f"AM chain {chain_id + 1}/{config.am_chain_count} start")
    current = simplex_project(initial_samples[chain_id % len(initial_samples)])
    history = [current.copy()]
    current_eval = worker_evaluate((0, current))
    current_log_like = -0.5 * current_eval["sse"] / (sigma**2)
    current_log_prior = sample_based_log_prior(current, initial_ppd, kernel_scale)

    accepted_count = 0
    rows: list[dict[str, Any]] = []
    for step in range(config.am_samples_per_chain):
        if step == 0 or (step + 1) % config.progress_step_interval == 0 or step + 1 == config.am_samples_per_chain:
            log_progress(
                f"AM chain {chain_id + 1}: step {step + 1}/{config.am_samples_per_chain}, "
                f"accepted={accepted_count}, current_nse={current_eval['mean_nse']:.4f}"
            )

        cov = adaptive_covariance(history, config)
        proposal = rng.multivariate_normal(mean=current, cov=cov)
        proposal = simplex_project(proposal)
        proposal_eval = worker_evaluate((0, proposal))
        proposal_log_like = -0.5 * proposal_eval["sse"] / (sigma**2)
        proposal_log_prior = sample_based_log_prior(proposal, initial_ppd, kernel_scale)
        log_accept_ratio = proposal_log_like - current_log_like
        accept_prob = min(1.0, float(np.exp(log_accept_ratio)))
        accepted = bool(rng.random() < accept_prob)
        if accepted:
            current = proposal
            current_eval = proposal_eval
            current_log_like = proposal_log_like
            current_log_prior = proposal_log_prior
            history.append(current.copy())
            accepted_count += 1

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

    accept_rate = accepted_count / max(1, config.am_samples_per_chain)
    log_progress(f"AM chain {chain_id + 1} done: accept_rate={accept_rate:.4f}")
    return chain_id, rows, float(accept_rate)


def _run_am_chain_entry(args: tuple[int, dict[str, pd.DataFrame], pd.DataFrame, ExperimentConfig, float, float, int]) -> tuple[int, list[dict[str, Any]], float]:
    return _run_am_chain(*args)


def run_am(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], initial_ppd: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    obs = dataset.observed_delta[list(MONITOR_NODES)].to_numpy(dtype=float)
    sigma = max(float(np.std(obs)), 1e-6)
    kernel_scale = 0.01
    chain_workers = min(max(1, config.parallel_workers), config.am_chain_count)
    seed_rng = np.random.default_rng(config.random_seed + 1)
    chain_seeds = seed_rng.integers(0, np.iinfo(np.int64).max, size=config.am_chain_count, dtype=np.int64)

    log_progress(
        f"AM start: chains={config.am_chain_count}, samples_per_chain={config.am_samples_per_chain}, "
        f"warmup={config.am_warmup}, adapt_start={config.am_adapt_start}, init_cov={config.am_initial_covariance}, "
        f"chain_workers={chain_workers}"
    )

    chain_args = [
        (chain_id, generated_data, initial_ppd, config, sigma, kernel_scale, int(chain_seeds[chain_id]))
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


def posterior_predictive_validation(dataset: ExperimentDataset, generated_data: dict[str, pd.DataFrame], ppd_samples: pd.DataFrame, config: ExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_count = min(config.posterior_validation_samples, len(ppd_samples))
    draws = ppd_samples.sample(n=sample_count, random_state=config.random_seed)
    band_rows = []
    monitor_predictions = {node: [] for node in MONITOR_NODES}

    log_progress(f"Posterior predictive validation start: samples={sample_count}")
    for draw_idx, (_, draw) in enumerate(tqdm(draws.iterrows(), total=sample_count, desc="Posterior validation", leave=True), start=1):
        if draw_idx == 1 or draw_idx % max(1, config.progress_step_interval // 2) == 0 or draw_idx == sample_count:
            log_progress(f"Posterior predictive validation sample {draw_idx}/{sample_count}")
        shares = draw[list(CANDIDATE_NODES)].to_numpy(dtype=float)
        eval_result = parallel_evaluate([(0, shares)], generated_data, 1)[0]
        sim_delta = eval_result["sim_delta"]
        for node in MONITOR_NODES:
            monitor_predictions[node].append(sim_delta[node].to_numpy(dtype=float))

    coverage_rows = []
    for node in MONITOR_NODES:
        pred = np.vstack(monitor_predictions[node])
        p05 = np.quantile(pred, 0.05, axis=0)
        p50 = np.quantile(pred, 0.50, axis=0)
        p95 = np.quantile(pred, 0.95, axis=0)
        obs = dataset.observed_delta[node].to_numpy(dtype=float)[: pred.shape[1]]
        coverage = float(np.mean((obs >= p05) & (obs <= p95)))
        coverage_rows.append({"monitor": node, "coverage_90": coverage})
        for step_idx in range(pred.shape[1]):
            band_rows.append(
                {
                    "monitor": node,
                    "step": step_idx,
                    "relative_hour": float(dataset.total_process["relative_hour"].iloc[step_idx]),
                    "p05": float(p05[step_idx]),
                    "p50": float(p50[step_idx]),
                    "p95": float(p95[step_idx]),
                    "observed": float(obs[step_idx]),
                }
            )
    log_progress("Posterior predictive validation done")
    return pd.DataFrame(band_rows), pd.DataFrame(coverage_rows)
