from __future__ import annotations

import json
import math
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
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

OUTPUT_DIR = ROOT / "analysis" / "baseline_current"
RESULT_DIR = ROOT / "results" / "baseline_current"
FIG_DIR = OUTPUT_DIR / "figures"
BASELINE_ASCII_INP = RESULT_DIR / "baseline_current_ponding.inp"
TIMESERIES_CSV = RESULT_DIR / "baseline_current_timeseries.csv"
NODE_SUMMARY_CSV = RESULT_DIR / "baseline_current_node_summary.csv"
SUMMARY_JSON = OUTPUT_DIR / "baseline_current_summary.json"
REPORT_MD = OUTPUT_DIR / "baseline_current_report.md"

FIG_NETWORK = FIG_DIR / "0416_基线_管网结构与积水节点.png"
FIG_INPUT = FIG_DIR / "0416_基线_输入时序与时间分辨率.png"
FIG_OUTFALL = FIG_DIR / "0416_基线_排口流量与累计出流.png"
FIG_PONDING = FIG_DIR / "0416_基线_节点积水响应.png"
FIG_RANK = FIG_DIR / "0416_基线_积水节点排行.png"
FIG_BALANCE = FIG_DIR / "0416_基线_水量平衡.png"

OUTFALL_NODE = "J6"
DEFAULT_FOCUS_NODES = ["J11", "J62", "J60", "J61", "J9"]

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun", "FangSong", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False


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


def parse_options(inp_path: Path) -> dict[str, str]:
    return {row[0]: row[1] for row in read_section_rows(inp_path, "OPTIONS") if len(row) >= 2}


def parse_junctions(inp_path: Path) -> dict[str, Junction]:
    junctions: dict[str, Junction] = {}
    for row in read_section_rows(inp_path, "JUNCTIONS"):
        if len(row) >= 6:
            junctions[row[0]] = Junction(row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]))
    return junctions


def parse_coordinates(inp_path: Path) -> dict[str, tuple[float, float]]:
    coords: dict[str, tuple[float, float]] = {}
    for row in read_section_rows(inp_path, "COORDINATES"):
        if len(row) >= 3:
            coords[row[0]] = (float(row[1]), float(row[2]))
    return coords


def parse_conduits(inp_path: Path) -> list[tuple[str, str, str, float]]:
    links: list[tuple[str, str, str, float]] = []
    for row in read_section_rows(inp_path, "CONDUITS"):
        if len(row) >= 4:
            links.append((row[0], row[1], row[2], float(row[3])))
    return links


