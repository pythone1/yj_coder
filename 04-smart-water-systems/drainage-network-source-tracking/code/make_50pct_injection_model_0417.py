"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: make_50pct_injection_model_0417.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import re
import shutil

import numpy as np
import pandas as pd

try:
    from pyswmm import Links, Nodes, Simulation

    HAS_PYSWMM = True
except Exception as exc:  # pragma: no cover
    HAS_PYSWMM = False
    PYSWMM_ERROR = repr(exc)


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = next((d for d in [ROOT / "models", *ROOT.iterdir()] if d.is_dir() and any(d.glob("*.inp"))), ROOT / "models")
RAW_INP = next((p for p in MODEL_DIR.glob("*.inp") if not p.name.startswith("0520_")), MODEL_DIR / "raw_model.inp")
CLEAN_INP = MODEL_DIR / "0520_clean_baseline_no_truth_inflow.inp"

MODEL_50_INP = MODEL_DIR / "0520_injection_50pct_truth_nodes.inp"
HTML_OUT = MODEL_DIR / "0520_50pct_injection_waveform_visualization.html"
REPORT_OUT = MODEL_DIR / "0520_50pct_injection_report.md"
SUMMARY_JSON = MODEL_DIR / "0520_50pct_injection_summary.json"
TS_50_CSV = MODEL_DIR / "0520_50pct_injection_timeseries.csv"
CLEAN_TS_CSV = MODEL_DIR / "0520_50pct_clean_baseline_timeseries.csv"

RUNTIME_DIR = ROOT / "runtime_0520_50pct"
RUNTIME_DIR.mkdir(exist_ok=True)
RUNTIME_50 = RUNTIME_DIR / "injection_50pct.inp"
RUNTIME_CLEAN = RUNTIME_DIR / "clean_baseline.inp"

TARGET_NODES = {"J11", "J20", "J48"}
INJECTION_50_SERIES = "48h\u964d\u96e8\u91cf(50%)"
INJECTION_PREFIX = "48h\u964d\u96e8\u91cf"
BASELINE_TS = "48h\u6c61\u6c34\u91cf"


def section_map(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    section = ""
    for line in text.splitlines():
        match = re.match(r"^\s*\[(.+?)\]", line.strip())
        if match:
            section = match.group(1).upper()
            continue
        if section:
            sections[section].append(line)
    return sections


def active_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip() and not line.strip().startswith(";")]


def parse_model(inp: Path) -> dict[str, object]:
    text = inp.read_text(encoding="gbk", errors="ignore")
    sections = section_map(text)

    junctions = []
    for line in active_lines(sections.get("JUNCTIONS", [])):
        parts = line.split()
        if len(parts) >= 6:
            junctions.append(
                {
                    "name": parts[0],
                    "invert": float(parts[1]),
                    "max_depth": float(parts[2]),
                    "ponded_area": float(parts[5]),
                }
            )

    outfalls = []
    for line in active_lines(sections.get("OUTFALLS", [])):
        parts = line.split()
        if len(parts) >= 2:
            outfalls.append({"name": parts[0], "invert": float(parts[1]), "type": parts[2] if len(parts) > 2 else ""})

    conduits = []
    for line in active_lines(sections.get("CONDUITS", [])):
        parts = line.split()
        if len(parts) >= 4:
            conduits.append({"name": parts[0], "up": parts[1], "down": parts[2], "length": float(parts[3])})

    coords = {}
    for line in active_lines(sections.get("COORDINATES", [])):
        parts = line.split()
        if len(parts) >= 3:
            coords[parts[0]] = (float(parts[1]), float(parts[2]))

    inflows = []
    for line in active_lines(sections.get("INFLOWS", [])):
        parts = line.split()
        if len(parts) >= 3:
            inflows.append({"node": parts[0], "parameter": parts[1], "series": parts[2], "raw": line})

    timeseries: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for line in active_lines(sections.get("TIMESERIES", [])):
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            t = float(parts[-2])
            v = float(parts[-1])
        except ValueError:
            continue
        timeseries[" ".join(parts[:-2])].append((t, v))

    return {
        "text": text,
        "sections": sections,
        "junctions": junctions,
        "outfalls": outfalls,
        "conduits": conduits,
        "coords": coords,
        "inflows": inflows,
        "timeseries": timeseries,
    }


