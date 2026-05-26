from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import paper_route_full_dim as model


RESULT_DIR = Path(r"E:\PY\LSTM\swmm_case\paper_route_full_dim_results\midscale_ppd")


def run_chain(
    evaluator: model.pilot.PaperEvaluator,
    initial_ppd_df: pd.DataFrame,
    config: model.Config,
    chain_id: int,
) -> pd.DataFrame:
    # 多链 AM 的目的是减少“单条链偶然卡在局部区域”的风险。
    chain_seed = model.DEFAULT_SEED + chain_id
    np.random.seed(chain_seed)
    posterior = model.am_full_dim(evaluator, initial_ppd_df, config)
    posterior["chain"] = chain_id
    return posterior


def main() -> None:
    # 这一版参数故意收小，目标是让 PyCharm 里更容易跑通。
    # 在注水规模放大后，先用更轻量的 GA/AM 验证整条链路。
    np.random.seed(model.DEFAULT_SEED)
    config = model.Config()
    config.result_dir = RESULT_DIR
    config.truth_scale_factor = 2.0
    config.ga_pop_count = 2
    config.ga_pop_size = 5
    config.ga_generations = 3
    config.ga_migration_interval = 2
    config.initial_ppd_keep_ratio = 0.50
    config.am_samples = 18
    config.am_burn_in = 5
    config.adaptive_start = 6
    config.ensure_dirs()

    evaluator = model.pilot.PaperEvaluator(
        model.pilot.Config(
            result_dir=config.result_dir,
            pilot_candidate_limit=config.pilot_candidate_limit,
            eval_stride_seconds=config.eval_stride_seconds,
            truth_scale_factor=config.truth_scale_factor,
        )
    )
    scan_df = model.pilot.run_single_scan(evaluator)
    q_r = float(sum(np.sum(evaluator.truth_templates[node]) for node in model.pilot.TRUTH_NODES) * config.eval_stride_seconds)

    ga_best, ga_history, merged_last_gen_df, all_generation_df, initial_ppd_df = model.ga_search_full_dim(evaluator, scan_df, config)
    posterior_chains = [run_chain(evaluator, initial_ppd_df, config, chain_id) for chain_id in range(1, 3)]
    posterior = pd.concat(posterior_chains, ignore_index=True)
    tail_parts = []
    for chain_id, chain_df in enumerate(posterior_chains, start=1):
        tail_df = chain_df.iloc[config.am_burn_in :].copy()
        tail_df["chain"] = chain_id
        tail_parts.append(tail_df)
    tail = pd.concat(tail_parts, ignore_index=True)
    final_result, final_series = model.choose_final_solution(
        evaluator,
        ga_best,
        initial_ppd_df,
        posterior,
        tail,
        evaluator.candidate_nodes,
    )
    weights_df = model.weights_from_tail(tail, evaluator.candidate_nodes)
    tau = float(weights_df["tau"].iloc[0])
    weights_df["final_share"] = weights_df["node"].map(final_series.to_dict())
    weights_df["final_is_active"] = weights_df["final_share"] >= tau

    predicted_nodes = set(weights_df.loc[weights_df["final_is_active"], "node"].tolist())
    metrics = model.pilot.classification_metrics(evaluator.candidate_nodes, set(model.pilot.TRUTH_NODES), predicted_nodes)
    true_share_map = {
        node: float(np.sum(evaluator.truth_templates[node])) / max(float(np.sum(evaluator.common_pattern)), 1e-8)
        for node in model.pilot.TRUTH_NODES
    }
    pred_share_map = final_series.to_dict()
    mae_all_nodes = float(np.mean([abs(pred_share_map.get(node, 0.0) - true_share_map.get(node, 0.0)) for node in evaluator.candidate_nodes]))
    mae_truth_nodes = float(np.mean([abs(pred_share_map.get(node, 0.0) - true_share_map.get(node, 0.0)) for node in model.pilot.TRUTH_NODES]))

    summary = {
        "candidate_count": len(evaluator.candidate_nodes),
        "candidate_nodes": evaluator.candidate_nodes,
        "truth_nodes": model.pilot.TRUTH_NODES,
        "predicted_nodes": sorted(predicted_nodes),
        "merged_last_generation_size": int(len(merged_last_gen_df)),
        "initial_ppd_size": int(len(initial_ppd_df)),
        "final_mean_nse": float(final_result["mean_nse"]),
        "final_sse": float(final_result["sse"]),
        "final_solution_name": final_result["solution_name"],
        "truth_scale_factor": config.truth_scale_factor,
        "q_r": q_r,
        "tau": tau,
        "acc": float(metrics["acc"]),
        "mcc": float(metrics["mcc"]),
        "mae_all_nodes": mae_all_nodes,
        "mae_truth_nodes": mae_truth_nodes,
        "am_accept_rate_mean": float(np.mean([chain_df["accepted_rate"].iloc[-1] for chain_df in posterior_chains])),
        "am_accept_rate_min": float(np.min([chain_df["accepted_rate"].iloc[-1] for chain_df in posterior_chains])),
        "am_accept_rate_max": float(np.max([chain_df["accepted_rate"].iloc[-1] for chain_df in posterior_chains])),
        "am_accept_rate": float(np.mean([chain_df["accepted_rate"].iloc[-1] for chain_df in posterior_chains])),
        "proposal_scale_sd": float(posterior_chains[0]["proposal_scale_sd"].iloc[-1]),
        "final_cov_trace_mean": float(np.mean([chain_df["cov_trace"].iloc[-1] for chain_df in posterior_chains])),
        "chain_count": len(posterior_chains),
    }

    (config.result_dir / "full_dim_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    ga_history.to_csv(config.result_dir / "full_dim_ga_history.csv", index=False, encoding="utf-8-sig")
    all_generation_df.to_csv(config.result_dir / "full_dim_ga_population.csv", index=False, encoding="utf-8-sig")
    merged_last_gen_df.to_csv(config.result_dir / "full_dim_merged_last_generation.csv", index=False, encoding="utf-8-sig")
    initial_ppd_df.to_csv(config.result_dir / "full_dim_initial_ppd.csv", index=False, encoding="utf-8-sig")
    scan_df.to_csv(config.result_dir / "full_dim_single_scan.csv", index=False, encoding="utf-8-sig")
    posterior.to_csv(config.result_dir / "full_dim_am_samples.csv", index=False, encoding="utf-8-sig")
    weights_df.to_csv(config.result_dir / "full_dim_weights.csv", index=False, encoding="utf-8-sig")
    final_result["delta"].to_csv(config.result_dir / "full_dim_fitted_delta.csv", index=False, encoding="utf-8-sig")
    evaluator.observed_delta.to_csv(config.result_dir / "full_dim_truth_delta.csv", index=False, encoding="utf-8-sig")
    model.pilot.build_monitor_dashboard(evaluator.observed_delta, final_result["delta"], config.result_dir / "full_dim_monitor_fit.html")
    model.build_posterior_bar(weights_df, config.result_dir / "full_dim_posterior_bar.html")
    model.build_convergence_figure(ga_history, posterior, config.result_dir / "full_dim_convergence.html")
    model.write_report(summary, weights_df, scan_df, config.result_dir / "full_dim_report.md")
    model.write_overview(summary, weights_df, config.result_dir / "full_dim_overview.html")
    print("Mid-scale validation complete:", config.result_dir)
    print(summary)


if __name__ == "__main__":
    main()
