"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: simulation_0416.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

﻿from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from config_0416 import CANDIDATE_NODES, MONITOR_NODES, OUTFALL_NODE, STEP_SECONDS, runtime_model_path


@dataclass
class ExperimentDataset:
    total_process: pd.DataFrame
    truth_injection: pd.DataFrame
    baseline_monitor: pd.DataFrame
    event_monitor: pd.DataFrame
    observed_delta: pd.DataFrame
    outlet: pd.DataFrame
    qr_m3: float


_GLOBAL_GENERATED_DATA: dict[str, pd.DataFrame] | None = None
_GLOBAL_RUNTIME_INP: str | None = None
_GLOBAL_SCORE_CACHE: dict[tuple[float, ...], dict[str, Any]] = {}
_RUNTIME_TEMPLATE_CACHE: dict[str, list[str]] = {}


def build_dataset(generated_data: dict[str, pd.DataFrame]) -> ExperimentDataset:
    total_process = generated_data["total_process"].copy()
    return ExperimentDataset(
        total_process=total_process,
        truth_injection=generated_data["truth_injection"].copy(),
        baseline_monitor=generated_data["baseline_monitor"].copy(),
        event_monitor=generated_data["event_monitor"].copy(),
        observed_delta=generated_data["observed_delta"].copy(),
        outlet=generated_data["outlet"].copy(),
        qr_m3=float(total_process["total_volume_m3"].sum()),
    )


def simplex_project(vector: np.ndarray) -> np.ndarray:
    x = np.asarray(vector, dtype=float).copy()
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    if np.all(x <= 0):
        return np.ones_like(x) / len(x)
    sorted_x = np.sort(x)[::-1]
    cssv = np.cumsum(sorted_x) - 1
    idx = np.arange(1, len(x) + 1)
    cond = sorted_x - cssv / idx > 0
    rho = idx[cond][-1]
    theta = cssv[cond][-1] / rho
    projected = np.maximum(x - theta, 0)
    total = projected.sum()
    if total <= 0:
        return np.ones_like(x) / len(x)
    return projected / total


def find_outfall_link(inp_path: str, outfall_node: str = OUTFALL_NODE) -> str:
    current_section = ""
    with open(inp_path, "r", encoding="gbk", errors="ignore") as file:
        for line in file:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1].upper()
                continue
            if current_section != "CONDUITS" or not stripped or stripped.startswith(";"):
                continue
            parts = stripped.split()
            if len(parts) >= 3 and parts[2] == outfall_node:
                return parts[0]
    raise ValueError(f"Unable to find link flowing into outfall {outfall_node}")


def shares_to_inflow_series(shares: np.ndarray, total_process: pd.DataFrame) -> dict[str, np.ndarray]:
    weights = simplex_project(shares)
    total_cms = total_process["total_flow_cms"].to_numpy(dtype=float)
    return {node: total_cms * weights[idx] for idx, node in enumerate(CANDIDATE_NODES)}


def _format_time_label(relative_hour: float) -> str:
    total_minutes = int(round(relative_hour * 60.0))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _shares_key(shares: np.ndarray, decimals: int = 4) -> tuple[float, ...]:
    arr = simplex_project(np.asarray(shares, dtype=float)).reshape(-1)
    return tuple(float(v) for v in np.round(arr, decimals=max(0, int(decimals))))


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "shares": np.asarray(result["shares"], dtype=float).copy(),
        "mean_nse": float(result["mean_nse"]),
        "sse": float(result["sse"]),
    }


def _is_runtime_sim_row(section: str, stripped: str) -> bool:
    if not stripped or stripped.startswith(";"):
        return False
    parts = stripped.split()
    if section == "INFLOWS" and len(parts) >= 3:
        return parts[2].startswith("TS_") and parts[2].endswith("_SIM")
    if section == "TIMESERIES" and parts:
        return parts[0].startswith("TS_") and parts[0].endswith("_SIM")
    return False


