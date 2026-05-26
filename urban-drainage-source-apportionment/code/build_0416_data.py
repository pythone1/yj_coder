from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from config_0416 import (
    ASCII_BASELINE_TEMPLATE,
    BASELINE_MODEL_INP,
    BASELINE_MODEL_RPT,
    BASELINE_MONITOR_CSV,
    CANDIDATE_NODES,
    DATA_SUMMARY_JSON,
    DATA_DIR,
    EVENT_MONITOR_CSV,
    MONITOR_NODES,
    OUTFALL_NODE,
    OUTLET_SERIES_CSV,
    OBSERVED_DELTA_CSV,
    RUNTIME_DIR,
    STEP_SECONDS,
    TOTAL_PROCESS_CSV,
    TRUTH_EVENT_MODEL_INP,
    TRUTH_EVENT_MODEL_RPT,
    TRUTH_INJECTION_CSV,
    TRUTH_INJECTION_NODES,
    ensure_dirs,
    runtime_model_path,
)
from simulation_0416 import build_dataset, evaluate_shares
from setup_0520_workflow import ensure_0520_baseline_event_models


def log(message: str) -> None:
    print(message, flush=True)


def find_outfall_link_name(inp_path: Path) -> str:
    current_section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].upper()
            continue
        if current_section != "CONDUITS" or not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) >= 3 and parts[2] == OUTFALL_NODE:
            return parts[0]
    raise ValueError(f"Unable to find conduit flowing into outfall node {OUTFALL_NODE}")


def run_model_collect(inp_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    outlet_link_name = find_outfall_link_name(inp_path)
    monitor_rows: list[dict[str, object]] = []
    outlet_rows: list[dict[str, object]] = []
    with Simulation(str(inp_path)) as sim:
        sim.step_advance(STEP_SECONDS)
        nodes = Nodes(sim)
        links = Links(sim)
        node_handles = {name: nodes[name] for name in MONITOR_NODES}
        outlet_link = links[outlet_link_name]
        for step_idx, _ in enumerate(sim):
            row = {"step": step_idx, "time": sim.current_time}
            for node_name in MONITOR_NODES:
                row[node_name] = float(node_handles[node_name].total_inflow)
            monitor_rows.append(row)
            outlet_rows.append(
                {
                    "step": step_idx,
                    "time": sim.current_time,
                    "outfall_link_flow_cms": float(outlet_link.flow),
                }
            )
    return pd.DataFrame(monitor_rows), pd.DataFrame(outlet_rows)


def parse_no_flooding(rpt_path: Path) -> bool | None:
    if not rpt_path.exists():
        return None
    return "No nodes were flooded." in rpt_path.read_text(encoding="gbk", errors="ignore")


def _extract_inflow_mapping(inp_path: Path) -> dict[str, str]:
    inflow_map: dict[str, str] = {}
    current_section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].upper()
            continue
        if current_section != "INFLOWS" or not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) >= 3:
            node_name = parts[0]
            ts_name = parts[2]
            inflow_map[node_name] = ts_name
    return inflow_map


def _parse_relative_hour(label: str) -> float:
    if ":" not in label:
        return float(label)
    hh, mm, *rest = label.split(":")
    ss = rest[0] if rest else "0"
    return int(hh) + int(mm) / 60.0 + int(ss) / 3600.0


def _format_time_label(relative_hour: float) -> str:
    total_minutes = int(round(float(relative_hour) * 60.0))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _relative_hours_from_sim_time(frame: pd.DataFrame) -> np.ndarray:
    if frame.empty or "time" not in frame.columns:
        return np.array([], dtype=float)
    times = pd.to_datetime(frame["time"])
    start_time = times.iloc[0] - pd.Timedelta(seconds=STEP_SECONDS)
    return ((times - start_time).dt.total_seconds() / 3600.0).to_numpy(dtype=float)


