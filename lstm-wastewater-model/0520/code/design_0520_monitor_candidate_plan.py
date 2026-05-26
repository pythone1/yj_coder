from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import heapq
import json
import math

import pandas as pd

from config_0416 import CANDIDATE_NODES as CONFIG_CANDIDATE_NODES
from config_0416 import MONITOR_NODES as CONFIG_MONITOR_NODES
from config_0416 import TRUTH_INJECTION_NODES as CONFIG_INJECTION_NODES


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_0520"
OUT_HTML = ANALYSIS_DIR / "0520_monitor_candidate_injection_plan.html"
OUT_CSV = ANALYSIS_DIR / "0520_monitor_candidate_injection_plan.csv"
OUT_MD = ANALYSIS_DIR / "0520_monitor_candidate_injection_plan.md"
OUT_JSON = ANALYSIS_DIR / "0520_monitor_candidate_injection_plan.json"

NODES_CSV = ANALYSIS_DIR / "0520_all_nodes_full_fields.csv"
LINKS_CSV = ANALYSIS_DIR / "0520_links_classified.csv"
SUBS_CSV = ANALYSIS_DIR / "0520_subcatchments.csv"

OUTFALL_NODE = "293"

# Monitors: final control + branch-level control points.
MONITOR_NODES = list(CONFIG_MONITOR_NODES)

# Twenty candidate source locations, selected as representative simplified zones.
CANDIDATE_NODES = list(CONFIG_CANDIDATE_NODES)

# Planned injection points, chosen from candidates with different monitor signatures.
INJECTION_NODES = list(CONFIG_INJECTION_NODES)

MONITOR_DESC = {
    "286": "下游总控点，靠近排口前主汇合区，用于判断全局水量变化是否被捕获。",
    "242": "中部主干控制点，覆盖南侧主干和东南支线进入下游前的响应。",
    "250": "东南/中东支线控制点，区分63、118、306、64等东侧候选区。",
    "201": "远东南支线控制点，增强118、120、306、64、91等远端区域的局部敏感性。",
    "226": "西北长支线控制点，覆盖215、216等远端北部候选区。",
    "206": "西侧支线汇合控制点，覆盖103、241、273等支线进入主网前的变化。",
    "313": "中北支线控制点，覆盖308、310、312等上游支线，避免只靠下游总控点判断。",
}

CANDIDATE_DESC = {
    "103": "大汇水面积节点，代表西南侧长支线末端区域。",
    "215": "全网北端大汇水面积节点，代表最远端北部来源。",
    "63": "东南主支线高汇水节点，靠近250监测控制区。",
    "62": "中南支线高汇水节点，进入242主干控制区。",
    "118": "东北远端大汇水节点，经过201、250、242等多级监测点。",
    "306": "东南端高汇水节点，代表远端末梢区域。",
    "308": "中北支线高汇水节点，进入313控制区。",
    "241": "西侧支线代表点，进入206控制区。",
    "10": "南侧主干代表点，覆盖中下游主干区域。",
    "124": "242附近支线入口代表点。",
    "216": "西北支线代表点，进入226控制区。",
    "120": "东北支线中游代表点，进入201控制区。",
    "310": "中北支线代表点，进入313控制区。",
    "64": "东南支线代表点，进入201/250控制区。",
    "40": "南侧局部支线代表点，进入242控制区。",
    "312": "中北支线汇入段代表点，进入313控制区。",
    "155": "东南下游末梢代表点，进入242控制区。",
    "37": "南侧支线代表点，进入242控制区。",
    "91": "东侧支线汇合段代表点，进入201控制区。",
    "273": "西侧近中游支线代表点，进入206控制区。",
}


# Use the canonical point scheme from config_0416.py so visualization and
# algorithm inputs cannot drift apart.
MONITOR_NODES = list(CONFIG_MONITOR_NODES)
CANDIDATE_NODES = list(CONFIG_CANDIDATE_NODES)
INJECTION_NODES = list(CONFIG_INJECTION_NODES)

