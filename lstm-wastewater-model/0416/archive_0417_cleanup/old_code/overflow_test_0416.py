from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyswmm import Links, Nodes, Simulation

from config_0416 import MODEL_2D_INP, OUTFALL_NODE, RESULT_DIR


TARGET_NODE = "J11"
SURFACE_NODE = "J272"
ORIFICE_LINK = "OR10"
INJECTION_TS_NAME = "TS_J11_OVERFLOW_TEST"

OUTPUT_DIR = RESULT_DIR / "overflow_test"
TEST_INP = OUTPUT_DIR / "overflow_J11_2D.inp"
TIMESERIES_CSV = OUTPUT_DIR / "overflow_J11_timeseries.csv"
SUMMARY_JSON = OUTPUT_DIR / "overflow_J11_summary.json"
REPORT_MD = OUTPUT_DIR / "overflow_J11_report.md"
FIG_TIMESERIES = OUTPUT_DIR / "overflow_J11_timeseries.png"
FIG_ORIFICE = OUTPUT_DIR / "overflow_J11_orifice_direction.png"
FIG_CONTEXT = OUTPUT_DIR / "overflow_J11_network_context.png"


def injection_flow_cms(relative_hour: float) -> float:
    """Large single-node injection used to force 1D -> 2D exchange."""
    if relative_hour < 1.0:
        return 0.0
    if relative_hour < 2.0:
        return 8.0 * (relative_hour - 1.0)
    if relative_hour <= 4.0:
        return 8.0
    if relative_hour <= 5.0:
        return 8.0 * (5.0 - relative_hour)
    return 0.0


def read_section_rows(inp_path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    current_section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].upper()
            continue
        if current_section != section_name.upper() or not stripped or stripped.startswith(";"):
            continue
        rows.append(stripped.split())
    return rows


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


def find_outfall_link(inp_path: Path) -> str:
    for link_name, up, down in parse_conduits(inp_path):
        if down == OUTFALL_NODE:
            return link_name
    raise RuntimeError(f"Cannot find conduit flowing into outfall {OUTFALL_NODE}")


def build_overflow_inp() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MODEL_2D_INP, TEST_INP)

    lines = TEST_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    output: list[str] = []
    section = ""
    inflow_inserted = False
    timeseries_inserted = False

    timeseries_rows = []
    for hour in range(0, 49):
        timeseries_rows.append(f"{INJECTION_TS_NAME:<24} {hour:<10} {injection_flow_cms(float(hour)):.6f}")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            output.append(line)
            continue

        if section == "INFLOWS" and stripped and not stripped.startswith(";"):
            # Isolate the test: remove original external inflows and replace
            # them with one deliberately large J11 inflow.
            continue

        output.append(line)
        if section == "INFLOWS" and stripped.startswith(";;--------------") and not inflow_inserted:
            output.append(f"{TARGET_NODE:<16} FLOW             {INJECTION_TS_NAME:<16} FLOW     1.0      1.0      0.0")
            inflow_inserted = True
        if section == "TIMESERIES" and stripped.startswith(";;--------------") and not timeseries_inserted:
            output.extend(timeseries_rows)
            timeseries_inserted = True

    TEST_INP.write_text("\n".join(output) + "\n", encoding="gbk")


