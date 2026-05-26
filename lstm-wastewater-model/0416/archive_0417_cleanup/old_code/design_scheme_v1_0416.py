from __future__ import annotations

import json
import math
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

MODEL_DIR = ROOT / "models" / "scheme_v1_clean"
RESULT_DIR = ROOT / "results" / "scheme_v1"
ANALYSIS_DIR = ROOT / "analysis" / "scheme_v1"
FIG_DIR = ANALYSIS_DIR / "figures"
HTML_DIR = ANALYSIS_DIR / "html"

CLEAN_INP = MODEL_DIR / "0416_scheme_v1_clean_no_inflow.inp"
EVENT_INP = MODEL_DIR / "0416_scheme_v1_event.inp"
EVENT_RUN_INP = RESULT_DIR / "scheme_v1_event_run.inp"
SCHEME_JSON = ANALYSIS_DIR / "0416_scheme_v1_design.json"
REPORT_MD = ANALYSIS_DIR / "0416_scheme_v1_report.md"
EVENT_TS_CSV = RESULT_DIR / "scheme_v1_event_timeseries.csv"
NODE_SUMMARY_CSV = RESULT_DIR / "scheme_v1_node_summary.csv"

FIG_SCHEME = FIG_DIR / "0416_方案V1_注入监测候选布局.png"
FIG_TOPOLOGY = FIG_DIR / "0416_方案V1_主线支线拓扑.png"
FIG_INJECTION = FIG_DIR / "0416_方案V1_注入波形.png"
FIG_RESPONSE = FIG_DIR / "0416_方案V1_监测响应.png"
HTML_OUT = HTML_DIR / "0416_方案V1_交互布局.html"

OUTFALL_NODE = "J6"
CANDIDATE_NODES: list[str] = [
    "J1", "J2", "J5", "J21", "J29", "J31", "J41",
    "J72", "J86", "J10", "J11", "J64", "J65", "J91", "J92",
    "J20", "J27", "J79", "J50", "J49",
]
MONITOR_NODES = ["J3", "J20", "J27", "J79", "J84", "J9", "J50", "J7", "J75", "J78"]
INJECTION_SPECS = [
    {"node": "J1", "line": "北侧上游支线", "start_h": 3.0, "ramp_h": 1.0, "plateau_h": 3.0, "peak_cms": 0.012},
    {"node": "J72", "line": "西南上游支线", "start_h": 6.0, "ramp_h": 1.0, "plateau_h": 3.0, "peak_cms": 0.010},
    {"node": "J49", "line": "主线中下游", "start_h": 9.0, "ramp_h": 1.0, "plateau_h": 3.0, "peak_cms": 0.008},
]

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun", "FangSong", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False


def rows(inp: Path, section_name: str) -> list[list[str]]:
    out: list[list[str]] = []
    section = ""
    for raw in inp.read_text(encoding="gbk", errors="ignore").splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            continue
        if section == section_name.upper() and s and not s.startswith(";"):
            out.append(s.split())
    return out


def parse_model(inp: Path) -> dict[str, object]:
    nodes = [r[0] for r in rows(inp, "JUNCTIONS")]
    coords = {r[0]: (float(r[1]), float(r[2])) for r in rows(inp, "COORDINATES") if len(r) >= 3}
    junctions = {
        r[0]: {
            "elev": float(r[1]),
            "max_depth": float(r[2]),
            "ponding_area": float(r[5]),
            "rim": float(r[1]) + float(r[2]),
        }
        for r in rows(inp, "JUNCTIONS")
        if len(r) >= 6
    }
    conduits = [(r[0], r[1], r[2], float(r[3])) for r in rows(inp, "CONDUITS") if len(r) >= 4]
    outfalls = [r[0] for r in rows(inp, "OUTFALLS")]
    return {"nodes": nodes, "coords": coords, "junctions": junctions, "conduits": conduits, "outfalls": outfalls}


def referenced_timeseries_for_clean_model(lines: list[str]) -> set[str]:
    referenced: set[str] = set()
    section = ""
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            continue
        if not s or s.startswith(";"):
            continue
        parts = s.split()
        if section == "INFLOWS" and len(parts) >= 3:
            referenced.add(parts[2])
        if section == "RAINGAGES" and len(parts) >= 6 and parts[4].upper() == "TIMESERIES":
            referenced.add(parts[5])
    return referenced