def summarize_series(name: str, values: list[tuple[float, float]]) -> dict[str, object]:
    ordered = sorted(values)
    times = np.array([t for t, _ in ordered], dtype=float)
    flow = np.array([v for _, v in ordered], dtype=float)
    dt_h = float(np.median(np.diff(times))) if len(times) > 1 else 0.0
    max_value = float(flow.max()) if len(flow) else 0.0
    peak_hours = [float(t) for t, v in ordered if abs(v - max_value) < 1e-12]
    return {
        "name": name,
        "points": int(len(flow)),
        "start_h": float(times.min()) if len(times) else None,
        "end_h": float(times.max()) if len(times) else None,
        "dt_h": dt_h,
        "nonzero_points": int(np.count_nonzero(np.abs(flow) > 1e-12)),
        "max_flow_cms": max_value,
        "peak_hours": peak_hours,
        "sum_flow_values": float(flow.sum()) if len(flow) else 0.0,
        "volume_m3": float(flow.sum() * dt_h * 3600.0) if dt_h > 0 else 0.0,
    }


def make_50pct_model(text: str) -> list[dict[str, str]]:
    lines = []
    section = ""
    changed = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^\[(.+?)\]", stripped)
        if match:
            section = match.group(1).upper()
            lines.append(line)
            continue

        if section == "INFLOWS" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            if len(parts) >= 7 and parts[0] in TARGET_NODES:
                node = parts[0]
                old_series = parts[2]
                new_line = f"{node:<16} FLOW             {INJECTION_50_SERIES:<18} FLOW     1.0      1        0"
                lines.append(new_line)
                changed.append({"node": node, "old_series": old_series, "new_series": INJECTION_50_SERIES})
                continue
        lines.append(line)

    MODEL_50_INP.write_text("\n".join(lines) + "\n", encoding="gbk")
    shutil.copyfile(MODEL_50_INP, RUNTIME_50)
    if CLEAN_INP.exists():
        shutil.copyfile(CLEAN_INP, RUNTIME_CLEAN)
    return changed


