# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import timedelta

import numpy as np
import pandas as pd
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute

from 公共配置与数据 import (
    BASELINE_MONITOR_CSV,
    CANDIDATE_NODES,
    DRY_OUT,
    EVENT_MONITOR_CSV,
    MONITOR_NODES,
    OBSERVED_DELTA_CSV,
    OUTFALL_NODE,
    OUTLET_SERIES_CSV,
    RESULT_DIR,
    SCENARIO_JSON,
    STEP_SECONDS,
    TIMESERIES_DETAIL_CSV,
    TOTAL_PROCESS_CSV,
    TOTAL_QR_M3,
    TOTAL_STEPS,
    TRUTH_INJECTION_CSV,
    TRUTH_INJECTION_NODES,
    TRUTH_TOTAL_VOLUME_M3,
    ensure_directories,
    load_generated_data,
    runtime_model_path,
)
from 模型仿真与评估 import build_dataset, evaluate_shares


EVENT_STEP_COUNT = TOTAL_STEPS - 1
EVENT_HOURS = np.arange(1, TOTAL_STEPS, dtype=float) * STEP_SECONDS / 3600.0
INJECTION_STEP_COUNT = int(24 * 3600 / STEP_SECONDS)


def build_synthetic_rainfall_shape(target_hours: np.ndarray) -> np.ndarray:
    shape = np.zeros_like(target_hours, dtype=float)
    rise_mask = (target_hours > 0.0) & (target_hours <= 8.0)
    peak_mask = (target_hours > 8.0) & (target_hours <= 16.0)
    fall_mask = (target_hours > 16.0) & (target_hours <= 24.0)

    # 0-8 h: linear rise from 0 to 1
    shape[rise_mask] = target_hours[rise_mask] / 8.0
    # 8-16 h: stay at peak
    shape[peak_mask] = 1.0
    # 16-24 h: linear decay from 1 to 0
    shape[fall_mask] = (24.0 - target_hours[fall_mask]) / 8.0
    return np.maximum(shape, 0.0)


def build_total_process() -> pd.DataFrame:
    target_hours = EVENT_HOURS[:INJECTION_STEP_COUNT]
    target_y = build_synthetic_rainfall_shape(target_hours)
    target_y = np.maximum(target_y, 1e-12)
    weights = target_y / target_y.sum()
    inject_volume = TOTAL_QR_M3 * weights

    total_volume = np.zeros(EVENT_STEP_COUNT, dtype=float)
    total_strength = np.zeros(EVENT_STEP_COUNT, dtype=float)
    total_weight = np.zeros(EVENT_STEP_COUNT, dtype=float)
    total_volume[:INJECTION_STEP_COUNT] = inject_volume
    total_strength[:INJECTION_STEP_COUNT] = target_y
    total_weight[:INJECTION_STEP_COUNT] = weights

    synthetic_hour_index = np.full(EVENT_STEP_COUNT, -1, dtype=int)
    synthetic_hour_index[:INJECTION_STEP_COUNT] = np.floor(target_hours).astype(int)

    return pd.DataFrame(
        {
            "步号": np.arange(EVENT_STEP_COUNT, dtype=int),
            "相对小时": EVENT_HOURS,
            "原始小时序号": synthetic_hour_index,
            "原始小时插值强度": total_strength,
            "时间权重": total_weight,
            "总入流体积_m3": total_volume,
            "总入流量_CMS": total_volume / STEP_SECONDS,
        }
    )


def interpolate_series_to_event_grid(series_items: list[tuple], target_hours: np.ndarray) -> np.ndarray:
    if not series_items:
        raise RuntimeError("空时间序列，无法插值")
    zero_time = series_items[0][0] - timedelta(hours=1)
    source_x = np.array([(t - zero_time).total_seconds() / 3600.0 for t, _ in series_items], dtype=float)
    source_y = np.array([v for _, v in series_items], dtype=float)
    return np.interp(target_hours, source_x, source_y, left=float(source_y[0]), right=float(source_y[-1]))