MONITOR_DESC = {
    "286": "排口前总控断面，所有分支最终进入该点，用于检验全局水量响应。",
    "242": "南侧主干下游控制断面，监测10、62、124、40、155、37等主干和南侧支线变化。",
    "250": "东南主干下游控制断面，监测63及东侧远端支线进入主干后的变化。",
    "65": "右侧最末端的出口监测点，右侧两条末端支路的水都会先经过这里，再往主干走。",
    "226": "西北长支线下游控制断面，监测215、216、60等北部远端来源。",
    "206": "西侧支线下游控制断面，监测103、241、273等西侧来源。",
    "313": "中北支线下游控制断面，监测308、310、312等中北来源。",
}

CANDIDATE_DESC = {
    "10": "主干注入/候选点，位于南侧主干中下游，受242和286监测。",
    "62": "中南支线候选点，进入242主干控制区。",
    "124": "242上游支线入口候选点，用于区分近主干支线响应。",
    "40": "南侧局部支线候选点，距离10和37有一定间隔，受242监测。",
    "155": "东南末梢候选点，代表远端小支线，受242监测。",
    "63": "主干注入/候选点，位于东南主干进入250前，受250、242、286多级监测。",
    "103": "西侧枝干注入/候选点，位于206上游，代表西侧长支线远端。",
    "241": "西侧支线候选点，与103、273分处不同位置，受206监测。",
    "273": "西侧中游候选点，靠近支线汇入206前的中游段。",
    "215": "北部枝干注入/候选点，位于226上游，代表最远端北部来源。",
    "216": "西北支线中游候选点，进入226控制区。",
    "60": "北部泵站附近候选点，代表北部支线入口段。",
    "308": "中北远端候选点，进入313控制区。",
    "310": "中北支线中游候选点，与308、312形成上中下分散。",
    "312": "中北支线下游候选点，位于313监测点上游。",
    "118": "右上角末端候选点，水会经过65，再到250、242、286。",
    "306": "右下角末端候选点，水会经过65，再到250、242、286。",
    "64": "右下角支路中段候选点，和306拉开距离，水会经过65。",
    "91": "右侧支路汇合前候选点，水会经过65。",
    "85": "右上角支路中段候选点，和118、91拉开距离，水会经过65。",
}

MONITOR_DESC.update(
    {
        "223": "西北长支线下游监测点，用于捕捉北部远端来源向主干汇入前的变化。",
        "239": "西北支线靠近主干的监测点，用于和223形成上下游对照。",
        "267": "西侧支线汇入主干前的监测点，用于识别103、241、273、308、310、312等西侧和中北来源。",
        "8": "中下游主干监测点，用于承接南侧主干、右侧支线和排口前总控之间的变化。",
        "251": "东南主干监测点，用于识别178、118、304、64、91、85等右侧来源。",
        "252": "右侧末端支线监测点，用于增强304、64、91、85等远端响应的可分辨性。",
        "189": "南侧局部支线监测点，用于补充178附近局部来水响应。",
        "37": "南侧支线监测点，用于识别42附近注入和南侧局部支线变化。",
    }
)

CANDIDATE_DESC.update(
    {
        "42": "南侧支线注入/候选点，位于37监测点响应范围内，用于检验局部分支识别能力。",
        "178": "东南主干注入/候选点，位于251和189相关响应范围内，用于形成局部与主干共同响应。",
        "304": "右侧远端注入/候选点，位于252、251下游监测组合内，用于检验右侧末端来源识别能力。",
    }
)