def run_collect(inp: Path, csv_out: Path, parsed: dict[str, object]) -> tuple[pd.DataFrame | None, dict[str, object]]:
    if not HAS_PYSWMM:
        return None, {"ok": False, "error": PYSWMM_ERROR}

    outfalls = list(parsed["outfalls"])
    conduits = list(parsed["conduits"])
    outfall = str(outfalls[0]["name"]) if outfalls else ""
    outfall_link = next((str(c["name"]) for c in conduits if str(c["down"]) == outfall), "")
    stats = {str(j["name"]): {"max_depth_m": 0.0, "max_flooding_cms": 0.0, "max_total_inflow_cms": 0.0} for j in parsed["junctions"]}
    rows = []

    try:
        with Simulation(str(inp), str(inp.with_suffix(".rpt")), str(inp.with_suffix(".out"))) as sim:
            sim.step_advance(300)
            nodes = Nodes(sim)
            links = Links(sim)
            targets = {node: nodes[node] for node in sorted(TARGET_NODES)}
            out_link = links[outfall_link] if outfall_link else None
            all_nodes = {node: nodes[node] for node in stats}
            for index, _ in enumerate(sim):
                row = {"step": index, "time": str(sim.current_time), "elapsed_hour": index * 300 / 3600.0}
                if out_link is not None:
                    row["outfall_link_flow_cms"] = float(out_link.flow)
                for node, handle in targets.items():
                    row[f"{node}_total_inflow_cms"] = float(handle.total_inflow)
                    row[f"{node}_depth_m"] = float(handle.depth)
                    row[f"{node}_flooding_cms"] = float(handle.flooding)
                for node, handle in all_nodes.items():
                    item = stats[node]
                    item["max_depth_m"] = max(item["max_depth_m"], float(handle.depth))
                    item["max_flooding_cms"] = max(item["max_flooding_cms"], max(0.0, float(handle.flooding)))
                    item["max_total_inflow_cms"] = max(item["max_total_inflow_cms"], float(handle.total_inflow))
                rows.append(row)
    except Exception as exc:
        return None, {"ok": False, "error": repr(exc)}

    frame = pd.DataFrame(rows)
    frame.to_csv(csv_out, index=False, encoding="utf-8-sig")
    summary = {
        "ok": True,
        "rows": int(len(frame)),
        "runtime_inp": str(inp),
        "runtime_rpt": str(inp.with_suffix(".rpt")),
        "runtime_out": str(inp.with_suffix(".out")),
    }
    if "outfall_link_flow_cms" in frame:
        summary["outfall_total_volume_m3"] = float(frame["outfall_link_flow_cms"].sum() * 300.0)
        summary["outfall_peak_flow_cms"] = float(frame["outfall_link_flow_cms"].max())
    flooded = [{"node": node, **item} for node, item in stats.items() if item["max_flooding_cms"] > 1e-12]
    summary["flooded_node_count"] = len(flooded)
    summary["top_flooded_nodes"] = sorted(flooded, key=lambda item: item["max_flooding_cms"], reverse=True)[:10]
    return frame, summary


