from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import numpy as np

from config_clean import CANDIDATE_NODES, ExperimentConfig, RESULT_DIR, ensure_dirs, load_generated_data, runtime_model_path
from ga_am_clean import (
    extract_ppd,
    log_progress,
    posterior_predictive_validation,
    roulette_initial_ppd,
    run_am,
    run_ga,
)
from simulation_clean import build_dataset, evaluate_shares


OUTPUT_DIR = RESULT_DIR / "clean_small_run"


def save_csv(df, name: str) -> None:
    df.to_csv(OUTPUT_DIR / name, index=False, encoding="utf-8-sig")


def main() -> None:
    ensure_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = ExperimentConfig()
    generated = load_generated_data()
    dataset = build_dataset(generated)

    log_progress("Loaded corrected 0327 generated data")
    log_progress(f"Observed delta rows={len(dataset.observed_delta)}, monitors={len(dataset.observed_delta.columns) - 2}")
    log_progress(f"Q_R={dataset.qr_m3:.2f} m3")

    ga_all_df, ga_history_df, ga_last_df, ga_best_shares = run_ga(dataset, generated, config)
    save_csv(ga_all_df, "0327_GA全部方案.csv")
    save_csv(ga_history_df, "0327_GA每代最佳.csv")
    save_csv(ga_last_df, "0327_GA末代合并.csv")

    rng = np.random.default_rng(config.random_seed + 99)
    initial_ppd_df = roulette_initial_ppd(ga_last_df, ga_best_shares, config, rng)
    save_csv(initial_ppd_df, "0327_initial_PPD.csv")

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    save_csv(am_df, "0327_AM样本.csv")

    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    save_csv(ppd_samples_df, "0327_PPD样本.csv")
    save_csv(posterior_df, "0327_后验节点权重.csv")

    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)
    save_csv(bands_df, "0327_posterior_predictive_bands.csv")
    save_csv(coverage_df, "0327_posterior_predictive_coverage.csv")

    posterior_median_map = dict(zip(posterior_df["节点"], posterior_df["后验中位数"]))
    posterior_median_shares = np.array([posterior_median_map[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_median_shares = posterior_median_shares / max(float(posterior_median_shares.sum()), 1e-12)

    top_post_row = am_df.sort_values("log_posterior", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_post_row[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_best_shares = posterior_best_shares / max(float(posterior_best_shares.sum()), 1e-12)

    runtime_inp = str(runtime_model_path(0))
    ga_best_eval = evaluate_shares(ga_best_shares, dataset, runtime_inp)
    posterior_median_eval = evaluate_shares(posterior_median_shares, dataset, runtime_inp)
    posterior_best_eval = evaluate_shares(posterior_best_shares, dataset, runtime_inp)

    final_name = "posterior_median"
    final_eval = posterior_median_eval
    final_eval["sim_delta"].to_csv(OUTPUT_DIR / "0327_最终方案模拟增量.csv", index=False, encoding="utf-8-sig")

    summary = {
        "run_mode": "0327 clean small run",
        "ga_best_mean_nse": float(ga_best_eval["mean_nse"]),
        "posterior_median_nse": float(posterior_median_eval["mean_nse"]),
        "posterior_best_nse": float(posterior_best_eval["mean_nse"]),
        "final_solution_name": final_name,
        "final_mean_nse": float(final_eval["mean_nse"]),
        "predicted_top3": posterior_df.head(3)["节点"].tolist(),
        "initial_ppd_count": int(len(initial_ppd_df)),
        "posterior_validation_sample_count": int(config.posterior_validation_samples),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "am_accept_rate_by_chain": {
            str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()
        },
        "am_sd": float(2.42 / len(CANDIDATE_NODES)),
        "am_dimension_d": int(len(CANDIDATE_NODES)),
        "config": config.__dict__,
        "data_paths": {
            "output_dir": str(OUTPUT_DIR),
        },
    }
    (OUTPUT_DIR / "0327_结果汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log_progress("Run finished")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