def extract_truth_injection_from_event_inp(relative_hours: np.ndarray | None = None) -> pd.DataFrame:
    inflow_map = _extract_inflow_mapping(TRUTH_EVENT_MODEL_INP)
    truth_nodes = tuple(node for node in TRUTH_INJECTION_NODES if node in inflow_map)
    if not truth_nodes:
        raise RuntimeError(
            f"No truth injection nodes found in {TRUTH_EVENT_MODEL_INP.name}. "
            f"Configured truth nodes={TRUTH_INJECTION_NODES}"
        )

    text = TRUTH_EVENT_MODEL_INP.read_text(encoding="gbk", errors="ignore")
    wanted_series = {inflow_map[node] for node in truth_nodes}
    series_points: dict[str, list[tuple[float, float]]] = {name: [] for name in wanted_series}
    in_ts = False

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_ts = stripped[1:-1].upper() == "TIMESERIES"
            continue
        if not in_ts or not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            continue
        ts_name = parts[0]
        if ts_name not in wanted_series:
            continue
        rel_hour = _parse_relative_hour(parts[1])
        series_points[ts_name].append((rel_hour, float(parts[2])))

    for ts_name, points in series_points.items():
        if not points:
            raise RuntimeError(f"Timeseries {ts_name} referenced by truth inflows but has no rows")
        points.sort(key=lambda item: item[0])

    if relative_hours is None:
        first_series = series_points[inflow_map[truth_nodes[0]]]
        relative_hours = np.asarray([hour for hour, _ in first_series], dtype=float)
        if len(relative_hours) > 1:
            volume_step_seconds = float(np.median(np.diff(relative_hours)) * 3600.0)
        else:
            volume_step_seconds = float(STEP_SECONDS)
    else:
        relative_hours = np.asarray(relative_hours, dtype=float)
        volume_step_seconds = float(STEP_SECONDS)

    rows: dict[str, list[float]] = {"step": [], "relative_hour": []}
    interpolated: dict[str, np.ndarray] = {}
    for node in truth_nodes:
        ts_name = inflow_map[node]
        points = series_points[ts_name]
        source_hours = np.asarray([hour for hour, _ in points], dtype=float)
        source_values = np.asarray([value for _, value in points], dtype=float)
        interpolated[node] = np.interp(relative_hours, source_hours, source_values, left=source_values[0], right=source_values[-1])
        rows[f"{node}_flow_cms"] = []

    for idx, rel_hour in enumerate(relative_hours):
        rows["step"].append(idx)
        rows["relative_hour"].append(float(rel_hour))
        for node in truth_nodes:
            rows[f"{node}_flow_cms"].append(float(interpolated[node][idx]))

    df = pd.DataFrame(rows)
    for node in truth_nodes:
        df[f"{node}_volume_m3"] = df[f"{node}_flow_cms"] * volume_step_seconds
    return df


