from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyswmm import Links, Nodes, Simulation


ROOT = Path(r"E:\PY\LSTM\0416")
RAW_MODEL_DIR = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("0-"))
MODEL_INP = next(RAW_MODEL_DIR.glob("*.inp"))
MODEL_RPT = next(RAW_MODEL_DIR.glob("*.rpt"))

OUTPUT_DIR = ROOT / "analysis" / "ponding_scheme"
RESULT_DIR = ROOT / "results" / "ponding_test"
FIG_DIR = OUTPUT_DIR / "figures"

STRESS_NODE = "J11"
OUTFALL_NODE = "J6"
STRESS_TS_NAME = "TS_J11_PONDING_LONG"
STRESS_INP = RESULT_DIR / "ponding_J11_long_injection.inp"
STRESS_CSV = RESULT_DIR / "ponding_J11_long_injection_timeseries.csv"
STRESS_NODE_CSV = RESULT_DIR / "ponding_J11_long_injection_node_summary.csv"
SUMMARY_JSON = OUTPUT_DIR / "ponding_scheme_summary.json"
REPORT_MD = OUTPUT_DIR / "ponding_scheme_report.md"

FIG_NETWORK = FIG_DIR / "0416_ponding_network_overview.png"
FIG_BASE_FLOOD = FIG_DIR / "0416_ponding_base_flooding_summary.png"
FIG_STRESS_TS = FIG_DIR / "0416_ponding_J11_stress_timeseries.png"
FIG_RETURN = FIG_DIR / "0416_ponding_J11_return_phase.png"
FIG_STRESS_MAP = FIG_DIR / "0416_ponding_J11_stress_max_ponded_map.png"


@dataclass
class Junction:
    name: str
    elevation: float
    max_depth: float
    init_depth: float
    sur_depth: float
    ponded_area: float

    @property
    def rim_elevation(self) -> float:
        return self.elevation + self.max_depth


