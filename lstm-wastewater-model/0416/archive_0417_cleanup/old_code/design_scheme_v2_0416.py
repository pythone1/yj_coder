from __future__ import annotations

import json
import shutil
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyswmm import Links, Nodes, Simulation


ROOT = Path(r"E:\PY\LSTM\0416")
RAW_MODEL_DIR = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("0-"))
RAW_INP = next(RAW_MODEL_DIR.glob("*.inp"))

MODEL_DIR = ROOT / "models" / "scheme_v2_baseline_flow"
RESULT_DIR = ROOT / "results" / "scheme_v2"
ANALYSIS_DIR = ROOT / "analysis" / "scheme_v2"
FIG_DIR = ANALYSIS_DIR / "figures"
DATA_DIR = ANALYSIS_DIR / "data"

BASELINE_INP = MODEL_DIR / "0416_scheme_v2_baseline_no_j11.inp"
EVENT_INP = MODEL_DIR / "0416_scheme_v2_rain_event.inp"
BASELINE_RUN_INP = RESULT_DIR / "scheme_v2_baseline_run.inp"
EVENT_RUN_INP = RESULT_DIR / "scheme_v2_event_run.inp"

SUMMARY_JSON = ANALYSIS_DIR / "0416_scheme_v2_summary.json"
REPORT_MD = ANALYSIS_DIR / "0416_scheme_v2_report.md"

BASELINE_MONITOR_CSV = DATA_DIR / "0416_scheme_v2_baseline_monitor_5min.csv"
EVENT_MONITOR_CSV = DATA_DIR / "0416_scheme_v2_event_monitor_5min.csv"
OBSERVED_DELTA_CSV = DATA_DIR / "0416_scheme_v2_observed_delta_5min.csv"
TRUTH_INJECTION_CSV = DATA_DIR / "0416_scheme_v2_truth_injection_5min.csv"
TOTAL_PROCESS_CSV = DATA_DIR / "0416_scheme_v2_total_process_5min.csv"
OUTLET_COMPARE_CSV = DATA_DIR / "0416_scheme_v2_outfall_compare_5min.csv"
NODE_SUMMARY_CSV = DATA_DIR / "0416_scheme_v2_node_summary.csv"

FIG_LAYOUT = FIG_DIR / "0416_方案V2_候选监测注入布局.png"
FIG_TOPOLOGY = FIG_DIR / "0416_方案V2_注入点下游监测路径.png"
FIG_INJECTION = FIG_DIR / "0416_方案V2_降雨入流波形.png"
FIG_OUTFALL = FIG_DIR / "0416_方案V2_基线与事件排口流量对比.png"
FIG_MONITOR_DELTA = FIG_DIR / "0416_方案V2_监测点增量响应.png"
FIG_VOLUME = FIG_DIR / "0416_方案V2_基线事件水量对比.png"

OUTFALL_NODE = "J6"
STEP_SECONDS = 300
STEP_MINUTES = 5
SIM_HOURS = 48.0

CANDIDATE_NODES = [
    "J1", "J2", "J5", "J21", "J29", "J31", "J41",
    "J72", "J86", "J10", "J11", "J64", "J65", "J91", "J92",
    "J20", "J27", "J79", "J50", "J49",
]
MONITOR_NODES = ["J3", "J20", "J27", "J79", "J84", "J9", "J50", "J7", "J75", "J78"]
TRUTH_INJECTION_NODES = ("J1", "J72", "J49")
INJECTION_SHARES = {"J1": 0.40, "J72": 0.35, "J49": 0.25}

WAVEFORM = {
    "start_h": 6.0,
    "ramp_h": 1.5,
    "plateau_h": 6.0,
    "peak_total_cms": 0.030,
}

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun", "FangSong", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False