def build_clean_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    lines = RAW_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    active_timeseries = referenced_timeseries_for_clean_model(lines)
    output: list[str] = []
    section = ""
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            output.append(line)
            continue
        if section == "INFLOWS" and s and not s.startswith(";"):
            continue
        if section == "TIMESERIES" and s and not s.startswith(";"):
            parts = s.split()
            if len(parts) >= 3 and parts[0] in active_timeseries:
                parts[-1] = "0"
                output.append(" ".join(parts))
                continue
        output.append(line)
    CLEAN_INP.write_text("\n".join(output) + "\n", encoding="gbk")


def trapezoid_flow(hour: float, spec: dict[str, float | str]) -> float:
    start = float(spec["start_h"])
    ramp = float(spec["ramp_h"])
    plateau = float(spec["plateau_h"])
    peak = float(spec["peak_cms"])
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


def build_event_model() -> pd.DataFrame:
    shutil.copyfile(CLEAN_INP, EVENT_INP)
    time_hours = [i / 12.0 for i in range(0, 48 * 12 + 1)]
    series_rows: list[str] = []
    inflow_rows: list[str] = []
    records: list[dict[str, float | str]] = []
    for spec in INJECTION_SPECS:
        node = str(spec["node"])
        ts = f"TS_SCHEMEV1_{node}"
        inflow_rows.append(f"{node:<16} FLOW             {ts:<18} FLOW     1.0      1.0      0.0")
        for hour in time_hours:
            q = trapezoid_flow(hour, spec)
            series_rows.append(f"{ts:<24} {hour:<10.4f} {q:.8f}")
            records.append({"node": node, "relative_hour": hour, "flow_cms": q, "line": spec["line"]})

    lines = EVENT_INP.read_text(encoding="gbk", errors="ignore").splitlines()
    output: list[str] = []
    section = ""
    inserted_inflows = False
    inserted_ts = False
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            output.append(line)
            continue
        output.append(line)
        if section == "INFLOWS" and s.startswith(";;--------------") and not inserted_inflows:
            output.extend(inflow_rows)
            inserted_inflows = True
        if section == "TIMESERIES" and s.startswith(";;--------------") and not inserted_ts:
            output.extend(series_rows)
            inserted_ts = True
    EVENT_INP.write_text("\n".join(output) + "\n", encoding="gbk")
    injection_df = pd.DataFrame(records)
    return injection_df


def graph_helpers(model: dict[str, object]) -> dict[str, object]:
    succ: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    pred: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for link, up, down, length in model["conduits"]:
        succ[up].append((down, link, length))
        pred[down].append((up, link, length))
    for key in succ:
        succ[key].sort()

    @lru_cache(None)
    def upstream_set(node: str) -> frozenset[str]:
        acc: set[str] = set()
        for up, _link, _length in pred.get(node, []):
            acc.add(up)
            acc.update(upstream_set(up))
        return frozenset(acc)

    @lru_cache(None)
    def downstream_path(node: str) -> tuple[str, ...]:
        path: list[str] = []
        seen: set[str] = set()
        current = node
        while current not in seen and succ.get(current):
            seen.add(current)
            nxt, _link, _length = succ[current][0]
            path.append(nxt)
            current = nxt
        return tuple(path)

    return {"succ": succ, "pred": pred, "upstream_set": upstream_set, "downstream_path": downstream_path}