def extract_baseline_on_event_grid() -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_monitor = pd.DataFrame({"步号": np.arange(EVENT_STEP_COUNT, dtype=int), "相对小时": EVENT_HOURS})
    baseline_outlet = baseline_monitor[["步号", "相对小时"]].copy()

    with Output(str(DRY_OUT)) as out:
        for node in MONITOR_NODES:
            items = list(out.node_series(node, NodeAttribute.TOTAL_INFLOW).items())
            baseline_monitor[node] = interpolate_series_to_event_grid(items, EVENT_HOURS)

        outfall_items = list(out.node_series(OUTFALL_NODE, NodeAttribute.TOTAL_INFLOW).items())
        baseline_outlet["排口基线_CMS"] = interpolate_series_to_event_grid(outfall_items, EVENT_HOURS)

    return baseline_monitor, baseline_outlet


def build_truth_injection(total_process: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    truth_shares = np.zeros(len(CANDIDATE_NODES), dtype=float)
    total_truth = float(sum(TRUTH_TOTAL_VOLUME_M3.values()))

    rows: list[dict] = []
    total_cms = total_process["总入流量_CMS"].to_numpy(dtype=float)
    total_volume = total_process["总入流体积_m3"].to_numpy(dtype=float)

    for idx, node in enumerate(CANDIDATE_NODES):
        truth_shares[idx] = TRUTH_TOTAL_VOLUME_M3.get(node, 0.0) / total_truth

    for node in TRUTH_INJECTION_NODES:
        share = TRUTH_TOTAL_VOLUME_M3[node] / total_truth
        node_cms = total_cms * share
        node_volume = total_volume * share
        for step_idx, rel_hour in enumerate(total_process["相对小时"].to_numpy(dtype=float)):
            rows.append(
                {
                    "节点": node,
                    "步号": int(step_idx),
                    "相对小时": float(rel_hour),
                    "节点总量占比": float(share),
                    "该步体积_m3": float(node_volume[step_idx]),
                    "注入流量_CMS": float(node_cms[step_idx]),
                }
            )

    return pd.DataFrame(rows), truth_shares


def save_generated_data(
    total_process: pd.DataFrame,
    truth_df: pd.DataFrame,
    baseline_monitor: pd.DataFrame,
    event_monitor: pd.DataFrame,
    observed_delta: pd.DataFrame,
    outlet_df: pd.DataFrame,
) -> None:
    total_process.to_csv(TOTAL_PROCESS_CSV, index=False, encoding="utf-8-sig")
    truth_df.to_csv(TRUTH_INJECTION_CSV, index=False, encoding="utf-8-sig")
    baseline_monitor.to_csv(BASELINE_MONITOR_CSV, index=False, encoding="utf-8-sig")
    event_monitor.to_csv(EVENT_MONITOR_CSV, index=False, encoding="utf-8-sig")
    observed_delta.to_csv(OBSERVED_DELTA_CSV, index=False, encoding="utf-8-sig")
    outlet_df.to_csv(OUTLET_SERIES_CSV, index=False, encoding="utf-8-sig")


def validate_truth_pipeline(truth_shares: np.ndarray) -> dict:
    generated = load_generated_data()
    dataset = build_dataset(generated)
    result = evaluate_shares(truth_shares, dataset, str(runtime_model_path(0)))

    obs = dataset.observed_delta.copy().reset_index(drop=True)
    sim = result["sim_delta"].copy().reset_index(drop=True)
    common = min(len(obs), len(sim))
    obs = obs.iloc[:common].reset_index(drop=True)
    sim = sim.iloc[:common].reset_index(drop=True)

    event_saved = generated["event_monitor"].copy().iloc[:common].reset_index(drop=True)
    event_eval = result["event_monitor"].copy().iloc[:common].reset_index(drop=True)

    per_node = {}
    event_consistency = {}
    for node in MONITOR_NODES:
        node_sse = float(((obs[node] - sim[node]) ** 2).sum())
        denom = float(((obs[node] - obs[node].mean()) ** 2).sum())
        node_nse = (1.0 - node_sse / denom) if denom > 1e-12 else None
        per_node[node] = {
            "sse": node_sse,
            "nse": node_nse,
            "obs_max": float(obs[node].max()),
            "sim_max": float(sim[node].max()),
        }
        diff = (event_saved[node] - event_eval[node]).abs()
        event_consistency[node] = {
            "max_abs_event_diff": float(diff.max()),
            "mean_abs_event_diff": float(diff.mean()),
        }

    return {
        "truth_shares": {node: float(truth_shares[i]) for i, node in enumerate(CANDIDATE_NODES) if truth_shares[i] > 0},
        "mean_nse": float(result["mean_nse"]),
        "sse": float(result["sse"]),
        "per_node": per_node,
        "event_consistency": event_consistency,
    }


def main() -> None:
    ensure_directories()

    total_process = build_total_process()
    baseline_monitor, baseline_outlet = extract_baseline_on_event_grid()
    truth_df, truth_shares = build_truth_injection(total_process)

    # First pass: generate a canonical truth-event through the same evaluator
    # path used by GA/AM, then save an initial on-disk dataset.
    placeholder_event = baseline_monitor.copy()
    placeholder_delta = baseline_monitor.copy()
    for node in MONITOR_NODES:
        placeholder_delta[node] = 0.0

    temp_generated = {
        "total_process": total_process.copy(),
        "truth_injection": truth_df.copy(),
        "baseline_monitor": baseline_monitor.copy(),
        "event_monitor": placeholder_event,
        "observed_delta": placeholder_delta,
        "outlet": baseline_outlet.copy(),
    }
    canonical_dataset = build_dataset(temp_generated)
    canonical_result = evaluate_shares(truth_shares, canonical_dataset, str(runtime_model_path(0)))

    event_monitor = canonical_result["event_monitor"].copy()
    observed_delta = canonical_result["sim_delta"].copy()
    event_outlet = canonical_result["event_outlet"].copy()

    common_len = min(
        len(total_process),
        len(baseline_monitor),
        len(baseline_outlet),
        len(event_monitor),
        len(observed_delta),
        len(event_outlet),
    )
    total_process = total_process.iloc[:common_len].reset_index(drop=True)
    baseline_monitor = baseline_monitor.iloc[:common_len].reset_index(drop=True)
    baseline_outlet = baseline_outlet.iloc[:common_len].reset_index(drop=True)
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    observed_delta = observed_delta.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)
    truth_df = truth_df[truth_df["步号"] < common_len].copy().reset_index(drop=True)

    outlet_df = baseline_outlet.copy()
    outlet_df["排口事件_CMS"] = event_outlet["排口连边流量_CMS"].to_numpy(dtype=float)
    outlet_df["排口增量_CMS"] = outlet_df["排口事件_CMS"] - outlet_df["排口基线_CMS"]

    save_generated_data(total_process, truth_df, baseline_monitor, event_monitor, observed_delta, outlet_df)

    # Second pass: reload exactly what GA/AM will later read from disk, then run
    # truth once more and overwrite event/delta/outlet with that final canonical
    # result. This removes any remaining in-memory vs on-disk chain mismatch.
    reloaded = load_generated_data()
    reloaded_dataset = build_dataset(reloaded)
    final_truth = evaluate_shares(truth_shares, reloaded_dataset, str(runtime_model_path(0)))

    final_event_monitor = final_truth["event_monitor"].copy().iloc[:common_len].reset_index(drop=True)
    final_observed_delta = final_truth["sim_delta"].copy().iloc[:common_len].reset_index(drop=True)
    final_event_outlet = final_truth["event_outlet"].copy().iloc[:common_len].reset_index(drop=True)

    final_outlet_df = baseline_outlet.copy()
    final_outlet_df["排口事件_CMS"] = final_event_outlet["排口连边流量_CMS"].to_numpy(dtype=float)
    final_outlet_df["排口增量_CMS"] = final_outlet_df["排口事件_CMS"] - final_outlet_df["排口基线_CMS"]

    save_generated_data(total_process, truth_df, baseline_monitor, final_event_monitor, final_observed_delta, final_outlet_df)

    summary = {
        "time_grid_steps": int(common_len),
        "time_grid_start_hour": float(total_process["相对小时"].iloc[0]),
        "time_grid_end_hour": float(total_process["相对小时"].iloc[-1]),
        "injection_steps": int((total_process["总入流量_CMS"] > 0).sum()),
        "Qr_m3": float(total_process["总入流体积_m3"].sum()),
    }
    SCENARIO_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULT_DIR / "0327_修正数据链汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    truth_validation = validate_truth_pipeline(truth_shares)
    (RESULT_DIR / "0327_真值回灌验证.json").write_text(json.dumps(truth_validation, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"data_summary": summary, "truth_validation": truth_validation}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
