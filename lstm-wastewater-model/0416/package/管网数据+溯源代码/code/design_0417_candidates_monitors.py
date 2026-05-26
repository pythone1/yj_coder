from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
import heapq
import json
import math
import shutil

import numpy as np
import pandas as pd
from pyswmm import Nodes, Simulation


ROOT = Path(r"E:\PY\LSTM\0416")
MODEL_DIR = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("0-"))
EVENT_INP = MODEL_DIR / "0417_32h_injection_50pct_J20_J48_J11.inp"
CLEAN_INP = MODEL_DIR / "0417_32h_clean_baseline_no_J20_J48_J11.inp"

HTML_OUT = MODEL_DIR / "0417_scheme_design_candidates_monitors.html"
REPORT_OUT = MODEL_DIR / "0417_scheme_design_report.md"
SUMMARY_JSON = MODEL_DIR / "0417_scheme_design_summary.json"
CONFIG_SNIPPET = MODEL_DIR / "0417_scheme_config_snippet.py"
ALL_NODE_DELTA_CSV = MODEL_DIR / "0417_scheme_all_node_delta_metrics.csv"

RUNTIME_DIR = ROOT / "runtime_0417_scheme_design"
RUNTIME_DIR.mkdir(exist_ok=True)
RUNTIME_EVENT = RUNTIME_DIR / "event_50pct.inp"
RUNTIME_CLEAN = RUNTIME_DIR / "clean_baseline.inp"

TRUTH_NODES = ("J20", "J48", "J11")
OUTFALL_NODE = "J6"
CANDIDATE_COUNT = 20


