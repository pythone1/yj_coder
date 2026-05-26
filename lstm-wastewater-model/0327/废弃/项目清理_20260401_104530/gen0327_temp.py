from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pyswmm import Links, Nodes, Simulation


PROJECT_DIR = Path(r"E:\PY\LSTM\0327")
SOURCE_DIR = Path(r"E:\PY\LSTM\模型文件有污水量\模型文件有污水量")
PARSED_DIR = Path(r"E:\PY\LSTM\模型文件有污水量\解析结果")

CODE_DIR = PROJECT_DIR / "代码"
DATA_DIR = PROJECT_DIR / "数据"
ASCII_DIR = PROJECT_DIR / "data_ascii"
RESULT_DIR = PROJECT_DIR / "结果"
GENERATED_DIR = DATA_DIR / "生成数据"

DRY_SOURCE = SOURCE_DIR / "盱眙污水管3（入渗点无雨水量）.inp"
WET_SOURCE = SOURCE_DIR / "盱眙污水管3（入渗点有雨水量）.inp"
DRY_ASCII = ASCII_DIR / "dry_original.inp"
WET_ASCII = ASCII_DIR / "wet_original.inp"
DRY_BASE = ASCII_DIR / "dry_base_core.inp"

TRUTH_NODES = ("J76", "J124", "J140")
TRUTH_VOLUMES_M3 = (18000.0, 26000.0, 32000.0)
MONITOR_NODES = ("J191", "J74", "J78", "J91", "J59", "J123", "J126", "J137", "J145", "J231")
OUTFALL_NODE = "J132"
SOURCE_SERIES_NAME = "2天污水量"
STEP_SECONDS = 600
TOTAL_HOURS = 6
TOTAL_STEPS = int(TOTAL_HOURS * 3600 / STEP_SECONDS)


SECTION_ROW_DELETE = {
    "JUNCTIONS": {"J197"},
    "OUTFALLS": {"J242"},
    "STORAGE": {"J241"},
    "CONDUITS": {"C90", "C95"},
    "XSECTIONS": {"C90", "C95"},
    "INFLOWS": {"J106", "J197"},
    "COORDINATES": {"J197", "J241", "J242"},
}

SECTION_TAG_DELETE = {
    "TAGS": {("Node", "J197"), ("Node", "J241"), ("Node", "J242")}
}


def ensure_dirs() -> None:
    ASCII_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def copy_originals() -> None:
    shutil.copyfile(DRY_SOURCE, DRY_ASCII)
    shutil.copyfile(WET_SOURCE, WET_ASCII)


def rewrite_filtered_inp(source_path: Path, target_path: Path) -> None:
    raw = source_path.read_bytes()
    lines = raw.splitlines(keepends=True)
    current_section = ""
    output: list[bytes] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(b"[") and stripped.endswith(b"]"):
            current_section = stripped[1:-1].decode("ascii", errors="ignore").upper()
            output.append(line)
            continue

        if not stripped or stripped.startswith(b";"):
            output.append(line)
            continue

        tokens = stripped.split()
        if not tokens:
            output.append(line)
            continue

        first = tokens[0].decode("ascii", errors="ignore")
        delete_first = SECTION_ROW_DELETE.get(current_section, set())
        if first in delete_first:
            continue

        delete_tags = SECTION_TAG_DELETE.get(current_section, set())
        if len(tokens) >= 2:
            first_two = (
                tokens[0].decode("ascii", errors="ignore"),
                tokens[1].decode("ascii", errors="ignore"),
            )
            if first_two in delete_tags:
                continue

        output.append(line)

    target_path.write_bytes(b"".join(output))


def read_hourly_series(series_name: str = SOURCE_SERIES_NAME) -> pd.DataFrame:
    csv_path = PARSED_DIR / "盱眙污水管3（入渗点无雨水量）_时间序列明细.csv"
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df = df[df["时间序列名称"] == series_name].copy()
    if df.empty:
        raise ValueError(f"未找到时间序列：{series_name}")
    df["时间序号"] = df["时间序号"].astype(float).astype(int)
    df["数值"] = df["数值"].astype(float)
    return df[["时间序号", "数值"]].sort_values("时间序号").reset_index(drop=True)