def read_section_rows(inp_path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            continue
        if section == section_name.upper() and stripped and not stripped.startswith(";"):
            rows.append(stripped.split())
    return rows


def parse_options(inp_path: Path) -> dict[str, str]:
    options: dict[str, str] = {}
    for row in read_section_rows(inp_path, "OPTIONS"):
        if len(row) >= 2:
            options[row[0]] = row[1]
    return options


def parse_junctions(inp_path: Path) -> dict[str, Junction]:
    junctions: dict[str, Junction] = {}
    for row in read_section_rows(inp_path, "JUNCTIONS"):
        if len(row) >= 6:
            junctions[row[0]] = Junction(
                name=row[0],
                elevation=float(row[1]),
                max_depth=float(row[2]),
                init_depth=float(row[3]),
                sur_depth=float(row[4]),
                ponded_area=float(row[5]),
            )
    return junctions


def parse_coordinates(inp_path: Path) -> dict[str, tuple[float, float]]:
    coords: dict[str, tuple[float, float]] = {}
    for row in read_section_rows(inp_path, "COORDINATES"):
        if len(row) >= 3:
            coords[row[0]] = (float(row[1]), float(row[2]))
    return coords


def parse_conduits(inp_path: Path) -> list[tuple[str, str, str]]:
    links: list[tuple[str, str, str]] = []
    for row in read_section_rows(inp_path, "CONDUITS"):
        if len(row) >= 3:
            links.append((row[0], row[1], row[2]))
    return links


def parse_counts(inp_path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            counts[section] = 0
            continue
        if section and stripped and not stripped.startswith(";"):
            counts[section] += 1
    return counts


def parse_rpt_flooding(rpt_path: Path) -> pd.DataFrame:
    lines = rpt_path.read_text(encoding="gbk", errors="ignore").splitlines()
    start = None
    for idx, line in enumerate(lines):
        if "Node Flooding Summary" in line:
            start = idx
            break
    rows: list[dict[str, object]] = []
    if start is None:
        return pd.DataFrame(rows)
    for line in lines[start + 8 : start + 140]:
        stripped = line.strip()
        if not stripped or "Outfall Loading Summary" in stripped:
            break
        parts = stripped.split()
        if len(parts) < 7 or not parts[0].startswith("J"):
            continue
        try:
            rows.append(
                {
                    "node": parts[0],
                    "hours_flooded": float(parts[1]),
                    "max_rate_cms": float(parts[2]),
                    "time_of_max": f"{parts[3]} {parts[4]}",
                    "flood_volume_m3": float(parts[5]) * 1000.0,
                    "max_ponded_depth_m": float(parts[6]),
                }
            )
        except ValueError:
            continue
    return pd.DataFrame(rows)


def parse_rpt_key_lines(rpt_path: Path) -> dict[str, str]:
    flow_keys = [
        "Wet Weather Inflow",
        "External Inflow",
        "External Outflow",
        "Flooding Loss",
        "Final Stored Volume",
    ]
    found: dict[str, str] = {}
    lines = rpt_path.read_text(encoding="gbk", errors="ignore").splitlines()
    for idx, line in enumerate(lines):
        if "Runoff Quantity Continuity" in line:
            for candidate in lines[idx : idx + 25]:
                if "Continuity Error" in candidate:
                    found["Runoff Continuity Error"] = candidate.strip()
                    break
        if "Flow Routing Continuity" in line:
            for candidate in lines[idx : idx + 25]:
                if "Continuity Error" in candidate:
                    found["Flow Routing Continuity Error"] = candidate.strip()
                    break
        for key in flow_keys:
            if key in line:
                found.setdefault(key, line.strip())
    return found


def find_outfall_link(conduits: list[tuple[str, str, str]], outfall_node: str) -> str:
    for link_name, _up, down in conduits:
        if down == outfall_node:
            return link_name
    raise RuntimeError(f"Cannot find conduit flowing into outfall {outfall_node}")


def injection_flow_cms(relative_hour: float) -> float:
    """A deliberately long stress inflow to force ponding and delayed drainage."""
    peak = 2.0
    if relative_hour < 1.0:
        return 0.0
    if relative_hour < 2.0:
        return peak * (relative_hour - 1.0)
    if relative_hour <= 14.0:
        return peak
    if relative_hour <= 15.0:
        return peak * (15.0 - relative_hour)
    return 0.0


def build_stress_inp() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MODEL_INP, STRESS_INP)

    lines = STRESS_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    output: list[str] = []
    section = ""
    inflow_inserted = False
    stress_ts_inserted = False

    stress_rows = [
        f"{STRESS_TS_NAME:<24} {hour:<10} {injection_flow_cms(float(hour)):.6f}"
        for hour in range(0, 49)
    ]

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            output.append(line)
            continue

        if section == "INFLOWS" and stripped and not stripped.startswith(";"):
            # Controlled test: remove original dry/rain-derived external inflow.
            continue

        if section == "TIMESERIES" and stripped and not stripped.startswith(";"):
            # Controlled test: zero all original rain/inflow time series so that
            # only the synthetic J11 inflow drives the system.
            parts = stripped.split()
            if len(parts) >= 3:
                parts[-1] = "0"
                output.append(" ".join(parts))
                continue

        output.append(line)

        if section == "INFLOWS" and stripped.startswith(";;--------------") and not inflow_inserted:
            output.append(f"{STRESS_NODE:<16} FLOW             {STRESS_TS_NAME:<16} FLOW     1.0      1.0      0.0")
            inflow_inserted = True

        if section == "TIMESERIES" and stripped.startswith(";;--------------") and not stress_ts_inserted:
            output.extend(stress_rows)
            stress_ts_inserted = True

    STRESS_INP.write_text("\n".join(output) + "\n", encoding="gbk")


def run_stress_simulation(junctions: dict[str, Junction], conduits: list[tuple[str, str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    outfall_link = find_outfall_link(conduits, OUTFALL_NODE)
    rows: list[dict[str, float | int | str]] = []
    node_stats: dict[str, dict[str, float]] = {
        name: {
            "max_ponded_depth_m": 0.0,
            "max_depth_m": 0.0,
            "max_flooding_cms": 0.0,
            "flooding_volume_m3": 0.0,
            "max_ponded_volume_m3": 0.0,
            "return_volume_after_injection_m3": 0.0,
        }
        for name in junctions
    }
    previous_ponded_by_node = {name: 0.0 for name in junctions}
    previous_system_ponded = 0.0
    cumulative_injection = 0.0
    cumulative_flooding = 0.0
    cumulative_outfall = 0.0
    cumulative_return_after_injection = 0.0
    cumulative_delayed_outfall = 0.0
    min_flooding_rate = 0.0

    with Simulation(str(STRESS_INP)) as sim:
        sim.step_advance(60)
        nodes_api = Nodes(sim)
        links_api = Links(sim)
        nodes = {name: nodes_api[name] for name in junctions}
        stress_node = nodes[STRESS_NODE]
        outfall = links_api[outfall_link]

        for step, _ in enumerate(sim):
            relative_hour = step / 60.0
            dt = 60.0
            injection = injection_flow_cms(relative_hour)
            injection_ended = relative_hour > 15.0

            system_ponded_storage = 0.0
            system_flooding_rate = 0.0
            max_node_ponded_depth = 0.0
            active_ponded_nodes = 0

            for name, node in nodes.items():
                full_depth = float(node.full_depth)
                depth = float(node.depth)
                ponded_depth = max(0.0, depth - full_depth)
                ponded_area = float(node.ponding_area)
                ponded_volume = ponded_depth * ponded_area
                flooding = float(node.flooding)
                min_flooding_rate = min(min_flooding_rate, flooding)

                system_ponded_storage += ponded_volume
                system_flooding_rate += max(0.0, flooding)
                max_node_ponded_depth = max(max_node_ponded_depth, ponded_depth)
                if ponded_depth > 1e-6:
                    active_ponded_nodes += 1

                stats = node_stats[name]
                stats["max_ponded_depth_m"] = max(stats["max_ponded_depth_m"], ponded_depth)
                stats["max_depth_m"] = max(stats["max_depth_m"], depth)
                stats["max_flooding_cms"] = max(stats["max_flooding_cms"], max(0.0, flooding))
                stats["flooding_volume_m3"] += max(0.0, flooding) * dt
                stats["max_ponded_volume_m3"] = max(stats["max_ponded_volume_m3"], ponded_volume)
                if injection_ended and previous_ponded_by_node[name] > ponded_volume:
                    stats["return_volume_after_injection_m3"] += previous_ponded_by_node[name] - ponded_volume
                previous_ponded_by_node[name] = ponded_volume

            outfall_flow = max(0.0, float(outfall.flow))
            cumulative_injection += injection * dt
            cumulative_flooding += system_flooding_rate * dt
            cumulative_outfall += outfall_flow * dt
            if injection_ended:
                cumulative_delayed_outfall += outfall_flow * dt
                if previous_system_ponded > system_ponded_storage:
                    cumulative_return_after_injection += previous_system_ponded - system_ponded_storage

            rows.append(
                {
                    "step": step,
                    "time": sim.current_time.isoformat(sep=" "),
                    "relative_hour": relative_hour,
                    "injection_cms": injection,
                    "cumulative_injection_m3": cumulative_injection,
                    "target_depth_m": float(stress_node.depth),
                    "target_full_depth_m": float(stress_node.full_depth),
                    "target_ponded_depth_m": max(0.0, float(stress_node.depth) - float(stress_node.full_depth)),
                    "target_head_m": float(stress_node.head),
                    "target_flooding_cms": max(0.0, float(stress_node.flooding)),
                    "target_total_inflow_cms": float(stress_node.total_inflow),
                    "target_total_outflow_cms": float(stress_node.total_outflow),
                    "system_flooding_cms": system_flooding_rate,
                    "cumulative_flooding_m3": cumulative_flooding,
                    "system_ponded_storage_m3": system_ponded_storage,
                    "max_node_ponded_depth_m": max_node_ponded_depth,
                    "active_ponded_nodes": active_ponded_nodes,
                    "outfall_flow_cms": outfall_flow,
                    "cumulative_outfall_m3": cumulative_outfall,
                    "cumulative_delayed_outfall_after_injection_m3": cumulative_delayed_outfall,
                    "cumulative_return_after_injection_m3": cumulative_return_after_injection,
                    "min_raw_node_flooding_cms_seen": min_flooding_rate,
                }
            )
            previous_system_ponded = system_ponded_storage

    df = pd.DataFrame(rows)
    node_df = pd.DataFrame(
        [{"node": name, **stats} for name, stats in node_stats.items()]
    ).sort_values("max_ponded_depth_m", ascending=False)
    STRESS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(STRESS_CSV, index=False, encoding="utf-8-sig")
    node_df.to_csv(STRESS_NODE_CSV, index=False, encoding="utf-8-sig")
    return df, node_df


def plot_network(
    coords: dict[str, tuple[float, float]],
    conduits: list[tuple[str, str, str]],
    junctions: dict[str, Junction],
    base_flood: pd.DataFrame,
) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=180)
    for _name, up, down in conduits:
        if up in coords and down in coords:
            x1, y1 = coords[up]
            x2, y2 = coords[down]
            ax.plot([x1, x2], [y1, y2], color="#8f969d", lw=0.8, alpha=0.6, zorder=1)

    node_names = [name for name in junctions if name in coords]
    xs = [coords[name][0] for name in node_names]
    ys = [coords[name][1] for name in node_names]
    rims = [junctions[name].rim_elevation for name in node_names]
    sizes = [35 + 35 * math.sqrt(max(0.0, junctions[name].ponded_area)) for name in node_names]
    sc = ax.scatter(xs, ys, c=rims, s=sizes, cmap="viridis", edgecolor="white", linewidth=0.45, zorder=2)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.82)
    cbar.set_label("Rim elevation (m)")

    flooded_nodes = set(base_flood["node"].tolist()) if not base_flood.empty else set()
    fx = [coords[name][0] for name in flooded_nodes if name in coords]
    fy = [coords[name][1] for name in flooded_nodes if name in coords]
    if fx:
        ax.scatter(fx, fy, facecolors="none", edgecolors="#d62728", s=120, linewidth=1.2, label="Base event ponded nodes", zorder=3)

    for label, color, marker, size in [(STRESS_NODE, "#ff7f0e", "*", 220), (OUTFALL_NODE, "#1f77b4", "s", 130)]:
        if label in coords:
            ax.scatter([coords[label][0]], [coords[label][1]], c=color, marker=marker, s=size, edgecolor="black", linewidth=0.8, label=label, zorder=4)
            ax.text(coords[label][0], coords[label][1], f" {label}", fontsize=9, weight="bold")

    ax.set_title("0416 Ponding Model Network Overview")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_NETWORK)
    plt.close(fig)


def plot_base_flood(base_flood: pd.DataFrame) -> None:
    if base_flood.empty:
        return
    top = base_flood.sort_values("flood_volume_m3", ascending=False).head(15)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=180)
    axes[0].bar(top["node"], top["flood_volume_m3"], color="#2f6f73")
    axes[0].set_title("Base RPT: Top Flood/Ponding Volumes")
    axes[0].set_ylabel("Flood volume reported by SWMM (m3)")
    axes[0].tick_params(axis="x", rotation=45)

    top_depth = base_flood.sort_values("max_ponded_depth_m", ascending=False).head(15)
    axes[1].bar(top_depth["node"], top_depth["max_ponded_depth_m"], color="#bf6f30")
    axes[1].set_title("Base RPT: Top Maximum Ponded Depths")
    axes[1].set_ylabel("Maximum ponded depth (m)")
    axes[1].tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(FIG_BASE_FLOOD)
    plt.close(fig)


