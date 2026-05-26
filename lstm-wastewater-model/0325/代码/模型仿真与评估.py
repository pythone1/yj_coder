from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from 公共配置与数据 import (
    实验配置,
    基线模型路径,
    获取工作模型路径,
    提取数据行,
    读取_inp分段,
    根据总体积生成节点注入序列,
    结果目录,
)


def simplex投影(vector: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    arr = np.maximum(arr, 0.0)
    total = float(arr.sum())
    if total <= 0:
        return np.ones_like(arr) / len(arr)
    return arr / total


@dataclass
class 仿真结果:
    监测流量: pd.DataFrame
    排口流量: pd.Series


def 查找排口上游连边(inp_path: Path, outfall: str) -> str:
    sections = 读取_inp分段(inp_path)
    for row in 提取数据行(sections, "CONDUITS"):
        if len(row) >= 3 and row[2] == outfall:
            return row[0]
    for row in 提取数据行(sections, "PUMPS"):
        if len(row) >= 3 and row[2] == outfall:
            return row[0]
    raise ValueError(f"未找到流向排口 {outfall} 的上游连边。")


def 运行一次仿真(
    inp_path: Path,
    monitor_nodes: Iterable[str],
    outfall: str,
    injection_series: Dict[str, np.ndarray],
    config: 实验配置,
) -> 仿真结果:
    monitor_nodes = list(monitor_nodes)
    outlet_link_name = 查找排口上游连边(inp_path, outfall)

    rows: list[dict] = []
    outlet_values: list[float] = []

    with Simulation(str(inp_path)) as sim:
        sim.step_advance(config.时间步秒数)
        nodes = Nodes(sim)
        links = Links(sim)
        node_objects = {name: nodes[name] for name in set(monitor_nodes) | set(injection_series)}
        outlet_link = links[outlet_link_name]

        for step_index, _ in enumerate(sim):
            if step_index >= config.事件步数:
                break

            for node_name, series in injection_series.items():
                node_objects[node_name].generated_inflow(float(series[step_index]))

            row = {"步号": step_index, "时间": sim.current_time}
            for node_name in monitor_nodes:
                row[node_name] = float(node_objects[node_name].total_inflow)
            rows.append(row)
            outlet_values.append(float(outlet_link.flow))

    monitor_df = pd.DataFrame(rows)
    outlet_series = pd.Series(outlet_values, name=outfall)
    return 仿真结果(监测流量=monitor_df, 排口流量=outlet_series)


@dataclass
class 数据集:
    基线监测: pd.DataFrame
    事件监测: pd.DataFrame
    观测增量: pd.DataFrame
    排口基线: pd.Series
    排口事件: pd.Series
    Qr_m3: float
    真值注入序列: Dict[str, np.ndarray]


def 构造实验数据(config: 实验配置) -> 数据集:
    truth_totals = dict(zip(config.真值注入点, config.真值总体积立方米))
    truth_series = 根据总体积生成节点注入序列(truth_totals, config)

    baseline = 运行一次仿真(
        基线模型路径,
        config.监测点,
        config.唯一排口,
        {},
        config,
    )
    event = 运行一次仿真(
        基线模型路径,
        config.监测点,
        config.唯一排口,
        truth_series,
        config,
    )

    observed_delta = event.监测流量.copy()
    for node_name in config.监测点:
        observed_delta[node_name] = event.监测流量[node_name] - baseline.监测流量[node_name]

    # 当前按用户最新明确要求：Q_R 直接取三处真值注入的总量积分。
    qr = float(sum(np.sum(series) * config.时间步秒数 for series in truth_series.values()))

    return 数据集(
        基线监测=baseline.监测流量,
        事件监测=event.监测流量,
        观测增量=observed_delta,
        排口基线=baseline.排口流量,
        排口事件=event.排口流量,
        Qr_m3=qr,
        真值注入序列=truth_series,
    )


def 计算NSE(obs: np.ndarray, sim: np.ndarray) -> float:
    denominator = np.sum((obs - np.mean(obs)) ** 2)
    if denominator <= 1e-12:
        return -1.0
    numerator = np.sum((obs - sim) ** 2)
    return float(1.0 - numerator / denominator)


class 目标函数评估器:
    def __init__(self, dataset: 数据集, config: 实验配置, model_path: Path | None = None):
        self.dataset = dataset
        self.config = config
        self.model_path = model_path or 基线模型路径
        self._cache: Dict[tuple[float, ...], dict] = {}

    def 评估方案(self, shares: np.ndarray) -> dict:
        shares = simplex投影(shares)
        key = tuple(np.round(shares, 8))
        if key in self._cache:
            return self._cache[key]

        node_totals = {
            node: float(share * self.dataset.Qr_m3)
            for node, share in zip(self.config.候选节点, shares)
            if share > 1e-9
        }
        injection_series = 根据总体积生成节点注入序列(node_totals, self.config)
        sim = 运行一次仿真(
            self.model_path,
            self.config.监测点,
            self.config.唯一排口,
            injection_series,
            self.config,
        )

        sim_delta = sim.监测流量.copy()
        nse_values: list[float] = []
        for node_name in self.config.监测点:
            sim_delta[node_name] = sim.监测流量[node_name] - self.dataset.基线监测[node_name]
            nse_values.append(
                计算NSE(
                    self.dataset.观测增量[node_name].to_numpy(dtype=float),
                    sim_delta[node_name].to_numpy(dtype=float),
                )
            )

        mean_nse = float(np.mean(nse_values))
        sse = float(
            sum(
                np.sum(
                    (
                        self.dataset.观测增量[node_name].to_numpy(dtype=float)
                        - sim_delta[node_name].to_numpy(dtype=float)
                    )
                    ** 2
                )
                for node_name in self.config.监测点
            )
        )

        result = {
            "shares": shares,
            "node_totals": node_totals,
            "mean_nse": mean_nse,
            "loss": 1.0 - mean_nse,
            "sse": sse,
            "sim_delta": sim_delta,
        }
        self._cache[key] = result
        return result


def 保存实验数据(dataset: 数据集) -> None:
    结果目录.mkdir(parents=True, exist_ok=True)
    dataset.基线监测.to_csv(结果目录 / "0325_基线监测.csv", index=False, encoding="utf-8-sig")
    dataset.事件监测.to_csv(结果目录 / "0325_事件监测.csv", index=False, encoding="utf-8-sig")
    dataset.观测增量.to_csv(结果目录 / "0325_观测增量.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        {
            "步号": np.arange(len(dataset.排口基线)),
            "排口基线_CMS": dataset.排口基线,
            "排口事件_CMS": dataset.排口事件,
            "排口增量_CMS": dataset.排口事件 - dataset.排口基线,
        }
    ).to_csv(结果目录 / "0325_排口过程.csv", index=False, encoding="utf-8-sig")


__all__ = [
    "数据集",
    "仿真结果",
    "simplex投影",
    "构造实验数据",
    "计算NSE",
    "目标函数评估器",
    "保存实验数据",
]