BRANCH_GROUP = {
    "286": "排口总控",
    "242": "南侧主干",
    "250": "东南主干",
    "65": "右侧末端",
    "226": "西北长支线",
    "206": "西侧支线",
    "313": "中北支线",
    "10": "南侧主干",
    "62": "南侧主干",
    "124": "南侧主干",
    "40": "南侧支线",
    "155": "南侧支线",
    "63": "东南主干",
    "103": "西侧支线",
    "241": "西侧支线",
    "273": "西侧支线",
    "215": "西北长支线",
    "216": "西北长支线",
    "60": "西北长支线",
    "308": "中北支线",
    "310": "中北支线",
    "312": "中北支线",
    "118": "右侧末端",
    "306": "右侧末端",
    "64": "右侧末端",
    "91": "右侧末端",
    "85": "右侧末端",
    "223": "西北长支线",
    "239": "西北长支线",
    "267": "西侧支线",
    "8": "中下游主干",
    "251": "东南主干",
    "252": "右侧末端",
    "189": "南侧局部支线",
    "37": "南侧局部支线",
    "42": "南侧局部支线",
    "178": "东南主干",
    "304": "右侧末端",
}


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except Exception:
        return default


def build_shortest_tree(nodes: pd.DataFrame, links: pd.DataFrame) -> tuple[dict[str, float], dict[str, str], dict[str, list[str]]]:
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for _, row in links[links["type"].isin(["conduit", "pump"])].iterrows():
        a, b = str(row["from_node"]), str(row["to_node"])
        length = safe_float(row.get("length_m"), 1.0)
        if length <= 0:
            length = 1.0
        adj[a].append((b, length))
        adj[b].append((a, length))

    dist: dict[str, float] = {OUTFALL_NODE: 0.0}
    parent: dict[str, str] = {OUTFALL_NODE: ""}
    queue: list[tuple[float, str]] = [(0.0, OUTFALL_NODE)]
    while queue:
        d, node = heapq.heappop(queue)
        if d != dist[node]:
            continue
        for nxt, length in adj[node]:
            nd = d + length
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                parent[nxt] = node
                heapq.heappush(queue, (nd, nxt))

    children: dict[str, list[str]] = defaultdict(list)
    for node, par in parent.items():
        if par:
            children[par].append(node)

    for node in nodes["node"].astype(str):
        dist.setdefault(node, float("nan"))
        parent.setdefault(node, "")
    return dist, parent, children


def path_to_outfall(node: str, parent: dict[str, str]) -> list[str]:
    path: list[str] = []
    while node:
        path.append(node)
        node = parent.get(node, "")
    return path


def direct_area_by_node(subs: pd.DataFrame) -> dict[str, float]:
    if subs.empty:
        return {}
    return {str(k): float(v) for k, v in subs.groupby("outlet")["area_ha"].sum().to_dict().items()}


def tree_area_by_node(direct_area: dict[str, float], children: dict[str, list[str]]) -> dict[str, float]:
    cache: dict[str, float] = {}

    def calc(node: str) -> float:
        if node in cache:
            return cache[node]
        total = direct_area.get(node, 0.0) + sum(calc(child) for child in children.get(node, []))
        cache[node] = total
        return total

    for node in set(direct_area) | set(children):
        calc(node)
    return cache