def plot_stress_timeseries(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(13, 11), dpi=180, sharex=True)
    x = df["relative_hour"]
    axes[0].plot(x, df["injection_cms"], color="#111111", lw=1.6)
    axes[0].set_ylabel("Injection (CMS)")
    axes[0].set_title("J11 Long Injection Stress Test")

    axes[1].plot(x, df["target_depth_m"], label="J11 depth", color="#1f77b4")
    axes[1].plot(x, df["target_full_depth_m"], label="J11 full depth", color="#d62728", ls="--")
    axes[1].fill_between(x, 0, df["target_ponded_depth_m"], color="#ffbb78", alpha=0.5, label="J11 ponded depth above rim")
    axes[1].set_ylabel("Depth (m)")
    axes[1].legend(loc="upper right")

    axes[2].plot(x, df["system_ponded_storage_m3"], color="#2ca02c", label="System ponded storage")
    axes[2].plot(x, df["cumulative_return_after_injection_m3"], color="#9467bd", label="Computed storage drawdown after injection")
    axes[2].set_ylabel("Volume (m3)")
    axes[2].legend(loc="upper right")

    axes[3].plot(x, df["outfall_flow_cms"], color="#17becf", label="Outfall flow")
    axes[3].plot(x, df["system_flooding_cms"], color="#e377c2", label="System flooding to ponding")
    axes[3].set_xlabel("Relative hour")
    axes[3].set_ylabel("Flow (CMS)")
    axes[3].legend(loc="upper right")
    for ax in axes:
        ax.axvspan(1, 15, color="#dddddd", alpha=0.25)
        ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_STRESS_TS)
    plt.close(fig)