def plot_svg(data: dict[str, tuple[list[float] | np.ndarray, list[float] | np.ndarray]], ylabel: str) -> str:
    if not data:
        return ""
    all_x = [float(x) for x_values, _ in data.values() for x in x_values]
    all_y = [float(y) for _, y_values in data.values() for y in y_values]
    minx, maxx = min(all_x), max(all_x)
    miny, maxy = min(all_y), max(all_y)
    if maxy == miny:
        maxy += 1
    colors = ["#c2410c", "#2563eb", "#16a34a", "#9333ea", "#dc2626", "#0891b2"]

    def px(value: float) -> float:
        return 60 + (value - minx) / (maxx - minx or 1) * 900

    def py(value: float) -> float:
        return 275 - (value - miny) / (maxy - miny) * 240

    parts = [
        "<svg viewBox='0 0 1000 325' class='plot'>",
        "<line x1='60' y1='275' x2='960' y2='275' class='axis'/>",
        "<line x1='60' y1='35' x2='60' y2='275' class='axis'/>",
        f"<text x='60' y='22' class='small'>{ylabel} max {maxy:.4g}</text>",
    ]
    for index, (name, (xs, ys)) in enumerate(data.items()):
        color = colors[index % len(colors)]
        points = " ".join(f"{px(float(x)):.1f},{py(float(y)):.1f}" for x, y in zip(xs, ys))
        parts.append(f"<polyline points='{points}' fill='none' stroke='{color}' stroke-width='2.4'><title>{name}</title></polyline>")
        parts.append(f"<text x='{75 + (index % 3) * 285}' y='{307 - 18 * (index // 3)}' fill='{color}' class='legend'>{name}</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def network_svg(parsed: dict[str, object]) -> str:
    coords = dict(parsed["coords"])
    conduits = list(parsed["conduits"])
    outfalls = {str(item["name"]) for item in parsed["outfalls"]}
    xs = [value[0] for value in coords.values()]
    ys = [value[1] for value in coords.values()]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    def sx(value: float) -> float:
        return 45 + (value - minx) / (maxx - minx or 1) * 910

    def sy(value: float) -> float:
        return 620 - (value - miny) / (maxy - miny or 1) * 560

    parts = ["<svg viewBox='0 0 1000 660' class='network'>"]
    for conduit in conduits:
        up, down = str(conduit["up"]), str(conduit["down"])
        if up in coords and down in coords:
            x1, y1 = coords[up]
            x2, y2 = coords[down]
            parts.append(f"<line x1='{sx(x1):.1f}' y1='{sy(y1):.1f}' x2='{sx(x2):.1f}' y2='{sy(y2):.1f}' class='pipe'/>")
    for node, (x, y) in coords.items():
        css = "node"
        radius = 3.4
        if node in TARGET_NODES:
            css, radius = "inject", 7
        if node in outfalls:
            css, radius = "outfall", 7
        parts.append(f"<circle cx='{sx(x):.1f}' cy='{sy(y):.1f}' r='{radius}' class='{css}'><title>{node}</title></circle>")
        if node in TARGET_NODES or node in outfalls:
            parts.append(f"<text x='{sx(x) + 8:.1f}' y='{sy(y) - 8:.1f}' class='label'>{node}</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def table_html(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    parts = ["<table><thead><tr>"]
    parts.extend(f"<th>{title}</th>" for title, _ in columns)
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = f"{value:.6g}"
            parts.append(f"<td>{value}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def write_outputs(
    raw_parsed: dict[str, object],
    model_50_parsed: dict[str, object],
    changed: list[dict[str, str]],
    frame_50: pd.DataFrame | None,
    run_50: dict[str, object],
    clean_frame: pd.DataFrame | None,
    clean_run: dict[str, object],
) -> None:
    timeseries: dict[str, list[tuple[float, float]]] = raw_parsed["timeseries"]  # type: ignore[assignment]
    injection_names = sorted(name for name in timeseries if name.startswith(INJECTION_PREFIX))
    summaries = [summarize_series(name, timeseries[name]) for name in injection_names]
    summary_map = {item["name"]: item for item in summaries}
    base_volume = float(summary_map.get("48h\u964d\u96e8\u91cf(100%)", {}).get("volume_m3", 0.0))
    for item in summaries:
        item["ratio_to_100"] = float(item["volume_m3"]) / base_volume if base_volume else None
        item["peak_hours_text"] = ",".join(f"{h:g}" for h in item["peak_hours"])

    waveform_plot = {}
    for name in injection_names:
        values = sorted(timeseries[name])
        waveform_plot[name] = ([item[0] for item in values], [item[1] for item in values])

    result_plot = {}
    if frame_50 is not None and "outfall_link_flow_cms" in frame_50:
        result_plot["50%注水模型排口流量"] = (frame_50["elapsed_hour"].to_numpy(), frame_50["outfall_link_flow_cms"].to_numpy())
    if clean_frame is not None and "outfall_link_flow_cms" in clean_frame:
        result_plot["旱天基线排口流量"] = (clean_frame["elapsed_hour"].to_numpy(), clean_frame["outfall_link_flow_cms"].to_numpy())

    node_plot = {}
    if frame_50 is not None:
        for node in sorted(TARGET_NODES):
            col = f"{node}_total_inflow_cms"
            if col in frame_50:
                node_plot[f"{node}节点总入流"] = (frame_50["elapsed_hour"].to_numpy(), frame_50[col].to_numpy())

    css = (
        "body{margin:0;background:#f6f1e8;color:#1f2933;font-family:'Microsoft YaHei','SimHei',sans-serif}"
        "header{padding:28px 36px;background:#17324d;color:white}main{padding:24px 36px}"
        ".panel{background:white;border-radius:16px;padding:18px;margin:16px 0;box-shadow:0 8px 24px #0001}"
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:white;border-radius:16px;padding:18px;box-shadow:0 8px 24px #0001}.card b{font-size:28px;color:#c2410c}"
        "table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px 10px;text-align:left;font-size:14px}th{background:#f1f5f9}"
        ".plot,.network{width:100%;height:auto;background:#fbfaf6;border:1px solid #eadfce;border-radius:12px}"
        ".axis{stroke:#475569}.small{font-size:13px;fill:#475569}.legend{font-size:13px;font-weight:700}.pipe{stroke:#8b9bad;stroke-width:1.2;opacity:.72}.node{fill:#8aa0b5;opacity:.72}.inject{fill:#f97316;stroke:#7c2d12;stroke-width:2}.outfall{fill:#dc2626;stroke:#7f1d1d;stroke-width:2}.label{font-size:16px;font-weight:700;fill:#111827}"
        ".warn{background:#fff7ed;border-left:5px solid #f97316;padding:12px 16px;border-radius:8px;margin:8px 0}"
    )
    total_50_volume = float(summary_map[INJECTION_50_SERIES]["volume_m3"]) * len(TARGET_NODES)
    clean_volume = float(clean_run.get("outfall_total_volume_m3", 0.0)) if clean_run.get("ok") else 0.0
    delta_volume = float(run_50.get("outfall_total_volume_m3", 0.0)) - clean_volume if run_50.get("ok") and clean_run.get("ok") else 0.0
    html = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>50%注水模型与波形分析</title><style>{css}</style></head><body>",
        f"<header><h1>50%注水模型与三档注水波形分析</h1><p>{MODEL_50_INP.name}</p></header><main>",
        "<section class='cards'>",
        f"<div class='card'>50%单井体积<br><b>{float(summary_map[INJECTION_50_SERIES]['volume_m3']):.0f} m3</b></div>",
        f"<div class='card'>三井总注水<br><b>{total_50_volume:.0f} m3</b></div>",
        f"<div class='card'>50%峰值<br><b>{float(summary_map[INJECTION_50_SERIES]['max_flow_cms']):.5f} cms</b></div>",
        f"<div class='card'>较基线增量<br><b>{delta_volume:.0f} m3</b></div>",
        f"<div class='card'>模拟溢流节点<br><b>{run_50.get('flooded_node_count', 'NA')}</b></div>",
        "</section>",
        "<section class='panel'><h2>结论</h2>",
        "<div class='warn'>三条注水波形形状完全一致，仅幅值按 0.5 : 1 : 2 缩放；当前新生成的独立模型把 J11、J20、J48 全部改为 50% 注水线。</div>",
        "</section>",
        "<section class='panel'><h2>三档注水波形</h2>",
        table_html(summaries, [("时序", "name"), ("点数", "points"), ("非零点", "nonzero_points"), ("峰值cms", "max_flow_cms"), ("体积m3", "volume_m3"), ("相对100%", "ratio_to_100"), ("峰值小时", "peak_hours_text")]),
        plot_svg(waveform_plot, "外部入流 m3/s"),
        "</section>",
        "<section class='panel'><h2>50%注水模型空间位置</h2>",
        network_svg(raw_parsed),
        "</section>",
        "<section class='panel'><h2>50%注水后排口响应</h2>",
        plot_svg(result_plot, "排口流量 m3/s"),
        "</section>",
        "<section class='panel'><h2>三个注入节点响应</h2>",
        plot_svg(node_plot, "节点总入流 m3/s"),
        "</section>",
        "<section class='panel'><h2>模型修改记录</h2>",
        table_html(changed, [("节点", "node"), ("原引用", "old_series"), ("新引用", "new_series")]),
        "</section>",
        "</main></body></html>",
    ]
    HTML_OUT.write_text("".join(html), encoding="utf-8")

    inflows_50 = model_50_parsed["inflows"]
    report = [
        "# 0520 50%注水独立模型与波形分析",
        "",
        f"- 原始模型: `{RAW_INP}`",
        f"- 50%注水模型: `{MODEL_50_INP}`",
        f"- 旱天基线模型: `{CLEAN_INP}`",
        f"- 网页可视化: `{HTML_OUT}`",
        f"- 50%模型模拟结果CSV: `{TS_50_CSV}`",
        f"- 旱天基线模拟结果CSV: `{CLEAN_TS_CSV}`",
        "",
        "## 1. 注水波形",
        "- 三条注水波形的时间形状一致，区别只是幅值和体积按比例缩放。",
    ]
    for item in summaries:
        report.append(
            f"- `{item['name']}`: 单井体积 `{float(item['volume_m3']):.2f} m3`，峰值 `{float(item['max_flow_cms']):.6g} m3/s`，"
            f"相对100%比例 `{float(item['ratio_to_100']):.2f}`，峰值小时 `{item['peak_hours_text']}`。"
        )
    report.extend(
        [
            "",
            "## 2. 新生成的50%注水模型",
            f"- 已生成独立文件 `{MODEL_50_INP.name}`，没有覆盖原始模型。",
            f"- `J11/J20/J48` 三个节点均引用 `{INJECTION_50_SERIES}`。",
            f"- 三井总外部注入体积 `{total_50_volume:.2f} m3`。",
            "",
            "当前50%模型 [INFLOWS]:",
        ]
    )
    for item in inflows_50:
        if item["node"] in TARGET_NODES:
            report.append(f"- `{item['node']}` -> `{item['series']}`")
    report.append("")
    report.append("## 3. 50%模型模拟结果")
    if run_50.get("ok"):
        report.append(f"- 排口总出流 `{float(run_50.get('outfall_total_volume_m3', 0.0)):.2f} m3`。")
        report.append(f"- 排口峰值流量 `{float(run_50.get('outfall_peak_flow_cms', 0.0)):.6g} m3/s`。")
        report.append(f"- 出现积水/溢流响应节点 `{run_50.get('flooded_node_count')}` 个。")
        report.append(f"- 最大响应节点: `{json.dumps(run_50.get('top_flooded_nodes', [])[:5], ensure_ascii=False)}`。")
    else:
        report.append(f"- 50%模型模拟失败: `{run_50.get('error')}`")
    if clean_run.get("ok"):
        report.append(f"- 旱天基线排口总出流 `{float(clean_run.get('outfall_total_volume_m3', 0.0)):.2f} m3`。")
        report.append(f"- 50%注水模型相对旱天基线排口增量 `{delta_volume:.2f} m3`。")
    else:
        report.append(f"- 旱天基线模拟失败: `{clean_run.get('error')}`")
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = {
        "raw_inp": str(RAW_INP),
        "model_50_inp": str(MODEL_50_INP),
        "clean_inp": str(CLEAN_INP),
        "html": str(HTML_OUT),
        "report": str(REPORT_OUT),
        "csv": str(TS_50_CSV),
        "changed_inflows": changed,
        "waveform_summaries": summaries,
        "model_50_inflows": inflows_50,
        "run_50": run_50,
        "clean_run": clean_run,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    raw_parsed = parse_model(RAW_INP)
    changed = make_50pct_model(str(raw_parsed["text"]))
    model_50_parsed = parse_model(MODEL_50_INP)
    runtime_50_parsed = parse_model(RUNTIME_50)
    frame_50, run_50 = run_collect(RUNTIME_50, TS_50_CSV, runtime_50_parsed)
    if RUNTIME_CLEAN.exists():
        runtime_clean_parsed = parse_model(RUNTIME_CLEAN)
        clean_frame, clean_run = run_collect(RUNTIME_CLEAN, CLEAN_TS_CSV, runtime_clean_parsed)
    else:
        clean_frame, clean_run = None, {"ok": False, "error": f"missing clean baseline: {RUNTIME_CLEAN}"}
    write_outputs(raw_parsed, model_50_parsed, changed, frame_50, run_50, clean_frame, clean_run)
    print(
        json.dumps(
            {
                "model_50_inp": str(MODEL_50_INP),
                "html": str(HTML_OUT),
                "report": str(REPORT_OUT),
                "summary": str(SUMMARY_JSON),
                "csv": str(TS_50_CSV),
                "clean_csv": str(CLEAN_TS_CSV),
                "changed": changed,
                "run_50": run_50,
                "clean_run": clean_run,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
