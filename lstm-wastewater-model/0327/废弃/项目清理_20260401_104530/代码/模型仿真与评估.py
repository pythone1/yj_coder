from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from 公共配置与数据 import (
    CANDIDATE_NODES,
    DRY_BASE_COPY,
    MONITOR_NODES,
    OUTFALL_NODE,
    STEP_SECONDS,
    runtime_model_path,
)


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


def build_dataset(generated_data: dict[str, pd.DataFrame]) -> ExperimentDataset:
    total_process = generated_data["total_process"].copy()
    truth_injection = generated_data["truth_injection"].copy()
    baseline_monitor = generated_data["baseline_monitor"].copy()
    event_monitor = generated_data["event_monitor"].copy()
    observed_delta = generated_data["observed_delta"].copy()
    outlet = generated_data["outlet"].copy()
    qr_m3 = float(total_process["总入流体积_m3"].sum())
    return ExperimentDataset(total_process, truth_injection, baseline_monitor, event_monitor, observed_delta, outlet, qr_m3)


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
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].upper()
            continue
        if current_section != "CONDUITS" or not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) >= 3 and parts[2] == outfall_node:
            return parts[0]
    raise ValueError(f"未找到流向排口 {outfall_node} 的连边")


def shares_to_inflow_series(shares: np.ndarray, total_process: pd.DataFrame) -> dict[str, np.ndarray]:
    weights = simplex_project(shares)
    total_cms = total_process["总入流量_CMS"].to_numpy(dtype=float)
    return {node: total_cms * weights[idx] for idx, node in enumerate(CANDIDATE_NODES)}


def run_event_simulation(runtime_inp: str, injection_series: dict[str, np.ndarray]) -> tuple[pd.DataFrame, pd.DataFrame]:
    outlet_link_name = find_outfall_link(runtime_inp)
    monitor_rows: list[dict[str, Any]] = []
    outlet_rows: list[dict[str, Any]] = []
    with Simulation(runtime_inp) as sim:
        sim.step_advance(STEP_SECONDS)
        nodes = Nodes(sim)
        links = Links(sim)
        node_handles = {name: nodes[name] for name in set(MONITOR_NODES) | set(injection_series)}
        outlet_link = links[outlet_link_name]
        series_length = len(next(iter(injection_series.values())))
        for step_idx, _ in enumerate(sim):
            if step_idx >= series_length:
                break
            for node_name, series in injection_series.items():
                node_handles[node_name].generated_inflow(float(series[step_idx]))
            row = {"步号": step_idx, "时间": sim.current_time}
            for monitor in MONITOR_NODES:
                row[monitor] = float(node_handles[monitor].total_inflow)
            monitor_rows.append(row)
            outlet_rows.append(
                {
                    "步号": step_idx,
                    "时间": sim.current_time,
                    "排口连边流量_CMS": float(outlet_link.flow),
                }
            )
    return pd.DataFrame(monitor_rows), pd.DataFrame(outlet_rows)


def evaluate_shares(shares: np.ndarray, dataset: ExperimentDataset, runtime_inp: str) -> dict[str, Any]:
    injection_series = shares_to_inflow_series(shares, dataset.total_process)
    event_monitor, event_outlet = run_event_simulation(runtime_inp, injection_series)

    common_len = min(len(event_monitor), len(dataset.baseline_monitor), len(dataset.observed_delta), len(dataset.total_process), len(dataset.outlet))
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)

    sim_delta = event_monitor.copy()
    for node in MONITOR_NODES:
        sim_delta[node] = event_monitor[node].to_numpy(dtype=float) - dataset.baseline_monitor[node].to_numpy(dtype=float)[:common_len]

    nse_list = []
    sse = 0.0
    for node in MONITOR_NODES:
        obs = dataset.observed_delta[node].to_numpy(dtype=float)[:common_len]
        sim = sim_delta[node].to_numpy(dtype=float)
        denom = float(np.sum((obs - np.mean(obs)) ** 2))
        node_sse = float(np.sum((obs - sim) ** 2))
        sse += node_sse
        if denom <= 1e-12:
            nse = 1.0 if node_sse <= 1e-12 else -np.inf
        else:
            nse = 1.0 - node_sse / denom
        nse_list.append(nse)

    mean_nse = float(np.mean(nse_list))
    event_outlet = event_outlet.copy()
    event_outlet["相对小时"] = dataset.total_process["相对小时"].to_numpy(dtype=float)[:common_len]
    event_outlet["排口基线_CMS"] = dataset.outlet["排口基线_CMS"].to_numpy(dtype=float)[:common_len]
    event_outlet["排口增量_CMS"] = event_outlet["排口连边流量_CMS"] - event_outlet["排口基线_CMS"]
    sim_delta["相对小时"] = dataset.total_process["相对小时"].to_numpy(dtype=float)[:common_len]
    return {
        "shares": simplex_project(shares),
        "mean_nse": mean_nse,
        "sse": sse,
        "sim_delta": sim_delta,
        "event_monitor": event_monitor,
        "event_outlet": event_outlet,
    }


def worker_initializer(generated_data: dict[str, pd.DataFrame]) -> None:
    global _GLOBAL_GENERATED_DATA
    _GLOBAL_GENERATED_DATA = generated_data


def worker_evaluate(task: tuple[int, np.ndarray]) -> dict[str, Any]:
    if _GLOBAL_GENERATED_DATA is None:
        raise RuntimeError("worker 未初始化")
    worker_id, shares = task
    dataset = build_dataset(_GLOBAL_GENERATED_DATA)
    runtime_inp = runtime_model_path(worker_id)
    return evaluate_shares(shares, dataset, str(runtime_inp))


# Chinese aliases for compatibility.
实验数据集 = ExperimentDataset
构建数据集 = build_dataset
simplex投影 = simplex_project
查找排口连边 = find_outfall_link
shares转注水序列 = shares_to_inflow_series
运行事件仿真 = run_event_simulation
评估份额 = evaluate_shares