def plot_return_phase(df: pd.DataFrame) -> None:
    post = df[df["relative_hour"] >= 15].copy()
    if post.empty:
        return
    fig, ax1 = plt.subplots(figsize=(12, 5.5), dpi=180)
    x = post["relative_hour"]
    ax1.plot(x, post["system_ponded_storage_m3"], color="#2ca02c", lw=1.8, label="Ponded storage")
    ax1.set_xlabel("Relative hour")
    ax1.set_ylabel("Ponded storage (m3)", color="#2ca02c")
    ax1.tick_params(axis="y", labelcolor="#2ca02c")
    ax1.grid(alpha=0.22)

    ax2 = ax1.twinx()
    ax2.plot(x, post["cumulative_delayed_outfall_after_injection_m3"], color="#1f77b4", lw=1.8, label="Delayed outfall after injection")
    ax2.plot(x, post["cumulative_return_after_injection_m3"], color="#9467bd", lw=1.4, ls="--", label="Storage drawdown after injection")
    ax2.set_ylabel("Cumulative volume (m3)", color="#1f77b4")
    ax2.tick_params(axis="y", labelcolor="#1f77b4")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper right")
    ax1.set_title("Post-Injection Ponded Storage Drawdown")
    fig.tight_layout()
    fig.savefig(FIG_RETURN)
    plt.close(fig)