def run_overflow_simulation() -> pd.DataFrame:
    outfall_link_name = find_outfall_link(TEST_INP)
    rows: list[dict[str, float | int | str]] = []
    with Simulation(str(TEST_INP)) as sim:
        sim.step_advance(60)
        nodes = Nodes(sim)
        links = Links(sim)
        target = nodes[TARGET_NODE]
        surface = nodes[SURFACE_NODE]
        outfall = nodes[OUTFALL_NODE]
        orifice = links[ORIFICE_LINK]
        outfall_link = links[outfall_link_name]

        for step_idx, _ in enumerate(sim):
            hour = step_idx / 60.0
            rows.append(
                {
                    "step": step_idx,
                    "time": sim.current_time,
                    "relative_hour": hour,
                    "injection_cms": injection_flow_cms(hour),
                    "target_depth_m": float(target.depth),
                    "target_head_m": float(target.head),
                    "target_total_inflow_cms": float(target.total_inflow),
                    "target_total_outflow_cms": float(target.total_outflow),
                    "target_flooding_cms": float(target.flooding),
                    "target_volume_m3": float(target.volume),
                    "surface_depth_m": float(surface.depth),
                    "surface_head_m": float(surface.head),
                    "surface_total_inflow_cms": float(surface.total_inflow),
                    "surface_total_outflow_cms": float(surface.total_outflow),
                    "surface_flooding_cms": float(surface.flooding),
                    "surface_volume_m3": float(surface.volume),
                    "orifice_flow_cms": float(orifice.flow),
                    "orifice_depth_m": float(orifice.depth),
                    "orifice_volume_m3": float(orifice.volume),
                    "outfall_node_total_inflow_cms": float(outfall.total_inflow),
                    "outfall_link_flow_cms": float(outfall_link.flow),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(TIMESERIES_CSV, index=False, encoding="utf-8-sig")
    return df


def make_summary(df: pd.DataFrame) -> dict[str, object]:
    dt_seconds = 60.0
    positive_orifice = df["orifice_flow_cms"].clip(lower=0)
    negative_orifice = (-df["orifice_flow_cms"].clip(upper=0))
    summary = {
        "test_inp": str(TEST_INP),
        "target_node": TARGET_NODE,
        "surface_node": SURFACE_NODE,
        "orifice_link": ORIFICE_LINK,
        "injection_peak_cms": float(df["injection_cms"].max()),
        "injection_volume_m3": float((df["injection_cms"] * dt_seconds).sum()),
        "target_max_depth_m": float(df["target_depth_m"].max()),
        "target_max_head_m": float(df["target_head_m"].max()),
        "target_max_flooding_cms": float(df["target_flooding_cms"].max()),
        "surface_max_depth_m": float(df["surface_depth_m"].max()),
        "surface_max_head_m": float(df["surface_head_m"].max()),
        "surface_max_volume_m3": float(df["surface_volume_m3"].max()),
        "orifice_max_positive_flow_cms_1d_to_2d": float(positive_orifice.max()),
        "orifice_max_negative_flow_cms_2d_to_1d": float(negative_orifice.max()),
        "orifice_positive_volume_m3_1d_to_2d": float((positive_orifice * dt_seconds).sum()),
        "orifice_negative_volume_m3_2d_to_1d": float((negative_orifice * dt_seconds).sum()),
        "outfall_volume_m3": float((df["outfall_link_flow_cms"].clip(lower=0) * dt_seconds).sum()),
        "has_1d_to_2d_exchange": bool(positive_orifice.max() > 1e-6),
        "has_2d_to_1d_backflow": bool(negative_orifice.max() > 1e-6),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def draw_timeseries(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(13, 12), sharex=True)

    axes[0].plot(df["relative_hour"], df["injection_cms"], color="#d62728", lw=2, label="J11 injection")
    axes[0].set_ylabel("CMS")
    axes[0].set_title("J11 overflow stress test")
    axes[0].legend()
    axes[0].grid(alpha=0.25, linestyle="--")

    axes[1].plot(df["relative_hour"], df["target_depth_m"], color="#1f77b4", lw=2, label="J11 depth")
    axes[1].plot(df["relative_hour"], df["surface_depth_m"], color="#ff7f0e", lw=2, label="J272 2D depth")
    axes[1].set_ylabel("m")
    axes[1].legend()
    axes[1].grid(alpha=0.25, linestyle="--")

    axes[2].plot(df["relative_hour"], df["orifice_flow_cms"], color="#2ca02c", lw=2, label="OR10 flow, positive = J11 to J272")
    axes[2].axhline(0, color="#333333", lw=0.8)
    axes[2].set_ylabel("CMS")
    axes[2].legend()
    axes[2].grid(alpha=0.25, linestyle="--")

    axes[3].plot(df["relative_hour"], df["outfall_link_flow_cms"], color="#111111", lw=2, label=f"{OUTFALL_NODE} outfall link flow")
    axes[3].set_ylabel("CMS")
    axes[3].set_xlabel("Relative hour")
    axes[3].legend()
    axes[3].grid(alpha=0.25, linestyle="--")

    fig.tight_layout()
    fig.savefig(FIG_TIMESERIES, dpi=200)
    plt.close(fig)


def draw_orifice_direction(df: pd.DataFrame) -> None:
    positive = df["orifice_flow_cms"].clip(lower=0)
    negative = (-df["orifice_flow_cms"].clip(upper=0))
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.fill_between(df["relative_hour"], 0, positive, color="#d62728", alpha=0.45, label="1D to 2D")
    ax.fill_between(df["relative_hour"], 0, -negative, color="#1f77b4", alpha=0.45, label="2D to 1D")
    ax.axhline(0, color="#333333", lw=0.8)
    ax.set_title("OR10 exchange direction")
    ax.set_xlabel("Relative hour")
    ax.set_ylabel("Flow CMS")
    ax.legend()
    ax.grid(alpha=0.25, linestyle="--")
    fig.tight_layout()
    fig.savefig(FIG_ORIFICE, dpi=200)
    plt.close(fig)


def draw_context() -> None:
    coords = parse_coordinates(TEST_INP)
    links = parse_conduits(TEST_INP)
    jx, jy = coords[TARGET_NODE]
    sx, sy = coords[SURFACE_NODE]

    fig, ax = plt.subplots(figsize=(10, 8))
    for _, up, down in links:
        if up not in coords or down not in coords:
            continue
        x1, y1 = coords[up]
        x2, y2 = coords[down]
        if max(abs(x1 - jx), abs(y1 - jy), abs(x2 - jx), abs(y2 - jy)) > 250:
            continue
        ax.plot([x1, x2], [y1, y2], color="#b8c4d0", lw=0.6, zorder=1)
    for name, (x, y) in coords.items():
        if abs(x - jx) <= 250 and abs(y - jy) <= 250:
            ax.scatter(x, y, s=8, color="#9ca3af", zorder=2)
    ax.scatter([jx], [jy], s=130, marker="^", color="#d62728", edgecolors="black", label=f"Injection node {TARGET_NODE}", zorder=5)
    ax.scatter([sx], [sy], s=130, marker="s", color="#ffbf00", edgecolors="black", label=f"2D node {SURFACE_NODE}", zorder=5)
    ax.plot([jx, sx], [jy, sy], color="#2ca02c", lw=2.5, label=f"Orifice {ORIFICE_LINK}", zorder=4)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("J11 overflow test local topology")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()
    ax.grid(alpha=0.25, linestyle="--")
    fig.tight_layout()
    fig.savefig(FIG_CONTEXT, dpi=200)
    plt.close(fig)


def write_report(summary: dict[str, object]) -> None:
    text = f"""# 0416 J11 单点大注水溢流试验

## 试验设置

- 注水节点：`{TARGET_NODE}`
- 对应 2D 表面节点：`{SURFACE_NODE}`
- 连接孔口：`{ORIFICE_LINK}`
- 注水峰值：{summary["injection_peak_cms"]} CMS
- 注水总量：{summary["injection_volume_m3"]:.2f} m3
- 生成的对比 INP：`{TEST_INP}`

## 关键结果

- J11 最大井内水深：{summary["target_max_depth_m"]:.4f} m
- J272 最大地表/2D 节点水深：{summary["surface_max_depth_m"]:.4f} m
- OR10 最大 1D→2D 流量：{summary["orifice_max_positive_flow_cms_1d_to_2d"]:.4f} CMS
- OR10 最大 2D→1D 回流：{summary["orifice_max_negative_flow_cms_2d_to_1d"]:.4f} CMS
- 1D→2D 交换总量：{summary["orifice_positive_volume_m3_1d_to_2d"]:.2f} m3
- 2D→1D 回流总量：{summary["orifice_negative_volume_m3_2d_to_1d"]:.2f} m3
- 排口累计出流：{summary["outfall_volume_m3"]:.2f} m3

## 如何理解

本试验验证的是 PCSWMM 生成的 1D/2D 孔口耦合：当 J11 注入大量水后，井内水位抬升，水通过 OR10 进入 J272 所在的 2D 表面系统；如果后续地表水头高于地下水头，OR10 会出现负流量，对应 2D→1D 回流。

## 输出文件

- 时间序列数据：`{TIMESERIES_CSV}`
- 汇总数据：`{SUMMARY_JSON}`
- 过程图：`{FIG_TIMESERIES}`
- 孔口方向图：`{FIG_ORIFICE}`
- 局部拓扑图：`{FIG_CONTEXT}`
"""
    REPORT_MD.write_text(text, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_overflow_inp()
    df = run_overflow_simulation()
    summary = make_summary(df)
    draw_timeseries(df)
    draw_orifice_direction(df)
    draw_context()
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
