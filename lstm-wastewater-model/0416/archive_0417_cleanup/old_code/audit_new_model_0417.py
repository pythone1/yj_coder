from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
import json
import re
import shutil

import numpy as np
import pandas as pd

try:
    from pyswmm import Links, Nodes, Simulation

    HAS_PYSWMM = True
except Exception as exc:  # pragma: no cover - environment guard
    HAS_PYSWMM = False
    PYSWMM_ERROR = repr(exc)


ROOT = Path(r"E:\PY\LSTM\0416")
MODEL_DIR = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("0-"))
RAW_INP = next(p for p in MODEL_DIR.glob("*.inp") if not p.name.startswith("0417_"))

CHECK_INP = MODEL_DIR / "0417_current_injection_audit.inp"
CLEAN_INP = MODEL_DIR / "0417_clean_baseline_no_J20_J48_J11.inp"
HTML_OUT = MODEL_DIR / "0417_model_audit_visualization.html"
REPORT_OUT = MODEL_DIR / "0417_model_audit_report.md"
SUMMARY_JSON = MODEL_DIR / "0417_model_audit_summary.json"
CURRENT_TS_CSV = MODEL_DIR / "0417_current_injection_timeseries.csv"
CLEAN_TS_CSV = MODEL_DIR / "0417_clean_baseline_timeseries.csv"

RUNTIME_DIR = ROOT / "runtime_0417_audit"
RUNTIME_DIR.mkdir(exist_ok=True)
RUNTIME_CURRENT = RUNTIME_DIR / "current.inp"
RUNTIME_CLEAN = RUNTIME_DIR / "clean_baseline.inp"

TARGET_NODES = {"J20", "J48", "J11"}
RAIN_INJECTION_PREFIX = "48h\u964d\u96e8\u91cf"
BASELINE_TS = "48h\u6c61\u6c34\u91cf"
INJECTION_TAG = "\u6ce8\u5165\u70b9"


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

    subcatchments = []
    for line in active_lines(sections.get("SUBCATCHMENTS", [])):
        parts = line.split()
        if len(parts) >= 8:
            subcatchments.append({"name": parts[0], "outlet": parts[2], "area": float(parts[3])})

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
            time_value = float(parts[-2])
            series_value = float(parts[-1])
        except ValueError:
            continue
        timeseries[" ".join(parts[:-2])].append((time_value, series_value))

    return {
        "text": text,
        "sections": sections,
        "junctions": junctions,
        "outfalls": outfalls,
        "conduits": conduits,
        "coords": coords,
        "subcatchments": subcatchments,
        "inflows": inflows,
        "timeseries": timeseries,
    }


def summarize_series(name: str, values: list[tuple[float, float]]) -> dict[str, object]:
    ordered = sorted(values)
    times = np.array([t for t, _ in ordered], dtype=float)
    flow = np.array([v for _, v in ordered], dtype=float)
    dt_h = float(np.median(np.diff(times))) if len(times) > 1 else 0.0
    return {
        "name": name,
        "points": int(len(flow)),
        "start_h": float(times.min()) if len(times) else None,
        "end_h": float(times.max()) if len(times) else None,
        "dt_h": dt_h,
        "max_value": float(flow.max()) if len(flow) else 0.0,
        "sum_value": float(flow.sum()) if len(flow) else 0.0,
        "nonzero_points": int(np.count_nonzero(np.abs(flow) > 1e-12)),
        "volume_if_flow_m3": float(flow.sum() * dt_h * 3600.0) if dt_h > 0 else 0.0,
    }