def _runtime_template_lines(runtime_inp: str) -> list[str]:
    cached = _RUNTIME_TEMPLATE_CACHE.get(runtime_inp)
    if cached is not None:
        return cached

    section = ""
    clean_lines: list[str] = []
    for line in Path(runtime_inp).read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            clean_lines.append(line)
            continue
        if _is_runtime_sim_row(section, stripped):
            continue
        clean_lines.append(line)
    _RUNTIME_TEMPLATE_CACHE[runtime_inp] = clean_lines
    return clean_lines


def _inject_timeseries_into_inp(runtime_inp: str, injection_series: dict[str, np.ndarray], total_process: pd.DataFrame) -> None:
    inp_path = Path(runtime_inp)
    lines = _runtime_template_lines(runtime_inp)
    time_labels = [_format_time_label(v) for v in total_process["relative_hour"].to_numpy(dtype=float)]
    injected_ts_names = {node: f"TS_{node}_SIM" for node in injection_series}

    section = ""
    inflow_payload: list[str] = []
    timeseries_payload: list[str] = []

    for node_name, series in injection_series.items():
        ts_name = injected_ts_names[node_name]
        if np.allclose(series, 0.0):
            continue
        inflow_payload.append(f"{node_name:<16} FLOW             {ts_name:<16} FLOW     1.0      1.0      0.0")
        for label, value in zip(time_labels, series):
            timeseries_payload.append(f"{ts_name:<24} {label:<10} {float(value):.12f}")

    output_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            output_lines.append(line)
            continue
        output_lines.append(line)
        if section == "INFLOWS" and stripped.startswith(";;--------------") and inflow_payload:
            output_lines.extend(inflow_payload)
            inflow_payload = []
        if section == "TIMESERIES" and stripped.startswith(";;--------------") and timeseries_payload:
            output_lines.extend(timeseries_payload)
            timeseries_payload = []

    if inflow_payload or timeseries_payload:
        raise RuntimeError("Failed to inject runtime inflow/timeseries into INP sections")

    inp_path.write_text("\n".join(output_lines) + "\n", encoding="gbk")


