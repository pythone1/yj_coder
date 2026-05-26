from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config_0416 import (
    ANALYSIS_DIR,
    BASELINE_MODEL_INP,
    CANDIDATE_NODES,
    DATA_DIR,
    MODEL_2D_INP,
    MONITOR_NODES,
    RESULT_DIR,
    RUNTIME_DIR,
    SIMULATION_HOURS,
    SOURCE_MODEL_INP,
    SOURCE_MODEL_RPT,
    STEP_SECONDS,
    STEP_MINUTES,
    TRUTH_EVENT_DURATION_MINUTES,
    TRUTH_EVENT_START_HOUR,
    TRUTH_INJECTION_DESIGN_CSV,
    TRUTH_INJECTION_DESIGN_JSON,
    TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3,
    TRUTH_INJECTION_NODES,
    TRUTH_INJECTION_SHARES,
    TRUTH_INJECTION_TOTAL_VOLUME_M3,
    TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL,
    TRUTH_INJECTION_WAVEFORM_MODE,
    WORKFLOW_GUIDE_TXT,
    ensure_dirs,
)


GENERATED_TS_PREFIXES = ("TS_0520_TRUE_", "TS_")
PREVIOUS_0417_50PCT_HOURLY_FLOW_CMS = [
    0.0, 0.0, 0.0, 0.00385, 0.00385, 0.0042, 0.0049, 0.00525,
    0.00595, 0.0063, 0.0077, 0.0049, 0.00665, 0.00735, 0.0301,
    0.04795, 0.04235, 0.0399, 0.0364, 0.03325, 0.03115, 0.0063,
    0.0049, 0.0042, 0.0042, 0.0042, 0.0042, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]
PREVIOUS_0417_50PCT_NONZERO_24H_FLOW_CMS = PREVIOUS_0417_50PCT_HOURLY_FLOW_CMS[3:27]


def _format_time_label(relative_hour: float) -> str:
    total_minutes = int(round(relative_hour * 60.0))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _parse_baseline_outfall_volume_m3() -> float:
    if TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL <= 0:
        return TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3
    if not SOURCE_MODEL_RPT.exists():
        return TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3 / TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL
    text = SOURCE_MODEL_RPT.read_text(encoding="gbk", errors="ignore")
    for line in text.splitlines():
        if "External Outflow" not in line:
            continue
        values = [float(item) for item in re.findall(r"[-+]?\d+(?:\.\d+)?", line)]
        if values:
            # SWMM continuity summary commonly reports million liters in this model.
            return max(values) * 1000.0
    return TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3 / TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL


def _set_simulation_time_window(lines: list[str]) -> list[str]:
    start_date = "02/27/2026"
    start_time = "00:00:00"
    start_dt = datetime.strptime(f"{start_date} {start_time}", "%m/%d/%Y %H:%M:%S")
    end_dt = start_dt + timedelta(hours=float(SIMULATION_HOURS))
    end_date = end_dt.strftime("%m/%d/%Y")
    end_time = end_dt.strftime("%H:%M:%S")

    replacements = {
        "START_DATE": start_date,
        "START_TIME": start_time,
        "REPORT_START_DATE": start_date,
        "REPORT_START_TIME": start_time,
        "END_DATE": end_date,
        "END_TIME": end_time,
        "REPORT_STEP": "00:10:00",
        "WET_STEP": "00:10:00",
        "DRY_STEP": "00:10:00",
    }
    output: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            output.append(line)
            continue
        if section == "OPTIONS" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            key = parts[0] if parts else ""
            if key in replacements:
                output.append(f"{key:<20} {replacements[key]}")
                continue
        output.append(line)
    return output


