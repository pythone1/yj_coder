from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config_0416 import CANDIDATE_NODES
from simulation_0416 import ExperimentDataset, evaluate_shares, simplex_project


def posterior_median_shares(posterior_df: pd.DataFrame) -> np.ndarray:
    median_map = dict(zip(posterior_df["node"], posterior_df["posterior_median"]))
    return simplex_project(np.array([median_map[node] for node in CANDIDATE_NODES], dtype=float))


def posterior_best_shares(am_df: pd.DataFrame) -> np.ndarray:
    target_col = "acceptance_log_target" if "acceptance_log_target" in am_df.columns else "log_like"
    top_target_row = am_df.sort_values(target_col, ascending=False).iloc[0]
    return simplex_project(np.array([top_target_row[node] for node in CANDIDATE_NODES], dtype=float))


def save_solution_outputs(
    output_dir: Path,
    solutions: dict[str, np.ndarray],
    dataset: ExperimentDataset,
    runtime_inp: str,
) -> tuple[dict[str, dict[str, float]], str]:
    evaluations: dict[str, dict[str, Any]] = {}
    score_rows = []
    for name, shares in solutions.items():
        result = evaluate_shares(shares, dataset, runtime_inp)
        evaluations[name] = result
        result["sim_delta"].to_csv(output_dir / f"0520_solution_{name}_delta.csv", index=False, encoding="utf-8-sig")
        result["event_monitor"].to_csv(output_dir / f"0520_solution_{name}_event_monitor.csv", index=False, encoding="utf-8-sig")
        result["event_outlet"].to_csv(output_dir / f"0520_solution_{name}_outlet.csv", index=False, encoding="utf-8-sig")
        score_rows.append(
            {
                "solution": name,
                "mean_nse": float(result["mean_nse"]),
                "sse": float(result["sse"]),
                "primary_role": (
                    "GA objective: maximize mean_nse"
                    if name == "ga_best"
                    else "AM selected by acceptance_log_target; with prior off this equals max log_like / min SSE"
                    if name == "posterior_best_map"
                    else "posterior summary: not an optimizer objective"
                ),
            }
        )

    score_df = pd.DataFrame(score_rows)
    score_df.to_csv(output_dir / "0520_solution_scores.csv", index=False, encoding="utf-8-sig")

    share_rows = []
    for name, shares in solutions.items():
        row = {"solution": name}
        projected = simplex_project(shares)
        for idx, node in enumerate(CANDIDATE_NODES):
            row[node] = float(projected[idx])
        share_rows.append(row)
    pd.DataFrame(share_rows).to_csv(output_dir / "0520_solution_shares.csv", index=False, encoding="utf-8-sig")

    # Do not rank GA and AM final products by a single mixed metric.
    # GA is optimized by mean NSE, while AM is accepted by acceptance_log_target.
    # With GA prior disabled in AM acceptance, this target equals the SSE likelihood.
    recommended = "posterior_best_map" if "posterior_best_map" in evaluations else str(score_df.sort_values("sse").iloc[0]["solution"])
    recommended_result = evaluations[recommended]
    recommended_result["sim_delta"].to_csv(output_dir / "0520_final_solution_delta.csv", index=False, encoding="utf-8-sig")
    recommended_result["event_monitor"].to_csv(output_dir / "0520_final_solution_event_monitor.csv", index=False, encoding="utf-8-sig")
    recommended_result["event_outlet"].to_csv(output_dir / "0520_final_solution_outlet.csv", index=False, encoding="utf-8-sig")

    scores = {
        row["solution"]: {"mean_nse": float(row["mean_nse"]), "sse": float(row["sse"])}
        for row in score_rows
    }
    return scores, recommended