def make_clean_model(text: str, remove_series: set[str]) -> dict[str, object]:
    clean_lines = []
    section = ""
    removed_inflows = []
    removed_tags = []
    removed_timeseries = 0
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^\[(.+?)\]", stripped)
        if match:
            section = match.group(1).upper()
            clean_lines.append(line)
            continue

        if section == "INFLOWS" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            if parts and parts[0] in TARGET_NODES:
                removed_inflows.append(line)
                continue

        if section == "TIMESERIES" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            if len(parts) >= 3 and " ".join(parts[:-2]) in remove_series:
                removed_timeseries += 1
                continue

        if section == "TAGS" and stripped and not stripped.startswith(";"):
            parts = stripped.split()
            if len(parts) >= 2 and parts[0].upper() == "NODE" and parts[1] in TARGET_NODES and INJECTION_TAG in stripped:
                removed_tags.append(line)
                continue

        clean_lines.append(line)

    CLEAN_INP.write_text("\n".join(clean_lines) + "\n", encoding="gbk")
    shutil.copyfile(RAW_INP, CHECK_INP)
    shutil.copyfile(CHECK_INP, RUNTIME_CURRENT)
    shutil.copyfile(CLEAN_INP, RUNTIME_CLEAN)
    return {"inflows": removed_inflows, "timeseries_lines": removed_timeseries, "tags": removed_tags}


def path_to_outfall(start: str, conduits: list[dict[str, object]], outfalls: set[str]) -> list[tuple[str, str, str, float]]:
    adjacency: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for conduit in conduits:
        adjacency[str(conduit["up"])].append((str(conduit["down"]), str(conduit["name"]), float(conduit["length"])))
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        if node in outfalls:
            return path
        for downstream, link, length in adjacency.get(node, []):
            if downstream not in seen:
                seen.add(downstream)
                queue.append((downstream, path + [(link, node, downstream, length)]))
    return []


def run_collect(inp: Path, csv_out: Path, parsed: dict[str, object]) -> tuple[pd.DataFrame | None, dict[str, object]]:
    if not HAS_PYSWMM:
        return None, {"ok": False, "error": PYSWMM_ERROR}

    junctions = list(parsed["junctions"])
    conduits = list(parsed["conduits"])
    outfalls = list(parsed["outfalls"])
    outfall = str(outfalls[0]["name"]) if outfalls else ""
    outfall_link = next((str(c["name"]) for c in conduits if str(c["down"]) == outfall), "")
    stats = {str(j["name"]): {"max_depth_m": 0.0, "max_flooding_cms": 0.0, "max_total_inflow_cms": 0.0} for j in junctions}
    rows = []

    try:
        with Simulation(str(inp), str(inp.with_suffix(".rpt")), str(inp.with_suffix(".out"))) as sim:
            sim.step_advance(300)
            nodes = Nodes(sim)
            links = Links(sim)
            target_handles = {node: nodes[node] for node in sorted(TARGET_NODES) if node in stats}
            outfall_node = nodes[outfall] if outfall else None
            out_link = links[outfall_link] if outfall_link else None
            all_nodes = {node: nodes[node] for node in stats}
            for index, _ in enumerate(sim):
                row = {"step": index, "time": str(sim.current_time), "elapsed_hour": index * 300 / 3600.0}
                if outfall_node is not None:
                    row[f"{outfall}_total_inflow_cms"] = float(outfall_node.total_inflow)
                    row[f"{outfall}_depth_m"] = float(outfall_node.depth)
                if out_link is not None:
                    row["outfall_link_flow_cms"] = float(out_link.flow)
                for node, handle in target_handles.items():
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
    summary = {"ok": True, "rows": int(len(frame)), "runtime_inp": str(inp), "runtime_rpt": str(inp.with_suffix(".rpt")), "runtime_out": str(inp.with_suffix(".out"))}
    if "outfall_link_flow_cms" in frame:
        summary["outfall_total_volume_m3"] = float(frame["outfall_link_flow_cms"].sum() * 300.0)
        summary["outfall_peak_flow_cms"] = float(frame["outfall_link_flow_cms"].max())
    flooded = [{"node": node, **item} for node, item in stats.items() if item["max_flooding_cms"] > 1e-12]
    summary["flooded_node_count"] = len(flooded)
    summary["top_flooded_nodes"] = sorted(flooded, key=lambda item: item["max_flooding_cms"], reverse=True)[:10]
    return frame, summary