def parse_subcatchments(inp_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in read_section_rows(inp_path, "SUBCATCHMENTS"):
        if len(row) >= 7:
            rows.append({"name": row[0], "outlet": row[2], "area_ha": float(row[3]), "imperv_pct": float(row[4])})
    return pd.DataFrame(rows)


def parse_raingages(inp_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_section_rows(inp_path, "RAINGAGES"):
        if len(row) >= 6:
            rows.append({"name": row[0], "format": row[1], "interval": row[2], "timeseries": row[5]})
    return rows


def parse_inflows(inp_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_section_rows(inp_path, "INFLOWS"):
        if len(row) >= 4:
            rows.append({"node": row[0], "timeseries": row[2], "type": row[3]})
    return rows


def parse_timeseries(inp_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in read_section_rows(inp_path, "TIMESERIES"):
        if len(row) >= 3:
            try:
                rows.append({"name": " ".join(row[:-2]), "time_hour": float(row[-2]), "value": float(row[-1])})
            except ValueError:
                pass
    return pd.DataFrame(rows)


def find_outfall_link(conduits: list[tuple[str, str, str, float]]) -> str:
    for link_name, _up, down, _length in conduits:
        if down == OUTFALL_NODE:
            return link_name
    raise RuntimeError(f"Cannot find conduit flowing into {OUTFALL_NODE}")


def parse_duration_hours(options: dict[str, str]) -> float:
    start = datetime.strptime(f"{options['START_DATE']} {options['START_TIME']}", "%m/%d/%Y %H:%M:%S")
    end = datetime.strptime(f"{options['END_DATE']} {options['END_TIME']}", "%m/%d/%Y %H:%M:%S")
    return (end - start).total_seconds() / 3600.0


def parse_step_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    return int(float(value))


def parse_rpt_summary(rpt_path: Path) -> tuple[dict[str, float], dict[str, float], dict[str, float], pd.DataFrame]:
    lines = rpt_path.read_text(encoding="gbk", errors="ignore").splitlines()
    flow: dict[str, float] = {}
    outfall: dict[str, float] = {}
    time_step: dict[str, float] = {}
    for idx, line in enumerate(lines):
        if "Runoff Quantity Continuity" in line:
            for candidate in lines[idx : idx + 25]:
                if "Continuity Error" in candidate:
                    flow["径流连续性误差_%"] = float(candidate.split()[-1])
                    break
        if "Flow Routing Continuity" in line:
            for candidate in lines[idx : idx + 25]:
                if "Continuity Error" in candidate:
                    flow["路由连续性误差_%"] = float(candidate.split()[-1])
                    break
        for key, label in [
            ("Wet Weather Inflow", "降雨径流入流_m3"),
            ("External Inflow", "外部入流_m3"),
            ("External Outflow", "排口出流_m3"),
            ("Flooding Loss", "洪泛损失_m3"),
            ("Final Stored Volume", "期末存储_m3"),
        ]:
            if key in line:
                flow[label] = float(line.split()[-1]) * 1000.0
        for label, pattern in [
            ("最小实际路由步长_s", "Minimum Time Step"),
            ("平均实际路由步长_s", "Average Time Step"),
            ("最大实际路由步长_s", "Maximum Time Step"),
            ("平均迭代次数", "Average Iterations per Step"),
            ("未收敛步比例_%", "% of Steps Not Converging"),
        ]:
            if pattern in line:
                match = re.search(r"[-+]?\d+(?:\.\d+)?", line.split(":")[-1])
                if match:
                    time_step[label] = float(match.group(0))
        parts = line.split()
        if len(parts) >= 5 and parts[0] == OUTFALL_NODE:
            try:
                outfall = {
                    "流量出现频率_%": float(parts[1]),
                    "平均流量_CMS": float(parts[2]),
                    "最大流量_CMS": float(parts[3]),
                    "总出流_m3": float(parts[4]) * 1000.0,
                }
            except ValueError:
                pass

    flood_rows: list[dict[str, object]] = []
    start = next((i for i, line in enumerate(lines) if "Node Flooding Summary" in line), None)
    if start is not None:
        for line in lines[start + 8 : start + 140]:
            parts = line.split()
            if not parts or "Outfall" in line:
                break
            if len(parts) >= 7 and parts[0].startswith("J"):
                flood_rows.append(
                    {
                        "node": parts[0],
                        "hours_flooded": float(parts[1]),
                        "max_rate_cms": float(parts[2]),
                        "time_of_max": f"{parts[3]} {parts[4]}",
                        "flood_volume_m3": float(parts[5]) * 1000.0,
                        "max_ponded_depth_m": float(parts[6]),
                    }
                )
    return flow, outfall, time_step, pd.DataFrame(flood_rows)


def get_focus_nodes(rpt_flood: pd.DataFrame) -> list[str]:
    focus = list(DEFAULT_FOCUS_NODES)
    if not rpt_flood.empty:
        for name in rpt_flood.sort_values("flood_volume_m3", ascending=False)["node"].head(8):
            if name not in focus:
                focus.append(str(name))
    return focus


def run_baseline_simulation(
    junctions: dict[str, Junction],
    conduits: list[tuple[str, str, str, float]],
    focus_nodes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MODEL_INP, BASELINE_ASCII_INP)
    outfall_link = find_outfall_link(conduits)
    rows: list[dict[str, float | int | str]] = []
    node_stats = {
        name: {
            "max_depth_m": 0.0,
            "max_ponded_depth_m": 0.0,
            "max_flooding_cms": 0.0,
            "flooding_volume_m3": 0.0,
            "max_ponded_volume_m3": 0.0,
            "ponding_minutes": 0.0,
        }
        for name in junctions
    }
    cumulative_outfall = 0.0
    cumulative_flooding = 0.0

    with Simulation(str(BASELINE_ASCII_INP)) as sim:
        sim.step_advance(60)
        nodes_api = Nodes(sim)
        links_api = Links(sim)
        nodes = {name: nodes_api[name] for name in junctions}
        focus = {name: nodes[name] for name in focus_nodes if name in nodes}
        outfall = links_api[outfall_link]
        for step, _ in enumerate(sim):
            dt = 60.0
            system_ponded = 0.0
            system_flooding = 0.0
            active_nodes = 0
            max_ponded_depth = 0.0
            for name, node in nodes.items():
                depth = float(node.depth)
                full_depth = float(node.full_depth)
                ponded_depth = max(0.0, depth - full_depth)
                ponded_volume = ponded_depth * float(node.ponding_area)
                flooding = max(0.0, float(node.flooding))
                stats = node_stats[name]
                stats["max_depth_m"] = max(stats["max_depth_m"], depth)
                stats["max_ponded_depth_m"] = max(stats["max_ponded_depth_m"], ponded_depth)
                stats["max_flooding_cms"] = max(stats["max_flooding_cms"], flooding)
                stats["flooding_volume_m3"] += flooding * dt
                stats["max_ponded_volume_m3"] = max(stats["max_ponded_volume_m3"], ponded_volume)
                if ponded_depth > 1e-6:
                    stats["ponding_minutes"] += 1.0
                    active_nodes += 1
                system_ponded += ponded_volume
                system_flooding += flooding
                max_ponded_depth = max(max_ponded_depth, ponded_depth)

            outfall_flow = max(0.0, float(outfall.flow))
            cumulative_outfall += outfall_flow * dt
            cumulative_flooding += system_flooding * dt
            row: dict[str, float | int | str] = {
                "step": step,
                "time": sim.current_time.isoformat(sep=" "),
                "relative_hour": step / 60.0,
                "outfall_flow_cms": outfall_flow,
                "cumulative_outfall_m3": cumulative_outfall,
                "system_flooding_cms": system_flooding,
                "cumulative_system_flooding_m3": cumulative_flooding,
                "system_ponded_storage_m3": system_ponded,
                "active_ponded_nodes": active_nodes,
                "max_node_ponded_depth_m": max_ponded_depth,
            }
            for name, node in focus.items():
                row[f"{name}_depth_m"] = float(node.depth)
                row[f"{name}_full_depth_m"] = float(node.full_depth)
                row[f"{name}_ponded_depth_m"] = max(0.0, float(node.depth) - float(node.full_depth))
                row[f"{name}_flooding_cms"] = max(0.0, float(node.flooding))
                row[f"{name}_total_inflow_cms"] = float(node.total_inflow)
            rows.append(row)

    sim_df = pd.DataFrame(rows)
    node_df = pd.DataFrame([{"node": name, **stats} for name, stats in node_stats.items()])
    node_df = node_df.sort_values(["flooding_volume_m3", "max_ponded_depth_m"], ascending=False)
    sim_df.to_csv(TIMESERIES_CSV, index=False, encoding="utf-8-sig")
    node_df.to_csv(NODE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    return sim_df, node_df


def plot_network(
    coords: dict[str, tuple[float, float]],
    conduits: list[tuple[str, str, str, float]],
    junctions: dict[str, Junction],
    rpt_flood: pd.DataFrame,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 8), dpi=180)
    for _link, up, down, _length in conduits:
        if up in coords and down in coords:
            ax.plot([coords[up][0], coords[down][0]], [coords[up][1], coords[down][1]], color="#9da3a8", lw=0.8, alpha=0.65)
    names = [name for name in junctions if name in coords]
    sc = ax.scatter(
        [coords[name][0] for name in names],
        [coords[name][1] for name in names],
        c=[junctions[name].rim_elevation for name in names],
        s=62,
        cmap="viridis",
        edgecolor="white",
        linewidth=0.45,
        zorder=2,
    )
    cbar = fig.colorbar(sc, ax=ax, shrink=0.82)
    cbar.set_label("井盖高程 / 满井高程（m）")
    flooded = set(rpt_flood["node"]) if not rpt_flood.empty else set()
    fx = [coords[name][0] for name in flooded if name in coords]
    fy = [coords[name][1] for name in flooded if name in coords]
    if fx:
        ax.scatter(fx, fy, facecolors="none", edgecolors="#d62728", s=130, linewidth=1.2, label="基线发生积水节点")
    for label, color, marker, size in [("J11", "#ff7f0e", "*", 230), (OUTFALL_NODE, "#1f77b4", "s", 130)]:
        if label in coords:
            ax.scatter([coords[label][0]], [coords[label][1]], c=color, marker=marker, s=size, edgecolor="black", linewidth=0.8, label=label, zorder=4)
            ax.text(coords[label][0], coords[label][1], f" {label}", fontsize=10, weight="bold")
    ax.set_title("0416 当前基线：管网结构与积水节点分布")
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_NETWORK)
    plt.close(fig)


def plot_input_timeseries(ts_df: pd.DataFrame, raingages: list[dict[str, str]], inflows: list[dict[str, str]], options: dict[str, str], time_step: dict[str, float]) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), dpi=180)
    for item in raingages:
        one = ts_df[ts_df["name"] == item["timeseries"]]
        if not one.empty:
            axes[0].plot(one["time_hour"], one["value"], lw=1.8, marker="o", ms=2.5, label=item["timeseries"])
    axes[0].set_title("降雨时序（雨量输入）")
    axes[0].set_ylabel("雨量值")
    axes[0].grid(alpha=0.22)
    axes[0].legend(loc="upper right")
    for item in inflows:
        one = ts_df[ts_df["name"] == item["timeseries"]]
        if not one.empty:
            axes[1].plot(one["time_hour"], one["value"], lw=1.8, marker="o", ms=2.5, color="#d62728", label=f"{item['node']} 外部入流")
    axes[1].set_title("外部入流时序")
    axes[1].set_ylabel("流量（m3/s）")
    axes[1].grid(alpha=0.22)
    axes[1].legend(loc="upper right")
    labels = ["报告步长", "湿步长", "旱步长", "设定路由步长", "平均实际路由步长"]
    values = [
        parse_step_seconds(options["REPORT_STEP"]),
        parse_step_seconds(options["WET_STEP"]),
        parse_step_seconds(options["DRY_STEP"]),
        float(options["ROUTING_STEP"]),
        time_step.get("平均实际路由步长_s", float("nan")),
    ]
    axes[2].bar(labels, values, color=["#4c78a8", "#72b7b2", "#72b7b2", "#f58518", "#54a24b"])
    axes[2].set_title("模型时间分辨率")
    axes[2].set_ylabel("秒")
    axes[2].grid(axis="y", alpha=0.22)
    for idx, value in enumerate(values):
        if not math.isnan(value):
            axes[2].text(idx, value, f"{value:g}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_INPUT)
    plt.close(fig)


def plot_outfall(sim_df: pd.DataFrame, outfall: dict[str, float]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 7.5), dpi=180, sharex=True)
    x = sim_df["relative_hour"]
    axes[0].plot(x, sim_df["outfall_flow_cms"], color="#1f77b4", lw=1.6)
    axes[0].set_title("基线排口 J6 流量过程")
    axes[0].set_ylabel("流量（m3/s）")
    axes[0].grid(alpha=0.22)
    max_row = sim_df.loc[sim_df["outfall_flow_cms"].idxmax()]
    axes[0].scatter([max_row["relative_hour"]], [max_row["outfall_flow_cms"]], c="#d62728", zorder=3)
    axes[0].annotate(
        f"峰值 {max_row['outfall_flow_cms']:.3f} m3/s\n{max_row['time']}",
        xy=(max_row["relative_hour"], max_row["outfall_flow_cms"]),
        xytext=(max_row["relative_hour"] + 2, max_row["outfall_flow_cms"] * 0.86),
        arrowprops={"arrowstyle": "->", "color": "#d62728"},
        fontsize=9,
    )
    axes[1].plot(x, sim_df["cumulative_outfall_m3"], color="#2ca02c", lw=1.6)
    axes[1].set_title("基线排口累计出流")
    axes[1].set_xlabel("相对时间（小时）")
    axes[1].set_ylabel("累计出流量（m3）")
    axes[1].grid(alpha=0.22)
    axes[1].text(
        0.01,
        0.92,
        f"RPT 平均 {outfall.get('平均流量_CMS', 0):.3f} m3/s；峰值 {outfall.get('最大流量_CMS', 0):.3f} m3/s；总出流 {outfall.get('总出流_m3', 0):.0f} m3",
        transform=axes[1].transAxes,
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.82},
    )
    fig.tight_layout()
    fig.savefig(FIG_OUTFALL)
    plt.close(fig)