def save_generated_data(
    total_process: pd.DataFrame,
    truth_injection: pd.DataFrame,
    baseline_monitor: pd.DataFrame,
    event_monitor: pd.DataFrame,
    observed_delta: pd.DataFrame,
    outlet: pd.DataFrame,
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    total_process.to_csv(TOTAL_PROCESS_CSV, index=False, encoding="utf-8-sig")
    truth_injection.to_csv(TRUTH_INJECTION_CSV, index=False, encoding="utf-8-sig")
    baseline_monitor.to_csv(BASELINE_MONITOR_CSV, index=False, encoding="utf-8-sig")
    event_monitor.to_csv(EVENT_MONITOR_CSV, index=False, encoding="utf-8-sig")
    observed_delta.to_csv(OBSERVED_DELTA_CSV, index=False, encoding="utf-8-sig")
    outlet.to_csv(OUTLET_SERIES_CSV, index=False, encoding="utf-8-sig")


def load_generated_data() -> dict[str, pd.DataFrame]:
    return {
        "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
        "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
        "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
        "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
        "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
        "outlet": pd.read_csv(OUTLET_SERIES_CSV, encoding="utf-8-sig"),
    }


def build_truth_shares(truth_injection: pd.DataFrame) -> np.ndarray:
    truth_volume_map = {}
    for node in TRUTH_INJECTION_NODES:
        volume_col = f"{node}_volume_m3"
        truth_volume_map[node] = float(truth_injection[volume_col].sum()) if volume_col in truth_injection else 0.0
    total_truth = float(sum(truth_volume_map.values()))
    shares = np.zeros(len(CANDIDATE_NODES), dtype=float)
    for idx, node in enumerate(CANDIDATE_NODES):
        shares[idx] = truth_volume_map.get(node, 0.0) / max(total_truth, 1e-12)
    return shares


def integrate_outfall_volume(outlet: pd.DataFrame) -> float:
    return float(outlet["outfall_link_flow_cms"].to_numpy(dtype=float).sum() * STEP_SECONDS)


def scale_injection_to_outfall_delta(
    truth_injection: pd.DataFrame,
    baseline_outlet: pd.DataFrame,
    event_outlet: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    raw_total_volume = float(
        sum(
            truth_injection[f"{node}_volume_m3"].sum()
            for node in TRUTH_INJECTION_NODES
            if f"{node}_volume_m3" in truth_injection
        )
    )
    baseline_outfall_volume = integrate_outfall_volume(baseline_outlet)
    event_outfall_volume = integrate_outfall_volume(event_outlet)
    outfall_delta_volume = event_outfall_volume - baseline_outfall_volume
    if raw_total_volume <= 1e-12:
        raise RuntimeError("Raw truth injection volume is zero; cannot rescale total process.")
    if outfall_delta_volume <= 0:
        raise RuntimeError(
            "Event outfall volume is not greater than baseline outfall volume; "
            f"baseline={baseline_outfall_volume:.6f}, event={event_outfall_volume:.6f}"
        )

    scale_factor = outfall_delta_volume / raw_total_volume
    scaled = truth_injection.copy()
    for node in TRUTH_INJECTION_NODES:
        flow_col = f"{node}_flow_cms"
        volume_col = f"{node}_volume_m3"
        if flow_col in scaled:
            scaled[flow_col] = scaled[flow_col].to_numpy(dtype=float) * scale_factor
        if volume_col in scaled:
            scaled[volume_col] = scaled[volume_col].to_numpy(dtype=float) * scale_factor
    return scaled, {
        "raw_truth_injection_total_volume_m3": raw_total_volume,
        "baseline_outfall_total_volume_m3": baseline_outfall_volume,
        "event_outfall_total_volume_m3": event_outfall_volume,
        "outfall_delta_total_volume_m3": outfall_delta_volume,
        "total_process_scale_factor": scale_factor,
    }


def main() -> None:
    ensure_dirs()
    ensure_0520_baseline_event_models(force=True)
    baseline_ascii = RUNTIME_DIR / "build_baseline.inp"
    event_ascii = RUNTIME_DIR / "build_truth_event.inp"
    shutil.copyfile(BASELINE_MODEL_INP, ASCII_BASELINE_TEMPLATE)
    shutil.copyfile(BASELINE_MODEL_INP, baseline_ascii)
    shutil.copyfile(TRUTH_EVENT_MODEL_INP, event_ascii)

    log("Collecting baseline monitor series from the 0520 clean baseline model")
    baseline_monitor_raw, baseline_outlet_raw = run_model_collect(baseline_ascii)

    log("Collecting event monitor series from the configured 0520 truth event model")
    event_monitor_raw, event_outlet_raw = run_model_collect(event_ascii)

    overlap_steps = min(len(baseline_monitor_raw), len(event_monitor_raw), len(event_outlet_raw))
    relative_hours_full = _relative_hours_from_sim_time(baseline_monitor_raw).astype(float)[:overlap_steps]
    truth_injection = extract_truth_injection_from_event_inp(relative_hours_full).reset_index(drop=True)

    baseline_monitor = baseline_monitor_raw.iloc[:overlap_steps].reset_index(drop=True)
    baseline_outlet = baseline_outlet_raw.iloc[:overlap_steps].reset_index(drop=True)
    event_monitor = event_monitor_raw.iloc[:overlap_steps].reset_index(drop=True)
    event_outlet = event_outlet_raw.iloc[:overlap_steps].reset_index(drop=True)

    common_len = overlap_steps
    if common_len <= 0:
        raise RuntimeError("No overlapping time window found between baseline/event simulations and extracted truth series.")

    truth_injection, volume_calibration = scale_injection_to_outfall_delta(
        truth_injection,
        baseline_outlet,
        event_outlet,
    )
    relative_hour = truth_injection["relative_hour"].to_numpy(dtype=float)
    truth_shares = build_truth_shares(truth_injection)

    total_process = pd.DataFrame(
        {
            "step": truth_injection["step"],
            "relative_hour": relative_hour,
            "time_label": [_format_time_label(h) for h in relative_hour],
            "total_flow_cms": sum(
                truth_injection[f"{node}_flow_cms"] for node in TRUTH_INJECTION_NODES if f"{node}_flow_cms" in truth_injection
            ),
        }
    )
    total_process["total_volume_m3"] = total_process["total_flow_cms"] * STEP_SECONDS
    total_process["weight"] = total_process["total_volume_m3"] / max(float(total_process["total_volume_m3"].sum()), 1e-12)

    baseline_monitor["relative_hour"] = relative_hour
    baseline_outlet["relative_hour"] = relative_hour

    placeholder_event = baseline_monitor.copy()
    placeholder_delta = baseline_monitor.copy()
    for node_name in MONITOR_NODES:
        placeholder_delta[node_name] = 0.0
    placeholder_outlet = baseline_outlet[["step", "relative_hour", "outfall_link_flow_cms"]].copy()
    placeholder_outlet["outfall_link_flow_cms"] = 0.0

    temp_generated = {
        "total_process": total_process.copy(),
        "truth_injection": truth_injection.copy(),
        "baseline_monitor": baseline_monitor.copy(),
        "event_monitor": placeholder_event,
        "observed_delta": placeholder_delta,
        "outlet": placeholder_outlet,
    }
    canonical_dataset = build_dataset(temp_generated)
    canonical_result = evaluate_shares(truth_shares, canonical_dataset, str(runtime_model_path(0)))

    event_monitor = canonical_result["event_monitor"].copy().iloc[:common_len].reset_index(drop=True)
    observed_delta = canonical_result["sim_delta"].copy().iloc[:common_len].reset_index(drop=True)
    event_outlet = canonical_result["event_outlet"].copy().iloc[:common_len].reset_index(drop=True)
    event_outlet["relative_hour"] = relative_hour[: len(event_outlet)]

    save_generated_data(
        total_process,
        truth_injection,
        baseline_monitor,
        event_monitor,
        observed_delta,
        event_outlet,
    )

    reloaded = load_generated_data()
    reloaded_dataset = build_dataset(reloaded)
    final_truth = evaluate_shares(truth_shares, reloaded_dataset, str(runtime_model_path(0)))

    final_event_monitor = final_truth["event_monitor"].copy().iloc[:common_len].reset_index(drop=True)
    final_observed_delta = final_truth["sim_delta"].copy().iloc[:common_len].reset_index(drop=True)
    final_event_outlet = final_truth["event_outlet"].copy().iloc[:common_len].reset_index(drop=True)
    final_event_outlet["relative_hour"] = relative_hour[: len(final_event_outlet)]

    save_generated_data(
        total_process,
        truth_injection,
        baseline_monitor,
        final_event_monitor,
        final_observed_delta,
        final_event_outlet,
    )

    summary = {
        "baseline_inp": str(BASELINE_MODEL_INP),
        "truth_event_inp": str(TRUTH_EVENT_MODEL_INP),
        "rows": common_len,
        "first_relative_hour": float(relative_hour[0]) if len(relative_hour) else None,
        "last_relative_hour": float(relative_hour[-1]) if len(relative_hour) else None,
        "time_axis_source": f"PySWMM simulation current_time; report step is {STEP_SECONDS} seconds.",
        "injection_waveform_source": "Truth event FLOW waveform from 0520_truth_event.inp; interpolated to PySWMM output timestamps.",
        "total_process_volume_source": "event_outfall_total_volume_minus_baseline_outfall_total_volume",
        **volume_calibration,
        "truth_total_volume_m3": float(total_process["total_volume_m3"].sum()),
        "truth_scaled_volumes_m3": {
            node: float(truth_injection[f"{node}_volume_m3"].sum())
            for node in TRUTH_INJECTION_NODES
            if f"{node}_volume_m3" in truth_injection
        },
        "truth_replay_mean_nse": float(final_truth["mean_nse"]),
        "truth_replay_sse": float(final_truth["sse"]),
        "baseline_no_flooding": parse_no_flooding(baseline_ascii.with_suffix(".rpt")),
        "event_no_flooding": parse_no_flooding(event_ascii.with_suffix(".rpt")),
        "note": (
            "0520 dataset generated from configured baseline/event INP files; "
            f"{len(CANDIDATE_NODES)} candidate nodes and {len(MONITOR_NODES)} monitor nodes. "
            "Truth inflow is interpolated to PySWMM output timestamps."
        ),
    }
    DATA_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

