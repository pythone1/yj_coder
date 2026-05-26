from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute

from 公共配置与数据 import (
    实验配置,
    复制原始文件到ASCII目录,
    生成基线副本,
    生成数据口径说明,
    确保目录,
    时间序列明细文件,
    真值注入点,
    真值总量_m3,
    总入流量_QR,
    总步数,
    注入步数,
    注入时长小时,
    时间步秒数,
    总时长小时,
    监测点,
    唯一排口,
    原始旱天文件,
    原始有雨文件,
    基线副本,
    旱天结果库,
    总入流过程文件,
    真值注水文件,
    基线监测文件,
    事件监测文件,
    观测增量文件,
    排口过程文件,
    方案文件,
    结果目录,
    运行目录,
)
from 模型仿真与评估 import 运行事件仿真


def copy_timeseries_csv() -> None:
    src = Path(r"E:\PY\LSTM\模型文件有污水量\解析结果\盱眙污水管3（入渗点无雨水量）_时间序列明细.csv")
    if not src.exists():
        raise FileNotFoundError(f"缺少时间序列明细文件：{src}")
    时间序列明细文件.write_bytes(src.read_bytes())


def read_hourly_series(series_name: str = "2天污水量") -> pd.DataFrame:
    df = pd.read_csv(时间序列明细文件, encoding="utf-8-sig")
    df = df[df["时间序列名称"] == series_name].copy()
    if df.empty:
        raise ValueError(f"未找到时间序列：{series_name}")
    df["时间序号"] = df["时间序号"].astype(float).astype(int)
    df["数值"] = df["数值"].astype(float)
    return df[["时间序号", "数值"]].sort_values("时间序号").reset_index(drop=True)


def build_total_process_10min() -> pd.DataFrame:
    hourly = read_hourly_series()
    if len(hourly) < 总时长小时:
        raise ValueError("原始 2天污水量 序列长度不足 48 小时")

    inject_hourly = hourly.iloc[:注入时长小时].copy().reset_index(drop=True)
    old_x = np.arange(len(inject_hourly), dtype=float)
    new_x = np.linspace(0.0, len(inject_hourly) - 1, 注入步数)
    interp_values = np.interp(new_x, old_x, inject_hourly["数值"].to_numpy(dtype=float))
    interp_values = np.maximum(interp_values, 1e-12)
    inject_weights = interp_values / interp_values.sum()
    first24_volume = 总入流量_QR * inject_weights

    all_volume = np.zeros(总步数, dtype=float)
    all_strength = np.zeros(总步数, dtype=float)
    all_weight = np.zeros(总步数, dtype=float)
    all_volume[:注入步数] = first24_volume
    all_strength[:注入步数] = interp_values
    all_weight[:注入步数] = inject_weights

    return pd.DataFrame(
        {
            "步号": np.arange(总步数, dtype=int),
            "相对小时": np.arange(总步数, dtype=float) * 时间步秒数 / 3600.0,
            "原始小时序号": np.where(np.arange(总步数) < 注入步数, np.floor(np.arange(总步数) / 6).astype(int), -1),
            "原始小时插值强度": all_strength,
            "时间权重": all_weight,
            "总入流体积_m3": all_volume,
            "总入流量_CMS": all_volume / 时间步秒数,
        }
    )


def build_truth_injection(total_process: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for node in 真值注入点:
        share = 真值总量_m3[node] / 总入流量_QR
        node_step_volume = total_process["总入流体积_m3"].to_numpy(dtype=float) * share
        for step_idx, (hour_value, volume) in enumerate(zip(total_process["相对小时"], node_step_volume)):
            rows.append(
                {
                    "节点": node,
                    "步号": step_idx,
                    "相对小时": float(hour_value),
                    "节点总量占比": share,
                    "该步体积_m3": float(volume),
                    "注入流量_CMS": float(volume / 时间步秒数),
                }
            )
    return pd.DataFrame(rows)


def build_injection_series(truth_df: pd.DataFrame) -> dict[str, np.ndarray]:
    series_map: dict[str, np.ndarray] = {}
    for node in 真值注入点:
        node_df = truth_df[truth_df["节点"] == node].sort_values("步号")
        series_map[node] = node_df["注入流量_CMS"].to_numpy(dtype=float)
    return series_map


def extract_original_baseline() -> tuple[pd.DataFrame, pd.DataFrame]:
    with Output(str(旱天结果库)) as out:
        ten_x = np.arange(总步数, dtype=float) * 时间步秒数 / 3600.0

        baseline_monitor = pd.DataFrame({"步号": np.arange(总步数, dtype=int), "相对小时": ten_x})
        baseline_outlet = baseline_monitor[["步号", "相对小时"]].copy()

        for node in 监测点:
            ts = out.node_series(node, NodeAttribute.TOTAL_INFLOW)
            vals = np.array(list(ts.values()), dtype=float)
            hour_x = np.arange(1, len(vals) + 1, dtype=float)
            baseline_monitor[node] = np.interp(ten_x, hour_x, vals, left=float(vals[0]), right=float(vals[-1]))

        outfall_ts = out.node_series(唯一排口, NodeAttribute.TOTAL_INFLOW)
        outfall_vals = np.array(list(outfall_ts.values()), dtype=float)
        hour_x = np.arange(1, len(outfall_vals) + 1, dtype=float)
        baseline_outlet["排口基线_CMS"] = np.interp(ten_x, hour_x, outfall_vals, left=float(outfall_vals[0]), right=float(outfall_vals[-1]))

    return baseline_monitor, baseline_outlet


def save_outlet_plot(outlet_df: pd.DataFrame) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=outlet_df["相对小时"], y=outlet_df["排口基线_CMS"], mode="lines", name="排口基线"))
    fig.add_trace(go.Scatter(x=outlet_df["相对小时"], y=outlet_df["排口事件_CMS"], mode="lines", name="排口事件"))
    fig.add_trace(go.Scatter(x=outlet_df["相对小时"], y=outlet_df["排口增量_CMS"], mode="lines", name="排口增量"))
    fig.update_layout(title="0327 排口过程检查", template="plotly_white", xaxis_title="相对小时", yaxis_title="流量(CMS)")
    (结果目录 / "0327_排口过程检查.html").write_text(pio.to_html(fig, include_plotlyjs="cdn", full_html=True), encoding="utf-8")