def plot_ponding(sim_df: pd.DataFrame, node_df: pd.DataFrame, focus_nodes: list[str]) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), dpi=180, sharex=True)
    x = sim_df["relative_hour"]
    axes[0].plot(x, sim_df["system_ponded_storage_m3"], color="#2ca02c", lw=1.6, label="系统积水暂存量")
    axes[0].set_title("基线系统积水响应")
    axes[0].set_ylabel("暂存量（m3）")
    axes[0].grid(alpha=0.22)
    axes[0].legend(loc="upper right")
    axes[1].plot(x, sim_df["active_ponded_nodes"], color="#ff7f0e", lw=1.6)
    axes[1].set_title("同时发生积水的节点数量")
    axes[1].set_ylabel("节点数")
    axes[1].grid(alpha=0.22)
    for name in focus_nodes[:6]:
        col = f"{name}_ponded_depth_m"
        if col in sim_df.columns:
            axes[2].plot(x, sim_df[col], lw=1.2, label=name)
    axes[2].set_title("重点节点井上积水深")
    axes[2].set_xlabel("相对时间（小时）")
    axes[2].set_ylabel("积水深（m）")
    axes[2].grid(alpha=0.22)
    axes[2].legend(loc="upper right", ncol=3)
    max_row = sim_df.loc[sim_df["system_ponded_storage_m3"].idxmax()]
    axes[0].scatter([max_row["relative_hour"]], [max_row["system_ponded_storage_m3"]], c="#d62728", zorder=3)
    axes[0].annotate(
        f"峰值 {max_row['system_ponded_storage_m3']:.1f} m3\n{max_row['time']}",
        xy=(max_row["relative_hour"], max_row["system_ponded_storage_m3"]),
        xytext=(max_row["relative_hour"] + 2, max_row["system_ponded_storage_m3"] * 0.84),
        arrowprops={"arrowstyle": "->", "color": "#d62728"},
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(FIG_PONDING)
    plt.close(fig)

    top = node_df.head(18)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=180)
    axes[0].bar(top["node"], top["flooding_volume_m3"], color="#2f6f73")
    axes[0].set_title("溢流/积水体积 Top 节点")
    axes[0].set_ylabel("体积（m3）")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(axis="y", alpha=0.2)
    axes[1].bar(top["node"], top["max_ponded_depth_m"], color="#bf6f30")
    axes[1].set_title("最大井上积水深 Top 节点")
    axes[1].set_ylabel("积水深（m）")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_RANK)
    plt.close(fig)