def run_event_simulation(
    runtime_inp: str,
    injection_series: dict[str, np.ndarray],
    total_process: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _inject_timeseries_into_inp(runtime_inp, injection_series, total_process)
    outlet_link_name = find_outfall_link(runtime_inp)
    monitor_rows: list[dict[str, Any]] = []
    outlet_rows: list[dict[str, Any]] = []
    with Simulation(runtime_inp) as sim:
        sim.step_advance(STEP_SECONDS)
        nodes = Nodes(sim)
        links = Links(sim)
        node_handles = {name: nodes[name] for name in set(MONITOR_NODES)}
        outlet_link = links[outlet_link_name]
        series_length = len(total_process)
        for step_idx, _ in enumerate(sim):
            if step_idx >= series_length:
                break
            row = {"step": step_idx, "time": sim.current_time}
            for monitor in MONITOR_NODES:
                row[monitor] = float(node_handles[monitor].total_inflow)
            monitor_rows.append(row)
            outlet_rows.append(
                {
                    "step": step_idx,
                    "time": sim.current_time,
                    "outfall_link_flow_cms": float(outlet_link.flow),
                }
            )
    return pd.DataFrame(monitor_rows), pd.DataFrame(outlet_rows)


def evaluate_shares(shares: np.ndarray, dataset: ExperimentDataset, runtime_inp: str, include_series: bool = True) -> dict[str, Any]:
    injection_series = shares_to_inflow_series(shares, dataset.total_process)
    event_monitor, event_outlet = run_event_simulation(runtime_inp, injection_series, dataset.total_process)

    expected_len = min(
        len(dataset.baseline_monitor),
        len(dataset.observed_delta),
        len(dataset.total_process),
        len(dataset.outlet),
    )
    if len(event_monitor) < expected_len or len(event_outlet) < expected_len:
        fallback_event = dataset.baseline_monitor.iloc[:expected_len].copy().reset_index(drop=True)
        fallback_delta = fallback_event.copy()
        for node_name in MONITOR_NODES:
            fallback_delta[node_name] = 0.0
        fallback_outlet = dataset.outlet.iloc[:expected_len].copy().reset_index(drop=True)
        result = {
            "shares": simplex_project(shares),
            "mean_nse": -999.0,
            "sse": 1.0e12,
            "sim_delta": fallback_delta,
            "event_monitor": fallback_event,
            "event_outlet": fallback_outlet,
        }
        return result if include_series else compact_result(result)

    common_len = min(
        len(event_monitor),
        len(event_outlet),
        expected_len,
    )
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)

    sim_delta_payload: dict[str, Any] = {
        "step": event_monitor["step"].to_numpy(dtype=int),
        "time": event_monitor["time"].to_numpy(),
    }
    for node in MONITOR_NODES:
        sim_delta_payload[node] = event_monitor[node].to_numpy(dtype=float) - dataset.baseline_monitor[node].to_numpy(dtype=float)[:common_len]
    sim_delta = pd.DataFrame(sim_delta_payload)

    nse_list = []
    sse = 0.0
    for node in MONITOR_NODES:
        obs = dataset.observed_delta[node].to_numpy(dtype=float)[:common_len]
        sim = sim_delta[node].to_numpy(dtype=float)
        if (not np.all(np.isfinite(obs))) or (not np.all(np.isfinite(sim))):
            result = {
                "shares": simplex_project(shares),
                "mean_nse": -999.0,
                "sse": 1.0e12,
                "sim_delta": sim_delta,
                "event_monitor": event_monitor,
                "event_outlet": event_outlet,
            }
            return result if include_series else compact_result(result)
        denom = float(np.sum((obs - np.mean(obs)) ** 2))
        node_sse = float(np.sum((obs - sim) ** 2))
        sse += node_sse
        nse = (1.0 - node_sse / denom) if denom > 1e-12 else (1.0 if node_sse <= 1e-12 else -999.0)
        nse_list.append(nse)

    mean_nse = float(np.mean(nse_list))
    sim_delta["relative_hour"] = dataset.total_process["relative_hour"].to_numpy(dtype=float)[:common_len]
    event_outlet = event_outlet.copy()
    event_outlet["relative_hour"] = dataset.total_process["relative_hour"].to_numpy(dtype=float)[:common_len]
    result = {
        "shares": simplex_project(shares),
        "mean_nse": mean_nse,
        "sse": sse,
        "sim_delta": sim_delta,
        "event_monitor": event_monitor,
        "event_outlet": event_outlet,
    }
    return result if include_series else compact_result(result)


def worker_initializer(generated_data: dict[str, pd.DataFrame]) -> None:
    global _GLOBAL_GENERATED_DATA, _GLOBAL_RUNTIME_INP, _GLOBAL_SCORE_CACHE, _RUNTIME_TEMPLATE_CACHE
    _GLOBAL_GENERATED_DATA = generated_data
    _GLOBAL_RUNTIME_INP = str(runtime_model_path(os.getpid(), force=True))
    _GLOBAL_SCORE_CACHE = {}
    _RUNTIME_TEMPLATE_CACHE = {}


def worker_evaluate(task: tuple[int, np.ndarray] | tuple[int, np.ndarray, bool] | tuple[int, np.ndarray, bool, int]) -> dict[str, Any]:
    if _GLOBAL_GENERATED_DATA is None:
        raise RuntimeError("Worker not initialized")
    if len(task) == 2:
        _, shares = task
        include_series = True
        cache_decimals = 4
    elif len(task) == 3:
        _, shares, include_series = task
        cache_decimals = 4
    else:
        _, shares, include_series, cache_decimals = task
    dataset = build_dataset(_GLOBAL_GENERATED_DATA)
    runtime_inp = _GLOBAL_RUNTIME_INP or str(runtime_model_path(os.getpid()))
    if not include_series:
        key = _shares_key(shares, cache_decimals)
        cached = _GLOBAL_SCORE_CACHE.get(key)
        if cached is not None:
            result = compact_result(cached)
            result["cache_hit"] = True
            return result
        result = evaluate_shares(shares, dataset, runtime_inp, include_series=False)
        _GLOBAL_SCORE_CACHE[key] = compact_result(result)
        result["cache_hit"] = False
        return result
    return evaluate_shares(shares, dataset, runtime_inp, include_series=True)