def classify_layout(model: dict[str, object], helper: dict[str, object]) -> dict[str, object]:
    nodes = list(model["nodes"])
    candidate_nodes = [node for node in CANDIDATE_NODES if node in nodes]
    monitor_nodes = [node for node in MONITOR_NODES if node in nodes]
    upstream_set = helper["upstream_set"]
    downstream_path = helper["downstream_path"]
    node_metrics = []
    for node in nodes:
        path = downstream_path(node)
        node_metrics.append(
            {
                "node": node,
                "upstream_count": len(upstream_set(node)),
                "downstream_junction_count": sum(1 for p in path if p in nodes),
                "downstream_path": list(path),
                "is_candidate": node in candidate_nodes,
                "is_monitor": node in monitor_nodes,
                "is_injection": node in [str(s["node"]) for s in INJECTION_SPECS],
            }
        )

    injection_downstream_monitors: dict[str, list[str]] = {}
    for spec in INJECTION_SPECS:
        node = str(spec["node"])
        path = set(downstream_path(node))
        injection_downstream_monitors[node] = [m for m in monitor_nodes if m in path]
    return {
        "candidate_nodes": candidate_nodes,
        "monitor_nodes": monitor_nodes,
        "injection_specs": INJECTION_SPECS,
        "node_metrics": node_metrics,
        "injection_downstream_monitors": injection_downstream_monitors,
    }


def find_outfall_link(model: dict[str, object]) -> str:
    for link, _up, down, _length in model["conduits"]:
        if down == OUTFALL_NODE:
            return link
    raise RuntimeError(f"Cannot find link into outfall {OUTFALL_NODE}")