def plot_stress_map(
    coords: dict[str, tuple[float, float]],
    conduits: list[tuple[str, str, str]],
    node_df: pd.DataFrame,
) -> None:
    node_stats = node_df.set_index("node")
    fig, ax = plt.subplots(figsize=(12, 8), dpi=180)
    for _name, up, down in conduits:
        if up in coords and down in coords:
            x1, y1 = coords[up]
            x2, y2 = coords[down]
            ax.plot([x1, x2], [y1, y2], color="#a0a0a0", lw=0.75, alpha=0.55, zorder=1)
    names = [name for name in node_stats.index if name in coords]
    xs = [coords[name][0] for name in names]
    ys = [coords[name][1] for name in names]
    vals = [float(node_stats.loc[name, "max_ponded_depth_m"]) for name in names]
    sizes = [45 + min(260, 20 * math.sqrt(max(0.0, v))) for v in vals]
    sc = ax.scatter(xs, ys, c=vals, s=sizes, cmap="magma", edgecolor="white", linewidth=0.45, zorder=2)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.82)
    cbar.set_label("Max ponded depth in stress test (m)")
    for label, color, marker, size in [(STRESS_NODE, "#00e5ff", "*", 240), (OUTFALL_NODE, "#79ff69", "s", 130)]:
        if label in coords:
            ax.scatter([coords[label][0]], [coords[label][1]], c=color, marker=marker, s=size, edgecolor="black", linewidth=0.8, label=label, zorder=4)
            ax.text(coords[label][0], coords[label][1], f" {label}", fontsize=9, weight="bold")
    ax.set_title("Stress Test: Maximum Ponded Depth by Node")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_STRESS_MAP)
    plt.close(fig)