def plot_balance(flow: dict[str, float]) -> None:
    labels = ["降雨径流入流", "外部入流", "排口出流", "期末存储", "洪泛损失"]
    values = [flow.get(k, 0.0) for k in ["降雨径流入流_m3", "外部入流_m3", "排口出流_m3", "期末存储_m3", "洪泛损失_m3"]]
    fig, ax = plt.subplots(figsize=(11, 6), dpi=180)
    bars = ax.bar(labels, values, color=["#4c78a8", "#f58518", "#54a24b", "#b279a2", "#e45756"])
    ax.set_title("基线水量平衡（RPT 汇总）")
    ax.set_ylabel("体积（m3）")
    ax.grid(axis="y", alpha=0.22)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.0f}", ha="center", va="bottom", fontsize=10)
    ax.text(
        0.02,
        0.92,
        f"路由连续性误差：{flow.get('路由连续性误差_%', 0):.3f}%",
        transform=ax.transAxes,
        fontsize=11,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.82},
    )
    fig.tight_layout()
    fig.savefig(FIG_BALANCE)
    plt.close(fig)


def table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    if not rows:
        return "无\n"
    header = "| " + " | ".join(title for title, _ in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        vals = []
        for _title, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = f"{value:.3f}"
            vals.append(str(value))
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep, *body])


