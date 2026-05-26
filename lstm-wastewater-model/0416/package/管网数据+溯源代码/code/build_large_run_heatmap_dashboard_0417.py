from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_0416 import (  # noqa: E402
    CANDIDATE_NODES,
    MODEL_1D_INP,
    MONITOR_NODES,
    OUTFALL_NODE,
    RESULT_DIR,
    TRUTH_INJECTION_NODES,
)


RUN_DIR = RESULT_DIR / "large_run"
ANALYSIS_DIR = RUN_DIR / "analysis_large_0417"
OUT_HTML = ANALYSIS_DIR / "large_run_heatmap_dashboard.html"

WIDTH = 1180
HEIGHT = 760
PADDING = 48


def read_section(inp_path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].upper()
            continue
        if section == section_name.upper():
            rows.append(line.split())
    return rows


def parse_network(inp_path: Path) -> tuple[list[dict], list[dict], dict]:
    coords: dict[str, tuple[float, float]] = {}
    for row in read_section(inp_path, "COORDINATES"):
        if len(row) >= 3:
            coords[row[0]] = (float(row[1]), float(row[2]))

    junctions = {row[0] for row in read_section(inp_path, "JUNCTIONS") if row}
    outfalls = {row[0] for row in read_section(inp_path, "OUTFALLS") if row}

    xs = [xy[0] for xy in coords.values()]
    ys = [xy[1] for xy in coords.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale = min((WIDTH - PADDING * 2) / span_x, (HEIGHT - PADDING * 2) / span_y)
    used_w = span_x * scale
    used_h = span_y * scale
    offset_x = (WIDTH - used_w) / 2
    offset_y = (HEIGHT - used_h) / 2

    def project(node_id: str) -> tuple[float, float]:
        x, y = coords[node_id]
        sx = offset_x + (x - min_x) * scale
        sy = HEIGHT - (offset_y + (y - min_y) * scale)
        return round(sx, 3), round(sy, 3)

    nodes: list[dict] = []
    for node_id in sorted(coords):
        x, y = project(node_id)
        role = "普通节点"
        if node_id in outfalls:
            role = "排口"
        elif node_id in TRUTH_INJECTION_NODES:
            role = "真值注入点"
        elif node_id in MONITOR_NODES:
            role = "监测点"
        elif node_id in CANDIDATE_NODES:
            role = "候选井"
        nodes.append(
            {
                "id": node_id,
                "x": x,
                "y": y,
                "rawX": coords[node_id][0],
                "rawY": coords[node_id][1],
                "role": role,
                "isJunction": node_id in junctions,
                "isCandidate": node_id in CANDIDATE_NODES,
                "isTruth": node_id in TRUTH_INJECTION_NODES,
                "isMonitor": node_id in MONITOR_NODES,
                "isOutfall": node_id in outfalls or node_id == OUTFALL_NODE,
            }
        )

    links: list[dict] = []
    for row in read_section(inp_path, "CONDUITS"):
        if len(row) < 3:
            continue
        link_id, from_node, to_node = row[0], row[1], row[2]
        if from_node not in coords or to_node not in coords:
            continue
        x1, y1 = project(from_node)
        x2, y2 = project(to_node)
        links.append(
            {
                "id": link_id,
                "from": from_node,
                "to": to_node,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )

    meta = {
        "junctionCount": len(junctions),
        "outfallCount": len(outfalls),
        "conduitCount": len(links),
        "coordinateCount": len(coords),
        "bounds": {
            "minX": min_x,
            "maxX": max_x,
            "minY": min_y,
            "maxY": max_y,
        },
    }
    return nodes, links, meta


def candidate_dict(row: pd.Series | dict, candidates: list[str]) -> dict[str, float]:
    return {node: float(row.get(node, 0.0)) for node in candidates}


def mean_values(df: pd.DataFrame, candidates: list[str]) -> dict[str, float]:
    if df.empty:
        return {node: 0.0 for node in candidates}
    return {node: float(df[node].mean()) for node in candidates}


def median_values(df: pd.DataFrame, candidates: list[str]) -> dict[str, float]:
    if df.empty:
        return {node: 0.0 for node in candidates}
    return {node: float(df[node].median()) for node in candidates}


def frequency_values(df: pd.DataFrame, candidates: list[str], threshold: float = 0.01) -> dict[str, float]:
    if df.empty:
        return {node: 0.0 for node in candidates}
    return {node: float((df[node] >= threshold).mean()) for node in candidates}


def sort_by_am_target(df: pd.DataFrame) -> pd.DataFrame:
    if "acceptance_log_target" in df.columns:
        return df.sort_values("acceptance_log_target", ascending=False)
    if "log_like" in df.columns:
        return df.sort_values("log_like", ascending=False)
    return df.sort_values("sse", ascending=True)


def top_nodes(values: dict[str, float], limit: int = 6) -> str:
    items = sorted(values.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return "，".join(f"{node}={value:.3f}" for node, value in items if value > 0)


def make_panel(title: str, description: str, rows: list[dict]) -> dict:
    return {"title": title, "description": description, "rows": rows}


def build_dashboard_data() -> dict:
    candidates = list(CANDIDATE_NODES)
    nodes, links, network_meta = parse_network(MODEL_1D_INP)

    solution_shares = pd.read_csv(RUN_DIR / "0417_solution_shares.csv").set_index("solution")
    solution_scores = pd.read_csv(RUN_DIR / "0417_solution_scores.csv").set_index("solution")
    ga_all = pd.read_csv(RUN_DIR / "0417_GA_all.csv")
    initial_ppd = pd.read_csv(RUN_DIR / "0417_initial_PPD.csv")
    ppd_samples = pd.read_csv(RUN_DIR / "0417_PPD_samples.csv")
    am_samples = pd.read_csv(RUN_DIR / "0417_AM_samples.csv")
    posterior_weights = pd.read_csv(RUN_DIR / "0417_posterior_node_weights.csv").set_index("node")
    summary = json.loads((RUN_DIR / "0417_summary.json").read_text(encoding="utf-8"))

    truth_values = {node: (1.0 / len(TRUTH_INJECTION_NODES) if node in TRUTH_INJECTION_NODES else 0.0) for node in candidates}

    ga_sorted = ga_all.sort_values("mean_nse", ascending=False)
    ga_top50 = ga_sorted.head(50)
    ga_high_099 = ga_sorted[ga_sorted["mean_nse"] >= 0.99]
    ga_high_0995 = ga_sorted[ga_sorted["mean_nse"] >= 0.995]
    ga_top100 = ga_sorted.head(100)
    ppd_sorted = sort_by_am_target(ppd_samples)
    am_sorted = sort_by_am_target(am_samples)

    layers = [
        {
            "id": "truth",
            "name": "真值注入份额",
            "description": "J20、J48、J11 三个真值点各占三分之一，用作识别目标。",
            "values": truth_values,
        },
        {
            "id": "posterior_best_map",
            "name": "AM 后验最优 MAP",
            "description": "按 AM 后验样本中 SSE 最小、NSE 最高的代表解绘制，是当前大参数版本最佳结果。",
            "values": candidate_dict(solution_shares.loc["posterior_best_map"], candidates),
        },
        {
            "id": "ga_best",
            "name": "GA 全局最优",
            "description": "GA 阶段按 mean NSE 选出的全局最优解，可以看到仍存在明显近邻代偿。",
            "values": candidate_dict(solution_shares.loc["ga_best"], candidates),
        },
        {
            "id": "posterior_median_summary",
            "name": "后验中位数汇总",
            "description": "逐节点后验中位数再归一化后的汇总解，多峰代偿下只作统计参考，不作为唯一最终解。",
            "values": candidate_dict(solution_shares.loc["posterior_median_summary"], candidates),
        },
        {
            "id": "ga_top50_mean",
            "name": "GA Top50 平均",
            "description": "GA 高分前 50 个样本的平均份额，用于观察高分解共同偏向哪些候选井。",
            "values": mean_values(ga_top50, candidates),
        },
        {
            "id": "ga_high_099_mean",
            "name": "GA NSE≥0.99 平均",
            "description": "所有 GA 高分样本的平均份额，反映高分代偿群体分布。",
            "values": mean_values(ga_high_099, candidates),
        },
        {
            "id": "initial_ppd_mean",
            "name": "GA 初始 PPD 平均",
            "description": "进入 AM 前的初始池平均分布，代表 GA 给 AM 的起点信息。",
            "values": mean_values(initial_ppd, candidates),
        },
        {
            "id": "ppd_mean",
            "name": "AM 后验 PPD 均值",
            "description": "AM warmup 后样本的均值，展示后验总体质量中心。",
            "values": mean_values(ppd_samples, candidates),
        },
        {
            "id": "ppd_median",
            "name": "AM 后验 PPD 中位数",
            "description": "AM warmup 后样本逐节点中位数，主要用于不确定性描述。",
            "values": median_values(ppd_samples, candidates),
        },
        {
            "id": "ga_top100_frequency",
            "name": "GA Top100 出现频率",
            "description": "GA 前 100 个高分样本中，各候选井份额超过 1% 的频率，值越高说明越常被高分解采用。",
            "values": frequency_values(ga_top100, candidates),
        },
    ]

    key_rows = []
    for name, label in [
        ("truth", "真值注入"),
        ("posterior_best_map", "AM 后验最优 MAP"),
        ("ga_best", "GA 全局最优"),
        ("posterior_median_summary", "后验中位数汇总"),
    ]:
        if name == "truth":
            values = truth_values
            metric = "目标解"
        else:
            values = candidate_dict(solution_shares.loc[name], candidates)
            score = solution_scores.loc[name]
            metric = f"NSE={score['mean_nse']:.6f}，SSE={score['sse']:.6g}"
        key_rows.append({"label": f"{label}｜{metric}", "values": values})

    ga_generation_rows = []
    for generation, group in ga_all.groupby("generation"):
        row = group.sort_values("mean_nse", ascending=False).iloc[0]
        ga_generation_rows.append(
            {
                "label": f"第 {int(generation)} 代最优｜NSE={row['mean_nse']:.6f}",
                "values": candidate_dict(row, candidates),
            }
        )

    high_score_rows = []
    for label, df in [
        ("GA Top50 平均", ga_top50),
        ("GA Top100 平均", ga_top100),
        ("GA NSE≥0.99 平均", ga_high_099),
        ("GA NSE≥0.995 平均", ga_high_0995),
        ("GA Top100 出现频率", ga_top100),
    ]:
        if "出现频率" in label:
            values = frequency_values(df, candidates)
        else:
            values = mean_values(df, candidates)
        high_score_rows.append({"label": f"{label}｜样本数={len(df)}", "values": values})

    am_chain_rows = []
    for chain, group in ppd_samples.groupby("chain"):
        best = sort_by_am_target(group).iloc[0]
        am_chain_rows.append(
            {
                "label": f"链 {int(chain)} MAP｜NSE={best['mean_nse']:.6f}，SSE={best['sse']:.6g}",
                "values": candidate_dict(best, candidates),
            }
        )
        am_chain_rows.append(
            {
                "label": f"链 {int(chain)} 均值｜样本数={len(group)}",
                "values": mean_values(group, candidates),
            }
        )

    posterior_rows = []
    for field, label in [
        ("posterior_mean", "后验均值"),
        ("posterior_median", "后验中位数"),
        ("p05", "后验 5% 分位"),
        ("p95", "后验 95% 分位"),
    ]:
        values = {node: float(posterior_weights.loc[node][field]) for node in candidates if node in posterior_weights.index}
        posterior_rows.append({"label": label, "values": values})

    panels = [
        make_panel(
            "一、关键解热力图",
            "把真值、GA 最优、AM MAP 和后验中位数放在一起，重点看识别质量和代偿位置。",
            key_rows,
        ),
        make_panel(
            "二、GA 分代最优热力图",
            "每一代取 mean NSE 最高样本，观察 GA 从随机猜测到高分解的迁移路径。",
            ga_generation_rows,
        ),
        make_panel(
            "三、GA 高分群体热力图",
            "统计高分样本整体偏向，判断高分是否集中在真值点，还是分散到代偿点。",
            high_score_rows,
        ),
        make_panel(
            "四、AM 链路热力图",
            "每条链分别展示 MAP 和后验均值，检查多链是否收敛到同一类解。",
            am_chain_rows,
        ),
        make_panel(
            "五、后验统计热力图",
            "展示 AM 后验均值、中位数和分位区间，用于识别不确定性与多峰代偿。",
            posterior_rows,
        ),
    ]

    cards = [
        {
            "title": "管网结构",
            "value": f"{network_meta['junctionCount']} 个检查井 / {network_meta['conduitCount']} 根管段 / {network_meta['outfallCount']} 个排口",
            "note": "结构来自 clean baseline INP 的 COORDINATES 与 CONDUITS。",
        },
        {
            "title": "大参数 GA",
            "value": f"样本 {len(ga_all)}，最优 NSE {ga_sorted.iloc[0]['mean_nse']:.6f}",
            "note": f"GA 最优前六节点：{top_nodes(candidate_dict(solution_shares.loc['ga_best'], candidates))}",
        },
        {
            "title": "AM 后验",
            "value": f"样本 {len(am_samples)}，PPD {len(ppd_samples)}",
            "note": f"AM MAP 前六节点：{top_nodes(candidate_dict(solution_shares.loc['posterior_best_map'], candidates))}",
        },
        {
            "title": "代偿现象",
            "value": "高分不等于唯一定位",
            "note": "J20 附近的 J2/J1/J21、J48 附近的 J84/J72/J86 仍可能形成高分代偿。",
        },
    ]

    return {
        "meta": {
            "title": "0417 大参数 GA-AM 识别热力图",
            "model": str(MODEL_1D_INP),
            "runDir": str(RUN_DIR),
            "summary": summary,
            "network": network_meta,
            "candidateNodes": candidates,
            "monitorNodes": list(MONITOR_NODES),
            "truthNodes": list(TRUTH_INJECTION_NODES),
            "outfallNode": OUTFALL_NODE,
        },
        "nodes": nodes,
        "links": links,
        "layers": layers,
        "panels": panels,
        "cards": cards,
    }


def build_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>0417 大参数 GA-AM 识别热力图</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --ink: #20302b;
      --muted: #66756f;
      --panel: #fffaf0;
      --line: rgba(32, 48, 43, 0.14);
      --pipe: rgba(55, 69, 64, 0.34);
      --accent: #0f766e;
      --danger: #c2410c;
      --monitor: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 12% 8%, rgba(15, 118, 110, .16), transparent 28rem),
        radial-gradient(circle at 86% 18%, rgba(194, 65, 12, .13), transparent 26rem),
        linear-gradient(135deg, #f7f2e8 0%, #e9efe7 100%);
      color: var(--ink);
      font-family: "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "PingFang SC", sans-serif;
      line-height: 1.55;
    }}
    header {{
      padding: 34px 42px 18px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 30px;
      letter-spacing: .02em;
    }}
    .subtitle {{
      max-width: 1180px;
      color: var(--muted);
      font-size: 15px;
    }}
    main {{
      padding: 0 42px 42px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: rgba(255, 250, 240, .82);
      box-shadow: 0 18px 45px rgba(32, 48, 43, .08);
    }}
    .card h3 {{
      margin: 0 0 8px;
      font-size: 14px;
      color: var(--muted);
      font-weight: 700;
    }}
    .card .value {{
      font-size: 20px;
      font-weight: 800;
      margin-bottom: 8px;
    }}
    .card .note {{
      color: var(--muted);
      font-size: 13px;
    }}
    .panel {{
      margin-top: 18px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: rgba(255, 250, 240, .88);
      box-shadow: 0 22px 50px rgba(32, 48, 43, .09);
    }}
    .panel h2 {{
      margin: 0 0 8px;
      font-size: 20px;
    }}
    .hint {{
      color: var(--muted);
      font-size: 14px;
      margin: 0 0 14px;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin: 14px 0 16px;
      padding: 12px;
      border-radius: 16px;
      background: rgba(255,255,255,.48);
      border: 1px solid var(--line);
    }}
    select, button {{
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fffdf7;
      color: var(--ink);
      padding: 9px 12px;
      font: inherit;
    }}
    label {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--muted);
      font-size: 14px;
    }}
    .map-wrap {{
      position: relative;
      overflow: hidden;
      border-radius: 20px;
      background:
        linear-gradient(90deg, rgba(32,48,43,.04) 1px, transparent 1px),
        linear-gradient(rgba(32,48,43,.04) 1px, transparent 1px),
        #fcf8ed;
      background-size: 32px 32px;
      border: 1px solid var(--line);
    }}
    svg {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px 18px;
      color: var(--muted);
      font-size: 13px;
      margin-top: 12px;
    }}
    .legend span {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .swatch {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      display: inline-block;
      border: 2px solid rgba(32,48,43,.25);
    }}
    .tooltip {{
      position: fixed;
      z-index: 50;
      display: none;
      max-width: 290px;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(20, 30, 27, .92);
      color: white;
      font-size: 13px;
      pointer-events: none;
      box-shadow: 0 12px 28px rgba(0,0,0,.22);
    }}
    .matrix {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,.52);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 1180px;
      font-size: 12px;
    }}
    th, td {{
      padding: 7px 8px;
      border-bottom: 1px solid rgba(32,48,43,.08);
      text-align: center;
      white-space: nowrap;
    }}
    th:first-child, td:first-child {{
      position: sticky;
      left: 0;
      z-index: 2;
      text-align: left;
      background: rgba(255,250,240,.96);
      min-width: 250px;
      font-weight: 700;
    }}
    .cell {{
      border-radius: 8px;
      font-variant-numeric: tabular-nums;
      font-weight: 700;
    }}
    details {{
      margin-top: 16px;
    }}
    summary {{
      cursor: pointer;
      font-weight: 800;
      margin-bottom: 8px;
    }}
    .explain {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 14px;
    }}
    .explain div {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 13px 14px;
      background: rgba(255,255,255,.42);
    }}
    .explain b {{
      display: block;
      margin-bottom: 6px;
    }}
    @media (max-width: 980px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .cards {{ grid-template-columns: 1fr; }}
      .explain {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>0417 大参数 GA-AM 识别热力图</h1>
    <p class="subtitle">
      该网页基于大参数运行结果重新生成，编码固定为 UTF-8。上半部分展示管网结构、候选井、监测点、真值点和排口；下半部分展示 GA、AM、后验和代偿频率的阶段热力图。
    </p>
  </header>
  <main>
    <section class="cards" id="cards"></section>

    <section class="panel">
      <h2>管网结构 GIS 热力图</h2>
      <p class="hint" id="layerHint"></p>
      <div class="toolbar">
        <label>热力层
          <select id="layerSelect"></select>
        </label>
        <label><input type="checkbox" id="togglePipes" checked> 显示管段</label>
        <label><input type="checkbox" id="toggleNodes" checked> 显示普通节点</label>
        <label><input type="checkbox" id="toggleLabels" checked> 显示候选井标签</label>
        <label><input type="checkbox" id="toggleMonitors" checked> 显示监测点</label>
        <label><input type="checkbox" id="toggleTruth" checked> 标注真值点</label>
      </div>
      <div class="map-wrap">
        <svg id="networkSvg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="管网结构热力图"></svg>
      </div>
      <div class="legend">
        <span><i class="swatch" style="background:#1d4ed8"></i>监测点</span>
        <span><i class="swatch" style="background:#111827"></i>排口</span>
        <span><i class="swatch" style="background:#ffffff;border-color:#c2410c"></i>真值点红色外圈</span>
        <span><i class="swatch" style="background:#d9f99d"></i>低份额</span>
        <span><i class="swatch" style="background:#f97316"></i>高份额</span>
      </div>
      <div class="explain">
        <div><b>读图方式</b>圆越大、颜色越偏橙红，表示该候选井在当前热力层中的份额或出现频率越高。蓝色方块是监测点，黑色方块是排口。</div>
        <div><b>结构含义</b>管段为 clean baseline INP 中的 CONDUITS，节点位置来自 COORDINATES；这是结构示意热力图，不是带底图坐标的真实 GIS 投影。</div>
      </div>
    </section>

    <section class="panel">
      <h2>阶段结果矩阵热力图</h2>
      <p class="hint">每一行是一个阶段或一个代表解，每一列是 20 个候选井。颜色越深表示份额或频率越高。</p>
      <div id="panels"></div>
    </section>
  </main>
  <div class="tooltip" id="tooltip"></div>
  <script>
    const DATA = {payload};
    const candidates = DATA.meta.candidateNodes;
    const layerSelect = document.getElementById('layerSelect');
    const svg = document.getElementById('networkSvg');
    const tooltip = document.getElementById('tooltip');

    function fmt(v) {{
      if (!Number.isFinite(v)) return '0.000';
      return v.toFixed(3);
    }}

    function colorScale(value, maxValue=0.34) {{
      const t = Math.max(0, Math.min(1, value / maxValue));
      if (t < 0.20) return '#d9f99d';
      if (t < 0.40) return '#bef264';
      if (t < 0.60) return '#facc15';
      if (t < 0.80) return '#fb923c';
      return '#ea580c';
    }}

    function textColor(value, maxValue=0.34) {{
      return value / maxValue > 0.62 ? '#fffaf0' : '#20302b';
    }}

    function showTip(event, html) {{
      tooltip.innerHTML = html;
      tooltip.style.display = 'block';
      tooltip.style.left = `${{event.clientX + 14}}px`;
      tooltip.style.top = `${{event.clientY + 14}}px`;
    }}

    function hideTip() {{
      tooltip.style.display = 'none';
    }}

    function renderCards() {{
      const wrap = document.getElementById('cards');
      wrap.innerHTML = DATA.cards.map(card => `
        <article class="card">
          <h3>${{card.title}}</h3>
          <div class="value">${{card.value}}</div>
          <div class="note">${{card.note}}</div>
        </article>
      `).join('');
    }}

    function initLayers() {{
      layerSelect.innerHTML = DATA.layers.map(layer => `<option value="${{layer.id}}">${{layer.name}}</option>`).join('');
      layerSelect.value = 'posterior_best_map';
    }}

    function currentLayer() {{
      return DATA.layers.find(layer => layer.id === layerSelect.value) || DATA.layers[0];
    }}

    function renderNetwork() {{
      const layer = currentLayer();
      const values = layer.values;
      document.getElementById('layerHint').textContent = layer.description;
      const showPipes = document.getElementById('togglePipes').checked;
      const showNodes = document.getElementById('toggleNodes').checked;
      const showLabels = document.getElementById('toggleLabels').checked;
      const showMonitors = document.getElementById('toggleMonitors').checked;
      const showTruth = document.getElementById('toggleTruth').checked;
      svg.innerHTML = '';

      if (showPipes) {{
        const pipeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const link of DATA.links) {{
          const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          line.setAttribute('x1', link.x1);
          line.setAttribute('y1', link.y1);
          line.setAttribute('x2', link.x2);
          line.setAttribute('y2', link.y2);
          line.setAttribute('stroke', 'rgba(55,69,64,.38)');
          line.setAttribute('stroke-width', '2.2');
          line.setAttribute('stroke-linecap', 'round');
          line.addEventListener('mousemove', event => showTip(event, `<b>管段 ${{link.id}}</b><br>${{link.from}} → ${{link.to}}`));
          line.addEventListener('mouseleave', hideTip);
          pipeGroup.appendChild(line);
        }}
        svg.appendChild(pipeGroup);
      }}

      if (showNodes) {{
        const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const node of DATA.nodes) {{
          if (node.isCandidate || node.isMonitor || node.isOutfall) continue;
          const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          dot.setAttribute('cx', node.x);
          dot.setAttribute('cy', node.y);
          dot.setAttribute('r', '2.7');
          dot.setAttribute('fill', 'rgba(32,48,43,.24)');
          nodeGroup.appendChild(dot);
        }}
        svg.appendChild(nodeGroup);
      }}

      if (showMonitors) {{
        const monitorGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const node of DATA.nodes.filter(n => n.isMonitor)) {{
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          rect.setAttribute('x', node.x - 5);
          rect.setAttribute('y', node.y - 5);
          rect.setAttribute('width', 10);
          rect.setAttribute('height', 10);
          rect.setAttribute('rx', 2);
          rect.setAttribute('fill', '#1d4ed8');
          rect.setAttribute('stroke', 'white');
          rect.setAttribute('stroke-width', '1.6');
          rect.addEventListener('mousemove', event => showTip(event, `<b>${{node.id}}</b><br>监测点`));
          rect.addEventListener('mouseleave', hideTip);
          monitorGroup.appendChild(rect);
        }}
        svg.appendChild(monitorGroup);
      }}

      const candidateGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      for (const node of DATA.nodes.filter(n => n.isCandidate)) {{
        const value = values[node.id] || 0;
        const r = 5 + 30 * Math.sqrt(Math.max(0, value));
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', r);
        circle.setAttribute('fill', colorScale(value));
        circle.setAttribute('fill-opacity', '0.88');
        circle.setAttribute('stroke', showTruth && node.isTruth ? '#c2410c' : 'rgba(32,48,43,.48)');
        circle.setAttribute('stroke-width', showTruth && node.isTruth ? '4' : '1.4');
        circle.addEventListener('mousemove', event => showTip(event, `<b>${{node.id}}</b><br>${{node.role}}<br>${{layer.name}}：${{fmt(value)}}<br>原始坐标：(${{node.rawX.toFixed(2)}}, ${{node.rawY.toFixed(2)}})`));
        circle.addEventListener('mouseleave', hideTip);
        candidateGroup.appendChild(circle);

        if (showLabels) {{
          const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          label.setAttribute('x', node.x + r + 3);
          label.setAttribute('y', node.y + 4);
          label.setAttribute('font-size', '12');
          label.setAttribute('font-weight', '800');
          label.setAttribute('fill', '#20302b');
          label.textContent = `${{node.id}} ${{fmt(value)}}`;
          candidateGroup.appendChild(label);
        }}
      }}
      svg.appendChild(candidateGroup);

      if (showMonitors) {{
        const monitorOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const node of DATA.nodes.filter(n => n.isMonitor)) {{
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          rect.setAttribute('x', node.x - 6);
          rect.setAttribute('y', node.y - 6);
          rect.setAttribute('width', 12);
          rect.setAttribute('height', 12);
          rect.setAttribute('rx', 2);
          rect.setAttribute('fill', 'rgba(29,78,216,.86)');
          rect.setAttribute('stroke', 'white');
          rect.setAttribute('stroke-width', '1.8');
          rect.addEventListener('mousemove', event => showTip(event, `<b>${{node.id}}</b><br>监测点${{node.isCandidate ? ' / 候选井' : ''}}`));
          rect.addEventListener('mouseleave', hideTip);
          monitorOverlay.appendChild(rect);
        }}
        svg.appendChild(monitorOverlay);
      }}

      const outfallGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      for (const node of DATA.nodes.filter(n => n.isOutfall)) {{
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', node.x - 7);
        rect.setAttribute('y', node.y - 7);
        rect.setAttribute('width', 14);
        rect.setAttribute('height', 14);
        rect.setAttribute('rx', 3);
        rect.setAttribute('fill', '#111827');
        rect.addEventListener('mousemove', event => showTip(event, `<b>${{node.id}}</b><br>排口`));
        rect.addEventListener('mouseleave', hideTip);
        outfallGroup.appendChild(rect);
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', node.x + 10);
        label.setAttribute('y', node.y - 8);
        label.setAttribute('font-size', '12');
        label.setAttribute('font-weight', '800');
        label.textContent = `${{node.id}} 排口`;
        outfallGroup.appendChild(label);
      }}
      svg.appendChild(outfallGroup);
    }}

    function renderPanels() {{
      const wrap = document.getElementById('panels');
      wrap.innerHTML = DATA.panels.map((panel, idx) => `
        <details ${{idx === 0 ? 'open' : ''}}>
          <summary>${{panel.title}}</summary>
          <p class="hint">${{panel.description}}</p>
          <div class="matrix">
            <table>
              <thead>
                <tr><th>阶段 / 样本</th>${{candidates.map(node => `<th>${{node}}</th>`).join('')}}</tr>
              </thead>
              <tbody>
                ${{panel.rows.map(row => `
                  <tr>
                    <td>${{row.label}}</td>
                    ${{candidates.map(node => {{
                      const value = row.values[node] || 0;
                      return `<td><div class="cell" style="background:${{colorScale(value, 0.34)}};color:${{textColor(value, 0.34)}}">${{fmt(value)}}</div></td>`;
                    }}).join('')}}
                  </tr>
                `).join('')}}
              </tbody>
            </table>
          </div>
        </details>
      `).join('');
    }}

    renderCards();
    initLayers();
    renderNetwork();
    renderPanels();

    layerSelect.addEventListener('change', renderNetwork);
    for (const id of ['togglePipes', 'toggleNodes', 'toggleLabels', 'toggleMonitors', 'toggleTruth']) {{
      document.getElementById(id).addEventListener('change', renderNetwork);
    }}
  </script>
</body>
</html>
"""


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    data = build_dashboard_data()
    with OUT_HTML.open("w", encoding="utf-8", newline="\n") as f:
        f.write(build_html(data))
    print(OUT_HTML)


if __name__ == "__main__":
    main()