def run_event(model: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EVENT_INP, EVENT_RUN_INP)
    outfall_link = find_outfall_link(model)
    monitor_rows: list[dict[str, float | int | str]] = []
    node_stats = {
        node: {
            "max_depth_m": 0.0,
            "max_ponded_depth_m": 0.0,
            "max_flooding_cms": 0.0,
            "flooding_volume_m3": 0.0,
            "max_total_inflow_cms": 0.0,
        }
        for node in model["nodes"]
    }
    cumulative_outfall = 0.0
    with Simulation(str(EVENT_RUN_INP)) as sim:
        sim.step_advance(60)
        nodes_api = Nodes(sim)
        links_api = Links(sim)
        nodes = {node: nodes_api[node] for node in model["nodes"]}
        monitors = {node: nodes_api[node] for node in MONITOR_NODES}
        outfall = links_api[outfall_link]
        for step, _ in enumerate(sim):
            if step >= 48 * 60:
                break
            system_flooding = 0.0
            active_ponded = 0
            for node, handle in nodes.items():
                depth = float(handle.depth)
                full = float(handle.full_depth)
                ponded = max(0.0, depth - full)
                flooding = max(0.0, float(handle.flooding))
                total_in = float(handle.total_inflow)
                stats = node_stats[node]
                stats["max_depth_m"] = max(stats["max_depth_m"], depth)
                stats["max_ponded_depth_m"] = max(stats["max_ponded_depth_m"], ponded)
                stats["max_flooding_cms"] = max(stats["max_flooding_cms"], flooding)
                stats["flooding_volume_m3"] += flooding * 60.0
                stats["max_total_inflow_cms"] = max(stats["max_total_inflow_cms"], total_in)
                system_flooding += flooding
                if ponded > 1e-8:
                    active_ponded += 1
            cumulative_outfall += max(0.0, float(outfall.flow)) * 60.0
            row: dict[str, float | int | str] = {
                "step": step,
                "time": sim.current_time.isoformat(sep=" "),
                "relative_hour": step / 60.0,
                "outfall_flow_cms": max(0.0, float(outfall.flow)),
                "cumulative_outfall_m3": cumulative_outfall,
                "system_flooding_cms": system_flooding,
                "active_ponded_nodes": active_ponded,
            }
            for monitor, handle in monitors.items():
                row[f"{monitor}_total_inflow_cms"] = float(handle.total_inflow)
                row[f"{monitor}_depth_m"] = float(handle.depth)
            monitor_rows.append(row)
    event_df = pd.DataFrame(monitor_rows)
    node_df = pd.DataFrame([{"node": node, **stats} for node, stats in node_stats.items()]).sort_values(
        ["max_flooding_cms", "max_total_inflow_cms"], ascending=False
    )
    event_df.to_csv(EVENT_TS_CSV, index=False, encoding="utf-8-sig")
    node_df.to_csv(NODE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    return event_df, node_df


def draw_scheme(model: dict[str, object], layout: dict[str, object]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    coords: dict[str, tuple[float, float]] = model["coords"]
    fig, ax = plt.subplots(figsize=(13, 8), dpi=180)
    for _link, up, down, _length in model["conduits"]:
        if up in coords and down in coords:
            ax.plot([coords[up][0], coords[down][0]], [coords[up][1], coords[down][1]], color="#b1b7bb", lw=0.8, alpha=0.65, zorder=1)
    candidates = [n for n in layout["candidate_nodes"] if n in coords]
    ax.scatter([coords[n][0] for n in candidates], [coords[n][1] for n in candidates], s=38, color="#d0d7de", edgecolor="white", linewidth=0.35, label=f"候选井 {len(candidates)} 个", zorder=2)
    monitors = [n for n in layout["monitor_nodes"] if n in coords]
    ax.scatter([coords[n][0] for n in monitors], [coords[n][1] for n in monitors], s=120, marker="s", color="#2367a2", edgecolor="white", linewidth=0.8, label=f"监测站 {len(monitors)} 个", zorder=3)
    for spec in INJECTION_SPECS:
        n = str(spec["node"])
        ax.scatter([coords[n][0]], [coords[n][1]], s=230, marker="*", color="#d9822b", edgecolor="black", linewidth=0.8, label="注入点" if spec == INJECTION_SPECS[0] else None, zorder=4)
        ax.text(coords[n][0], coords[n][1], f" {n}", fontsize=9, weight="bold")
    for n in monitors:
        ax.text(coords[n][0], coords[n][1], f" {n}", fontsize=8, color="#12395c")
    if OUTFALL_NODE in coords:
        ax.scatter([coords[OUTFALL_NODE][0]], [coords[OUTFALL_NODE][1]], s=150, marker="D", color="#2d8a54", edgecolor="black", label="排口 J6", zorder=4)
    ax.set_title("0416 方案V1：注入点、监测站、候选井布局")
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_SCHEME)
    plt.close(fig)


def draw_topology(model: dict[str, object], layout: dict[str, object], helper: dict[str, object]) -> None:
    coords: dict[str, tuple[float, float]] = model["coords"]
    downstream_path = helper["downstream_path"]
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=180)
    for spec in INJECTION_SPECS:
        n = str(spec["node"])
        path = [n] + [p for p in downstream_path(n) if p in coords]
        color = {"J1": "#4c78a8", "J72": "#e45756", "J10": "#f58518", "J49": "#54a24b"}.get(n, "#777")
        for a, b in zip(path[:-1], path[1:]):
            ax.plot([coords[a][0], coords[b][0]], [coords[a][1], coords[b][1]], color=color, lw=2.2, alpha=0.78)
        ax.scatter([coords[n][0]], [coords[n][1]], s=210, marker="*", color=color, edgecolor="black", label=f"{n} {spec['line']}")
    for m in MONITOR_NODES:
        if m in coords:
            ax.scatter([coords[m][0]], [coords[m][1]], s=90, marker="s", color="#1f2a2e", edgecolor="white", zorder=4)
            ax.text(coords[m][0], coords[m][1], f" {m}", fontsize=8)
    ax.set_title("0416 方案V1：注入点到排口的下游路径与监测控制点")
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.18)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_TOPOLOGY)
    plt.close(fig)


def draw_injection(injection_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=180)
    for node, one in injection_df.groupby("node"):
        ax.plot(one["relative_hour"], one["flow_cms"], lw=1.8, label=node)
    ax.set_title("0416 方案V1：设计注入波形")
    ax.set_xlabel("相对时间（小时）")
    ax.set_ylabel("注入流量（CMS）")
    ax.grid(alpha=0.22)
    ax.legend(title="注入点")
    fig.tight_layout()
    fig.savefig(FIG_INJECTION)
    plt.close(fig)


