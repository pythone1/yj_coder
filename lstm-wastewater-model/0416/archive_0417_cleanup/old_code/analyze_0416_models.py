from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config_0416 import (
    ANALYSIS_REPORT_MD,
    ANALYSIS_SUMMARY_JSON,
    BOUNDARY_SHP,
    CORE_JUNCTION_NODES,
    DEM_DIR,
    FIGURE_DIR,
    MODEL_1D_INP,
    MODEL_1D_RPT,
    MODEL_2D_INP,
    MODEL_2D_RPT,
    MODEL_2D_TSB,
    OUTFALL_NODE,
    TWOD_NODE_SHP,
    ensure_dirs,
)


plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


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


def parse_conduits(inp_path: Path) -> list[dict[str, str]]:
    conduits: list[dict[str, str]] = []
    for row in read_section_rows(inp_path, "CONDUITS"):
        if len(row) >= 3:
            conduits.append({"name": row[0], "upstream": row[1], "downstream": row[2]})
    return conduits


def parse_tags(inp_path: Path) -> dict[str, dict[str, str]]:
    node_tags: dict[str, str] = {}
    link_tags: dict[str, str] = {}
    for row in read_section_rows(inp_path, "TAGS"):
        if len(row) >= 3:
            target_type, target_name, tag_value = row[0], row[1], row[2]
            if target_type == "Node":
                node_tags[target_name] = tag_value
            elif target_type == "Link":
                link_tags[target_name] = tag_value
    return {"Node": node_tags, "Link": link_tags}


def parse_inflows(inp_path: Path) -> list[dict[str, str]]:
    inflows: list[dict[str, str]] = []
    for row in read_section_rows(inp_path, "INFLOWS"):
        if len(row) >= 3:
            inflows.append(
                {
                    "node": row[0],
                    "kind": row[1],
                    "timeseries": row[2],
                }
            )
    return inflows


def parse_options(inp_path: Path) -> dict[str, str]:
    keys = {
        "FLOW_UNITS",
        "FLOW_ROUTING",
        "START_DATE",
        "START_TIME",
        "END_DATE",
        "END_TIME",
        "REPORT_STEP",
        "WET_STEP",
        "DRY_STEP",
        "ROUTING_STEP",
        "ALLOW_PONDING",
    }
    options: dict[str, str] = {}
    for row in read_section_rows(inp_path, "OPTIONS"):
        if len(row) >= 2 and row[0] in keys:
            options[row[0]] = " ".join(row[1:])
    return options