def main() -> None:
    config = 实验配置()
    确保目录()
    复制原始文件到ASCII目录()
    copy_timeseries_csv()
    生成基线副本()
    生成数据口径说明(config)

    total_process = build_total_process_10min()
    truth_df = build_truth_injection(total_process)
    injection_series = build_injection_series(truth_df)
    baseline_monitor, baseline_outlet = extract_original_baseline()
    event_monitor, event_outlet = 运行事件仿真(str(基线副本), injection_series)

    common_len = min(len(total_process), len(baseline_monitor), len(event_monitor), len(baseline_outlet), len(event_outlet))
    total_process = total_process.iloc[:common_len].reset_index(drop=True)
    truth_df = truth_df[truth_df["步号"] < common_len].copy().reset_index(drop=True)
    baseline_monitor = baseline_monitor.iloc[:common_len].reset_index(drop=True)
    baseline_outlet = baseline_outlet.iloc[:common_len].reset_index(drop=True)
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)

    observed_delta = baseline_monitor.copy()
    for node in 监测点:
        observed_delta[node] = event_monitor[node].to_numpy(dtype=float) - baseline_monitor[node].to_numpy(dtype=float)

    outlet_df = baseline_outlet.copy()
    outlet_df["排口事件_CMS"] = event_outlet["排口连边流量_CMS"].to_numpy(dtype=float)
    outlet_df["排口增量_CMS"] = outlet_df["排口事件_CMS"] - outlet_df["排口基线_CMS"]

    total_process.to_csv(总入流过程文件, index=False, encoding="utf-8-sig")
    truth_df.to_csv(真值注水文件, index=False, encoding="utf-8-sig")
    baseline_monitor.to_csv(基线监测文件, index=False, encoding="utf-8-sig")
    event_monitor.to_csv(事件监测文件, index=False, encoding="utf-8-sig")
    observed_delta.to_csv(观测增量文件, index=False, encoding="utf-8-sig")
    outlet_df.to_csv(排口过程文件, index=False, encoding="utf-8-sig")
    save_outlet_plot(outlet_df)

    summary = {
        "原始旱天文件": str(原始旱天文件),
        "原始有雨文件": str(原始有雨文件),
        "当前基线副本": str(基线副本),
        "总时长小时": 总时长小时,
        "注入时长小时": 注入时长小时,
        "时间步秒数": 时间步秒数,
        "总步数": 总步数,
        "注入步数": 注入步数,
        "Q_R_m3": 总入流量_QR,
        "真值注入点": list(真值注入点),
        "排口基线最大流量CMS": float(outlet_df["排口基线_CMS"].max()),
        "排口事件最大流量CMS": float(outlet_df["排口事件_CMS"].max()),
        "排口增量最大流量CMS": float(outlet_df["排口增量_CMS"].max()),
        "排口事件非零步数": int((outlet_df["排口事件_CMS"].abs() > 1e-12).sum()),
        "监测点基线最大值": {node: float(baseline_monitor[node].max()) for node in 监测点},
    }
    方案文件.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (结果目录 / "0327_数据生成汇总.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (结果目录 / "0327_数据生成说明.md").write_text(
        "\n".join(
            [
                "# 0327 数据生成说明",
                "",
                "- 基线：直接读取原始 dry.out 的 48 小时时序，并线性细分到 10 分钟。",
                "- 事件：在 clean 基线副本上，对 J76 / J124 / J140 进行前 24 小时注水，后 24 小时不注水。",
                "- 总波形：来自原始 2天污水量 的前 24 小时，细分到 10 分钟，并按三点固定比例拆分。",
                "- 观测增量：事件监测 - 原始基线监测。",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