def draw_response(event_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), dpi=180, sharex=True)
    x = event_df["relative_hour"]
    for monitor in MONITOR_NODES:
        col = f"{monitor}_total_inflow_cms"
        if col in event_df.columns:
            axes[0].plot(x, event_df[col], lw=1.1, label=monitor)
    axes[0].set_title("0416 方案V1：监测站总入流响应")
    axes[0].set_ylabel("节点总入流（CMS）")
    axes[0].grid(alpha=0.22)
    axes[0].legend(ncol=5, fontsize=8)
    axes[1].plot(x, event_df["outfall_flow_cms"], color="#2d8a54", lw=1.7, label="排口 J6")
    axes[1].plot(x, event_df["system_flooding_cms"], color="#d84a3a", lw=1.2, label="系统溢流速率")
    axes[1].set_title("排口出流与溢流检查")
    axes[1].set_xlabel("相对时间（小时）")
    axes[1].set_ylabel("流量（CMS）")
    axes[1].grid(alpha=0.22)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(FIG_RESPONSE)
    plt.close(fig)


def write_html(model: dict[str, object], layout: dict[str, object]) -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    coords = model["coords"]
    links = [
        {"id": link, "from": up, "to": down, "x1": coords[up][0], "y1": coords[up][1], "x2": coords[down][0], "y2": coords[down][1], "length_m": length}
        for link, up, down, length in model["conduits"]
        if up in coords and down in coords
    ]
    nodes = []
    injection_nodes = {str(s["node"]) for s in INJECTION_SPECS}
    for node in model["nodes"]:
        if node not in coords:
            continue
        category = "候选井"
        if node in MONITOR_NODES:
            category = "监测站"
        if node in injection_nodes:
            category = "注入点"
        nodes.append({"id": node, "category": category, "x": coords[node][0], "y": coords[node][1]})
    if OUTFALL_NODE in coords:
        nodes.append({"id": OUTFALL_NODE, "category": "排口", "x": coords[OUTFALL_NODE][0], "y": coords[OUTFALL_NODE][1]})
    xs = [n["x"] for n in nodes]
    ys = [n["y"] for n in nodes]
    data = {
        "nodes": nodes,
        "links": links,
        "viewbox": {"x": min(xs) - 80, "y": min(ys) - 80, "w": max(xs) - min(xs) + 160, "h": max(ys) - min(ys) + 160},
        "stats": {
            "候选井": len(CANDIDATE_NODES),
            "监测站": len(MONITOR_NODES),
            "注入点": len(INJECTION_SPECS),
            "排口": 1,
            "管道": len(links),
        },
    }
    payload = json.dumps(data, ensure_ascii=False)
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>0416 方案V1 交互布局</title>
<style>
body{{margin:0;font-family:"Microsoft YaHei","SimHei",Arial,sans-serif;background:#f6f3ec;color:#1f2a2e}}
header{{background:#1f2a2e;color:white;padding:18px 24px}}h1{{margin:0;font-size:22px}}p{{margin:8px 0 0;color:#d6dedf}}
.wrap{{display:grid;grid-template-columns:330px 1fr;gap:16px;padding:16px}}.panel{{background:white;border-radius:14px;padding:14px;box-shadow:0 8px 24px rgba(31,42,46,.09)}}
.card{{display:inline-block;min-width:120px;margin:5px;padding:10px;border:1px solid #e4e0d7;border-radius:12px;background:#fffdf8}}.num{{font-size:24px;font-weight:800;display:block}}
label{{display:block;margin:8px 0}}svg{{width:100%;height:78vh;background:linear-gradient(145deg,#fffef9,#eef4f1);border-radius:14px}}.link{{stroke:#aab2b8;stroke-width:3;opacity:.65}}
.候选井{{fill:#c9d1d9}}.监测站{{fill:#2367a2}}.注入点{{fill:#d9822b}}.排口{{fill:#2d8a54}}.node{{stroke:white;stroke-width:5;cursor:pointer}}.hidden{{display:none}}.selected{{stroke:#111;stroke-width:10}}
#detail{{font-size:13px;line-height:1.7}}.chip{{display:inline-block;margin:4px;padding:4px 8px;border-radius:999px;border:1px solid #ddd4c6;cursor:pointer}}
</style></head><body><header><h1>0416 方案V1：注入点、监测站、候选井交互布局</h1><p>无入流基线 + 小流量注入事件；监测站均布设在注入点下游路径上。</p></header>
<div class="wrap"><aside class="panel"><div id="cards"></div><h3>分类开关</h3>
<label><input type="checkbox" data-layer="link" checked> 管道</label><label><input type="checkbox" data-layer="候选井" checked> 候选井</label>
<label><input type="checkbox" data-layer="监测站" checked> 监测站</label><label><input type="checkbox" data-layer="注入点" checked> 注入点</label><label><input type="checkbox" data-layer="排口" checked> 排口</label>
<h3>对象详情</h3><div id="detail">点击图上对象查看</div><h3>注入点</h3>{''.join(f'<span class="chip">{s["node"]} {s["line"]}</span>' for s in INJECTION_SPECS)}</aside>
<main class="panel"><svg id="svg"></svg></main></div>
<script>
const DATA={payload};const svg=document.getElementById('svg');const vb=DATA.viewbox;svg.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`);
document.getElementById('cards').innerHTML=Object.entries(DATA.stats).map(([k,v])=>`<span class="card"><span class="num">${{v}}</span>${{k}}</span>`).join('');
function detail(o,t){{document.getElementById('detail').innerHTML='<b>'+t+'：'+o.id+'</b><br>'+Object.entries(o).map(([k,v])=>k+': '+v).join('<br>')}}
DATA.links.forEach(l=>{{let e=document.createElementNS('http://www.w3.org/2000/svg','line');e.setAttribute('x1',l.x1);e.setAttribute('y1',l.y1);e.setAttribute('x2',l.x2);e.setAttribute('y2',l.y2);e.setAttribute('class','link');e.dataset.layer='link';e.onclick=()=>detail(l,'管道');svg.appendChild(e)}});
DATA.nodes.forEach(n=>{{let e=document.createElementNS('http://www.w3.org/2000/svg',n.category==='排口'?'rect':'circle');if(n.category==='排口'){{e.setAttribute('x',n.x-18);e.setAttribute('y',n.y-18);e.setAttribute('width',36);e.setAttribute('height',36)}}else{{e.setAttribute('cx',n.x);e.setAttribute('cy',n.y);e.setAttribute('r',n.category==='注入点'?24:n.category==='监测站'?20:13)}}e.setAttribute('class','node '+n.category);e.dataset.layer=n.category;e.onclick=()=>detail(n,'节点');svg.appendChild(e)}});
document.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>document.querySelectorAll(`[data-layer="${{cb.dataset.layer}}"]`).forEach(e=>e.classList.toggle('hidden',!cb.checked)));
</script></body></html>"""
    HTML_OUT.write_text(html, encoding="utf-8")


def total_volume_for_spec(spec: dict[str, float | str]) -> float:
    return float(spec["peak_cms"]) * (float(spec["plateau_h"]) + float(spec["ramp_h"])) * 3600.0


def write_report_and_summary(model: dict[str, object], layout: dict[str, object], injection_df: pd.DataFrame, event_df: pd.DataFrame, node_df: pd.DataFrame) -> dict[str, object]:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    total_volumes = {str(spec["node"]): total_volume_for_spec(spec) for spec in INJECTION_SPECS}
    candidate_nodes = list(layout["candidate_nodes"])
    monitor_nodes = list(layout["monitor_nodes"])
    max_flood = float(node_df["max_flooding_cms"].max())
    flood_volume = float(node_df["flooding_volume_m3"].sum())
    max_outfall = event_df.loc[event_df["outfall_flow_cms"].idxmax()]
    summary = {
        "clean_model": str(CLEAN_INP),
        "event_model": str(EVENT_INP),
        "candidate_count": len(candidate_nodes),
        "candidate_nodes": candidate_nodes,
        "monitor_count": len(monitor_nodes),
        "monitor_nodes": monitor_nodes,
        "injection_specs": INJECTION_SPECS,
        "injection_total_volume_m3": total_volumes,
        "downstream_monitors_by_injection": layout["injection_downstream_monitors"],
        "event_check": {
            "max_node_flooding_cms": max_flood,
            "total_flooding_volume_m3": flood_volume,
            "max_active_ponded_nodes": int(event_df["active_ponded_nodes"].max()),
            "outfall_peak_cms": float(max_outfall["outfall_flow_cms"]),
            "outfall_peak_time": str(max_outfall["time"]),
            "outfall_total_m3": float(event_df.iloc[-1]["cumulative_outfall_m3"]),
        },
        "outputs": {
            "report": str(REPORT_MD),
            "summary": str(SCHEME_JSON),
            "event_timeseries": str(EVENT_TS_CSV),
            "node_summary": str(NODE_SUMMARY_CSV),
            "html": str(HTML_OUT),
            "figures": [str(FIG_SCHEME), str(FIG_TOPOLOGY), str(FIG_INJECTION), str(FIG_RESPONSE)],
        },
    }
    SCHEME_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    inj_table = "\n".join(
        f"| {s['node']} | {s['line']} | {s['start_h']:.1f} | {s['peak_cms']:.3f} | {total_volumes[str(s['node'])]:.1f} | {', '.join(layout['injection_downstream_monitors'][str(s['node'])])} |"
        for s in INJECTION_SPECS
    )
    report = f"""# 0416 方案V1：无入流基线、注入点、监测站与候选井设计

## 1. 干净无入流模型

- 原始模型没有改动：`{RAW_INP}`
- 新建无入流基线：`{CLEAN_INP}`
- 处理方式：删除 `[INFLOWS]` 中的 J11 外部入流；只将原模型中被 `[INFLOWS]` 和 `[RAINGAGES]` 实际引用的时序置零。因此该模型没有 J11 外部入流，也没有雨量/污水量径流输入。

## 2. 方案V1布局

- 候选井规模：{len(candidate_nodes)} 个检查井，参考 0401 的 20 候选井做法，不再使用 100 个检查井全量搜索。
- 候选井布设：`{', '.join(candidate_nodes)}`。
- 监测站数量：{len(monitor_nodes)} 个，布设为 `{', '.join(monitor_nodes)}`。
- 监测原则：每个设计注入点下游至少有多个监测井；上游监测点不作为该注入点的判别依据。

| 注入点 | 所在线路 | 开始时间 h | 峰值 CMS | 注入总量 m3 | 下游监测井 |
| --- | --- | ---: | ---: | ---: | --- |
{inj_table}

注入波形为小流量梯形波：1 小时上升、3 小时平台、1 小时下降。峰值控制在 0.008-0.012 CMS，第一版目的是形成可识别信号，同时避免溢流。

## 3. 事件模拟校验

- 最大节点溢流速率：{max_flood:.8f} CMS。
- 总溢流体积：{flood_volume:.6f} m3。
- 最大同时积水节点数：{int(event_df['active_ponded_nodes'].max())}。
- 排口峰值：{float(max_outfall['outfall_flow_cms']):.5f} CMS，发生在 {max_outfall['time']}。
- 排口累计出流：{float(event_df.iloc[-1]['cumulative_outfall_m3']):.2f} m3。

判断：若最大节点溢流速率和总溢流体积为 0 或接近 0，则本版注入量没有触发溢流，适合作为第一版识别实验事件。

## 4. 输出

- 方案汇总：`{SCHEME_JSON}`
- 交互 HTML：`{HTML_OUT}`
- 事件逐分钟响应：`{EVENT_TS_CSV}`，用于看水力响应和溢流校验。
- GA/AM 正式输入数据由 `build_0416_data.py` 生成，当前统一为 5 分钟采样，以降低数据量。
- 节点统计：`{NODE_SUMMARY_CSV}`
- 布局图：`{FIG_SCHEME}`
- 下游路径图：`{FIG_TOPOLOGY}`
- 注入波形图：`{FIG_INJECTION}`
- 监测响应图：`{FIG_RESPONSE}`
"""
    REPORT_MD.write_text(report, encoding="utf-8")
    return summary


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    build_clean_model()
    injection_df = build_event_model()
    model = parse_model(CLEAN_INP)
    helper = graph_helpers(model)
    layout = classify_layout(model, helper)
    event_df, node_df = run_event(model)
    draw_scheme(model, layout)
    draw_topology(model, layout, helper)
    draw_injection(injection_df)
    draw_response(event_df)
    write_html(model, layout)
    summary = write_report_and_summary(model, layout, injection_df, event_df, node_df)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