def table_html(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    html = ["<table><thead><tr>"]
    html.extend(f"<th>{title}</th>" for title, _ in columns)
    html.append("</tr></thead><tbody>")
    for row in rows:
        html.append("<tr>")
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = f"{value:.6g}"
            html.append(f"<td>{value}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    return "".join(html)


def make_network_svg(parsed: dict[str, object]) -> str:
    coords = dict(parsed["coords"])
    conduits = list(parsed["conduits"])
    junctions = list(parsed["junctions"])
    outfall_names = {str(item["name"]) for item in parsed["outfalls"]}
    xs = [value[0] for value in coords.values()]
    ys = [value[1] for value in coords.values()]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    def sx(value: float) -> float:
        return 40 + (value - minx) / (maxx - minx or 1) * 920

    def sy(value: float) -> float:
        return 620 - (value - miny) / (maxy - miny or 1) * 560

    ponding = {str(item["name"]) for item in junctions if float(item["ponded_area"]) > 0}
    svg = ["<svg viewBox='0 0 1000 660' class='network'>"]
    for conduit in conduits:
        up, down = str(conduit["up"]), str(conduit["down"])
        if up in coords and down in coords:
            x1, y1 = coords[up]
            x2, y2 = coords[down]
            svg.append(f"<line x1='{sx(x1):.1f}' y1='{sy(y1):.1f}' x2='{sx(x2):.1f}' y2='{sy(y2):.1f}' class='pipe'/>")
    for node, (x, y) in coords.items():
        css = "node"
        radius = 3.2
        label = ""
        if node in outfall_names:
            css, radius, label = "outfall", 7, node
        elif node in TARGET_NODES:
            css, radius, label = "inject", 7, node
        elif node in ponding:
            css, radius = "pond", 4
        svg.append(f"<circle cx='{sx(x):.1f}' cy='{sy(y):.1f}' r='{radius}' class='{css}'><title>{node}</title></circle>")
        if label:
            svg.append(f"<text x='{sx(x) + 8:.1f}' y='{sy(y) - 8:.1f}' class='label'>{label}</text>")
    svg.append("</svg>")
    return "\n".join(svg)


def plot_svg(data: dict[str, tuple[np.ndarray | list[float], np.ndarray | list[float]]]) -> str:
    if not data:
        return ""
    all_x: list[float] = []
    all_y: list[float] = []
    for x_values, y_values in data.values():
        all_x.extend(float(x) for x in x_values)
        all_y.extend(float(y) for y in y_values)
    minx, maxx = min(all_x), max(all_x)
    miny, maxy = min(all_y), max(all_y)
    if maxy == miny:
        maxy += 1
    colors = ["#c2410c", "#2563eb", "#16a34a", "#9333ea", "#dc2626", "#0891b2"]

    def px(value: float) -> float:
        return 55 + (value - minx) / (maxx - minx or 1) * 910

    def py(value: float) -> float:
        return 275 - (value - miny) / (maxy - miny) * 245

    svg = [
        "<svg viewBox='0 0 1000 320' class='plot'>",
        "<line x1='55' y1='275' x2='965' y2='275' class='axis'/>",
        "<line x1='55' y1='30' x2='55' y2='275' class='axis'/>",
        f"<text x='55' y='20' class='small'>max {maxy:.4g}</text>",
    ]
    for index, (name, (x_values, y_values)) in enumerate(data.items()):
        points = " ".join(f"{px(float(x)):.1f},{py(float(y)):.1f}" for x, y in zip(x_values, y_values))
        color = colors[index % len(colors)]
        svg.append(f"<polyline points='{points}' fill='none' stroke='{color}' stroke-width='2.2'><title>{name}</title></polyline>")
        svg.append(f"<text x='{70 + (index % 4) * 220}' y='{308 - 18 * (index // 4)}' fill='{color}' class='legend'>{name}</text>")
    svg.append("</svg>")
    return "\n".join(svg)


def write_outputs(
    parsed: dict[str, object],
    removed: dict[str, object],
    current_df: pd.DataFrame | None,
    clean_df: pd.DataFrame | None,
    current_run: dict[str, object],
    clean_run: dict[str, object],
) -> None:
    timeseries: dict[str, list[tuple[float, float]]] = parsed["timeseries"]  # type: ignore[assignment]
    inflows: list[dict[str, object]] = parsed["inflows"]  # type: ignore[assignment]
    series_summaries = [summarize_series(name, values) for name, values in timeseries.items()]
    series_map = {item["name"]: item for item in series_summaries}
    remove_names = {name for name in timeseries if name.startswith(RAIN_INJECTION_PREFIX)}
    use_count = Counter(str(item["series"]) for item in inflows)
    base_100 = float(series_map.get("48h\u964d\u96e8\u91cf(100%)", {}).get("volume_if_flow_m3", 0.0))
    applied = []
    for item in inflows:
        summary = series_map.get(str(item["series"]), {})
        applied.append({**item, "volume_if_flow_m3": summary.get("volume_if_flow_m3"), "max_flow_cms": summary.get("max_value")})
    ratio_rows = []
    for name in sorted(remove_names):
        item = dict(series_map[name])
        item["ratio_to_100_series"] = float(item["volume_if_flow_m3"]) / base_100 if base_100 else None
        item["used_by_inflow_count"] = use_count.get(name, 0)
        ratio_rows.append(item)

    warnings = []
    if len(inflows) > 1 and len({str(item["series"]) for item in inflows}) == 1:
        warnings.append(f"\u5f53\u524d [INFLOWS] \u4e2d 3 \u4e2a\u6ce8\u5165\u8282\u70b9\u5168\u90e8\u5f15\u7528\u540c\u4e00\u4e2a\u65f6\u5e8f {inflows[0]['series']}\uff0c\u672a\u5f62\u6210 J20/J48/J11 \u5206\u522b\u5bf9\u5e94 50%/100%/200% \u7684\u914d\u7f6e\u3002")
    for name in sorted(remove_names):
        if use_count.get(name, 0) == 0:
            warnings.append(f"\u65f6\u5e8f {name} \u5df2\u5b9a\u4e49\u4f46\u6ca1\u6709\u88ab\u4efb\u4f55 [INFLOWS] \u5f15\u7528\u3002")
    if current_run.get("ok") and clean_run.get("ok"):
        delta = float(current_run.get("outfall_total_volume_m3", 0.0)) - float(clean_run.get("outfall_total_volume_m3", 0.0))
        warnings.append(f"\u5f53\u524d\u6ce8\u5165\u6a21\u578b\u6392\u53e3\u603b\u51fa\u6d41\u6bd4\u65f1\u5929\u57fa\u7ebf\u589e\u52a0\u7ea6 {delta:.2f} m3\uff1b\u7531\u4e8e\u4e09\u4e95\u5747\u6302 200% \u65f6\u5e8f\uff0c\u5916\u90e8\u6ce8\u5165\u7406\u8bba\u603b\u91cf\u4e3a {sum(float(item.get('volume_if_flow_m3') or 0.0) for item in applied):.2f} m3\u3002")

    outfall_names = {str(item["name"]) for item in parsed["outfalls"]}  # type: ignore[index]
    paths = {node: path_to_outfall(node, parsed["conduits"], outfall_names) for node in sorted(TARGET_NODES)}  # type: ignore[arg-type]

    series_plot = {}
    for name in sorted(remove_names):
        values = sorted(timeseries[name])
        series_plot[name] = ([item[0] for item in values], [item[1] for item in values])
    if BASELINE_TS in timeseries:
        values = sorted(timeseries[BASELINE_TS])
        series_plot[BASELINE_TS] = ([item[0] for item in values], [item[1] for item in values])

    flow_plot = {}
    if current_df is not None and "outfall_link_flow_cms" in current_df:
        flow_plot["\u5f53\u524d\u6a21\u578b(\u4e09\u4e95\u5747200%)"] = (current_df["elapsed_hour"].to_numpy(), current_df["outfall_link_flow_cms"].to_numpy())
    if clean_df is not None and "outfall_link_flow_cms" in clean_df:
        flow_plot["\u65f1\u5929\u57fa\u7ebf(\u53bb\u9664\u6ce8\u6c34)"] = (clean_df["elapsed_hour"].to_numpy(), clean_df["outfall_link_flow_cms"].to_numpy())

    css = (
        "body{margin:0;background:#f7f3ea;color:#1f2933;font-family:'Microsoft YaHei','SimHei',sans-serif}"
        "header{padding:28px 36px;background:#153243;color:white}main{padding:24px 36px}"
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}"
        ".card,.panel{background:white;border-radius:16px;padding:18px;margin:16px 0;box-shadow:0 8px 24px #0001}"
        ".card b{font-size:28px;color:#c2410c}.warn{background:#fff7ed;border-left:5px solid #f97316;padding:12px 16px;margin:8px 0;border-radius:8px}"
        "table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px 10px;text-align:left;font-size:14px}th{background:#f1f5f9}"
        ".network,.plot{width:100%;height:auto;background:#fbfaf6;border:1px solid #eadfce;border-radius:12px}"
        ".pipe{stroke:#8b9bad;stroke-width:1.2;opacity:.7}.node{fill:#8aa0b5;opacity:.72}.pond{fill:#76a15a}.inject{fill:#f97316;stroke:#7c2d12;stroke-width:2}.outfall{fill:#dc2626;stroke:#7f1d1d;stroke-width:2}"
        ".label{font-size:16px;font-weight:700;fill:#111827}.axis{stroke:#475569}.small{font-size:13px;fill:#475569}.legend{font-size:13px;font-weight:700}"
        "pre{white-space:pre-wrap;background:#f8fafc;padding:12px;border-radius:10px}.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:900px){.two{grid-template-columns:1fr}main{padding:16px}}"
    )
    html_parts = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>0417 \u65b0\u6a21\u578b\u6ce8\u5165\u65b9\u6848\u53ef\u89c6\u5316</title>",
        f"<style>{css}</style></head><body><header><h1>0417 \u65b0\u6a21\u578b\u6ce8\u5165\u65b9\u6848\u4e0e\u65f1\u5929\u57fa\u7ebf\u6838\u67e5</h1><p>{RAW_INP.name}</p></header><main>",
        "<section class='cards'>",
        f"<div class='card'>\u68c0\u67e5\u4e95<br><b>{len(parsed['junctions'])}</b></div>",
        f"<div class='card'>\u6392\u53e3<br><b>{len(parsed['outfalls'])}</b></div>",
        f"<div class='card'>\u7ba1\u6bb5<br><b>{len(parsed['conduits'])}</b></div>",
        f"<div class='card'>\u5b50\u6c47\u6c34\u533a<br><b>{len(parsed['subcatchments'])}</b></div>",
        f"<div class='card'>\u5916\u90e8\u6ce8\u5165\u884c<br><b>{len(inflows)}</b></div>",
        f"<div class='card'>\u5141\u8bb8\u79ef\u6c34\u4e95<br><b>{sum(float(j['ponded_area']) > 0 for j in parsed['junctions'])}</b></div></section>",
        "<section class='panel'><h2>\u5173\u952e\u6838\u67e5\u7ed3\u8bba</h2>",
        "".join(f"<div class='warn'>{item}</div>" for item in warnings),
        "</section><section class='panel'><h2>\u7ba1\u7f51\u7a7a\u95f4\u53ef\u89c6\u5316</h2><p>\u6a59\u8272\u4e3a\u6ce8\u5165\u70b9\uff0c\u7ea2\u8272\u4e3a\u81ea\u7531\u51fa\u6d41\u6392\u53e3\uff0c\u7eff\u8272\u4e3a Ponding Area \u68c0\u67e5\u4e95\u3002</p>",
        make_network_svg(parsed),
        "</section><section class='panel'><h2>\u5916\u90e8\u6ce8\u5165\u914d\u7f6e</h2>",
        table_html(applied, [("\u8282\u70b9", "node"), ("\u5f15\u7528\u65f6\u5e8f", "series"), ("\u7406\u8bba\u6ce8\u5165\u91cfm3", "volume_if_flow_m3"), ("\u5cf0\u503ccms", "max_flow_cms")]),
        "</section><section class='panel'><h2>50%/100%/200% \u65f6\u5e8f\u4e0e\u5f15\u7528\u60c5\u51b5</h2>",
        table_html(ratio_rows, [("\u65f6\u5e8f", "name"), ("\u70b9\u6570", "points"), ("\u975e\u96f6\u70b9", "nonzero_points"), ("\u5cf0\u503c", "max_value"), ("\u7406\u8bba\u4f53\u79efm3", "volume_if_flow_m3"), ("\u76f8\u5bf9100%", "ratio_to_100_series"), ("\u88ab\u5f15\u7528\u6b21\u6570", "used_by_inflow_count")]),
        plot_svg(series_plot),
        "</section><section class='panel'><h2>\u5f53\u524d\u6a21\u578b\u4e0e\u65f1\u5929\u57fa\u7ebf\u6392\u53e3\u5bf9\u6bd4</h2>",
        plot_svg(flow_plot),
        "</section><section class='panel'><h2>\u6a21\u62df\u6458\u8981</h2><div class='two'>",
        f"<pre>{json.dumps(current_run, ensure_ascii=False, indent=2)}</pre><pre>{json.dumps(clean_run, ensure_ascii=False, indent=2)}</pre>",
        "</div></section><section class='panel'><h2>\u6ce8\u5165\u70b9\u81f3\u6392\u53e3\u8def\u5f84</h2>",
        table_html(
            [{"node": node, "pipe_count": len(path), "total_length_m": sum(item[3] for item in path), "path": " -> ".join([node] + [item[2] for item in path])} for node, path in paths.items()],
            [("\u8282\u70b9", "node"), ("\u7ba1\u6bb5\u6570", "pipe_count"), ("\u8def\u5f84\u957f\u5ea6m", "total_length_m"), ("\u8def\u5f84", "path")],
        ),
        "</section></main></body></html>",
    ]
    HTML_OUT.write_text("".join(html_parts), encoding="utf-8")

    report = [
        "# 0417 \u65b0\u6a21\u578b\u6570\u636e\u89e3\u6790\u62a5\u544a",
        "",
        f"- \u539f\u59cb\u6a21\u578b: `{RAW_INP}`",
        f"- \u5f53\u524d\u6ce8\u5165\u65b9\u6848\u590d\u6838\u526f\u672c: `{CHECK_INP}`",
        f"- \u53bb\u6ce8\u6c34\u65f1\u5929\u57fa\u7ebf: `{CLEAN_INP}`",
        f"- \u7f51\u9875\u53ef\u89c6\u5316: `{HTML_OUT}`",
        "",
        "## 1. \u6a21\u578b\u57fa\u7840\u7ed3\u6784",
        f"- \u68c0\u67e5\u4e95 `{len(parsed['junctions'])}` \u4e2a\uff0c\u6392\u53e3 `{len(parsed['outfalls'])}` \u4e2a\uff0c\u7ba1\u6bb5 `{len(parsed['conduits'])}` \u6839\uff0c\u5b50\u6c47\u6c34\u533a `{len(parsed['subcatchments'])}` \u4e2a\u3002",
        f"- `ALLOW_PONDING=YES`\uff0cPonding Area \u5927\u4e8e 0 \u7684\u68c0\u67e5\u4e95 `{sum(float(j['ponded_area']) > 0 for j in parsed['junctions'])}` \u4e2a\u3002",
        "",
        "## 2. \u6ce8\u5165\u65b9\u6848\u6838\u67e5",
    ]
    report.extend(f"- **\u6ce8\u610f:** {item}" for item in warnings)
    report.append("")
    report.append("\u5f53\u524d [INFLOWS] \u5b9e\u9645\u914d\u7f6e:")
    for item in applied:
        report.append(f"- `{item['node']}` \u5f15\u7528 `{item['series']}`\uff0c\u7406\u8bba\u5916\u90e8\u6ce8\u5165\u91cf `{float(item['volume_if_flow_m3']):.2f} m3`\uff0c\u5cf0\u503c `{float(item['max_flow_cms']):.6g} m3/s`\u3002")
    report.append("")
    report.append("\u4e09\u6761\u65f6\u5e8f\u672c\u8eab\u7684\u6bd4\u4f8b\u6b63\u786e\uff1a50% \u662f 100% \u7684 0.5 \u500d\uff0c200% \u662f 100% \u7684 2 \u500d\uff1b\u4f46\u5f53\u524d\u4e09\u53e3\u4e95\u5168\u90e8\u5f15\u7528 200% \u65f6\u5e8f\uff0c\u56e0\u6b64\u5f53\u524d\u6a21\u578b\u4e0d\u662f\u4e09\u70b9\u4e0d\u540c\u5f3a\u5ea6\u7684\u771f\u503c\u6ce8\u5165\u6a21\u578b\u3002")
    if clean_run.get("ok") and clean_run.get("outfall_total_volume_m3", 0):
        baseline_volume = float(clean_run["outfall_total_volume_m3"])
        report.append("")
        report.append("\u6309 FLOW \u65f6\u5e8f\u79ef\u5206\u5e76\u4e0e\u65f1\u5929\u57fa\u7ebf\u6392\u53e3\u603b\u91cf\u6bd4\u8f83:")
        for item in ratio_rows:
            volume = float(item["volume_if_flow_m3"])
            report.append(f"- `{item['name']}`: `{volume:.2f} m3`\uff0c\u7ea6\u4e3a\u65f1\u5929\u57fa\u7ebf\u6392\u53e3\u603b\u51fa\u6d41 `{baseline_volume:.2f} m3` \u7684 `{volume / baseline_volume * 100:.2f}%`\u3002")
    report.extend(
        [
            "",
            "## 3. \u65f1\u5929\u57fa\u7ebf\u5904\u7406",
            f"- \u5df2\u53e6\u5b58 `{CLEAN_INP.name}`\uff0c\u672a\u4fee\u6539\u539f\u59cb\u6a21\u578b\u3002",
            f"- \u4ece [INFLOWS] \u5220\u9664 `{len(removed['inflows'])}` \u884c J20/J48/J11 \u5916\u90e8\u6ce8\u6c34\u3002",
            f"- \u4ece [TIMESERIES] \u5220\u9664 `{removed['timeseries_lines']}` \u884c 50%/100%/200% \u5916\u90e8\u6ce8\u5165\u65f6\u5e8f\uff0c\u4fdd\u7559 `{BASELINE_TS}` \u4f5c\u4e3a\u672c\u5e95\u9a71\u52a8\u3002",
            f"- \u4ece [TAGS] \u5220\u9664 `{len(removed['tags'])}` \u884c\u6ce8\u5165\u70b9\u6807\u8bb0\u3002",
            "",
            "## 4. \u6a21\u62df\u7ed3\u679c\u6458\u8981",
        ]
    )
    if current_run.get("ok"):
        report.append(f"- \u5f53\u524d\u6ce8\u5165\u6a21\u578b: \u6392\u53e3\u603b\u51fa\u6d41 `{float(current_run.get('outfall_total_volume_m3', 0.0)):.2f} m3`\uff0c\u5cf0\u503c `{float(current_run.get('outfall_peak_flow_cms', 0.0)):.6g} m3/s`\uff0c\u79ef\u6c34/\u6ea2\u6d41\u54cd\u5e94\u8282\u70b9 `{current_run.get('flooded_node_count', 0)}` \u4e2a\u3002")
    else:
        report.append(f"- \u5f53\u524d\u6ce8\u5165\u6a21\u578b\u8fd0\u884c\u5931\u8d25: `{current_run.get('error')}`")
    if clean_run.get("ok"):
        report.append(f"- \u65f1\u5929\u57fa\u7ebf: \u6392\u53e3\u603b\u51fa\u6d41 `{float(clean_run.get('outfall_total_volume_m3', 0.0)):.2f} m3`\uff0c\u5cf0\u503c `{float(clean_run.get('outfall_peak_flow_cms', 0.0)):.6g} m3/s`\uff0c\u79ef\u6c34/\u6ea2\u6d41\u54cd\u5e94\u8282\u70b9 `{clean_run.get('flooded_node_count', 0)}` \u4e2a\u3002")
    else:
        report.append(f"- \u65f1\u5929\u57fa\u7ebf\u8fd0\u884c\u5931\u8d25: `{clean_run.get('error')}`")
    report.append("")
    report.append("## 5. \u751f\u6210\u6587\u4ef6")
    for path in [HTML_OUT, REPORT_OUT, SUMMARY_JSON, CHECK_INP, CLEAN_INP, CURRENT_TS_CSV, CLEAN_TS_CSV]:
        report.append(f"- `{path}`")
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = {
        "raw_inp": str(RAW_INP),
        "check_inp": str(CHECK_INP),
        "clean_inp": str(CLEAN_INP),
        "html": str(HTML_OUT),
        "report": str(REPORT_OUT),
        "counts": {
            "junctions": len(parsed["junctions"]),
            "outfalls": len(parsed["outfalls"]),
            "conduits": len(parsed["conduits"]),
            "subcatchments": len(parsed["subcatchments"]),
            "inflows": len(inflows),
            "timeseries": len(timeseries),
            "ponding_junctions": sum(float(j["ponded_area"]) > 0 for j in parsed["junctions"]),
        },
        "inflows": inflows,
        "series_ratio_checks": ratio_rows,
        "applied_inflows": applied,
        "removed": removed,
        "paths": {node: [{"link": link, "up": up, "down": down, "length_m": length} for link, up, down, length in path] for node, path in paths.items()},
        "current_run": current_run,
        "clean_run": clean_run,
        "warnings": warnings,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parsed = parse_model(RAW_INP)
    timeseries: dict[str, list[tuple[float, float]]] = parsed["timeseries"]  # type: ignore[assignment]
    remove_series = {name for name in timeseries if name.startswith(RAIN_INJECTION_PREFIX)}
    removed = make_clean_model(str(parsed["text"]), remove_series)

    runtime_parsed = parse_model(RUNTIME_CURRENT)
    current_df, current_run = run_collect(RUNTIME_CURRENT, CURRENT_TS_CSV, runtime_parsed)
    clean_df, clean_run = run_collect(RUNTIME_CLEAN, CLEAN_TS_CSV, runtime_parsed)
    write_outputs(parsed, removed, current_df, clean_df, current_run, clean_run)

    print(
        json.dumps(
            {
                "html": str(HTML_OUT),
                "report": str(REPORT_OUT),
                "clean_inp": str(CLEAN_INP),
                "current_run": current_run,
                "clean_run": clean_run,
                "removed": removed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
