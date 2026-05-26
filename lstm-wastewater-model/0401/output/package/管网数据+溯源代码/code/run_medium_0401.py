from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import numpy as np
import pandas as pd

from build_0401_data import build_truth_shares, main as build_data_main
from config_0401 import (
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
from ga_am_0401 import (
    extract_ppd,
    log_progress,
    posterior_predictive_validation,
    roulette_initial_ppd,
    run_am,
    run_ga,
)
from simulation_0401 import build_dataset, evaluate_shares


OUTPUT_DIR = RESULT_DIR / "medium_run"


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
    return {
        "mean_nse": float(truth_eval["mean_nse"]),
        "sse": float(truth_eval["sse"]),
    }


def main() -> None:
    ensure_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log_progress("Rebuilding canonical 0401 generated data from confirmed templates")
    build_data_main()

    config = ExperimentConfig(
        ga_population_count=4,
        ga_population_size=24,
        ga_generations=12,
        ga_elite_ratio=0.25,
        ga_mutation_strength=0.18,
        ga_migration_interval=2,
        ga_migration_count=2,
        ga_competition_replace_count=2,
        am_chain_count=4,
        am_samples_per_chain=900,
        am_warmup=220,
        am_adapt_start=220,
        am_initial_covariance=0.0015,
        posterior_validation_samples=24,
        parallel_workers=8,
        random_seed=20260401,
        progress_step_interval=25,
    )

    generated = load_generated_data()
    dataset = build_dataset(generated)

    log_progress("Loaded 0401 generated data")
    log_progress(f"Observed delta rows={len(dataset.observed_delta)}, monitors={len(dataset.observed_delta.columns) - 3}")
    log_progress(f"Q_R={dataset.qr_m3:.2f} m3")

    truth_check = validate_truth_replay(dataset, generated)
    save_json(truth_check, OUTPUT_DIR / "0401_truth_replay_check.json")
    log_progress(f"Truth replay check: mean_nse={truth_check['mean_nse']:.6f}, sse={truth_check['sse']:.6e}")
    if truth_check["mean_nse"] < 0.999999 or truth_check["sse"] > 1e-8:
        raise RuntimeError(
            f"Truth replay check failed before medium run: mean_nse={truth_check['mean_nse']}, sse={truth_check['sse']}"
        )

    log_progress("Starting medium run (~target around 10-12 hours depending on machine and SWMM runtime)")

    ga_all_df, ga_history_df, ga_last_df, ga_best_shares = run_ga(dataset, generated, config)
    save_csv(ga_all_df, "0401_GA全部方案.csv")
    save_csv(ga_history_df, "0401_GA每代最佳.csv")
    save_csv(ga_last_df, "0401_GA末代合并.csv")

    rng = np.random.default_rng(config.random_seed + 99)
    initial_ppd_df = roulette_initial_ppd(ga_last_df, ga_best_shares, config, rng)
    save_csv(initial_ppd_df, "0401_initial_PPD.csv")

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    save_csv(am_df, "0401_AM样本.csv")

    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    save_csv(ppd_samples_df, "0401_PPD样本.csv")
    save_csv(posterior_df, "0401_后验节点权重.csv")

    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)
    save_csv(bands_df, "0401_posterior_predictive_bands.csv")
    save_csv(coverage_df, "0401_posterior_predictive_coverage.csv")

    posterior_median_map = dict(zip(posterior_df["node"], posterior_df["posterior_median"]))
    posterior_median_shares = np.array([posterior_median_map[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_median_shares = posterior_median_shares / max(float(posterior_median_shares.sum()), 1e-12)

    top_like_row = am_df.sort_values("log_like", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_like_row[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_best_shares = posterior_best_shares / max(float(posterior_best_shares.sum()), 1e-12)

    runtime_inp = str(runtime_model_path(0))
    ga_best_eval = evaluate_shares(ga_best_shares, dataset, runtime_inp)
    posterior_median_eval = evaluate_shares(posterior_median_shares, dataset, runtime_inp)
    posterior_best_eval = evaluate_shares(posterior_best_shares, dataset, runtime_inp)

    final_name = "posterior_median"
    final_eval = posterior_median_eval
    final_eval["sim_delta"].to_csv(OUTPUT_DIR / "0401_最终方案模拟增量.csv", index=False, encoding="utf-8-sig")
    final_eval["event_monitor"].to_csv(OUTPUT_DIR / "0401_最终方案事件监测.csv", index=False, encoding="utf-8-sig")
    final_eval["event_outlet"].to_csv(OUTPUT_DIR / "0401_最终方案排口过程.csv", index=False, encoding="utf-8-sig")

    summary = {
        "run_mode": "0401 clean medium run",
        "ga_best_mean_nse": float(ga_best_eval["mean_nse"]),
        "posterior_median_nse": float(posterior_median_eval["mean_nse"]),
        "posterior_best_nse": float(posterior_best_eval["mean_nse"]),
        "final_solution_name": final_name,
        "final_mean_nse": float(final_eval["mean_nse"]),
        "predicted_top3": posterior_df.head(3)["node"].tolist(),
        "initial_ppd_count": int(len(initial_ppd_df)),
        "posterior_validation_sample_count": int(config.posterior_validation_samples),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "am_accept_rate_by_chain": {str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()},
        "am_prior_type": "step1_initial_ppd_sample_based_prior",
        "am_acceptance_rule": "likelihood_ratio_as_stated_in_english_paper",
        "initial_ppd_role": "provides_starting_points_and_prior_information_from_step1",
        "am_best_sample_selection_metric": "log_like",
        "am_sd": float((2.4 ** 2) / len(CANDIDATE_NODES)),
        "am_dimension_d": int(len(CANDIDATE_NODES)),
        "am_execution_mode": "chain_parallel_process_pool",
        "am_chain_worker_count": int(min(max(1, config.parallel_workers), config.am_chain_count)),
        "config": config.__dict__,
        "data_paths": {"output_dir": str(OUTPUT_DIR)},
    }
    (OUTPUT_DIR / "0401_结果汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log_progress("0401 medium run ready")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