def build_summary_and_report(
    counts: dict[str, int],
    options: dict[str, str],
    junctions: dict[str, Junction],
    conduits: list[tuple[str, str, str, float]],
    subcatchments: pd.DataFrame,
    raingages: list[dict[str, str]],
    inflows: list[dict[str, str]],
    ts_df: pd.DataFrame,
    flow: dict[str, float],
    outfall: dict[str, float],
    time_step: dict[str, float],
    rpt_flood: pd.DataFrame,
    sim_df: pd.DataFrame,
    node_df: pd.DataFrame,
    focus_nodes: list[str],
) -> dict[str, object]:
    max_outfall = sim_df.loc[sim_df["outfall_flow_cms"].idxmax()]
    max_ponding = sim_df.loc[sim_df["system_ponded_storage_m3"].idxmax()]
    first_ponding = sim_df[sim_df["active_ponded_nodes"] > 0].head(1)
    last_ponding = sim_df[sim_df["active_ponded_nodes"] > 0].tail(1)
    ts_summary = (
        ts_df.groupby("name")
        .agg(点数=("value", "count"), 最大值=("value", "max"), 总和=("value", "sum"), 起始小时=("time_hour", "min"), 结束小时=("time_hour", "max"))
        .reset_index()
        .to_dict(orient="records")
        if not ts_df.empty
        else []
    )
    summary: dict[str, object] = {
        "model": {
            "inp": str(MODEL_INP),
            "rpt": str(MODEL_RPT),
            "counts": {k: counts.get(k, 0) for k in ["JUNCTIONS", "OUTFALLS", "CONDUITS", "SUBCATCHMENTS", "INFLOWS", "TIMESERIES", "ORIFICES", "STORAGE"]},
            "duration_hours": parse_duration_hours(options),
            "report_step_seconds": parse_step_seconds(options["REPORT_STEP"]),
            "wet_step_seconds": parse_step_seconds(options["WET_STEP"]),
            "dry_step_seconds": parse_step_seconds(options["DRY_STEP"]),
            "routing_step_seconds": float(options["ROUTING_STEP"]),
            "ponded_node_count": sum(1 for j in junctions.values() if j.ponded_area > 0),
            "ponded_area_values_m2": sorted({j.ponded_area for j in junctions.values()}),
            "total_conduit_length_m": sum(length for *_nodes, length in conduits),
            "total_subcatchment_area_ha": float(subcatchments["area_ha"].sum()) if not subcatchments.empty else 0.0,
            "options": options,
        },
        "input": {"raingages": raingages, "external_inflows": inflows, "timeseries_summary": ts_summary},
        "rpt": {
            "flow_continuity": flow,
            "outfall_summary": outfall,
            "time_step_stats": time_step,
            "flooded_node_count": int(len(rpt_flood)),
            "total_rpt_flood_volume_m3": float(rpt_flood["flood_volume_m3"].sum()) if not rpt_flood.empty else 0.0,
            "max_rpt_ponded_depth_m": float(rpt_flood["max_ponded_depth_m"].max()) if not rpt_flood.empty else 0.0,
            "top_rpt_flood_nodes": rpt_flood.sort_values("flood_volume_m3", ascending=False).head(15).to_dict(orient="records") if not rpt_flood.empty else [],
        },
        "simulation": {
            "rows": int(len(sim_df)),
            "start_time": str(sim_df.iloc[0]["time"]),
            "end_time": str(sim_df.iloc[-1]["time"]),
            "outfall_peak_cms": float(max_outfall["outfall_flow_cms"]),
            "outfall_peak_time": str(max_outfall["time"]),
            "sim_integrated_outfall_m3": float(sim_df.iloc[-1]["cumulative_outfall_m3"]),
            "max_system_ponded_storage_m3": float(max_ponding["system_ponded_storage_m3"]),
            "max_system_ponded_storage_time": str(max_ponding["time"]),
            "max_active_ponded_nodes": int(sim_df["active_ponded_nodes"].max()),
            "first_ponding": first_ponding[["time", "relative_hour", "active_ponded_nodes", "system_ponded_storage_m3"]].to_dict(orient="records"),
            "last_ponding": last_ponding[["time", "relative_hour", "active_ponded_nodes", "system_ponded_storage_m3"]].to_dict(orient="records"),
            "top_sim_ponding_nodes": node_df.head(15).to_dict(orient="records"),
            "focus_nodes": focus_nodes,
        },
        "outputs": {
            "report_md": str(REPORT_MD),
            "summary_json": str(SUMMARY_JSON),
            "timeseries_csv": str(TIMESERIES_CSV),
            "node_summary_csv": str(NODE_SUMMARY_CSV),
            "figures": [str(FIG_NETWORK), str(FIG_INPUT), str(FIG_OUTFALL), str(FIG_PONDING), str(FIG_RANK), str(FIG_BALANCE)],
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    model = summary["model"]
    rpt = summary["rpt"]
    sim = summary["simulation"]
    text = f"""# 0416 当前基线数据分析报告

## 1. 基础情况

- 当前模型：`{model['inp']}`
- 模拟时段：`{options['START_DATE']} {options['START_TIME']}` 到 `{options['END_DATE']} {options['END_TIME']}`，总时长 {model['duration_hours']:.1f} 小时。
- 时间分辨率：报告步长 {model['report_step_seconds']} 秒，湿步长 {model['wet_step_seconds']} 秒，旱步长 {model['dry_step_seconds']} 秒，设定动力波路由步长 {model['routing_step_seconds']:.0f} 秒。
- RPT 实际路由步长：最小 {time_step.get('最小实际路由步长_s', 0):.2f} 秒，平均 {time_step.get('平均实际路由步长_s', 0):.2f} 秒，最大 {time_step.get('最大实际路由步长_s', 0):.2f} 秒。
- 结构规模：检查井 {model['counts']['JUNCTIONS']} 个，排口 {model['counts']['OUTFALLS']} 个，管道 {model['counts']['CONDUITS']} 条，子汇水区 {model['counts']['SUBCATCHMENTS']} 个。
- 管道总长度约 {model['total_conduit_length_m']:.1f} m，汇水面积合计约 {model['total_subcatchment_area_ha']:.3f} ha。
- 积水设置：`ALLOW_PONDING = {options.get('ALLOW_PONDING')}`，{model['ponded_node_count']} 个节点设置 Ponding Area，取值 {model['ponded_area_values_m2']} m2。

## 2. 基线流量与水量平衡

- 降雨径流入流：{flow.get('降雨径流入流_m3', 0):.0f} m3。
- 外部入流：{flow.get('外部入流_m3', 0):.0f} m3。
- 排口出流：{flow.get('排口出流_m3', 0):.0f} m3。
- 期末存储：{flow.get('期末存储_m3', 0):.0f} m3。
- 洪泛损失：{flow.get('洪泛损失_m3', 0):.0f} m3。
- 路由连续性误差：{flow.get('路由连续性误差_%', 0):.3f}%。
- 排口 J6：平均流量 {outfall.get('平均流量_CMS', 0):.3f} m3/s，峰值流量 {outfall.get('最大流量_CMS', 0):.3f} m3/s，RPT 总出流 {outfall.get('总出流_m3', 0):.0f} m3。
- 逐分钟复跑积分：排口峰值 {sim['outfall_peak_cms']:.3f} m3/s，发生在 {sim['outfall_peak_time']}；积分总出流 {sim['sim_integrated_outfall_m3']:.0f} m3。

输入时序概况：

{table(ts_summary, [('时序名称', 'name'), ('点数', '点数'), ('最大值', '最大值'), ('总和', '总和'), ('起始小时', '起始小时'), ('结束小时', '结束小时')])}

## 3. 节点积水响应

- RPT 中发生溢流/积水的节点数：{rpt['flooded_node_count']} 个。
- RPT 报告的溢流到积水体积合计：{rpt['total_rpt_flood_volume_m3']:.0f} m3。
- RPT 最大 Ponded Depth：{rpt['max_rpt_ponded_depth_m']:.3f} m。
- 逐分钟复跑中，系统最大积水暂存量 {sim['max_system_ponded_storage_m3']:.3f} m3，发生在 {sim['max_system_ponded_storage_time']}。
- 同时发生积水的最大节点数：{sim['max_active_ponded_nodes']} 个。
- 首次出现积水：{sim['first_ponding']}。
- 最后仍有积水：{sim['last_ponding']}。

逐分钟复跑积水响应 Top 节点：

{table(sim['top_sim_ponding_nodes'][:10], [('节点', 'node'), ('最大积水深 m', 'max_ponded_depth_m'), ('最大溢流 CMS', 'max_flooding_cms'), ('溢流体积 m3', 'flooding_volume_m3'), ('积水分钟', 'ponding_minutes')])}

## 4. 输出文件

- 中文结构图：`{FIG_NETWORK}`
- 中文输入与时间分辨率图：`{FIG_INPUT}`
- 中文排口流量图：`{FIG_OUTFALL}`
- 中文积水响应图：`{FIG_PONDING}`
- 中文积水节点排行图：`{FIG_RANK}`
- 中文水量平衡图：`{FIG_BALANCE}`
- 逐分钟基线数据：`{TIMESERIES_CSV}`
- 节点响应统计：`{NODE_SUMMARY_CSV}`
"""
    REPORT_MD.write_text(text, encoding="utf-8")
    return summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    counts = parse_counts(MODEL_INP)
    options = parse_options(MODEL_INP)
    junctions = parse_junctions(MODEL_INP)
    coords = parse_coordinates(MODEL_INP)
    conduits = parse_conduits(MODEL_INP)
    subcatchments = parse_subcatchments(MODEL_INP)
    raingages = parse_raingages(MODEL_INP)
    inflows = parse_inflows(MODEL_INP)
    ts_df = parse_timeseries(MODEL_INP)
    flow, outfall, time_step, rpt_flood = parse_rpt_summary(MODEL_RPT)
    focus_nodes = get_focus_nodes(rpt_flood)

    sim_df, node_df = run_baseline_simulation(junctions, conduits, focus_nodes)

    plot_network(coords, conduits, junctions, rpt_flood)
    plot_input_timeseries(ts_df, raingages, inflows, options, time_step)
    plot_outfall(sim_df, outfall)
    plot_ponding(sim_df, node_df, focus_nodes)
    plot_balance(flow)

    summary = build_summary_and_report(
        counts,
        options,
        junctions,
        conduits,
        subcatchments,
        raingages,
        inflows,
        ts_df,
        flow,
        outfall,
        time_step,
        rpt_flood,
        sim_df,
        node_df,
        focus_nodes,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