def build_summary(
    counts: dict[str, int],
    options: dict[str, str],
    junctions: dict[str, Junction],
    base_flood: pd.DataFrame,
    rpt_lines: dict[str, str],
    stress_df: pd.DataFrame,
    node_df: pd.DataFrame,
) -> dict[str, object]:
    final = stress_df.iloc[-1]
    max_storage_idx = stress_df["system_ponded_storage_m3"].idxmax()
    max_storage_row = stress_df.loc[max_storage_idx]
    top_nodes = node_df.head(15).to_dict(orient="records")
    return {
        "model": {
            "raw_model_dir": str(RAW_MODEL_DIR),
            "inp": str(MODEL_INP),
            "rpt": str(MODEL_RPT),
            "counts": {k: counts.get(k, 0) for k in ["JUNCTIONS", "OUTFALLS", "STORAGE", "CONDUITS", "ORIFICES", "WEIRS", "PUMPS", "SUBCATCHMENTS", "INFLOWS", "TIMESERIES"]},
            "options": {k: options.get(k) for k in ["FLOW_UNITS", "FLOW_ROUTING", "ALLOW_PONDING", "REPORT_STEP", "ROUTING_STEP", "START_DATE", "END_DATE"]},
            "ponded_node_count": sum(1 for j in junctions.values() if j.ponded_area > 0),
            "ponded_area_values_m2": sorted({j.ponded_area for j in junctions.values()}),
            "rim_elevation_min_m": min(j.rim_elevation for j in junctions.values()),
            "rim_elevation_max_m": max(j.rim_elevation for j in junctions.values()),
        },
        "base_rpt": {
            "key_lines": rpt_lines,
            "flooded_node_count": int(len(base_flood)),
            "total_reported_flood_volume_m3": float(base_flood["flood_volume_m3"].sum()) if not base_flood.empty else 0.0,
            "max_reported_ponded_depth_m": float(base_flood["max_ponded_depth_m"].max()) if not base_flood.empty else 0.0,
            "top_flooded_nodes": base_flood.sort_values("flood_volume_m3", ascending=False).head(10).to_dict(orient="records") if not base_flood.empty else [],
        },
        "stress_test": {
            "test_inp": str(STRESS_INP),
            "target_node": STRESS_NODE,
            "peak_injection_cms": 2.0,
            "injection_start_hour": 1.0,
            "injection_end_hour": 15.0,
            "injection_volume_m3": float(final["cumulative_injection_m3"]),
            "max_system_ponded_storage_m3": float(stress_df["system_ponded_storage_m3"].max()),
            "time_of_max_system_ponded_storage": str(max_storage_row["time"]),
            "final_system_ponded_storage_m3": float(final["system_ponded_storage_m3"]),
            "computed_storage_drawdown_after_injection_m3": float(final["cumulative_return_after_injection_m3"]),
            "delayed_outfall_after_injection_m3": float(final["cumulative_delayed_outfall_after_injection_m3"]),
            "total_outfall_volume_m3": float(final["cumulative_outfall_m3"]),
            "total_flooding_to_ponding_m3": float(final["cumulative_flooding_m3"]),
            "max_target_ponded_depth_m": float(stress_df["target_ponded_depth_m"].max()),
            "max_target_flooding_cms": float(stress_df["target_flooding_cms"].max()),
            "max_active_ponded_nodes": int(stress_df["active_ponded_nodes"].max()),
            "min_raw_node_flooding_cms_seen": float(stress_df["min_raw_node_flooding_cms_seen"].min()),
            "top_stress_ponded_nodes": top_nodes,
        },
        "outputs": {
            "summary_json": str(SUMMARY_JSON),
            "report_md": str(REPORT_MD),
            "stress_timeseries_csv": str(STRESS_CSV),
            "stress_node_summary_csv": str(STRESS_NODE_CSV),
            "figures": [str(FIG_NETWORK), str(FIG_BASE_FLOOD), str(FIG_STRESS_TS), str(FIG_RETURN), str(FIG_STRESS_MAP)],
        },
    }


