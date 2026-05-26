from __future__ import annotations

import json
import shutil

import numpy as np
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from config_0401 import (
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
from simulation_0401 import build_dataset, evaluate_shares


def log(message: str) -> None:
    print(message, flush=True)


def find_outfall_link_name(inp_path) -> str:
    current_section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            current_section = s[1:-1].upper()
            continue
        if current_section != "CONDUITS" or not s or s.startswith(";"):
            continue
        parts = s.split()
        if len(parts) >= 3 and parts[2] == OUTFALL_NODE:
            return parts[0]
    raise ValueError(f"Unable to find conduit flowing into outfall node {OUTFALL_NODE}")


def run_model_collect(inp_path):
    outlet_link_name = find_outfall_link_name(inp_path)
    monitor_rows = []
    outlet_rows = []
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


def parse_no_flooding(rpt_path) -> bool:
    return "No nodes were flooded." in rpt_path.read_text(encoding="gbk", errors="ignore")


def extract_truth_injection_from_event_inp() -> pd.DataFrame:
    text = TRUTH_EVENT_MODEL_INP.read_text(encoding="gbk", errors="ignore")
    rows: dict[str, list[float]] = {"step": [], "relative_hour": []}
    for node in TRUTH_INJECTION_NODES:
        rows[f"{node}_flow_cms"] = []

    wanted = {f"TS_{node}_0327": node for node in TRUTH_INJECTION_NODES}
    temp = {node: [] for node in TRUTH_INJECTION_NODES}
    times: list[float] = []
    in_ts = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_ts = s[1:-1].upper() == "TIMESERIES"
            continue
        if not in_ts or not s or s.startswith(";"):
            continue
        parts = s.split()
        if len(parts) < 3:
            continue
        key = parts[0]
        if key not in wanted:
            continue
        hh, mm = parts[1].split(":")
        rel_hour = int(hh) + int(mm) / 60.0
        node = wanted[key]
        if node == TRUTH_INJECTION_NODES[0]:
            times.append(rel_hour)
        temp[node].append(float(parts[2]))

    for idx, rel_hour in enumerate(times):
        rows["step"].append(idx)
        rows["relative_hour"].append(rel_hour)
        for node in TRUTH_INJECTION_NODES:
            rows[f"{node}_flow_cms"].append(temp[node][idx])

    df = pd.DataFrame(rows)
    for node in TRUTH_INJECTION_NODES:
        df[f"{node}_volume_m3"] = df[f"{node}_flow_cms"] * STEP_SECONDS
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
    truth_volumes = {
        node: float(truth_injection[f"{node}_volume_m3"].sum()) for node in TRUTH_INJECTION_NODES
    }
    total_truth = float(sum(truth_volumes.values()))
    shares = np.zeros(len(CANDIDATE_NODES), dtype=float)
    for idx, node in enumerate(CANDIDATE_NODES):
        shares[idx] = truth_volumes.get(node, 0.0) / max(total_truth, 1e-12)
    return shares


def main() -> None:
    ensure_dirs()
    baseline_ascii = RUNTIME_DIR / "build_baseline.inp"
    event_ascii = RUNTIME_DIR / "build_truth_event.inp"
    shutil.copyfile(BASELINE_MODEL_INP, ASCII_BASELINE_TEMPLATE)
    shutil.copyfile(BASELINE_MODEL_INP, baseline_ascii)
    shutil.copyfile(TRUTH_EVENT_MODEL_INP, event_ascii)

    log("Collecting baseline monitor series from current confirmed baseline model")
    baseline_monitor, baseline_outlet = run_model_collect(baseline_ascii)

    log("Collecting event monitor series from current confirmed event model")
    event_monitor, event_outlet = run_model_collect(event_ascii)

    common_len = min(len(baseline_monitor), len(event_monitor), len(event_outlet))
    baseline_monitor = baseline_monitor.iloc[:common_len].reset_index(drop=True)
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)

    truth_injection = extract_truth_injection_from_event_inp().iloc[:common_len].reset_index(drop=True)
    expected_len = len(truth_injection)
    if len(baseline_monitor) < expected_len or len(event_monitor) < expected_len or len(event_outlet) < expected_len:
        raise RuntimeError(
            "Template simulation length is shorter than the expected truth injection length; "
            "refuse to build generated data from truncated model outputs."
        )
    relative_hour = truth_injection["relative_hour"].to_numpy(dtype=float)
    truth_shares = build_truth_shares(truth_injection)

    total_process = pd.DataFrame(
        {
            "step": truth_injection["step"],
            "relative_hour": relative_hour,
            "time_label": [f"{int(h):02d}:{int(round((h - int(h)) * 60)):02d}" for h in relative_hour],
            "total_flow_cms": sum(truth_injection[f"{node}_flow_cms"] for node in TRUTH_INJECTION_NODES),
        }
    )
    total_process["total_volume_m3"] = total_process["total_flow_cms"] * STEP_SECONDS
    total_process["weight"] = total_process["total_volume_m3"] / max(float(total_process["total_volume_m3"].sum()), 1e-12)

    baseline_monitor["relative_hour"] = relative_hour
    baseline_outlet["relative_hour"] = relative_hour

    # First pass: build a canonical truth event through the same evaluator path
    # used later by GA/AM, then save an initial on-disk dataset.
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

    # Second pass: reload exactly what the runtime will later read from disk,
    # then run truth once more and overwrite event/delta/outlet with that final
    # canonical result to remove any remaining chain mismatch.
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
        "truth_total_volume_m3": float(total_process["total_volume_m3"].sum()),
        "truth_scaled_volumes_m3": {
            node: float(truth_injection[f"{node}_volume_m3"].sum()) for node in TRUTH_INJECTION_NODES
        },
        "baseline_no_flooding": parse_no_flooding(BASELINE_MODEL_RPT),
        "event_no_flooding": parse_no_flooding(TRUTH_EVENT_MODEL_RPT),
    }
    DATA_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
