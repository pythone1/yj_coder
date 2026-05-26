from __future__ import annotations

import json
import multiprocessing
import time
from datetime import datetime

from 运行0327小参数实验 import (
    save_docs,
    save_monitor_fit_html,
    save_ppd_validation_html,
    save_structure_html,
    save_summary_pages,
)
from 公共配置与数据 import (
    CANDIDATE_NODES,
    RESULT_DIR,
    ExperimentConfig,
    ensure_directories,
    load_generated_data,
    runtime_model_path,
    validate_generated_data_exists,
    write_data_manifest,
)
from 模型仿真与评估 import build_dataset, evaluate_shares
from 遗传搜索与后验 import (
    extract_ppd,
    posterior_predictive_validation,
    roulette_initial_ppd,
    run_am,
    run_ga,
)


def main() -> None:
    ensure_directories()
    config = ExperimentConfig(
        ga_population_count=5,
        ga_population_size=80,
        ga_generations=25,
        ga_migration_interval=5,
        ga_migration_count=4,
        ga_competition_replace_count=4,
        am_chain_count=1,
        am_samples_per_chain=2000,
        am_warmup=500,
        am_adapt_start=100,
        posterior_validation_samples=24,
        parallel_workers=6,
    )

    start_wall = datetime.now().isoformat(timespec="seconds")
    start_perf = time.perf_counter()
    print(f"[RUN] start {start_wall}", flush=True)
    print(f"[RUN] config: GA={config.ga_population_count}x{config.ga_population_size}x{config.ga_generations}, AM={config.am_chain_count}x{config.am_samples_per_chain}, workers={config.parallel_workers}", flush=True)

    validate_generated_data_exists()
    write_data_manifest(config)
    generated = load_generated_data()
    dataset = build_dataset(generated)

    ga_all_df, ga_history_df, ga_last_df, ga_best_shares = run_ga(dataset, generated, config)
    ga_all_df.to_csv(RESULT_DIR / "0327_GA全部方案.csv", index=False, encoding="utf-8-sig")
    ga_history_df.to_csv(RESULT_DIR / "0327_GA每代最佳.csv", index=False, encoding="utf-8-sig")
    ga_last_df.to_csv(RESULT_DIR / "0327_GA末代合并.csv", index=False, encoding="utf-8-sig")

    import numpy as np

    rng = np.random.default_rng(config.random_seed + 99)
    initial_ppd_df = roulette_initial_ppd(ga_last_df, ga_best_shares, config, rng)
    initial_ppd_df.to_csv(RESULT_DIR / "0327_initial_PPD.csv", index=False, encoding="utf-8-sig")

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    am_df.to_csv(RESULT_DIR / "0327_AM样本.csv", index=False, encoding="utf-8-sig")

    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    ppd_samples_df.to_csv(RESULT_DIR / "0327_PPD样本.csv", index=False, encoding="utf-8-sig")
    posterior_df.to_csv(RESULT_DIR / "0327_后验节点权重.csv", index=False, encoding="utf-8-sig")

    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)
    bands_df.to_csv(RESULT_DIR / "0327_posterior_predictive_bands.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(RESULT_DIR / "0327_posterior_predictive_coverage.csv", index=False, encoding="utf-8-sig")

    posterior_median_map = dict(zip(posterior_df["节点"], posterior_df["后验中位数"]))
    posterior_median_shares = np.array([posterior_median_map[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_median_shares = posterior_median_shares / max(float(posterior_median_shares.sum()), 1e-12)

    top_post_row = am_df.sort_values("log_posterior", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_post_row[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_best_shares = posterior_best_shares / max(float(posterior_best_shares.sum()), 1e-12)

    runtime_inp = runtime_model_path(0)
    ga_best_eval = evaluate_shares(ga_best_shares, dataset, str(runtime_inp))
    posterior_median_eval = evaluate_shares(posterior_median_shares, dataset, str(runtime_inp))
    posterior_best_eval = evaluate_shares(posterior_best_shares, dataset, str(runtime_inp))

    final_name = "posterior_median"
    final_eval = posterior_median_eval
    final_eval["sim_delta"].to_csv(RESULT_DIR / "0327_最终方案模拟增量.csv", index=False, encoding="utf-8-sig")

    observed_plot_df = dataset.observed_delta.copy().iloc[: len(final_eval["sim_delta"])].reset_index(drop=True)
    observed_plot_df["相对小时"] = dataset.total_process["相对小时"].iloc[: len(observed_plot_df)].to_numpy(dtype=float)
    sim_plot_df = final_eval["sim_delta"].copy()

    end_perf = time.perf_counter()
    elapsed_seconds = end_perf - start_perf
    end_wall = datetime.now().isoformat(timespec="seconds")

    summary = {
        "run_mode": "0327 论文参数实验",
        "start_time": start_wall,
        "end_time": end_wall,
        "elapsed_seconds": elapsed_seconds,
        "Qr_m3": dataset.qr_m3,
        "ga_best_mean_nse": float(ga_best_eval["mean_nse"]),
        "posterior_median_nse": float(posterior_median_eval["mean_nse"]),
        "posterior_best_nse": float(posterior_best_eval["mean_nse"]),
        "final_solution_name": final_name,
        "final_mean_nse": float(final_eval["mean_nse"]),
        "predicted_top3": posterior_df.head(3)["节点"].tolist(),
        "initial_ppd_count": int(len(initial_ppd_df)),
        "posterior_validation_sample_count": int(config.posterior_validation_samples),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "am_accept_rate_by_chain": {str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()},
        "am_sd": float(2.42 / len(CANDIDATE_NODES)),
        "am_dimension_d": int(len(CANDIDATE_NODES)),
        "ga_population_count": config.ga_population_count,
        "ga_population_size": config.ga_population_size,
        "ga_generations": config.ga_generations,
        "ga_migration_interval": config.ga_migration_interval,
        "am_chain_count": config.am_chain_count,
        "am_samples_per_chain": config.am_samples_per_chain,
        "parallel_workers": config.parallel_workers,
    }

    save_structure_html()
    save_monitor_fit_html(observed_plot_df, sim_plot_df)
    save_ppd_validation_html(bands_df)
    save_summary_pages(summary)
    save_docs(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