def write_report(summary: dict[str, object]) -> None:
    model = summary["model"]
    base = summary["base_rpt"]
    stress = summary["stress_test"]
    outputs = summary["outputs"]

    top_base = base["top_flooded_nodes"][:8]
    top_stress = stress["top_stress_ponded_nodes"][:8]

    def markdown_table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
        if not rows:
            return "无\\n"
        header = "| " + " | ".join(title for title, _ in columns) + " |"
        sep = "| " + " | ".join("---" for _ in columns) + " |"
        body = []
        for row in rows:
            values = []
            for _title, key in columns:
                value = row.get(key, "")
                if isinstance(value, float):
                    value = f"{value:.3f}"
                values.append(str(value))
            body.append("| " + " | ".join(values) + " |")
        return "\n".join([header, sep, *body])

    text = f"""# 0416 允许积水模型结构与回流测试报告

## 1. 模型结构核查

- 当前模型文件：`{model['inp']}`
- 当前方案：纯 1D 管网 + 节点积水，`ALLOW_PONDING = {model['options'].get('ALLOW_PONDING')}`。
- 结构规模：检查井 {model['counts'].get('JUNCTIONS')} 个，排口 {model['counts'].get('OUTFALLS')} 个，管道 {model['counts'].get('CONDUITS')} 条，子汇水区 {model['counts'].get('SUBCATCHMENTS')} 个。
- 耦合检查：`ORIFICES = {model['counts'].get('ORIFICES')}`，`WEIRS = {model['counts'].get('WEIRS')}`，`STORAGE = {model['counts'].get('STORAGE')}`，说明当前文件没有继续采用 1D/2D 孔口耦合。
- 积水设置：{model['ponded_node_count']} 个检查井设置了非零 Ponding Area，取值为 {model['ponded_area_values_m2']} m2。
- 井盖/满管控制高程：rim elevation 范围为 {model['rim_elevation_min_m']:.3f} 到 {model['rim_elevation_max_m']:.3f} m。

## 2. 原模型 RPT 积水结果

- 径流连续性：{base['key_lines'].get('Runoff Continuity Error', '')}
- 管网水力路由连续性：{base['key_lines'].get('Flow Routing Continuity Error', '')}
- 洪泛损失：{base['key_lines'].get('Flooding Loss', '')}
- 期末存储：{base['key_lines'].get('Final Stored Volume', '')}
- 原 RPT 中发生节点溢流/积水的节点数：{base['flooded_node_count']} 个。
- 原 RPT 报告的总溢流到积水体积：{base['total_reported_flood_volume_m3']:.3f} m3。
- 原 RPT 最大 Ponded Depth：{base['max_reported_ponded_depth_m']:.3f} m。

原 RPT 溢流体积 Top 节点：

{markdown_table(top_base, [('节点', 'node'), ('积水时长 h', 'hours_flooded'), ('最大溢流 CMS', 'max_rate_cms'), ('溢流体积 m3', 'flood_volume_m3'), ('最大积水深 m', 'max_ponded_depth_m')])}

## 3. J11 长时间大流量注水测试

测试设置：清空原模型外部入流，并将原 TIMESERIES 全部置零，只保留 J11 人工注水。注水过程为 1 h 开始、2 h 达到 2.0 CMS、2-14 h 保持 2.0 CMS、15 h 降为 0，随后继续模拟到模型结束。

- 注水总量：{stress['injection_volume_m3']:.3f} m3。
- 最大系统积水暂存量：{stress['max_system_ponded_storage_m3']:.3f} m3，发生时间：{stress['time_of_max_system_ponded_storage']}。
- 期末系统积水暂存量：{stress['final_system_ponded_storage_m3']:.3f} m3。
- 注水结束后的积水暂存消退量：{stress['computed_storage_drawdown_after_injection_m3']:.3f} m3。
- 注水结束后的延迟排口出流量：{stress['delayed_outfall_after_injection_m3']:.3f} m3。
- 总排口出流量：{stress['total_outfall_volume_m3']:.3f} m3。
- J11 最大井上积水深：{stress['max_target_ponded_depth_m']:.3f} m。
- 同时存在积水的最大节点数：{stress['max_active_ponded_nodes']} 个。

判断：Ponding Area 方案没有独立的 2D 孔口，因此不会像 1D/2D 耦合模型那样出现“孔口负流量”。它的回流证据是：节点水深超过满井深后形成 ponded storage，注水结束后 ponded storage 明显下降，同时排口仍持续出流。这个过程代表暂存在节点地表积水区的水重新进入 1D 管网并被排出。

压力测试中最大积水深 Top 节点：

{markdown_table(top_stress, [('节点', 'node'), ('最大积水深 m', 'max_ponded_depth_m'), ('最大溢流 CMS', 'max_flooding_cms'), ('溢流体积 m3', 'flooding_volume_m3'), ('注水后回排量 m3', 'return_volume_after_injection_m3')])}

## 4. 输出文件

- 汇总 JSON：`{outputs['summary_json']}`
- 压力测试逐分钟数据：`{outputs['stress_timeseries_csv']}`
- 压力测试节点统计：`{outputs['stress_node_summary_csv']}`
- 结构图：`{outputs['figures'][0]}`
- 原 RPT 积水统计图：`{outputs['figures'][1]}`
- 压力测试时序图：`{outputs['figures'][2]}`
- 注水后回排阶段图：`{outputs['figures'][3]}`
- 压力测试积水空间分布图：`{outputs['figures'][4]}`
"""
    REPORT_MD.write_text(text, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    counts = parse_counts(MODEL_INP)
    options = parse_options(MODEL_INP)
    junctions = parse_junctions(MODEL_INP)
    coords = parse_coordinates(MODEL_INP)
    conduits = parse_conduits(MODEL_INP)
    base_flood = parse_rpt_flooding(MODEL_RPT)
    rpt_lines = parse_rpt_key_lines(MODEL_RPT)

    build_stress_inp()
    stress_df, node_df = run_stress_simulation(junctions, conduits)

    plot_network(coords, conduits, junctions, base_flood)
    plot_base_flood(base_flood)
    plot_stress_timeseries(stress_df)
    plot_return_phase(stress_df)
    plot_stress_map(coords, conduits, node_df)

    summary = build_summary(counts, options, junctions, base_flood, rpt_lines, stress_df, node_df)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