def _remove_generated_rows(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    section = ""
    generated_truth_ts = {f"TS_0520_TRUE_{node}" for node in TRUTH_INJECTION_NODES}
    generated_sim_prefix = "TS_"

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            cleaned.append(line)
            continue

        if section == "INFLOWS" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            node = parts[0] if parts else ""
            constituent = parts[1].upper() if len(parts) > 1 else ""
            ts_name = parts[2] if len(parts) > 2 else ""
            is_generated_truth = ts_name in generated_truth_ts
            is_runtime_sim = ts_name.startswith(generated_sim_prefix) and ts_name.endswith("_SIM")
            is_0520_flow = node in set(CANDIDATE_NODES) and constituent == "FLOW"
            if is_generated_truth or is_runtime_sim or is_0520_flow:
                continue

        if section == "TIMESERIES" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            ts_name = parts[0] if parts else ""
            if ts_name in generated_truth_ts or (ts_name.startswith(generated_sim_prefix) and ts_name.endswith("_SIM")):
                continue

        cleaned.append(line)
    return cleaned


def _insert_section_payload(lines: list[str], section_name: str, payload: list[str]) -> list[str]:
    if not payload:
        return lines

    output: list[str] = []
    section = ""
    inserted = False
    in_target = False
    pending_before_next_section = False

    for line in lines:
        stripped = line.strip()
        starts_new_section = stripped.startswith("[") and stripped.endswith("]")

        if starts_new_section and pending_before_next_section and not inserted:
            output.extend(payload)
            inserted = True
            pending_before_next_section = False

        if starts_new_section:
            section = stripped[1:-1].upper()
            in_target = section == section_name.upper()
            output.append(line)
            if in_target:
                pending_before_next_section = True
            continue

        output.append(line)
        if in_target and stripped.startswith(";;--------------") and not inserted:
            output.extend(payload)
            inserted = True
            pending_before_next_section = False

    if pending_before_next_section and not inserted:
        output.extend(payload)
        inserted = True
    if not inserted:
        output.append(f"[{section_name.upper()}]")
        output.extend(payload)
    return output


def _build_truth_injection_series() -> pd.DataFrame:
    if TRUTH_INJECTION_TOTAL_VOLUME_M3 > 0:
        total_volume_m3 = float(TRUTH_INJECTION_TOTAL_VOLUME_M3)
    else:
        total_volume_m3 = _parse_baseline_outfall_volume_m3() * TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL
    if not math.isfinite(total_volume_m3) or total_volume_m3 <= 0:
        total_volume_m3 = TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3

    if TRUTH_INJECTION_WAVEFORM_MODE == "0417_50pct_24h_10min":
        step_count = int(round(SIMULATION_HOURS * 60.0 / STEP_MINUTES))
        relative_hours = np.arange(step_count + 1, dtype=float) * STEP_MINUTES / 60.0
        anchor_hours = np.arange(0.0, 25.0, 1.0)
        anchor_flow = np.asarray([*PREVIOUS_0417_50PCT_NONZERO_24H_FLOW_CMS, 0.0], dtype=float) * 3.0
        shape = np.interp(relative_hours, anchor_hours, anchor_flow, left=anchor_flow[0], right=0.0)
        shape[relative_hours > TRUTH_EVENT_DURATION_MINUTES / 60.0] = 0.0
        volume_step_seconds = STEP_SECONDS
    else:
        step_count = int(round(SIMULATION_HOURS * 60.0 / STEP_MINUTES))
        relative_hours = np.arange(step_count + 1, dtype=float) * STEP_MINUTES / 60.0
        event_start = TRUTH_EVENT_START_HOUR
        event_end = event_start + TRUTH_EVENT_DURATION_MINUTES / 60.0
        shape = np.zeros_like(relative_hours)
        active = (relative_hours >= event_start) & (relative_hours <= event_end)
        x = (relative_hours[active] - event_start) / max(event_end - event_start, 1e-12)
        shape[active] = np.sin(np.pi * x)
        shape[shape < 1e-12] = 0.0
        volume_step_seconds = STEP_SECONDS

    unit_volume = float(np.sum(shape) * volume_step_seconds)
    if unit_volume <= 0:
        raise RuntimeError("Truth injection waveform is empty.")
    total_flow = shape * (total_volume_m3 / unit_volume)

    rows: dict[str, list[float] | list[str]] = {
        "step": list(range(len(relative_hours))),
        "relative_hour": relative_hours.tolist(),
        "time_label": [_format_time_label(hour) for hour in relative_hours],
        "total_flow_cms": total_flow.tolist(),
        "total_volume_m3": (total_flow * volume_step_seconds).tolist(),
    }
    for node in TRUTH_INJECTION_NODES:
        share = float(TRUTH_INJECTION_SHARES[node])
        rows[f"{node}_share"] = [share] * len(relative_hours)
        rows[f"{node}_flow_cms"] = (total_flow * share).tolist()
        rows[f"{node}_volume_m3"] = (total_flow * share * volume_step_seconds).tolist()

    return pd.DataFrame(rows)


def _write_baseline_and_event_models(truth_series: pd.DataFrame) -> None:
    if not SOURCE_MODEL_INP.exists():
        raise FileNotFoundError(f"Source INP not found: {SOURCE_MODEL_INP}")

    source_lines = SOURCE_MODEL_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    clean_lines = _set_simulation_time_window(_remove_generated_rows(source_lines))
    BASELINE_MODEL_INP.write_text("\n".join(clean_lines) + "\n", encoding="gbk")

    inflow_payload: list[str] = []
    timeseries_payload: list[str] = []
    for node in TRUTH_INJECTION_NODES:
        ts_name = f"TS_0520_TRUE_{node}"
        inflow_payload.append(f"{node:<16} FLOW             {ts_name:<16} FLOW     1.0      1.0      0.0")
        for label, flow in zip(truth_series["time_label"], truth_series[f"{node}_flow_cms"]):
            timeseries_payload.append(f"{ts_name:<24} {label:<10} {float(flow):.12f}")

    event_lines = _insert_section_payload(clean_lines, "INFLOWS", inflow_payload)
    event_lines = _insert_section_payload(event_lines, "TIMESERIES", timeseries_payload)
    MODEL_2D_INP.write_text("\n".join(event_lines) + "\n", encoding="gbk")


def _write_workflow_guide(truth_series: pd.DataFrame) -> None:
    total_volume = float(truth_series["total_volume_m3"].sum())
    peak_flow = float(truth_series["total_flow_cms"].max())
    content = f"""0520 管网溯源工作流说明

一、模型文件
1. 原始模型：{SOURCE_MODEL_INP}
2. 干净旱天基线：{BASELINE_MODEL_INP}
3. 真值注入事件模型：{MODEL_2D_INP}

二、当前布点
1. 候选井 {len(CANDIDATE_NODES)} 个：{", ".join(CANDIDATE_NODES)}
2. 监测点 {len(MONITOR_NODES)} 个：{", ".join(MONITOR_NODES)}
3. 真值注入点 {len(TRUTH_INJECTION_NODES)} 个：{", ".join(TRUTH_INJECTION_NODES)}

三、真值注入设置
1. 注入开始：第 {TRUTH_EVENT_START_HOUR:.1f} 小时
2. 注入时长：{TRUTH_EVENT_DURATION_MINUTES} 分钟
3. INP 注入时序步长：{STEP_MINUTES} 分钟
4. 波形：沿用上一版 0417 的 48h降雨量(50%) 形态，平移为第 0-24 小时注入，并插值到 10 分钟
5. 总注入量：{total_volume:.3f} m3
6. 峰值总流量：{peak_flow:.6f} m3/s
7. 分配比例：{json.dumps(TRUTH_INJECTION_SHARES, ensure_ascii=False)}
8. 数据构造时会再按“事件排口总出流 - 旱天排口总出流”校准总入流量，最终识别使用的校准量见 {DATA_DIR / "0520_data_summary.json"}

四、运行命令
1. 初始化模型和说明：
   & "D:\\APP\\anaconda\\envs\\LSTM\\python.exe" "{Path(__file__).resolve()}"
2. 只构造数据并校验真值回放：
   & "D:\\APP\\anaconda\\envs\\LSTM\\python.exe" "{Path(__file__).resolve().parent / "build_0416_data.py"}"
3. 小参数测试：
   & "D:\\APP\\anaconda\\envs\\LSTM\\python.exe" "{Path(__file__).resolve().parent / "run_small_0416.py"}"
4. 中参数运行：
   & "D:\\APP\\anaconda\\envs\\LSTM\\python.exe" "{Path(__file__).resolve().parent / "run_medium_0416.py"}"
5. 大参数运行：
   & "D:\\APP\\anaconda\\envs\\LSTM\\python.exe" "{Path(__file__).resolve().parent / "run_large_0416.py"}"

五、参数位置
1. 点位、模型路径、步长和真值注入参数：{Path(__file__).resolve().parent / "config_0416.py"}
2. 数据构造和真值回放：{Path(__file__).resolve().parent / "build_0416_data.py"}
3. 水力模拟和评分：{Path(__file__).resolve().parent / "simulation_0416.py"}
4. GA/AM 主算法：{Path(__file__).resolve().parent / "ga_am_0416.py"}
5. 小中大参数规模：run_small_0416.py、run_medium_0416.py、run_large_0416.py
"""
    WORKFLOW_GUIDE_TXT.write_text(content, encoding="utf-8")


def ensure_0520_baseline_event_models(force: bool = False) -> dict[str, object]:
    ensure_dirs()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    if force or not BASELINE_MODEL_INP.exists() or not MODEL_2D_INP.exists():
        truth_series = _build_truth_injection_series()
        _write_baseline_and_event_models(truth_series)
    else:
        truth_series = _build_truth_injection_series()

    truth_series.to_csv(TRUTH_INJECTION_DESIGN_CSV, index=False, encoding="utf-8-sig")
    summary = {
        "baseline_model": str(BASELINE_MODEL_INP),
        "truth_event_model": str(MODEL_2D_INP),
        "candidate_nodes": list(CANDIDATE_NODES),
        "monitor_nodes": list(MONITOR_NODES),
        "truth_injection_nodes": list(TRUTH_INJECTION_NODES),
        "truth_injection_shares": TRUTH_INJECTION_SHARES,
        "step_minutes": STEP_MINUTES,
        "simulation_hours": SIMULATION_HOURS,
        "event_start_hour": TRUTH_EVENT_START_HOUR,
        "event_duration_minutes": TRUTH_EVENT_DURATION_MINUTES,
        "waveform_mode": TRUTH_INJECTION_WAVEFORM_MODE,
        "truth_total_volume_m3": float(truth_series["total_volume_m3"].sum()),
        "truth_peak_total_flow_cms": float(truth_series["total_flow_cms"].max()),
    }
    TRUTH_INJECTION_DESIGN_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_workflow_guide(truth_series)
    return summary


def main() -> None:
    summary = ensure_0520_baseline_event_models(force=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