def select_hourly_window(hourly: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    window = TOTAL_HOURS
    peak_idx = int(hourly["数值"].astype(float).idxmax())
    start = max(0, min(peak_idx - window // 2, len(hourly) - window))
    end = start + window
    selected = hourly.iloc[start:end].copy().reset_index(drop=True)
    return selected, int(hourly.iloc[start]["时间序号"]), int(hourly.iloc[end - 1]["时间序号"])


def build_total_process_10min() -> pd.DataFrame:
    hourly_full = read_hourly_series()
    hourly, source_start_hour, source_end_hour = select_hourly_window(hourly_full)
    old_x = np.arange(len(hourly), dtype=float)
    new_x = np.linspace(0.0, len(hourly) - 1, TOTAL_STEPS)
    interpolated = np.interp(new_x, old_x, hourly["数值"].to_numpy(dtype=float))
    interpolated = np.maximum(interpolated, 1e-12)
    weights = interpolated / interpolated.sum()
    total_qr = float(sum(TRUTH_VOLUMES_M3))
    step_volume = total_qr * weights
    return pd.DataFrame(
        {
            "步号": np.arange(TOTAL_STEPS, dtype=int),
            "相对小时": np.arange(TOTAL_STEPS, dtype=float) * STEP_SECONDS / 3600.0,
            "原始窗口起点小时序号": source_start_hour,
            "原始窗口终点小时序号": source_end_hour,
            "原始小时插值强度": interpolated,
            "时间权重": weights,
            "总入流体积_m3": step_volume,
            "总入流量_CMS": step_volume / STEP_SECONDS,
        }
    )


def build_truth_injection(df_total: pd.DataFrame) -> pd.DataFrame:
    total_qr = float(sum(TRUTH_VOLUMES_M3))
    rows: list[dict] = []
    for node, total_volume in zip(TRUTH_NODES, TRUTH_VOLUMES_M3):
        share = total_volume / total_qr
        node_step_volume = df_total["总入流体积_m3"].to_numpy(dtype=float) * share
        for step_idx, (hour_value, volume) in enumerate(zip(df_total["相对小时"], node_step_volume)):
            rows.append(
                {
                    "节点": node,
                    "步号": step_idx,
                    "相对小时": float(hour_value),
                    "节点总量占比": share,
                    "该步体积_m3": float(volume),
                    "注入流量_CMS": float(volume / STEP_SECONDS),
                }
            )
    return pd.DataFrame(rows)


def build_injection_series(df_truth: pd.DataFrame) -> Dict[str, np.ndarray]:
    series_map: Dict[str, np.ndarray] = {}
    for node in TRUTH_NODES:
        node_df = df_truth[df_truth["节点"] == node].sort_values("步号")
        series_map[node] = node_df["注入流量_CMS"].to_numpy(dtype=float)
    return series_map


def find_outlet_link(inp_path: Path, outfall_node: str) -> str:
    lines = inp_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    current = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].upper()
            continue
        if current != "CONDUITS" or not stripped or stripped.startswith(";"):
            continue
        tokens = stripped.split()
        if len(tokens) >= 3 and tokens[2] == outfall_node:
            return tokens[0]
    raise ValueError(f"未找到流向排口 {outfall_node} 的连边")


def run_single_simulation(inp_path: Path, injection_series: Dict[str, np.ndarray]) -> tuple[pd.DataFrame, pd.DataFrame]:
    outlet_link_name = find_outlet_link(inp_path, OUTFALL_NODE)
    monitor_rows: list[dict] = []
    outlet_rows: list[dict] = []

    with Simulation(str(inp_path)) as sim:
        sim.step_advance(STEP_SECONDS)
        nodes = Nodes(sim)
        links = Links(sim)
        node_handles = {name: nodes[name] for name in set(MONITOR_NODES) | set(injection_series)}
        outlet_link = links[outlet_link_name]

        for step_idx, _ in enumerate(sim):
            if step_idx >= TOTAL_STEPS:
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


def save_outlet_plot(df_outlet: pd.DataFrame) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_outlet["相对小时"],
            y=df_outlet["排口基线_CMS"],
            mode="lines",
            name="排口基线流量",
            line=dict(color="#2f6fed", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_outlet["相对小时"],
            y=df_outlet["排口事件_CMS"],
            mode="lines",
            name="排口事件流量",
            line=dict(color="#d9485f", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_outlet["相对小时"],
            y=df_outlet["排口增量_CMS"],
            mode="lines",
            name="排口增量",
            line=dict(color="#1f9d55", width=2),
        )
    )
    fig.update_layout(
        title="0327 排口 J132 48 小时过程",
        xaxis_title="相对小时",
        yaxis_title="流量 (CMS)",
        template="plotly_white",
    )
    html = pio.to_html(fig, include_plotlyjs="cdn", full_html=True)
    (RESULT_DIR / "0327_排口过程检查.html").write_text(html, encoding="utf-8")


def clean_previous_outputs() -> None:
    for pattern in ("0327_*10分钟.csv",):
        for path in GENERATED_DIR.glob(pattern):
            path.unlink(missing_ok=True)
    for pattern in ("0327_排口过程检查.html", "0327_数据生成汇总.json", "0327_数据生成说明.md"):
        (RESULT_DIR / pattern).unlink(missing_ok=True)
    for pattern in ("0327_GA全部方案.csv", "0327_GA每代最佳.csv", "0327_GA末代合并.csv", "0327_initial_PPD.csv", "0327_AM样本.csv", "0327_PPD样本.csv", "0327_后验节点权重.csv", "0327_posterior_predictive_bands.csv", "0327_posterior_predictive_coverage.csv", "0327_最终方案模拟增量.csv", "0327_结果汇总.json", "0327_监测拟合.html", "0327_原始全网选点方案.html", "0327_PPD置信区间验证.html", "0327_详细汇报.md"):
        (RESULT_DIR / pattern).unlink(missing_ok=True)
    for pattern in ("*.out", "*.rpt"):
        for path in ASCII_DIR.glob(pattern):
            path.unlink(missing_ok=True)


def main() -> None:
    ensure_dirs()
    clean_previous_outputs()
    copy_originals()
    rewrite_filtered_inp(DRY_ASCII, DRY_BASE)

    df_total = build_total_process_10min()
    df_truth = build_truth_injection(df_total)
    truth_series = build_injection_series(df_truth)

    baseline_monitor, baseline_outlet = run_single_simulation(DRY_BASE, {})
    event_monitor, event_outlet = run_single_simulation(DRY_BASE, truth_series)

    observed_delta = event_monitor.copy()
    for node in MONITOR_NODES:
        observed_delta[node] = event_monitor[node] - baseline_monitor[node]

    outlet_df = pd.DataFrame(
        {
            "步号": event_outlet["步号"],
            "时间": event_outlet["时间"],
            "相对小时": np.arange(len(event_outlet), dtype=float) * STEP_SECONDS / 3600.0,
            "排口基线_CMS": baseline_outlet["排口连边流量_CMS"].to_numpy(dtype=float),
            "排口事件_CMS": event_outlet["排口连边流量_CMS"].to_numpy(dtype=float),
        }
    )
    outlet_df["排口增量_CMS"] = outlet_df["排口事件_CMS"] - outlet_df["排口基线_CMS"]

    df_total.to_csv(GENERATED_DIR / "0327_总入流过程_10分钟.csv", index=False, encoding="utf-8-sig")
    df_truth.to_csv(GENERATED_DIR / "0327_真值注水数据_10分钟.csv", index=False, encoding="utf-8-sig")
    baseline_monitor.to_csv(GENERATED_DIR / "0327_基线监测_10分钟.csv", index=False, encoding="utf-8-sig")
    event_monitor.to_csv(GENERATED_DIR / "0327_事件监测_10分钟.csv", index=False, encoding="utf-8-sig")
    observed_delta.to_csv(GENERATED_DIR / "0327_观测增量_10分钟.csv", index=False, encoding="utf-8-sig")
    outlet_df.to_csv(GENERATED_DIR / "0327_排口过程_10分钟.csv", index=False, encoding="utf-8-sig")

    save_outlet_plot(outlet_df)

    summary = {
        "原始旱天文件": str(DRY_SOURCE),
        "原始有雨水量文件": str(WET_SOURCE),
        "当前有效基线副本": str(DRY_BASE),
        "删除的入流": ["J106"],
        "删除的无关节点": ["J197", "J241", "J242"],
        "删除的无关连边": ["C90", "C95"],
        "时间来源": "原始模型 2天污水量 小时时序",
        "时间步长秒": STEP_SECONDS,
        "总时长小时": TOTAL_HOURS,
        "总步数": TOTAL_STEPS,
        "原始窗口起点小时序号": int(df_total["原始窗口起点小时序号"].iloc[0]),
        "原始窗口终点小时序号": int(df_total["原始窗口终点小时序号"].iloc[0]),
        "真值注入点": list(TRUTH_NODES),
        "真值总体积m3": list(TRUTH_VOLUMES_M3),
        "Qr_m3": float(sum(TRUTH_VOLUMES_M3)),
        "排口事件最大流量CMS": float(outlet_df["排口事件_CMS"].max()),
        "排口增量最大流量CMS": float(outlet_df["排口增量_CMS"].max()),
        "排口事件非零步数": int((outlet_df["排口事件_CMS"].abs() > 1e-12).sum()),
        "排口增量非零步数": int((outlet_df["排口增量_CMS"].abs() > 1e-12).sum()),
    }
    (RESULT_DIR / "0327_数据生成汇总.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (RESULT_DIR / "0327_数据生成说明.md").write_text(
        "\n".join(
            [
                "# 0327 十分钟数据生成说明",
                "",
                f"- 原始旱天文件：`{DRY_SOURCE}`",
                f"- 原始有雨水量文件：`{WET_SOURCE}`",
                f"- 当前有效基线副本：`{DRY_BASE}`",
                "- 在 ASCII 副本上删除 `J106` 外部入流，以及 `J197/J241/J242` 和 `C90/C95` 整段无关结构",
                "- 读取原始模型中的 `2天污水量` 小时时序，共 48 个小时点",
                "- 线性细分到 10 分钟分辨率，共 288 个时间步",
                "- 用 3 个真值注入点总体积占比拆分总入流波形，生成逐时注水数据",
                "- 运行基线工况与事件工况，并保存监测过程、观测增量和排口过程",
                "",
                f"- 排口事件最大流量：{summary['排口事件最大流量CMS']:.6f} CMS",
                f"- 排口增量最大流量：{summary['排口增量最大流量CMS']:.6f} CMS",
                f"- 排口事件非零步数：{summary['排口事件非零步数']}",
                f"- 排口增量非零步数：{summary['排口增量非零步数']}",
            ]
        ),
        encoding="utf-8",
    )
    (DATA_DIR / "0327_数据口径.json").write_text(
        json.dumps(
            {
                "dry_source": str(DRY_SOURCE),
                "wet_source": str(WET_SOURCE),
                "active_baseline_ascii_copy": str(DRY_BASE),
                "removed_inflow_nodes": ["J106"],
                "removed_irrelevant_nodes": ["J197", "J241", "J242"],
                "removed_irrelevant_links": ["C90", "C95"],
                "time_source": SOURCE_SERIES_NAME,
                "time_step_seconds": STEP_SECONDS,
                "duration_hours": TOTAL_HOURS,
                "steps": TOTAL_STEPS,
                "source_window_start_hour_index": int(df_total["原始窗口起点小时序号"].iloc[0]),
                "source_window_end_hour_index": int(df_total["原始窗口终点小时序号"].iloc[0]),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
