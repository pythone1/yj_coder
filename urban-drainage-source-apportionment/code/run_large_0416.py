from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import numpy as np
import pandas as pd

from build_0416_data import build_truth_shares, main as build_data_main
from config_0416 import (
    BASELINE_MONITOR_CSV,
    CANDIDATE_NODES,
    EVENT_MONITOR_CSV,
    ExperimentConfig,
    OBSERVED_DELTA_CSV,
    OUTLET_SERIES_CSV,
    RESULT_DIR,
    TOTAL_PROCESS_CSV,
    TRUTH_INJECTION_CSV,
    ensure_dirs,
    runtime_model_path,
)
from ga_am_0416 import (
    evaluation_cache_stats,
    extract_ppd,
    log_progress,
    posterior_predictive_validation,
    roulette_initial_ppd,
    run_am,
    run_ga,
)
from run_outputs_0416 import posterior_best_shares, posterior_median_shares, save_solution_outputs
from simulation_0416 import build_dataset, evaluate_shares


OUTPUT_DIR = RESULT_DIR / "large_run"


def load_generated_data() -> dict[str, pd.DataFrame]:
    return {
        "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
        "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
        "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
        "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
        "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
        "outlet": pd.read_csv(OUTLET_SERIES_CSV, encoding="utf-8-sig"),
    }


def save_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUTPUT_DIR / name, index=False, encoding="utf-8-sig")


def save_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_truth_replay(dataset, generated) -> dict[str, float]:
    truth_shares = build_truth_shares(generated["truth_injection"])
    truth_eval = evaluate_shares(truth_shares, dataset, str(runtime_model_path(0)))
    return {"mean_nse": float(truth_eval["mean_nse"]), "sse": float(truth_eval["sse"])}


def main() -> None:
    ensure_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log_progress("Rebuilding canonical 0520 data from configured baseline and event models")
    build_data_main()

    config = ExperimentConfig(
        ga_population_count=6,
        ga_population_size=80,
        ga_generations=30,
        ga_elite_ratio=0.08,
        ga_mutation_strength=0.25,
        ga_migration_interval=3,
        ga_migration_count=2,
        ga_competition_replace_count=2,
        ga_dedup_decimals=4,
        am_chain_count=12,
        am_samples_per_chain=1200,
        am_warmup=400,
        am_adapt_start=400,
        am_initial_covariance=0.0015,
        initial_ppd_keep_fraction=0.60,
        initial_ppd_min_count=300,
        initial_ppd_min_mean_nse=-100.0,
        initial_ppd_max_nse_drop=0.25,
        initial_ppd_rank_pressure=2.0,
        am_start_weighted=True,
        am_use_prior_in_acceptance=False,
        am_use_initial_ppd_covariance=True,
        am_prior_kernel_scale=0.01,
        am_proposal_method="tangent_projected_gaussian",
        posterior_validation_samples=96,
        parallel_workers=8,
        random_seed=20260520,
        progress_step_interval=50,
    )

    generated = load_generated_data()
    dataset = build_dataset(generated)

    truth_check = validate_truth_replay(dataset, generated)
    save_json(truth_check, OUTPUT_DIR / "0520_truth_replay_check.json")
    log_progress(f"Truth replay check: mean_nse={truth_check['mean_nse']:.6f}, sse={truth_check['sse']:.6e}")

    ga_all_df, ga_history_df, ga_last_df, ga_best_shares = run_ga(dataset, generated, config)
    save_csv(ga_all_df, "0520_GA_all.csv")
    save_csv(ga_history_df, "0520_GA_best_by_generation.csv")
    save_csv(ga_last_df, "0520_GA_last_generation.csv")

    rng = np.random.default_rng(config.random_seed + 99)
    ga_best_row = ga_all_df.sort_values(["mean_nse", "sse"], ascending=[False, True]).iloc[0]
    initial_ppd_df = roulette_initial_ppd(ga_last_df, ga_best_shares, config, rng, ga_best_row=ga_best_row)
    save_csv(initial_ppd_df, "0520_initial_PPD.csv")

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    save_csv(am_df, "0520_AM_samples.csv")

    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    save_csv(ppd_samples_df, "0520_PPD_samples.csv")
    save_csv(posterior_df, "0520_posterior_node_weights.csv")

    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)
    save_csv(bands_df, "0520_posterior_predictive_bands.csv")
    save_csv(coverage_df, "0520_posterior_predictive_coverage.csv")

    runtime_inp = str(runtime_model_path(0))
    solution_scores, recommended_solution = save_solution_outputs(
        OUTPUT_DIR,
        {
            "ga_best": ga_best_shares,
            "posterior_best_map": posterior_best_shares(ppd_samples_df),
            "posterior_median_summary": posterior_median_shares(posterior_df),
        },
        dataset,
        runtime_inp,
    )

    summary = {
        "run_mode": "0520 large run",
        "solution_scores": solution_scores,
        "recommended_solution_name": recommended_solution,
        "final_solution_name": recommended_solution,
        "posterior_median_top3": posterior_df.head(3)["node"].tolist(),
        "ga_last_score_stats": {
            "max_mean_nse": float(ga_last_df["mean_nse"].max()),
            "median_mean_nse": float(ga_last_df["mean_nse"].median()),
            "min_mean_nse": float(ga_last_df["mean_nse"].min()),
            "unique_count": int(len(ga_last_df)),
        },
        "initial_ppd_count": int(len(initial_ppd_df)),
        "initial_ppd_score_stats": {
            "max_mean_nse": float(initial_ppd_df["mean_nse"].max()),
            "median_mean_nse": float(initial_ppd_df["mean_nse"].median()),
            "min_mean_nse": float(initial_ppd_df["mean_nse"].min()),
        },
        "posterior_validation_sample_count": int(config.posterior_validation_samples),
        "ga_evaluation_cache": evaluation_cache_stats(),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "posterior_validation_target": str(coverage_df.iloc[0].get("target", "")) if not coverage_df.empty else "",
        "posterior_validation_mode": str(coverage_df.iloc[0].get("validation_mode", "")) if not coverage_df.empty else "",
        "posterior_coverage_to_noncoverage": str(coverage_df.iloc[0].get("coverage_to_noncoverage", "")) if not coverage_df.empty else "",
        "am_accept_rate_by_chain": {str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()},
        "config": config.__dict__,
        "data_paths": {"output_dir": str(OUTPUT_DIR)},
    }
    save_json(summary, OUTPUT_DIR / "0520_summary.json")
    log_progress("0520 large run ready")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()