def section_rows(inp: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    section = ""
    for raw in inp.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            continue
        if section == section_name.upper() and stripped and not stripped.startswith(";"):
            rows.append(stripped.split())
    return rows


def parse_model(inp: Path) -> dict[str, object]:
    junctions = [r[0] for r in section_rows(inp, "JUNCTIONS")]
    outfalls = [r[0] for r in section_rows(inp, "OUTFALLS")]
    conduits = [(r[0], r[1], r[2], float(r[3])) for r in section_rows(inp, "CONDUITS") if len(r) >= 4]
    coords = {r[0]: (float(r[1]), float(r[2])) for r in section_rows(inp, "COORDINATES") if len(r) >= 3}
    return {"junctions": junctions, "outfalls": outfalls, "conduits": conduits, "coords": coords}


def build_graph(conduits: list[tuple[str, str, str, float]]) -> tuple[dict[str, list[tuple[str, str, float]]], dict[str, list[tuple[str, float]]]]:
    directed: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    undirected: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for link, up, down, length in conduits:
        directed[up].append((down, link, length))
        undirected[up].append((down, length))
        undirected[down].append((up, length))
    return directed, undirected


def downstream_path(start: str, directed: dict[str, list[tuple[str, str, float]]], outfalls: set[str]) -> list[tuple[str, str, str, float]]:
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        if node in outfalls:
            return path
        for downstream, link, length in directed.get(node, []):
            if downstream not in seen:
                seen.add(downstream)
                queue.append((downstream, path + [(link, node, downstream, length)]))
    return []


def dijkstra(start: str, undirected: dict[str, list[tuple[str, float]]]) -> dict[str, float]:
    dist = {start: 0.0}
    heap = [(0.0, start)]
    while heap:
        current, node = heapq.heappop(heap)
        if current != dist[node]:
            continue
        for other, length in undirected.get(node, []):
            next_dist = current + length
            if next_dist < dist.get(other, math.inf):
                dist[other] = next_dist
                heapq.heappush(heap, (next_dist, other))
    return dist


def run_all_node_series(inp: Path, nodes_to_collect: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with Simulation(str(inp), str(inp.with_suffix(".rpt")), str(inp.with_suffix(".out"))) as sim:
        sim.step_advance(300)
        node_api = Nodes(sim)
        handles = {name: node_api[name] for name in nodes_to_collect}
        for step, _ in enumerate(sim):
            row: dict[str, object] = {"step": step, "time": str(sim.current_time), "elapsed_hour": step * 300.0 / 3600.0}
            for name, handle in handles.items():
                row[name] = float(handle.total_inflow)
            rows.append(row)
    return pd.DataFrame(rows)


def collect_delta_metrics(nodes: list[str]) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    shutil.copyfile(EVENT_INP, RUNTIME_EVENT)
    shutil.copyfile(CLEAN_INP, RUNTIME_CLEAN)
    event_df = run_all_node_series(RUNTIME_EVENT, nodes)
    clean_df = run_all_node_series(RUNTIME_CLEAN, nodes)
    common = min(len(event_df), len(clean_df))
    metrics: dict[str, dict[str, float]] = {}
    rows = []
    for node in nodes:
        delta = event_df[node].to_numpy(dtype=float)[:common] - clean_df[node].to_numpy(dtype=float)[:common]
        abs_delta = np.abs(delta)
        peak_idx = int(abs_delta.argmax()) if len(abs_delta) else 0
        item = {
            "node": node,
            "max_abs_delta_cms": float(abs_delta.max()) if len(abs_delta) else 0.0,
            "sum_abs_delta_m3": float(abs_delta.sum() * 300.0) if len(abs_delta) else 0.0,
            "positive_delta_m3": float(np.maximum(delta, 0.0).sum() * 300.0) if len(delta) else 0.0,
            "peak_hour": float(event_df["elapsed_hour"].iloc[peak_idx]) if len(abs_delta) else 0.0,
        }
        metrics[node] = item
        rows.append(item)
    frame = pd.DataFrame(rows).sort_values("max_abs_delta_cms", ascending=False)
    frame.to_csv(ALL_NODE_DELTA_CSV, index=False, encoding="utf-8-sig")
    return frame, metrics


def select_candidates(
    junctions: list[str],
    directed: dict[str, list[tuple[str, str, float]]],
    undirected: dict[str, list[tuple[str, float]]],
    outfalls: set[str],
) -> tuple[list[str], dict[str, dict[str, float | str]]]:
    valid = [node for node in junctions if downstream_path(node, directed, outfalls)]
    all_dist = {node: dijkstra(node, undirected) for node in valid}
    selected = list(TRUTH_NODES)

    while len(selected) < CANDIDATE_COUNT:
        best: tuple[float, str, float, float] | None = None
        for node in valid:
            if node in selected:
                continue
            nearest = min(all_dist[node].get(existing, math.inf) for existing in selected)
            path_len = sum(item[3] for item in downstream_path(node, directed, outfalls))
            score = nearest + 0.02 * path_len
            if best is None or score > best[0]:
                best = (score, node, nearest, path_len)
        if best is None:
            break
        selected.append(best[1])

    metrics = {}
    for node in selected:
        nearest_distance, nearest_node = min((all_dist[node].get(other, math.inf), other) for other in selected if other != node)
        metrics[node] = {
            "nearest_candidate": nearest_node,
            "nearest_candidate_distance_m": nearest_distance,
            "downstream_length_to_outfall_m": sum(item[3] for item in downstream_path(node, directed, outfalls)),
            "role": "真值注入点" if node in TRUTH_NODES else "远距覆盖候选井",
        }
    return selected, metrics


def path_nodes(start: str, directed: dict[str, list[tuple[str, str, float]]], outfalls: set[str]) -> list[str]:
    path = downstream_path(start, directed, outfalls)
    return [start] + [item[2] for item in path]


def cumulative_path_distance(start: str, directed: dict[str, list[tuple[str, str, float]]], outfalls: set[str]) -> dict[str, float]:
    dist = {start: 0.0}
    total = 0.0
    for _, _, down, length in downstream_path(start, directed, outfalls):
        total += length
        dist[down] = total
    return dist


def select_monitors(
    directed: dict[str, list[tuple[str, str, float]]],
    outfalls: set[str],
    sensitivity: dict[str, dict[str, float]],
) -> tuple[list[str], list[dict[str, object]]]:
    # 11个点：每条真值支路保留局部和中段监测，再保留共同下游，不把监测点放在注入井本身。
    selected = ["J25", "J27", "J47", "J49", "J62", "J61", "J9", "J50", "J7", "J75", "J78"]
    path_by_source = {source: path_nodes(source, directed, outfalls) for source in TRUTH_NODES}
    dist_by_source = {source: cumulative_path_distance(source, directed, outfalls) for source in TRUTH_NODES}
    role_map = {
        "J25": "J20近下游，先于J48，用于区分J20与J48",
        "J27": "J20支路中段，仍先于J48，增强J20局部约束",
        "J47": "J48近下游，先于J7汇合",
        "J49": "J48支路汇合前，约束J48下游响应",
        "J62": "J11近下游，直接捕捉J11分支响应",
        "J61": "J11支路中上段，增强J11局部约束",
        "J9": "J11支路中段，避免只靠末端公共响应",
        "J50": "J11支路汇合前，约束J11进入J7前的响应",
        "J7": "两条主响应路径汇合点，检测总响应是否闭合",
        "J75": "共同下游中段，检验汇合后传播",
        "J78": "近排口末端，检验最终出流响应",
    }

    rows = []
    for node in selected:
        downstream_of = [source for source, nodes in path_by_source.items() if node in nodes and node != source]
        distance_text = []
        for source in TRUTH_NODES:
            if node in dist_by_source[source] and node != source:
                distance_text.append(f"{source}:{dist_by_source[source][node]:.1f}m")
        item = {
            "node": node,
            "role": role_map[node],
            "downstream_of": ",".join(downstream_of),
            "distance_from_sources": "; ".join(distance_text),
            "max_abs_delta_cms": sensitivity.get(node, {}).get("max_abs_delta_cms", 0.0),
            "positive_delta_m3": sensitivity.get(node, {}).get("positive_delta_m3", 0.0),
            "peak_hour": sensitivity.get(node, {}).get("peak_hour", 0.0),
        }
        rows.append(item)
    return selected, rows


def svg_network(
    parsed: dict[str, object],
    candidates: list[str],
    monitors: list[str],
    directed: dict[str, list[tuple[str, str, float]]],
    outfalls: set[str],
) -> str:
    coords: dict[str, tuple[float, float]] = parsed["coords"]  # type: ignore[assignment]
    conduits: list[tuple[str, str, str, float]] = parsed["conduits"]  # type: ignore[assignment]
    xs = [x for x, _ in coords.values()]
    ys = [y for _, y in coords.values()]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    def sx(value: float) -> float:
        return 50 + (value - minx) / (maxx - minx or 1) * 1120

    def sy(value: float) -> float:
        return 760 - (value - miny) / (maxy - miny or 1) * 700

    candidate_set = set(candidates)
    monitor_set = set(monitors)
    truth_set = set(TRUTH_NODES)
    outfall_set = set(parsed["outfalls"])  # type: ignore[arg-type]
    highlighted_edges: dict[tuple[str, str], str] = {}
    colors = {"J20": "#f97316", "J48": "#dc2626", "J11": "#16a34a"}
    for source in TRUTH_NODES:
        for _, up, down, _ in downstream_path(source, directed, outfalls):
            highlighted_edges.setdefault((up, down), colors[source])

    parts = [
        "<svg viewBox='0 0 1220 820' class='network'>",
        "<defs><filter id='shadow'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-opacity='.25'/></filter></defs>",
    ]
    for _, up, down, _ in conduits:
        if up in coords and down in coords:
            cls = "pipe"
            color = highlighted_edges.get((up, down), "")
            style = f"stroke:{color};stroke-width:3.2;opacity:.72" if color else ""
            x1, y1 = coords[up]
            x2, y2 = coords[down]
            parts.append(f"<line x1='{sx(x1):.1f}' y1='{sy(y1):.1f}' x2='{sx(x2):.1f}' y2='{sy(y2):.1f}' class='{cls}' style='{style}'/>")

    for node, (x, y) in coords.items():
        if node not in parsed["junctions"] and node not in outfall_set:  # type: ignore[operator]
            continue
        css = "node"
        radius = 3.5
        label = ""
        if node in outfall_set:
            css, radius, label = "outfall", 8.5, node
        elif node in truth_set and node in monitor_set:
            css, radius, label = "truthmonitor", 9.5, node
        elif node in truth_set:
            css, radius, label = "truth", 9.5, node
        elif node in candidate_set and node in monitor_set:
            css, radius, label = "candmonitor", 8.0, node
        elif node in monitor_set:
            css, radius, label = "monitor", 7.6, node
        elif node in candidate_set:
            css, radius, label = "candidate", 6.6, node
        parts.append(f"<circle cx='{sx(x):.1f}' cy='{sy(y):.1f}' r='{radius}' class='{css}' filter='url(#shadow)'><title>{node}</title></circle>")
        if label:
            parts.append(f"<text x='{sx(x) + 9:.1f}' y='{sy(y) - 9:.1f}' class='label'>{label}</text>")

    legend = [
        ("真值注入点/候选井", "#dc2626"),
        ("候选井", "#f59e0b"),
        ("监测井", "#2563eb"),
        ("候选+监测", "#7c3aed"),
        ("排口", "#111827"),
    ]
    lx, ly = 32, 26
    parts.append("<rect x='18' y='12' width='260' height='142' rx='14' fill='white' opacity='.92'/>")
    for i, (name, color) in enumerate(legend):
        y = ly + i * 25
        parts.append(f"<circle cx='{lx}' cy='{y}' r='7' fill='{color}'/>")
        parts.append(f"<text x='{lx + 18}' y='{y + 5}' class='legend'>{name}</text>")
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
                value = f"{value:.4g}"
            parts.append(f"<td>{value}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def write_outputs(
    parsed: dict[str, object],
    candidates: list[str],
    candidate_metrics: dict[str, dict[str, float | str]],
    monitors: list[str],
    monitor_rows: list[dict[str, object]],
    delta_frame: pd.DataFrame,
    directed: dict[str, list[tuple[str, str, float]]],
    outfalls: set[str],
) -> None:
    candidate_rows = []
    for index, node in enumerate(candidates, start=1):
        item = dict(candidate_metrics[node])
        item["order"] = index
        item["node"] = node
        candidate_rows.append(item)

    min_sep = min(float(row["nearest_candidate_distance_m"]) for row in candidate_rows)
    median_sep = float(np.median([float(row["nearest_candidate_distance_m"]) for row in candidate_rows]))
    truth_paths = []
    for source in TRUTH_NODES:
        nodes = path_nodes(source, directed, outfalls)
        truth_paths.append(
            {
                "source": source,
                "path": " -> ".join(nodes),
                "link_count": len(nodes) - 1,
                "length_m": sum(item[3] for item in downstream_path(source, directed, outfalls)),
                "downstream_monitors": ", ".join(node for node in monitors if node in nodes and node != source),
            }
        )

    css = (
        "body{margin:0;background:#f6f1e8;color:#1f2933;font-family:'Microsoft YaHei','SimHei',sans-serif}"
        "header{padding:30px 40px;background:#18314f;color:#fff}main{padding:24px 40px}.panel{background:#fff;border-radius:16px;padding:18px;margin:16px 0;box-shadow:0 10px 28px #0001}"
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:#fff;border-radius:16px;padding:18px;box-shadow:0 10px 28px #0001}.card b{font-size:30px;color:#c2410c}"
        "table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px 10px;text-align:left;font-size:13px;vertical-align:top}th{background:#f1f5f9}.network{width:100%;height:auto;background:#fbfaf6;border:1px solid #eadfce;border-radius:14px}"
        ".pipe{stroke:#9aa8b6;stroke-width:1.2;opacity:.55}.node{fill:#9aa8b6;opacity:.45}.truth{fill:#dc2626;stroke:#7f1d1d;stroke-width:2}.candidate{fill:#f59e0b;stroke:#92400e;stroke-width:1.4}.monitor{fill:#2563eb;stroke:#1e3a8a;stroke-width:1.7}.candmonitor{fill:#7c3aed;stroke:#4c1d95;stroke-width:1.8}.truthmonitor{fill:#be123c;stroke:#4c0519;stroke-width:2}.outfall{fill:#111827;stroke:#000;stroke-width:2}.label{font-size:15px;font-weight:800;fill:#111827}.legend{font-size:13px;font-weight:700;fill:#111827}.note{background:#fff7ed;border-left:5px solid #f97316;padding:12px 16px;border-radius:8px;margin:8px 0}"
    )
    html = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>0417候选井与监测点设计</title><style>{css}</style></head><body>",
        "<header><h1>0417 候选井与监测点设计方案</h1><p>基于 J20、J48、J11 三处 50% 真值注水模型和旱天基线。</p></header><main>",
        "<section class='cards'>",
        f"<div class='card'>候选井<br><b>{len(candidates)}</b></div>",
        f"<div class='card'>监测井<br><b>{len(monitors)}</b></div>",
        f"<div class='card'>候选最近间距<br><b>{min_sep:.0f} m</b></div>",
        f"<div class='card'>候选中位间距<br><b>{median_sep:.0f} m</b></div>",
        "</section>",
        "<section class='panel'><h2>设计判断</h2>",
        "<div class='note'>候选井保留20个，并强制包含 J20、J48、J11；其余候选按管网无向距离做远距覆盖，避免把一串相邻井都放进候选集导致代偿。</div>",
        "<div class='note'>监测井选11个，不放在注入井本身；重点放在 J20 到 J48 之前、J48 到 J7 之前、J11 到 J7 之前，以及 J7 后共同下游。</div>",
        "</section>",
        "<section class='panel'><h2>空间布设图</h2>",
        svg_network(parsed, candidates, monitors, directed, outfalls),
        "</section>",
        "<section class='panel'><h2>候选井列表</h2>",
        table_html(candidate_rows, [("序号", "order"), ("节点", "node"), ("类型", "role"), ("最近候选", "nearest_candidate"), ("最近候选距离m", "nearest_candidate_distance_m"), ("至排口下游长度m", "downstream_length_to_outfall_m")]),
        "</section>",
        "<section class='panel'><h2>监测井列表与敏感性</h2>",
        table_html(monitor_rows, [("节点", "node"), ("作用", "role"), ("下游对应注入点", "downstream_of"), ("距注入点距离", "distance_from_sources"), ("最大增量cms", "max_abs_delta_cms"), ("正增量体积m3", "positive_delta_m3"), ("峰值小时", "peak_hour")]),
        "</section>",
        "<section class='panel'><h2>三处注入点到排口路径</h2>",
        table_html(truth_paths, [("注入点", "source"), ("管段数", "link_count"), ("路径长度m", "length_m"), ("下游监测井", "downstream_monitors"), ("路径", "path")]),
        "</section>",
        "</main></body></html>",
    ]
    HTML_OUT.write_text("".join(html), encoding="utf-8")

    CONFIG_SNIPPET.write_text(
        "CANDIDATE_NODES = (\n"
        + "".join(f'    "{node}",\n' for node in candidates)
        + ")\n\n"
        + "MONITOR_NODES = (\n"
        + "".join(f'    "{node}",\n' for node in monitors)
        + ")\n\n"
        + f'TRUTH_INJECTION_NODES = {TRUTH_NODES!r}\n',
        encoding="utf-8",
    )

    report = [
        "# 0417候选井与监测点设计报告",
        "",
        f"- 事件模型: `{EVENT_INP}`",
        f"- 旱天基线: `{CLEAN_INP}`",
        f"- 网页可视化: `{HTML_OUT}`",
        f"- 配置片段: `{CONFIG_SNIPPET}`",
        f"- 全节点敏感性CSV: `{ALL_NODE_DELTA_CSV}`",
        "",
        "## 1. 推荐方案",
        f"- 候选井 `{len(candidates)}` 个: `{', '.join(candidates)}`。",
        f"- 监测井 `{len(monitors)}` 个: `{', '.join(monitors)}`。",
        f"- 候选井最近拓扑间距最小值 `{min_sep:.1f} m`，中位值 `{median_sep:.1f} m`。",
        "",
        "## 2. 设计依据",
        "- 候选井强制包含 `J20、J48、J11`，其余节点按管网无向距离做远距覆盖，减少近邻候选井之间的代偿。",
        "- `J20` 下游会经过 `J48`，因此必须在 `J20 -> J48` 之间设置监测井，否则 J20 和 J48 容易互相代偿。",
        "- `J11` 与 `J20/J48` 两条响应路径在 `J7` 附近汇合，因此汇合前必须分别设置支路监测井，汇合后只保留少量校核点。",
        "- 监测井数量定为 11 个。少于这个数量会弱化 J20/J48/J11 的局部区分；明显多于这个数量会让共同下游点过多，稀释局部敏感性。",
        "",
        "## 3. 下游路径与监测覆盖",
    ]
    for item in truth_paths:
        report.append(f"- `{item['source']}`: 长度 `{float(item['length_m']):.1f} m`，下游监测井 `{item['downstream_monitors']}`。路径: `{item['path']}`")
    report.extend(["", "## 4. 文件"])
    for path in [HTML_OUT, REPORT_OUT, SUMMARY_JSON, CONFIG_SNIPPET, ALL_NODE_DELTA_CSV]:
        report.append(f"- `{path}`")
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = {
        "event_inp": str(EVENT_INP),
        "clean_inp": str(CLEAN_INP),
        "candidate_nodes": candidates,
        "candidate_metrics": candidate_metrics,
        "monitor_nodes": monitors,
        "monitor_rows": monitor_rows,
        "truth_paths": truth_paths,
        "min_candidate_spacing_m": min_sep,
        "median_candidate_spacing_m": median_sep,
        "top_sensitive_nodes": delta_frame.head(20).to_dict(orient="records"),
        "html": str(HTML_OUT),
        "report": str(REPORT_OUT),
        "config_snippet": str(CONFIG_SNIPPET),
        "all_node_delta_csv": str(ALL_NODE_DELTA_CSV),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parsed = parse_model(EVENT_INP)
    conduits: list[tuple[str, str, str, float]] = parsed["conduits"]  # type: ignore[assignment]
    junctions: list[str] = parsed["junctions"]  # type: ignore[assignment]
    outfalls = set(parsed["outfalls"])  # type: ignore[arg-type]
    directed, undirected = build_graph(conduits)

    delta_frame, sensitivity = collect_delta_metrics(junctions)
    candidates, candidate_metrics = select_candidates(junctions, directed, undirected, outfalls)
    monitors, monitor_rows = select_monitors(directed, outfalls, sensitivity)
    write_outputs(parsed, candidates, candidate_metrics, monitors, monitor_rows, delta_frame, directed, outfalls)

    print(
        json.dumps(
            {
                "candidates": candidates,
                "monitors": monitors,
                "html": str(HTML_OUT),
                "report": str(REPORT_OUT),
                "config_snippet": str(CONFIG_SNIPPET),
                "min_candidate_spacing_m": min(v["nearest_candidate_distance_m"] for v in candidate_metrics.values()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