def node_metrics(nodes: pd.DataFrame, links: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    nodes["node"] = nodes["node"].astype(str)
    dist, parent, children = build_shortest_tree(nodes, links)
    direct_area = direct_area_by_node(subs)
    tree_area = tree_area_by_node(direct_area, children)

    degree: dict[str, int] = defaultdict(int)
    for _, row in links[links["type"].isin(["conduit", "pump"])].iterrows():
        degree[str(row["from_node"])] += 1
        degree[str(row["to_node"])] += 1

    rows = []
    for _, row in nodes.iterrows():
        node = str(row["node"])
        path = path_to_outfall(node, parent)
        downstream_monitors = [m for m in MONITOR_NODES if m in path]
        rows.append(
            {
                "node": node,
                "x": safe_float(row.get("coord_x")),
                "y": safe_float(row.get("coord_y")),
                "node_type": row.get("inp_node_type", ""),
                "direct_area_ha": direct_area.get(node, 0.0),
                "simplified_upstream_area_ha": tree_area.get(node, 0.0),
                "distance_to_outfall_m": dist.get(node, float("nan")),
                "network_degree": degree.get(node, 0),
                "simplified_child_count": len(children.get(node, [])),
                "path_to_outfall": " -> ".join(path),
                "downstream_monitors": ";".join(downstream_monitors),
                "downstream_monitor_count": len(downstream_monitors),
            }
        )
    return pd.DataFrame(rows)


def build_plan_table(metrics: pd.DataFrame) -> pd.DataFrame:
    selected = set(MONITOR_NODES) | set(CANDIDATE_NODES) | set(INJECTION_NODES)
    df = metrics[metrics["node"].isin(selected)].copy()

    def role(node: str) -> str:
        roles = []
        if node in MONITOR_NODES:
            roles.append("监测点")
        if node in CANDIDATE_NODES:
            roles.append("候选段位")
        if node in INJECTION_NODES:
            roles.append("注入点")
        return "+".join(roles)

    def reason(node: str) -> str:
        if node in INJECTION_NODES:
            return "计划注入点；" + CANDIDATE_DESC.get(node, "")
        if node in MONITOR_NODES:
            return MONITOR_DESC.get(node, "")
        return CANDIDATE_DESC.get(node, "")

    df["role"] = df["node"].map(role)
    df["branch_group"] = df["node"].map(BRANCH_GROUP).fillna("其他")
    df["selection_reason"] = df["node"].map(reason)
    order_map = {n: i for i, n in enumerate(MONITOR_NODES + CANDIDATE_NODES)}
    df["sort_order"] = df["node"].map(order_map).fillna(999).astype(int)
    columns = [
        "node",
        "role",
        "branch_group",
        "x",
        "y",
        "direct_area_ha",
        "simplified_upstream_area_ha",
        "distance_to_outfall_m",
        "network_degree",
        "simplified_child_count",
        "downstream_monitors",
        "downstream_monitor_count",
        "selection_reason",
        "path_to_outfall",
    ]
    return df.sort_values(["sort_order", "node"])[columns]


def svg_map(nodes: pd.DataFrame, links: pd.DataFrame, plan: pd.DataFrame) -> str:
    node_lookup = nodes.set_index(nodes["node"].astype(str)).to_dict("index")
    xs = [safe_float(v.get("coord_x")) for v in node_lookup.values()]
    ys = [safe_float(v.get("coord_y")) for v in node_lookup.values()]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    width, height = 1280, 860

    def sx(x: float) -> float:
        return 45 + (x - minx) / (maxx - minx or 1) * (width - 90)

    def sy(y: float) -> float:
        return height - 45 - (y - miny) / (maxy - miny or 1) * (height - 90)

    candidate_set = set(CANDIDATE_NODES)
    monitor_set = set(MONITOR_NODES)
    injection_set = set(INJECTION_NODES)
    selected = set(plan["node"].astype(str))

    parts = [f"<svg viewBox='0 0 {width} {height}' class='network'>"]
    for _, row in links.iterrows():
        a, b = str(row["from_node"]), str(row["to_node"])
        if a not in node_lookup or b not in node_lookup:
            continue
        color = "#94a3b8" if row["type"] == "conduit" else "#8b5cf6"
        stroke = 1.0 if row["type"] == "conduit" else 2.6
        parts.append(
            f"<line x1='{sx(safe_float(node_lookup[a].get('coord_x'))):.2f}' y1='{sy(safe_float(node_lookup[a].get('coord_y'))):.2f}' "
            f"x2='{sx(safe_float(node_lookup[b].get('coord_x'))):.2f}' y2='{sy(safe_float(node_lookup[b].get('coord_y'))):.2f}' "
            f"stroke='{color}' stroke-width='{stroke}' opacity='.42' />"
        )

    for node, row in node_lookup.items():
        x, y = sx(safe_float(row.get("coord_x"))), sy(safe_float(row.get("coord_y")))
        r, fill, stroke, sw = 2.2, "#cbd5e1", "white", 0.8
        if str(row.get("inp_node_type")) == "outfall":
            r, fill, stroke, sw = 7.5, "#111827", "white", 1.5
        if node in candidate_set:
            r, fill, stroke, sw = 7.0, "#f59e0b", "#7c2d12", 1.5
        if node in monitor_set:
            r, fill, stroke, sw = 8.5, "#2563eb", "white", 2.0
        if node in injection_set:
            r, fill, stroke, sw = 10.0, "#dc2626", "white", 2.4
        parts.append(f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{r}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}' />")
        if node in selected or str(row.get("inp_node_type")) == "outfall":
            parts.append(f"<text x='{x + 9:.2f}' y='{y - 7:.2f}' class='label'>{node}</text>")

    parts.append("</svg>")
    return "\n".join(parts)


DISPLAY_COLUMNS = {
    "node": "节点",
    "role": "类型",
    "branch_group": "所在区域",
    "x": "X坐标",
    "y": "Y坐标",
    "direct_area_ha": "本节点接入面积ha",
    "simplified_upstream_area_ha": "上游影响范围ha",
    "distance_to_outfall_m": "到排口距离m",
    "network_degree": "连接管数",
    "simplified_child_count": "上游分叉数",
    "downstream_monitors": "下游能看到它的监测点",
    "downstream_monitor_count": "可响应监测点数量",
    "selection_reason": "为什么选这里",
}


def table_html(df: pd.DataFrame, columns: list[str]) -> str:
    view = df[columns].rename(columns=DISPLAY_COLUMNS)
    return view.to_html(index=False, classes="table", escape=True)


def write_outputs(nodes: pd.DataFrame, links: pd.DataFrame, plan: pd.DataFrame) -> None:
    plan.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    data = {
        "monitors": MONITOR_NODES,
        "candidates": CANDIDATE_NODES,
        "injections": INJECTION_NODES,
        "plan": plan.to_dict("records"),
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    monitor_df = plan[plan["node"].isin(MONITOR_NODES)].copy()
    cand_df = plan[plan["node"].isin(CANDIDATE_NODES)].copy()
    inj_df = plan[plan["node"].isin(INJECTION_NODES)].copy()

    md = [
        "# 0520监测点-候选段位-注入点方案",
        "",
        "## 方案原则",
        "- 监测点优先布置在主要分支下游汇入位置和主干关键控制位置。",
        "- 右侧末端和东南主干设置多级监测点，增强远端变化识别能力。",
        "- 候选点覆盖主干、枝干、远端末梢和右侧末端区域，并保持空间分散。",
        "- 注入点均纳入候选点集合，且位于监测点上游响应范围内。",
        "",
        f"## 监测点（{len(MONITOR_NODES)}个）\n{', '.join(MONITOR_NODES)}",
        "",
        f"## 候选段位（{len(CANDIDATE_NODES)}个）\n{', '.join(CANDIDATE_NODES)}",
        "",
        f"## 注入点（{len(INJECTION_NODES)}个）\n{', '.join(INJECTION_NODES)}",
        "",
        "## 注入点下游监测响应组合",
    ]
    for _, row in inj_df.iterrows():
        md.append(f"- {row['node']}: {row['downstream_monitors']}")
    md.extend(["", f"可视化文件：{OUT_HTML}", f"CSV方案表：{OUT_CSV}"])
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>0520监测点候选段位注入点方案</title>
<style>
body{{margin:0;background:#f6f8fb;color:#172033;font-family:'Microsoft YaHei','SimHei',Arial,sans-serif;}}
header{{background:#102a43;color:white;padding:24px 34px;}}
main{{padding:20px 34px 38px;}}
h1{{margin:0;font-size:26px;}} h2{{color:#12304a;margin:22px 0 12px;}}
.note{{background:#fff7ed;border-left:5px solid #f97316;padding:12px 14px;border-radius:8px;line-height:1.75;}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px;margin:16px 0;}}
.card{{background:white;border-radius:12px;padding:14px 16px;box-shadow:0 8px 24px #12304a12;}}
.card b{{font-size:26px;color:#0f766e;}}
.network{{width:100%;height:auto;background:white;border:1px solid #d8e2ec;border-radius:14px;box-shadow:0 8px 24px #12304a10;}}
.label{{font-size:12px;font-weight:700;fill:#111827;paint-order:stroke;stroke:white;stroke-width:3px;}}
.legend span{{display:inline-flex;align-items:center;margin-right:18px;gap:6px;}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;}}
.table{{border-collapse:collapse;width:100%;font-size:13px;background:white;}}
.table th,.table td{{border-bottom:1px solid #e5e7eb;padding:8px 9px;text-align:left;vertical-align:top;}}
.table th{{background:#eff6ff;color:#1e3a8a;position:sticky;top:0;}}
.scroll{{max-height:520px;overflow:auto;border-radius:12px;box-shadow:0 8px 24px #12304a10;}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr;}}main{{padding:16px;}}}}
</style>
</head>
<body>
<header><h1>0520管网简化布点方案</h1><p>{len(MONITOR_NODES)}个监测点 + {len(CANDIDATE_NODES)}个候选段位 + {len(INJECTION_NODES)}个注入点</p></header>
<main>
<section class="grid">
<div class="card"><span>监测点</span><br><b>{len(MONITOR_NODES)}</b><p>{', '.join(MONITOR_NODES)}</p></div>
<div class="card"><span>候选段位</span><br><b>{len(CANDIDATE_NODES)}</b><p>{', '.join(CANDIDATE_NODES)}</p></div>
<div class="card"><span>注入点</span><br><b>{len(INJECTION_NODES)}</b><p>{', '.join(INJECTION_NODES)}</p></div>
</section>
<section class="note">
本方案按照“分支下游控制、主干逐级校核、候选点空间分散”的原则布设。监测点优先布置在各主要来水分支的下游汇入位置和主干关键控制位置，确保不同分支的水量变化能够被识别；候选点覆盖主干、枝干、远端末梢和右侧末端区域，并尽量拉开空间距离，以降低相邻节点响应相似导致的代偿影响。
</section>
<h2>一、空间可视化</h2>
<div class="legend">
<span><i class="dot" style="background:#2563eb"></i>监测点</span>
<span><i class="dot" style="background:#f59e0b"></i>候选段位</span>
<span><i class="dot" style="background:#dc2626"></i>注入点</span>
<span><i class="dot" style="background:#111827"></i>排口</span>
</div>
{svg_map(nodes, links, plan)}
<h2>二、注入点响应组合</h2>
<div class="scroll">{table_html(inj_df, ['node','branch_group','downstream_monitors','direct_area_ha','simplified_upstream_area_ha','distance_to_outfall_m','selection_reason'])}</div>
<h2>三、监测点说明</h2>
<div class="scroll">{table_html(monitor_df, ['node','branch_group','x','y','simplified_upstream_area_ha','distance_to_outfall_m','network_degree','simplified_child_count','selection_reason'])}</div>
<h2>四、20个候选段位说明</h2>
<div class="scroll">{table_html(cand_df, ['node','branch_group','direct_area_ha','simplified_upstream_area_ha','distance_to_outfall_m','downstream_monitors','selection_reason'])}</div>
</main>
</body>
</html>"""
    OUT_HTML.write_text(html, encoding="utf-8")


def main() -> None:
    nodes = pd.read_csv(NODES_CSV, encoding="utf-8-sig")
    links = pd.read_csv(LINKS_CSV, encoding="utf-8-sig")
    subs = pd.read_csv(SUBS_CSV, encoding="utf-8-sig")
    metrics = node_metrics(nodes, links, subs)
    plan = build_plan_table(metrics)
    write_outputs(nodes, links, plan)
    print(f"html={OUT_HTML}")
    print(f"csv={OUT_CSV}")
    print(f"md={OUT_MD}")
    print(f"json={OUT_JSON}")
    print("monitors=" + ",".join(MONITOR_NODES))
    print("candidates=" + ",".join(CANDIDATE_NODES))
    print("injections=" + ",".join(INJECTION_NODES))
    print(plan[["node", "role", "downstream_monitors", "downstream_monitor_count"]].to_string(index=False))


if __name__ == "__main__":
    main()
