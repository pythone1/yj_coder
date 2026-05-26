from __future__ import annotations

import json
import multiprocessing
import shutil
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from 公共配置与数据 import (
    CANDIDATE_NODES,
    GENERATED_DATA_DIR,
    RESULT_DIR,
    ExperimentConfig,
    ensure_directories,
    load_generated_data,
    runtime_model_path,
    validate_generated_data_exists,
)
from 模型仿真与评估 import build_dataset, evaluate_shares
from 遗传搜索与后验 import extract_ppd, posterior_predictive_validation, run_am


INITIAL_PPD_PATH = RESULT_DIR / "0327_initial_PPD.csv"


AM_EXPERIMENTS: dict[str, dict[str, float | int]] = {
    "A1_multi_chain": {
        "am_chain_count": 3,
        "am_samples_per_chain": 1200,
        "am_warmup": 300,
        "am_adapt_start": 100,
        "am_initial_covariance": 0.002,
    },
    "A2_cov_0p005": {
        "am_chain_count": 3,
        "am_samples_per_chain": 1200,
        "am_warmup": 300,
        "am_adapt_start": 100,
        "am_initial_covariance": 0.005,
    },
    "A5_recommended": {
        "am_chain_count": 3,
        "am_samples_per_chain": 1500,
        "am_warmup": 500,
        "am_adapt_start": 200,
        "am_initial_covariance": 0.005,
    },
}


def build_am_only_config(overrides: dict[str, float | int]) -> ExperimentConfig:
    return ExperimentConfig(
        ga_population_count=5,
        ga_population_size=80,
        ga_generations=25,
        ga_migration_interval=5,
        ga_migration_count=4,
        ga_competition_replace_count=4,
        am_chain_count=int(overrides["am_chain_count"]),
        am_samples_per_chain=int(overrides["am_samples_per_chain"]),
        am_warmup=int(overrides["am_warmup"]),
        am_adapt_start=int(overrides["am_adapt_start"]),
        am_initial_covariance=float(overrides["am_initial_covariance"]),
        posterior_validation_samples=24,
        parallel_workers=6,
    )


def load_initial_ppd() -> pd.DataFrame:
    if not INITIAL_PPD_PATH.exists():
        raise FileNotFoundError(f"缺少 initial PPD 文件: {INITIAL_PPD_PATH}")
    return pd.read_csv(INITIAL_PPD_PATH, encoding="utf-8-sig")


def save_experiment_outputs(experiment_dir: Path, am_df: pd.DataFrame, ppd_samples_df: pd.DataFrame, posterior_df: pd.DataFrame, bands_df: pd.DataFrame, coverage_df: pd.DataFrame, summary: dict) -> None:
    am_df.to_csv(experiment_dir / "0327_AM样本.csv", index=False, encoding="utf-8-sig")
    ppd_samples_df.to_csv(experiment_dir / "0327_PPD样本.csv", index=False, encoding="utf-8-sig")
    posterior_df.to_csv(experiment_dir / "0327_后验节点权重.csv", index=False, encoding="utf-8-sig")
    bands_df.to_csv(experiment_dir / "0327_posterior_predictive_bands.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(experiment_dir / "0327_posterior_predictive_coverage.csv", index=False, encoding="utf-8-sig")
    (experiment_dir / "0327_AM调优汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (experiment_dir / "0327_AM参数.json").write_text(json.dumps(summary["config"], ensure_ascii=False, indent=2), encoding="utf-8")


def run_one_experiment(experiment_name: str, overrides: dict[str, float | int]) -> dict:
    ensure_directories()
    validate_generated_data_exists()
    generated = load_generated_data()
    dataset = build_dataset(generated)
    initial_ppd_df = load_initial_ppd()
    config = build_am_only_config(overrides)

    experiment_dir = RESULT_DIR / "AM调优" / experiment_name
    experiment_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(INITIAL_PPD_PATH, experiment_dir / "0327_initial_PPD.csv")

    start_wall = datetime.now().isoformat(timespec="seconds")
    start_perf = time.perf_counter()
    print(f"[AM-TUNE] start {experiment_name} @ {start_wall}", flush=True)
    print(f"[AM-TUNE] config: chains={config.am_chain_count}, samples={config.am_samples_per_chain}, warmup={config.am_warmup}, adapt_start={config.am_adapt_start}, init_cov={config.am_initial_covariance}", flush=True)

    am_df = run_am(dataset, generated, initial_ppd_df, config)
    ppd_samples_df, posterior_df = extract_ppd(am_df, config)
    bands_df, coverage_df = posterior_predictive_validation(dataset, generated, ppd_samples_df, config)

    posterior_median_map = dict(zip(posterior_df["节点"], posterior_df["后验中位数"]))
    posterior_median_shares = np.array([posterior_median_map[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_median_shares = posterior_median_shares / max(float(posterior_median_shares.sum()), 1e-12)

    top_post_row = am_df.sort_values("log_posterior", ascending=False).iloc[0]
    posterior_best_shares = np.array([top_post_row[node] for node in CANDIDATE_NODES], dtype=float)
    posterior_best_shares = posterior_best_shares / max(float(posterior_best_shares.sum()), 1e-12)

    runtime_inp = runtime_model_path(0)
    posterior_median_eval = evaluate_shares(posterior_median_shares, dataset, str(runtime_inp))
    posterior_best_eval = evaluate_shares(posterior_best_shares, dataset, str(runtime_inp))

    end_perf = time.perf_counter()
    summary = {
        "experiment_name": experiment_name,
        "start_time": start_wall,
        "end_time": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": end_perf - start_perf,
        "config": asdict(config),
        "initial_ppd_count": int(len(initial_ppd_df)),
        "posterior_sample_count": int(len(ppd_samples_df)),
        "posterior_median_nse": float(posterior_median_eval["mean_nse"]),
        "posterior_best_nse": float(posterior_best_eval["mean_nse"]),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "accept_rate_by_chain": {str(int(k)): float(v) for k, v in am_df.groupby("chain")["accepted"].mean().items()},
        "predicted_top5": posterior_df.head(5)["节点"].tolist(),
    }
    save_experiment_outputs(experiment_dir, am_df, ppd_samples_df, posterior_df, bands_df, coverage_df, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary


def save_experiment_table() -> None:
    rows = []
    for name, overrides in AM_EXPERIMENTS.items():
        row = {"experiment_name": name}
        row.update(overrides)
        rows.append(row)
    df = pd.DataFrame(rows)
    out_dir = RESULT_DIR / "AM调优"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "0327_AM调优参数表.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    save_experiment_table()
    all_summaries = []
    for name, overrides in AM_EXPERIMENTS.items():
        all_summaries.append(run_one_experiment(name, overrides))
    out_dir = RESULT_DIR / "AM调优"
    (out_dir / "0327_AM调优总汇总.json").write_text(json.dumps(all_summaries, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