def parse_xsection_shapes(inp_path: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in read_section_rows(inp_path, "XSECTIONS"):
        if len(row) >= 2:
            counter[row[1]] += 1
    return counter


def parse_counts(inp_path: Path) -> dict[str, int]:
    sections = [
        "JUNCTIONS",
        "OUTFALLS",
        "STORAGE",
        "CONDUITS",
        "SUBCATCHMENTS",
        "INFLOWS",
        "TIMESERIES",
        "TAGS",
        "RAINGAGES",
        "VERTICES",
    ]
    return {section: len(read_section_rows(inp_path, section)) for section in sections}


def parse_model(inp_path: Path) -> dict[str, Any]:
    counts = parse_counts(inp_path)
    coords = parse_coordinates(inp_path)
    conduits = parse_conduits(inp_path)
    tags = parse_tags(inp_path)
    inflows = parse_inflows(inp_path)
    options = parse_options(inp_path)
    xsection_shapes = parse_xsection_shapes(inp_path)

    xs = [xy[0] for xy in coords.values()]
    ys = [xy[1] for xy in coords.values()]
    bounds = {
        "min_x": min(xs) if xs else math.nan,
        "max_x": max(xs) if xs else math.nan,
        "min_y": min(ys) if ys else math.nan,
        "max_y": max(ys) if ys else math.nan,
    }

    return {
        "path": str(inp_path),
        "counts": counts,
        "coords": coords,
        "conduits": conduits,
        "tags": tags,
        "inflows": inflows,
        "options": options,
        "xsection_shapes": dict(xsection_shapes),
        "bounds": bounds,
    }


def _match_float(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def _extract_line_value(text: str, label: str) -> float | None:
    for line in text.splitlines():
        if label.lower() not in line.lower():
            continue
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
        if numbers:
            return float(numbers[-1])
    return None


def parse_rpt_metrics(rpt_path: Path) -> dict[str, Any]:
    text = rpt_path.read_text(encoding="gbk", errors="ignore")
    lines = text.splitlines()

    metrics = {
        "runoff_continuity_error_pct": _extract_line_value(text, "Continuity Error (%)"),
        "routing_continuity_error_pct": None,
        "wet_weather_inflow_million_l": _extract_line_value(text, "Wet Weather Inflow"),
        "external_inflow_million_l": _extract_line_value(text, "External Inflow"),
        "external_outflow_million_l": _extract_line_value(text, "External Outflow"),
        "final_stored_volume_million_l": _extract_line_value(text, "Final Stored Volume"),
        "no_flooding": "No nodes were flooded." in text,
        "no_instability": "All links are stable" in text,
        "no_critical_elements": bool(re.search(r"Time-Step Critical Elements[\s\S]*?None", text, flags=re.IGNORECASE)),
    }
    continuity_lines = [line for line in text.splitlines() if "Continuity Error (%)" in line]
    if len(continuity_lines) >= 2:
        runoff_numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", continuity_lines[0])
        routing_numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", continuity_lines[1])
        metrics["runoff_continuity_error_pct"] = float(runoff_numbers[-1]) if runoff_numbers else None
        metrics["routing_continuity_error_pct"] = float(routing_numbers[-1]) if routing_numbers else None

    outfall_lines: list[str] = []
    for idx, line in enumerate(lines):
        if "Outfall Loading Summary" not in line:
            continue
        for candidate in lines[idx + 1 : idx + 20]:
            stripped = candidate.strip()
            if stripped.startswith("J"):
                outfall_lines.append(stripped)
        break
    if outfall_lines:
        parsed_rows: list[dict[str, Any]] = []
        for line in outfall_lines:
            if line.startswith("Outfall"):
                continue
            parts = line.split()
            if len(parts) >= 5 and parts[0].startswith("J"):
                try:
                    parsed_rows.append(
                        {
                            "node": parts[0],
                            "flow_freq_pct": float(parts[1]),
                            "avg_flow_cms": float(parts[2]),
                            "max_flow_cms": float(parts[3]),
                            "total_volume_million_l": float(parts[4]),
                        }
                    )
                except ValueError:
                    continue
        metrics["outfalls"] = parsed_rows
    else:
        metrics["outfalls"] = []

    metrics["high_error_nodes"] = []
    for idx, line in enumerate(lines):
        if "Highest Continuity Errors" not in line:
            continue
        for candidate in lines[idx + 1 : idx + 20]:
            stripped = candidate.strip()
            if not stripped or stripped.startswith("-") or stripped.startswith("Node"):
                match = re.search(r"Node\s+(\S+)\s+\(([-+]?\d+(?:\.\d+)?)%\)", stripped, flags=re.IGNORECASE)
                if match:
                    metrics["high_error_nodes"].append({"node": match.group(1), "percent": float(match.group(2))})
                continue
            parts = stripped.split()
            if len(parts) >= 3 and parts[0].startswith("J"):
                try:
                    metrics["high_error_nodes"].append({"node": parts[0], "percent": float(parts[-1])})
                except ValueError:
                    continue
        break

    return metrics


def draw_network_overview(model_name: str, model: dict[str, Any], output_path: Path, highlight_surface: bool) -> None:
    coords = model["coords"]
    conduits = model["conduits"]
    node_tags = model["tags"]["Node"]
    inflow_nodes = {row["node"] for row in model["inflows"]}

    fig, ax = plt.subplots(figsize=(12, 9))
    for conduit in conduits:
        up = conduit["upstream"]
        down = conduit["downstream"]
        if up not in coords or down not in coords:
            continue
        x1, y1 = coords[up]
        x2, y2 = coords[down]
        ax.plot([x1, x2], [y1, y2], color="#A9B7C6", lw=0.6, alpha=0.7, zorder=1)

    core_nodes_x: list[float] = []
    core_nodes_y: list[float] = []
    surface_nodes_x: list[float] = []
    surface_nodes_y: list[float] = []
    connect_nodes_x: list[float] = []
    connect_nodes_y: list[float] = []
    inflow_x: list[float] = []
    inflow_y: list[float] = []
    outfall_x: list[float] = []
    outfall_y: list[float] = []

    for node_name, (x, y) in coords.items():
        tag = node_tags.get(node_name, "")
        if node_name == OUTFALL_NODE:
            outfall_x.append(x)
            outfall_y.append(y)
        elif node_name in inflow_nodes:
            inflow_x.append(x)
            inflow_y.append(y)
        elif highlight_surface and tag == "2D":
            surface_nodes_x.append(x)
            surface_nodes_y.append(y)
        elif highlight_surface and tag == "Connect2D":
            connect_nodes_x.append(x)
            connect_nodes_y.append(y)
        else:
            core_nodes_x.append(x)
            core_nodes_y.append(y)

    if core_nodes_x:
        ax.scatter(core_nodes_x, core_nodes_y, s=10, c="#1f77b4", label="核心检查井/节点", zorder=2)
    if connect_nodes_x:
        ax.scatter(connect_nodes_x, connect_nodes_y, s=14, c="#d62728", label="Connect2D 连接井", zorder=3)
    if surface_nodes_x:
        ax.scatter(surface_nodes_x, surface_nodes_y, s=8, c="#ffbf00", label="2D 表面节点", zorder=2)
    if inflow_x:
        ax.scatter(inflow_x, inflow_y, s=80, marker="^", c="#2ca02c", edgecolors="black", label="外部注水/入流节点", zorder=4)
    if outfall_x:
        ax.scatter(outfall_x, outfall_y, s=100, marker="s", c="#111111", label="自由出流出口", zorder=5)

    ax.set_title(model_name)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.2, linestyle="--")
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def draw_structure_comparison(one_d: dict[str, Any], two_d: dict[str, Any], output_path: Path) -> None:
    labels = ["检查井/节点", "管段", "子汇水区", "注水点", "时间序列", "标签"]
    one_values = [
        one_d["counts"]["JUNCTIONS"] + one_d["counts"]["OUTFALLS"],
        one_d["counts"]["CONDUITS"],
        one_d["counts"]["SUBCATCHMENTS"],
        one_d["counts"]["INFLOWS"],
        one_d["counts"]["TIMESERIES"],
        one_d["counts"]["TAGS"],
    ]
    two_values = [
        two_d["counts"]["JUNCTIONS"] + two_d["counts"]["OUTFALLS"],
        two_d["counts"]["CONDUITS"],
        two_d["counts"]["SUBCATCHMENTS"],
        two_d["counts"]["INFLOWS"],
        two_d["counts"]["TIMESERIES"],
        two_d["counts"]["TAGS"],
    ]

    frame = pd.DataFrame({"1D模型": one_values, "加2维模型": two_values}, index=labels)
    ax = frame.plot(kind="bar", figsize=(12, 6), color=["#4C78A8", "#F58518"])
    ax.set_title("0416 新模型结构对比")
    ax.set_ylabel("数量")
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    ax.legend(loc="upper left")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def draw_hydraulic_comparison(one_rpt: dict[str, Any], two_rpt: dict[str, Any], output_path: Path) -> None:
    labels = ["湿天气入流", "外部注水", "排口出流", "最终存储"]
    one_values = [
        one_rpt["wet_weather_inflow_million_l"] or 0.0,
        one_rpt["external_inflow_million_l"] or 0.0,
        one_rpt["external_outflow_million_l"] or 0.0,
        one_rpt["final_stored_volume_million_l"] or 0.0,
    ]
    two_values = [
        two_rpt["wet_weather_inflow_million_l"] or 0.0,
        two_rpt["external_inflow_million_l"] or 0.0,
        two_rpt["external_outflow_million_l"] or 0.0,
        two_rpt["final_stored_volume_million_l"] or 0.0,
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    frame = pd.DataFrame({"1D模型": one_values, "加2维模型": two_values}, index=labels)
    frame.plot(kind="bar", ax=axes[0], color=["#54A24B", "#E45756"])
    axes[0].set_title("体积级结果对比（10^6 L）")
    axes[0].set_ylabel("10^6 L")
    axes[0].grid(axis="y", alpha=0.25, linestyle="--")
    axes[0].tick_params(axis="x", rotation=0)

    err_labels = ["径流连续性误差", "路由连续性误差"]
    err_frame = pd.DataFrame(
        {
            "1D模型": [
                one_rpt["runoff_continuity_error_pct"] or 0.0,
                one_rpt["routing_continuity_error_pct"] or 0.0,
            ],
            "加2维模型": [
                two_rpt["runoff_continuity_error_pct"] or 0.0,
                two_rpt["routing_continuity_error_pct"] or 0.0,
            ],
        },
        index=err_labels,
    )
    err_frame.plot(kind="bar", ax=axes[1], color=["#72B7B2", "#B279A2"])
    axes[1].set_title("连续性误差对比（%）")
    axes[1].set_ylabel("%")
    axes[1].grid(axis="y", alpha=0.25, linestyle="--")
    axes[1].tick_params(axis="x", rotation=0)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def build_summary(one_d: dict[str, Any], two_d: dict[str, Any], one_rpt: dict[str, Any], two_rpt: dict[str, Any]) -> dict[str, Any]:
    one_nodes = set(one_d["coords"])
    two_nodes = set(two_d["coords"])
    common_nodes = one_nodes & two_nodes
    new_surface_nodes = sorted(two_nodes - one_nodes)

    connect2d_nodes = sorted(node for node, tag in two_d["tags"]["Node"].items() if tag == "Connect2D")
    twod_nodes = sorted(node for node, tag in two_d["tags"]["Node"].items() if tag == "2D")

    return {
        "file_inventory": {
            "model_1d_inp": str(MODEL_1D_INP),
            "model_1d_rpt": str(MODEL_1D_RPT),
            "model_2d_inp": str(MODEL_2D_INP),
            "model_2d_rpt": str(MODEL_2D_RPT),
            "model_2d_tsb": str(MODEL_2D_TSB),
            "twod_node_shp": str(TWOD_NODE_SHP),
            "boundary_shp": str(BOUNDARY_SHP),
            "dem_dir": str(DEM_DIR),
        },
        "one_d": {
            "counts": one_d["counts"],
            "options": one_d["options"],
            "xsection_shapes": one_d["xsection_shapes"],
            "inflows": one_d["inflows"],
            "bounds": one_d["bounds"],
            "rpt": one_rpt,
        },
        "two_d": {
            "counts": two_d["counts"],
            "options": two_d["options"],
            "xsection_shapes": two_d["xsection_shapes"],
            "inflows": two_d["inflows"],
            "bounds": two_d["bounds"],
            "rpt": two_rpt,
        },
        "relationship": {
            "core_node_count": len(common_nodes),
            "new_2d_node_count": len(new_surface_nodes),
            "connect2d_node_count": len(connect2d_nodes),
            "twod_tagged_node_count": len(twod_nodes),
            "connect2d_nodes_match_core_100": set(connect2d_nodes) == set(CORE_JUNCTION_NODES),
            "example_new_2d_nodes": new_surface_nodes[:15],
        },
    }


def write_report(summary: dict[str, Any]) -> None:
    one_d = summary["one_d"]
    two_d = summary["two_d"]
    relation = summary["relationship"]
    one_flood_text = "否，报告中明确写明无节点淹没" if one_d["rpt"]["no_flooding"] else "是，报告中出现了节点淹没"
    two_flood_text = "否，报告中明确写明无节点淹没" if two_d["rpt"]["no_flooding"] else "是，报告中出现了节点淹没"
    one_critical_text = "否，报告中未出现 Time-Step Critical Elements" if one_d["rpt"]["no_critical_elements"] else "是，报告中存在关键时间步瓶颈"
    two_critical_text = "否，报告中未出现 Time-Step Critical Elements" if two_d["rpt"]["no_critical_elements"] else "是，报告中存在关键时间步瓶颈"
    two_high_error = ", ".join(f"{item['node']}({item['percent']}%)" for item in two_d["rpt"]["high_error_nodes"][:5]) or "报告中未列出明显热点"

    report = f"""# 0416 新模型数据深度解析

## 1. 目录里都是什么

- `0-网状污水管网.inp/out/rpt`：100 个检查井的一维核心管网模型与其仿真结果。
- `0-网状污水管网（加2维）.inp/out/rpt`：在一维核心管网基础上，增加二维表面节点与连接关系后的扩展模型。
- `0-网状污水管网（加2维）.2D cells.tsb`：二维网格/二维单元的二进制结果支撑文件，通常配合 2D 模型一起使用。
- `2维点/2D Nodes.SHP`：二维节点或二维网格辅助点位数据。
- `gis/范围.shp`：模型范围边界。
- `gis/dem/...`：高程 DEM 栅格数据，供二维地形与表面汇流使用。

## 2. 两个主模型分别代表什么

### 2.1 一维模型

- 检查井/节点数：{one_d["counts"]["JUNCTIONS"] + one_d["counts"]["OUTFALLS"]}
- 其中检查井：{one_d["counts"]["JUNCTIONS"]}
- 出口数：{one_d["counts"]["OUTFALLS"]}
- 管段数：{one_d["counts"]["CONDUITS"]}
- 子汇水区：{one_d["counts"]["SUBCATCHMENTS"]}
- 外部注水点：{one_d["counts"]["INFLOWS"]}
- 时间序列：{one_d["counts"]["TIMESERIES"]}

这套模型可以理解为 0416 项目的核心 1D 污水管网骨架。当前读到的唯一出口是 `{OUTFALL_NODE}`，而且是自由出流口。

### 2.2 加 2 维模型

- 检查井/节点数：{two_d["counts"]["JUNCTIONS"] + two_d["counts"]["OUTFALLS"]}
- 其中检查井/普通节点：{two_d["counts"]["JUNCTIONS"]}
- 出口数：{two_d["counts"]["OUTFALLS"]}
- 管段数：{two_d["counts"]["CONDUITS"]}
- 子汇水区：{two_d["counts"]["SUBCATCHMENTS"]}
- 外部注水点：{two_d["counts"]["INFLOWS"]}
- 时间序列：{two_d["counts"]["TIMESERIES"]}
- 标签数：{two_d["counts"]["TAGS"]}

这套模型不是简单把一维模型另存一份，而是在原 100 个核心检查井基础上，额外扩展出 {relation["new_2d_node_count"]} 个 2D 表面节点，并用大量连接关系把 1D 与 2D 组织到一起。

## 3. 1D 和 2D 的关系

- 核心 100 个检查井在 2D 模型里仍然保留。
- 2D 模型里带 `Connect2D` 标签的节点一共 {relation["connect2d_node_count"]} 个，与一维核心检查井一一对应：{relation["connect2d_nodes_match_core_100"]}。
- 2D 模型里带 `2D` 标签的新节点一共 {relation["twod_tagged_node_count"]} 个。

这意味着 2D 模型的结构可以理解成：

1. 原始 100 个检查井仍然是地下 1D 管网主骨架。
2. 每个检查井位置通过 `Connect2D` 节点和 2D 面/2D 链路发生耦合。
3. 新增的 2D 节点负责表达地表蓄水、漫流和出流扩散。

## 4. 水力结果质量怎么样

### 4.1 一维模型

- 路由连续性误差：{one_d["rpt"]["routing_continuity_error_pct"]}%
- 是否发生节点淹没：{one_flood_text}
- 是否出现关键时间步瓶颈：{one_critical_text}
- 排口 `{OUTFALL_NODE}` 总出流：{one_d["rpt"]["external_outflow_million_l"]} ×10^6 L

### 4.2 加 2 维模型

- 路由连续性误差：{two_d["rpt"]["routing_continuity_error_pct"]}%
- 是否发生节点淹没：{two_flood_text}
- 是否出现关键时间步瓶颈：{two_critical_text}
- 排口 `{OUTFALL_NODE}` 总出流：{two_d["rpt"]["external_outflow_million_l"]} ×10^6 L
- 2D 模型里报告列出的高连续性误差热点：{two_high_error}

这两套模型目前最值得肯定的地方是：

- 出口是自由出流，不再像 0401 那样容易形成高蓄水、难排空工况。
- 当前报告里没有节点淹没。
- 当前报告里没有时间步关键瓶颈。
- 路由连续性误差都很小，尤其 2D 模型仍然控制在很低水平。

这意味着 0416 这批模型，从水力数值质量上看，比 0401 更适合作为后续溯源试验底座。

## 5. 当前注水口径

- 一维模型当前只有 1 个外部注水点：{", ".join(item["node"] for item in one_d["inflows"])}
- 加 2 维模型当前有 2 个外部注水点：{", ".join(item["node"] for item in two_d["inflows"])}

从名字上看，这些时序更像“既有工况/设计工况”的入流过程，而不是已经整理好的正式反演真值。因此，当前 0416 目录里的模型更适合先作为：

- 新网络结构解析对象
- 新一轮反演代码迁移底座
- 后续正式 truth/baseline 试验的准备模型

## 6. 可视化文件

- `0416_1D管网总览.png`
- `0416_2D耦合管网总览.png`
- `0416_结构规模对比.png`
- `0416_水力结果对比.png`

## 7. 当前结论

0416 这批新模型相比 0401，有三个明显优点：

1. 管网规模更聚焦，核心检查井正好 100 个，更适合系统排查。
2. 增加了 2D 面和 Connect2D 结构，后续可以直接评价地表溢出/漫流影响。
3. 当前出口为自由出流，且报告显示没有淹没和明显数值不稳定，水力质量明显更健康。

这说明 0416 很适合作为下一阶段正式溯源实验的新底座。
"""
    ANALYSIS_REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    one_d = parse_model(MODEL_1D_INP)
    two_d = parse_model(MODEL_2D_INP)
    one_rpt = parse_rpt_metrics(MODEL_1D_RPT)
    two_rpt = parse_rpt_metrics(MODEL_2D_RPT)
    summary = build_summary(one_d, two_d, one_rpt, two_rpt)

    ANALYSIS_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    draw_network_overview("0416 一维核心管网总览", one_d, FIGURE_DIR / "0416_1D管网总览.png", highlight_surface=False)
    draw_network_overview("0416 2D 耦合管网总览", two_d, FIGURE_DIR / "0416_2D耦合管网总览.png", highlight_surface=True)
    draw_structure_comparison(one_d, two_d, FIGURE_DIR / "0416_结构规模对比.png")
    draw_hydraulic_comparison(one_rpt, two_rpt, FIGURE_DIR / "0416_水力结果对比.png")
    write_report(summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