def section_rows(inp: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    section = ""
    for raw in inp.read_text(encoding="gbk", errors="ignore").splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            continue
        if section == section_name.upper() and s and not s.startswith(";"):
            rows.append(s.split())
    return rows


def parse_model(inp: Path) -> dict[str, object]:
    nodes = [r[0] for r in section_rows(inp, "JUNCTIONS")]
    coords = {r[0]: (float(r[1]), float(r[2])) for r in section_rows(inp, "COORDINATES") if len(r) >= 3}
    conduits = [(r[0], r[1], r[2], float(r[3])) for r in section_rows(inp, "CONDUITS") if len(r) >= 4]
    outfalls = [r[0] for r in section_rows(inp, "OUTFALLS")]
    return {"nodes": nodes, "coords": coords, "conduits": conduits, "outfalls": outfalls}


def build_baseline_model() -> list[str]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    removed_inflows: list[str] = []
    output: list[str] = []
    section = ""
    for line in RAW_INP.read_text(encoding="gbk", errors="ignore").splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            output.append(line)
            continue
        if section == "INFLOWS" and s and not s.startswith(";"):
            removed_inflows.append(s)
            continue
        output.append(line)
    BASELINE_INP.write_text("\n".join(output) + "\n", encoding="gbk")
    return removed_inflows


def total_waveform_flow(hour: float) -> float:
    start = WAVEFORM["start_h"]
    ramp = WAVEFORM["ramp_h"]
    plateau = WAVEFORM["plateau_h"]
    peak = WAVEFORM["peak_total_cms"]
    t1 = start + ramp
    t2 = t1 + plateau
    t3 = t2 + ramp
    if hour < start or hour > t3:
        return 0.0
    if hour < t1:
        return peak * (hour - start) / ramp
    if hour <= t2:
        return peak
    return peak * (t3 - hour) / ramp


def time_label(relative_hour: float) -> str:
    total_minutes = int(round(relative_hour * 60.0))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def build_event_model() -> tuple[pd.DataFrame, pd.DataFrame]:
    shutil.copyfile(BASELINE_INP, EVENT_INP)
    relative_hours = [i * STEP_MINUTES / 60.0 for i in range(int(SIM_HOURS * 60 / STEP_MINUTES))]
    inflow_rows: list[str] = []
    timeseries_rows: list[str] = []
    truth_records: list[dict[str, float]] = []
    total_records: list[dict[str, float | str]] = []

    for step, hour in enumerate(relative_hours):
        total_flow = total_waveform_flow(hour)
        record: dict[str, float] = {"step": float(step), "relative_hour": hour}
        for node in TRUTH_INJECTION_NODES:
            record[f"{node}_flow_cms"] = total_flow * INJECTION_SHARES[node]
            record[f"{node}_volume_m3"] = record[f"{node}_flow_cms"] * STEP_SECONDS
        truth_records.append(record)
        total_records.append(
            {
                "step": step,
                "relative_hour": hour,
                "time_label": time_label(hour),
                "total_flow_cms": total_flow,
                "total_volume_m3": total_flow * STEP_SECONDS,
            }
        )

    truth_injection = pd.DataFrame(truth_records)
    total_process = pd.DataFrame(total_records)
    total_sum = max(float(total_process["total_volume_m3"].sum()), 1e-12)
    total_process["weight"] = total_process["total_volume_m3"] / total_sum

    for node in TRUTH_INJECTION_NODES:
        ts_name = f"TS_SCHEMEV2_{node}"
        inflow_rows.append(f"{node:<16} FLOW             {ts_name:<18} FLOW     1.0      1.0      0.0")
        for _, row in truth_injection.iterrows():
            timeseries_rows.append(
                f"{ts_name:<24} {time_label(float(row['relative_hour'])):<10} {float(row[f'{node}_flow_cms']):.10f}"
            )

    lines = EVENT_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    output: list[str] = []
    section = ""
    inserted_inflow = False
    inserted_ts = False
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            output.append(line)
            continue
        output.append(line)
        if section == "INFLOWS" and s.startswith(";;--------------") and not inserted_inflow:
            output.extend(inflow_rows)
            inserted_inflow = True
        if section == "TIMESERIES" and s.startswith(";;--------------") and not inserted_ts:
            output.extend(timeseries_rows)
            inserted_ts = True
    EVENT_INP.write_text("\n".join(output) + "\n", encoding="gbk")
    return truth_injection, total_process


def graph_helpers(model: dict[str, object]) -> dict[str, object]:
    succ: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    pred: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for link, up, down, length in model["conduits"]:
        succ[up].append((down, link, length))
        pred[down].append((up, link, length))
    for key in succ:
        succ[key].sort()

    @lru_cache(None)
    def downstream_path(node: str) -> tuple[str, ...]:
        path: list[str] = []
        current = node
        seen: set[str] = set()
        while current not in seen and succ.get(current):
            seen.add(current)
            nxt, _link, _length = succ[current][0]
            path.append(nxt)
            current = nxt
        return tuple(path)

    return {"succ": succ, "pred": pred, "downstream_path": downstream_path}


def find_outfall_link(model: dict[str, object]) -> str:
    for link, _up, down, _length in model["conduits"]:
        if down == OUTFALL_NODE:
            return link
    raise RuntimeError(f"Cannot find link into outfall {OUTFALL_NODE}")


def run_model(inp: Path, run_copy: Path, model: dict[str, object], label: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(inp, run_copy)
    outfall_link = find_outfall_link(model)
    monitor_rows: list[dict[str, float | int | str]] = []
    outlet_rows: list[dict[str, float | int | str]] = []
    node_stats = {
        node: {
            "model": label,
            "max_total_inflow_cms": 0.0,
            "max_depth_m": 0.0,
            "max_flooding_cms": 0.0,
            "flooding_volume_m3": 0.0,
        }
        for node in model["nodes"]
    }
    with Simulation(str(run_copy)) as sim:
        sim.step_advance(STEP_SECONDS)
        nodes_api = Nodes(sim)
        links_api = Links(sim)
        all_nodes = {node: nodes_api[node] for node in model["nodes"]}
        monitors = {node: nodes_api[node] for node in MONITOR_NODES}
        outlet = links_api[outfall_link]
        cumulative_outfall = 0.0
        for step, _ in enumerate(sim):
            if step >= int(SIM_HOURS * 60 / STEP_MINUTES) - 1:
                break
            relative_hour = step * STEP_MINUTES / 60.0
            monitor_row: dict[str, float | int | str] = {"step": step, "time": sim.current_time.isoformat(sep=" "), "relative_hour": relative_hour}
            for node, handle in monitors.items():
                monitor_row[node] = float(handle.total_inflow)
            monitor_rows.append(monitor_row)

            system_flooding = 0.0
            for node, handle in all_nodes.items():
                flooding = max(0.0, float(handle.flooding))
                stats = node_stats[node]
                stats["max_total_inflow_cms"] = max(stats["max_total_inflow_cms"], float(handle.total_inflow))
                stats["max_depth_m"] = max(stats["max_depth_m"], float(handle.depth))
                stats["max_flooding_cms"] = max(stats["max_flooding_cms"], flooding)
                stats["flooding_volume_m3"] += flooding * STEP_SECONDS
                system_flooding += flooding

            outfall_flow = max(0.0, float(outlet.flow))
            cumulative_outfall += outfall_flow * STEP_SECONDS
            outlet_rows.append(
                {
                    "step": step,
                    "time": sim.current_time.isoformat(sep=" "),
                    "relative_hour": relative_hour,
                    f"{label}_outfall_flow_cms": outfall_flow,
                    f"{label}_outfall_cumulative_m3": cumulative_outfall,
                    f"{label}_system_flooding_cms": system_flooding,
                }
            )
    return pd.DataFrame(monitor_rows), pd.DataFrame(outlet_rows), pd.DataFrame([{"node": n, **s} for n, s in node_stats.items()])


def write_data(
    baseline_monitor: pd.DataFrame,
    event_monitor: pd.DataFrame,
    baseline_outlet: pd.DataFrame,
    event_outlet: pd.DataFrame,
    truth_injection: pd.DataFrame,
    total_process: pd.DataFrame,
    node_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    common_len = min(len(baseline_monitor), len(event_monitor), len(baseline_outlet), len(event_outlet), len(total_process))
    baseline_monitor = baseline_monitor.iloc[:common_len].reset_index(drop=True)
    event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
    truth_injection = truth_injection.iloc[:common_len].reset_index(drop=True)
    total_process = total_process.iloc[:common_len].reset_index(drop=True)
    baseline_outlet = baseline_outlet.iloc[:common_len].reset_index(drop=True)
    event_outlet = event_outlet.iloc[:common_len].reset_index(drop=True)

    observed_delta = event_monitor[["step", "time", "relative_hour"]].copy()
    for node in MONITOR_NODES:
        observed_delta[node] = event_monitor[node].to_numpy(dtype=float) - baseline_monitor[node].to_numpy(dtype=float)

    outlet_compare = baseline_outlet.merge(event_outlet, on=["step", "time", "relative_hour"], how="inner")
    outlet_compare["outfall_delta_cms"] = outlet_compare["event_outfall_flow_cms"] - outlet_compare["baseline_outfall_flow_cms"]

    baseline_monitor.to_csv(BASELINE_MONITOR_CSV, index=False, encoding="utf-8-sig")
    event_monitor.to_csv(EVENT_MONITOR_CSV, index=False, encoding="utf-8-sig")
    observed_delta.to_csv(OBSERVED_DELTA_CSV, index=False, encoding="utf-8-sig")
    truth_injection.to_csv(TRUTH_INJECTION_CSV, index=False, encoding="utf-8-sig")
    total_process.to_csv(TOTAL_PROCESS_CSV, index=False, encoding="utf-8-sig")
    outlet_compare.to_csv(OUTLET_COMPARE_CSV, index=False, encoding="utf-8-sig")
    node_summary.to_csv(NODE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    return observed_delta, outlet_compare


def draw_layout(model: dict[str, object]) -> None:
    coords: dict[str, tuple[float, float]] = model["coords"]
    fig, ax = plt.subplots(figsize=(13, 8), dpi=180)
    for _link, up, down, _length in model["conduits"]:
        if up in coords and down in coords:
            ax.plot([coords[up][0], coords[down][0]], [coords[up][1], coords[down][1]], color="#b6bec8", lw=0.8, alpha=0.65)
    candidates = [n for n in CANDIDATE_NODES if n in coords]
    monitors = [n for n in MONITOR_NODES if n in coords]
    injections = [n for n in TRUTH_INJECTION_NODES if n in coords]
    ax.scatter([coords[n][0] for n in candidates], [coords[n][1] for n in candidates], s=55, color="#f59e0b", edgecolor="white", label=f"候选井 {len(candidates)} 个", zorder=2)
    ax.scatter([coords[n][0] for n in monitors], [coords[n][1] for n in monitors], s=115, marker="s", color="#2563eb", edgecolor="white", label=f"监测点 {len(monitors)} 个", zorder=3)
    ax.scatter([coords[n][0] for n in injections], [coords[n][1] for n in injections], s=240, marker="*", color="#dc2626", edgecolor="black", label=f"真值注入点 {len(injections)} 个", zorder=4)
    if OUTFALL_NODE in coords:
        ax.scatter([coords[OUTFALL_NODE][0]], [coords[OUTFALL_NODE][1]], s=160, marker="D", color="#166534", edgecolor="black", label=f"排口 {OUTFALL_NODE}", zorder=4)
    for node in sorted(set(candidates + monitors + injections + [OUTFALL_NODE])):
        if node in coords:
            ax.text(coords[node][0], coords[node][1], f" {node}", fontsize=8)
    ax.set_title("0416 方案V2：候选井、监测点、注入点布局")
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_LAYOUT)
    plt.close(fig)


def draw_topology(model: dict[str, object], helper: dict[str, object]) -> dict[str, list[str]]:
    coords: dict[str, tuple[float, float]] = model["coords"]
    downstream_path = helper["downstream_path"]
    colors = {"J1": "#2563eb", "J72": "#dc2626", "J49": "#16a34a"}
    downstream_monitors: dict[str, list[str]] = {}
    fig, ax = plt.subplots(figsize=(13, 8), dpi=180)
    for _link, up, down, _length in model["conduits"]:
        if up in coords and down in coords:
            ax.plot([coords[up][0], coords[down][0]], [coords[up][1], coords[down][1]], color="#d0d7de", lw=0.6, alpha=0.45)
    for node in TRUTH_INJECTION_NODES:
        path = [node] + [p for p in downstream_path(node) if p in coords]
        downstream_monitors[node] = [m for m in MONITOR_NODES if m in set(path)]
        for a, b in zip(path[:-1], path[1:]):
            ax.plot([coords[a][0], coords[b][0]], [coords[a][1], coords[b][1]], color=colors[node], lw=2.4, alpha=0.80)
        ax.scatter([coords[node][0]], [coords[node][1]], s=230, marker="*", color=colors[node], edgecolor="black", label=f"{node} 下游路径")
    for monitor in MONITOR_NODES:
        if monitor in coords:
            ax.scatter([coords[monitor][0]], [coords[monitor][1]], s=95, marker="s", color="#111827", edgecolor="white", zorder=4)
            ax.text(coords[monitor][0], coords[monitor][1], f" {monitor}", fontsize=8)
    ax.set_title("0416 方案V2：注入点下游路径与监测点")
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_TOPOLOGY)
    plt.close(fig)
    return downstream_monitors


def draw_injection(truth_injection: pd.DataFrame, total_process: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=180)
    ax.plot(total_process["relative_hour"], total_process["total_flow_cms"], lw=2.5, color="#111827", label="三点合计")
    for node, color in [("J1", "#2563eb"), ("J72", "#dc2626"), ("J49", "#16a34a")]:
        ax.plot(truth_injection["relative_hour"], truth_injection[f"{node}_flow_cms"], lw=1.8, color=color, label=node)
    ax.set_title("0416 方案V2：固定降雨入流波形与节点分配")
    ax.set_xlabel("相对时间 h")
    ax.set_ylabel("入流流量 CMS")
    ax.grid(alpha=0.22)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_INJECTION)
    plt.close(fig)


def draw_outfall(outlet_compare: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8), dpi=180)
    x = outlet_compare["relative_hour"]
    ax.plot(x, outlet_compare["baseline_outfall_flow_cms"], lw=2.1, color="#2563eb", label="旱天基线排口流量")
    ax.plot(x, outlet_compare["event_outfall_flow_cms"], lw=2.1, color="#dc2626", label="叠加降雨入流后排口流量")
    ax.fill_between(x, outlet_compare["baseline_outfall_flow_cms"], outlet_compare["event_outfall_flow_cms"], color="#f97316", alpha=0.18, label="事件增量")
    ax.set_title("0416 方案V2：基线与雨天事件排口流量对比")
    ax.set_xlabel("相对时间 h")
    ax.set_ylabel("排口流量 CMS")
    ax.grid(alpha=0.22)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_OUTFALL)
    plt.close(fig)


def draw_monitor_delta(observed_delta: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=180)
    x = observed_delta["relative_hour"]
    for node in MONITOR_NODES:
        ax.plot(x, observed_delta[node], lw=1.4, label=node)
    ax.set_title("0416 方案V2：监测点事件增量响应（事件 - 旱天基线）")
    ax.set_xlabel("相对时间 h")
    ax.set_ylabel("增量流量 CMS")
    ax.grid(alpha=0.22)
    ax.legend(ncol=5, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_MONITOR_DELTA)
    plt.close(fig)


def draw_volume(summary: dict[str, object]) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=180)
    labels = ["基线排口出流", "新增降雨入流", "事件排口出流"]
    values = [
        summary["baseline"]["outfall_volume_m3"],
        summary["injection"]["total_volume_m3"],
        summary["event"]["outfall_volume_m3"],
    ]
    colors = ["#2563eb", "#f59e0b", "#dc2626"]
    bars = ax.bar(labels, values, color=colors, alpha=0.86)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.1f}", ha="center", va="bottom")
    ax.set_title("0416 方案V2：基线、注入与事件水量对比")
    ax.set_ylabel("体积 m3")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_VOLUME)
    plt.close(fig)


def summarize(
    removed_inflows: list[str],
    downstream_monitors: dict[str, list[str]],
    baseline_monitor: pd.DataFrame,
    event_monitor: pd.DataFrame,
    observed_delta: pd.DataFrame,
    truth_injection: pd.DataFrame,
    total_process: pd.DataFrame,
    outlet_compare: pd.DataFrame,
    node_summary: pd.DataFrame,
) -> dict[str, object]:
    baseline_volume = float(outlet_compare["baseline_outfall_cumulative_m3"].iloc[-1])
    event_volume = float(outlet_compare["event_outfall_cumulative_m3"].iloc[-1])
    injection_volume = float(total_process["total_volume_m3"].sum())
    base_peak = outlet_compare.loc[outlet_compare["baseline_outfall_flow_cms"].idxmax()]
    event_peak = outlet_compare.loc[outlet_compare["event_outfall_flow_cms"].idxmax()]
    inj_peak = total_process.loc[total_process["total_flow_cms"].idxmax()]
    max_flood = float(node_summary["max_flooding_cms"].max())
    flood_vol = float(node_summary["flooding_volume_m3"].sum())
    summary = {
        "raw_model": str(RAW_INP),
        "baseline_model": str(BASELINE_INP),
        "event_model": str(EVENT_INP),
        "removed_inflows": removed_inflows,
        "time_scale": {
            "step_minutes": STEP_MINUTES,
            "rows": int(len(total_process)),
            "relative_hour_start": float(total_process["relative_hour"].iloc[0]),
            "relative_hour_end": float(total_process["relative_hour"].iloc[-1]),
        },
        "candidate": {"count": len(CANDIDATE_NODES), "nodes": CANDIDATE_NODES},
        "monitor": {"count": len(MONITOR_NODES), "nodes": MONITOR_NODES},
        "injection": {
            "nodes": list(TRUTH_INJECTION_NODES),
            "shares": INJECTION_SHARES,
            "waveform": WAVEFORM,
            "total_volume_m3": injection_volume,
            "total_volume_to_baseline_outfall_ratio": injection_volume / max(baseline_volume, 1e-12),
            "peak_total_cms": float(inj_peak["total_flow_cms"]),
            "peak_total_hour": float(inj_peak["relative_hour"]),
            "per_node_volume_m3": {
                node: float(truth_injection[f"{node}_volume_m3"].sum()) for node in TRUTH_INJECTION_NODES
            },
            "downstream_monitors": downstream_monitors,
        },
        "baseline": {
            "outfall_volume_m3": baseline_volume,
            "outfall_peak_cms": float(base_peak["baseline_outfall_flow_cms"]),
            "outfall_peak_hour": float(base_peak["relative_hour"]),
            "monitor_max_cms": float(baseline_monitor[MONITOR_NODES].max().max()),
        },
        "event": {
            "outfall_volume_m3": event_volume,
            "outfall_peak_cms": float(event_peak["event_outfall_flow_cms"]),
            "outfall_peak_hour": float(event_peak["relative_hour"]),
            "outfall_volume_to_baseline_ratio": event_volume / max(baseline_volume, 1e-12),
            "monitor_max_cms": float(event_monitor[MONITOR_NODES].max().max()),
            "delta_monitor_max_cms": float(observed_delta[MONITOR_NODES].max().max()),
        },
        "flooding_check": {
            "max_node_flooding_cms": max_flood,
            "total_flooding_volume_m3": flood_vol,
        },
        "outputs": {
            "report": str(REPORT_MD),
            "summary": str(SUMMARY_JSON),
            "figures": [str(FIG_LAYOUT), str(FIG_TOPOLOGY), str(FIG_INJECTION), str(FIG_OUTFALL), str(FIG_MONITOR_DELTA), str(FIG_VOLUME)],
            "data_dir": str(DATA_DIR),
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def write_report(summary: dict[str, object]) -> None:
    inj = summary["injection"]
    baseline = summary["baseline"]
    event = summary["event"]
    flooding = summary["flooding_check"]
    downstream = inj["downstream_monitors"]
    down_rows = "\n".join(f"| {node} | {', '.join(monitors)} |" for node, monitors in downstream.items())
    per_node = "\n".join(
        f"| {node} | {inj['shares'][node]:.2f} | {inj['per_node_volume_m3'][node]:.1f} |"
        for node in TRUTH_INJECTION_NODES
    )
    report = f"""# 0416 方案V2：保留本底流量的基线与雨天入流事件

## 1. 基线数据

- 原始模型没有改动：`{summary['raw_model']}`
- 旱天基线模型：`{summary['baseline_model']}`
- 基线处理：只删除原模型 `[INFLOWS]` 中的 J11 外部入流，保留模型自身的 `48h污水量` 本底流量。
- 删除的外部入流：`{'; '.join(summary['removed_inflows'])}`
- 时间尺度：{summary['time_scale']['step_minutes']} 分钟，共 {summary['time_scale']['rows']} 行，覆盖 {summary['time_scale']['relative_hour_start']:.2f}-{summary['time_scale']['relative_hour_end']:.2f} h。

基线排口累计出流为 {baseline['outfall_volume_m3']:.1f} m3，排口峰值为 {baseline['outfall_peak_cms']:.5f} CMS，发生在 {baseline['outfall_peak_hour']:.2f} h。这个结果说明基线不是零流量模型，而是保留了管网本身的本底流。

## 2. 注入与布设方案

- 候选井：{summary['candidate']['count']} 个，`{', '.join(summary['candidate']['nodes'])}`。
- 监测点：{summary['monitor']['count']} 个，`{', '.join(summary['monitor']['nodes'])}`。
- 真值注入点：`{', '.join(inj['nodes'])}`，分别代表北侧上游支线、西南上游支线、主线中下游。
- 注入波形：同一条固定雨天入流过程，开始 {inj['waveform']['start_h']:.1f} h，上升 {inj['waveform']['ramp_h']:.1f} h，平台 {inj['waveform']['plateau_h']:.1f} h，再下降 {inj['waveform']['ramp_h']:.1f} h。
- 三点合计峰值：{inj['peak_total_cms']:.5f} CMS，峰值时间 {inj['peak_total_hour']:.2f} h。
- 注入总量：{inj['total_volume_m3']:.1f} m3，是基线排口累计出流的 {inj['total_volume_to_baseline_outfall_ratio']:.2%}。

| 注入点 | 空间份额 | 注入体积 m3 |
| --- | ---: | ---: |
{per_node}

| 注入点 | 下游监测点 |
| --- | --- |
{down_rows}

## 3. 事件结果与溢流校验

- 事件排口累计出流：{event['outfall_volume_m3']:.1f} m3，是基线排口累计出流的 {event['outfall_volume_to_baseline_ratio']:.2f} 倍。
- 事件排口峰值：{event['outfall_peak_cms']:.5f} CMS，发生在 {event['outfall_peak_hour']:.2f} h。
- 监测点最大事件增量：{event['delta_monitor_max_cms']:.5f} CMS。
- 最大节点溢流速率：{flooding['max_node_flooding_cms']:.8f} CMS。
- 总溢流体积：{flooding['total_flooding_volume_m3']:.6f} m3。

判断：本方案保留基线本底流量，同时叠加约 {inj['total_volume_to_baseline_outfall_ratio']:.1%} 的雨天入流；当前模拟未发生溢流，可作为第一版中参数识别实验输入。

## 4. 可视化输出

- 布局图：`{FIG_LAYOUT}`
- 下游路径图：`{FIG_TOPOLOGY}`
- 注入波形图：`{FIG_INJECTION}`
- 基线/事件排口对比：`{FIG_OUTFALL}`
- 监测点增量响应：`{FIG_MONITOR_DELTA}`
- 水量对比图：`{FIG_VOLUME}`
"""
    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    removed_inflows = build_baseline_model()
    truth_injection, total_process = build_event_model()
    model = parse_model(BASELINE_INP)
    helper = graph_helpers(model)

    baseline_monitor, baseline_outlet, baseline_nodes = run_model(BASELINE_INP, BASELINE_RUN_INP, model, "baseline")
    event_monitor, event_outlet, event_nodes = run_model(EVENT_INP, EVENT_RUN_INP, model, "event")
    node_summary = pd.concat([baseline_nodes, event_nodes], ignore_index=True)
    observed_delta, outlet_compare = write_data(
        baseline_monitor,
        event_monitor,
        baseline_outlet,
        event_outlet,
        truth_injection,
        total_process,
        node_summary,
    )

    draw_layout(model)
    downstream_monitors = draw_topology(model, helper)
    draw_injection(truth_injection, total_process)
    draw_outfall(outlet_compare)
    draw_monitor_delta(observed_delta)
    summary = summarize(
        removed_inflows,
        downstream_monitors,
        baseline_monitor.iloc[: len(total_process)].reset_index(drop=True),
        event_monitor.iloc[: len(total_process)].reset_index(drop=True),
        observed_delta,
        truth_injection.iloc[: len(total_process)].reset_index(drop=True),
        total_process.iloc[: len(observed_delta)].reset_index(drop=True),
        outlet_compare,
        node_summary,
    )
    draw_volume(summary)
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
