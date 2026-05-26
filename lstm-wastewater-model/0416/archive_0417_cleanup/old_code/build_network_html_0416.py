from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"E:\PY\LSTM\0416")
RAW_MODEL_DIR = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("0-"))
MODEL_INP = next(RAW_MODEL_DIR.glob("*.inp"))
MODEL_RPT = next(RAW_MODEL_DIR.glob("*.rpt"))
OUT_DIR = ROOT / "analysis" / "baseline_current" / "html"
HTML_OUT = OUT_DIR / "0416_基线_节点排口分类展示.html"
DATA_OUT = OUT_DIR / "0416_基线_节点排口分类数据.json"


def section_rows(path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    section = ""
    for raw in path.read_text(encoding="gbk", errors="ignore").splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].upper()
            continue
        if section == section_name.upper() and s and not s.startswith(";"):
            rows.append(s.split())
    return rows


def parse_flooding(path: Path) -> dict[str, dict[str, float | str]]:
    lines = path.read_text(encoding="gbk", errors="ignore").splitlines()
    start = next((i for i, line in enumerate(lines) if "Node Flooding Summary" in line), None)
    flooded: dict[str, dict[str, float | str]] = {}
    if start is None:
        return flooded
    for line in lines[start + 8 : start + 140]:
        parts = line.split()
        if not parts or "Outfall" in line:
            break
        if len(parts) >= 7 and parts[0].startswith("J"):
            flooded[parts[0]] = {
                "积水时长_h": float(parts[1]),
                "最大溢流_CMS": float(parts[2]),
                "最大时刻": f"{parts[3]} {parts[4]}",
                "溢流体积_m3": float(parts[5]) * 1000.0,
                "最大积水深_m": float(parts[6]),
            }
    return flooded


def build_data() -> dict[str, object]:
    coords = {r[0]: (float(r[1]), float(r[2])) for r in section_rows(MODEL_INP, "COORDINATES") if len(r) >= 3}
    inflow_nodes = {r[0] for r in section_rows(MODEL_INP, "INFLOWS") if len(r) >= 1}
    flooded = parse_flooding(MODEL_RPT)

    nodes: list[dict[str, object]] = []
    for r in section_rows(MODEL_INP, "JUNCTIONS"):
        if len(r) < 6 or r[0] not in coords:
            continue
        elev = float(r[1])
        max_depth = float(r[2])
        ponding_area = float(r[5])
        node_id = r[0]
        category = "积水检查井" if node_id in flooded else "普通检查井"
        if node_id in inflow_nodes:
            category = "外部入流节点"
        nodes.append(
            {
                "id": node_id,
                "type": "junction",
                "category": category,
                "x": coords[node_id][0],
                "y": coords[node_id][1],
                "井底高程_m": elev,
                "最大井深_m": max_depth,
                "井盖高程_m": elev + max_depth,
                "PondingArea_m2": ponding_area,
                "允许积水": ponding_area > 0,
                "发生积水": node_id in flooded,
                "外部入流": node_id in inflow_nodes,
                "flood": flooded.get(node_id, {}),
            }
        )
    for r in section_rows(MODEL_INP, "OUTFALLS"):
        if len(r) < 3 or r[0] not in coords:
            continue
        nodes.append(
            {
                "id": r[0],
                "type": "outfall",
                "category": "排口",
                "x": coords[r[0]][0],
                "y": coords[r[0]][1],
                "排口高程_m": float(r[1]),
                "排口类型": r[2],
            }
        )

    links: list[dict[str, object]] = []
    for r in section_rows(MODEL_INP, "CONDUITS"):
        if len(r) >= 4 and r[1] in coords and r[2] in coords:
            links.append(
                {
                    "id": r[0],
                    "from": r[1],
                    "to": r[2],
                    "length_m": float(r[3]),
                    "x1": coords[r[1]][0],
                    "y1": coords[r[1]][1],
                    "x2": coords[r[2]][0],
                    "y2": coords[r[2]][1],
                }
            )

    xs = [n["x"] for n in nodes]
    ys = [n["y"] for n in nodes]
    margin = 80
    viewbox = {
        "x": min(xs) - margin,
        "y": min(ys) - margin,
        "w": max(xs) - min(xs) + 2 * margin,
        "h": max(ys) - min(ys) + 2 * margin,
    }
    categories = {
        "普通检查井": sorted([n["id"] for n in nodes if n["category"] == "普通检查井"]),
        "积水检查井": sorted([n["id"] for n in nodes if n["category"] == "积水检查井"]),
        "外部入流节点": sorted([n["id"] for n in nodes if n["category"] == "外部入流节点"]),
        "排口": sorted([n["id"] for n in nodes if n["category"] == "排口"]),
        "管道": sorted([l["id"] for l in links]),
    }
    stats = {
        "检查井": sum(1 for n in nodes if n["type"] == "junction"),
        "排口": sum(1 for n in nodes if n["type"] == "outfall"),
        "管道": len(links),
        "允许积水节点": sum(1 for n in nodes if n.get("允许积水")),
        "发生积水节点": len(flooded),
        "外部入流节点": len(inflow_nodes),
        "管道总长_m": round(sum(float(l["length_m"]) for l in links), 3),
    }
    return {"model": str(MODEL_INP), "nodes": nodes, "links": links, "viewbox": viewbox, "categories": categories, "stats": stats}


def write_html(data: dict[str, object]) -> None:
    payload = json.dumps(data, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>0416 基线节点排口分类展示</title>
<style>
:root {{ --bg:#f6f3ec; --ink:#1f2a2e; --muted:#687177; --line:#9aa3a8; --card:#ffffff; --red:#d84a3a; --blue:#2367a2; --green:#2d8a54; --orange:#d9822b; }}
body {{ margin:0; font-family:"Microsoft YaHei","SimHei",Arial,sans-serif; background:var(--bg); color:var(--ink); }}
header {{ padding:18px 24px; background:#1f2a2e; color:white; }}
header h1 {{ margin:0 0 8px; font-size:22px; }}
header p {{ margin:0; color:#d6dedf; font-size:13px; }}
.layout {{ display:grid; grid-template-columns:360px 1fr; gap:16px; padding:16px; }}
.panel {{ background:var(--card); border-radius:14px; box-shadow:0 8px 24px rgba(31,42,46,.09); padding:14px; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.card {{ border:1px solid #e4e0d7; border-radius:12px; padding:10px; background:#fffdf8; }}
.num {{ display:block; font-size:24px; font-weight:800; color:#1f2a2e; }}
.label {{ color:var(--muted); font-size:12px; }}
.controls label {{ display:inline-flex; align-items:center; gap:6px; margin:6px 8px 6px 0; font-size:13px; }}
input[type="text"] {{ width:100%; box-sizing:border-box; padding:10px 12px; border:1px solid #ddd4c6; border-radius:10px; font-size:14px; }}
#mapWrap {{ height:74vh; overflow:hidden; position:relative; }}
svg {{ width:100%; height:100%; background:linear-gradient(145deg,#fffef9,#eef4f1); border-radius:14px; }}
.link {{ stroke:var(--line); stroke-width:3; opacity:.72; fill:none; }}
.node {{ stroke:#fff; stroke-width:5; cursor:pointer; }}
.normal {{ fill:#5e8c61; }}
.flooded {{ fill:var(--red); }}
.inflow {{ fill:var(--orange); }}
.outfall {{ fill:var(--blue); }}
.hidden {{ display:none; }}
.selected {{ stroke:#111; stroke-width:10; filter:drop-shadow(0 0 8px rgba(0,0,0,.35)); }}
.legend span {{ display:inline-block; margin:4px 10px 4px 0; font-size:13px; }}
.dot {{ width:12px; height:12px; border-radius:50%; vertical-align:-1px; margin-right:4px; }}
.blue {{ background:var(--blue); }} .red {{ background:var(--red); }} .green {{ background:#5e8c61; }} .orange {{ background:var(--orange); }} .gray {{ background:var(--line); }}
.cat h3 {{ margin:14px 0 8px; font-size:15px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px; max-height:150px; overflow:auto; }}
.chip {{ border:1px solid #ddd4c6; background:#fffdf8; border-radius:999px; padding:4px 8px; font-size:12px; cursor:pointer; }}
.chip:hover {{ background:#efe6d4; }}
#tip {{ position:absolute; pointer-events:none; display:none; background:#1f2a2e; color:white; padding:10px 12px; border-radius:10px; max-width:280px; font-size:12px; box-shadow:0 8px 22px rgba(0,0,0,.22); z-index:3; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
td {{ border-bottom:1px solid #eee6da; padding:6px 4px; vertical-align:top; }}
@media (max-width:900px) {{ .layout {{ grid-template-columns:1fr; }} #mapWrap {{ height:68vh; }} }}
</style>
</head>
<body>
<header>
  <h1>0416 当前基线：节点、排口、管道分类展示</h1>
  <p>数据来源：当前原始允许积水模型。该页面只做结构展示，不包含额外人工注水。</p>
</header>
<div class="layout">
  <aside class="panel">
    <div class="cards" id="cards"></div>
    <h3>分类显示</h3>
    <div class="controls">
      <label><input type="checkbox" data-layer="link" checked> 管道</label>
      <label><input type="checkbox" data-layer="normal" checked> 普通检查井</label>
      <label><input type="checkbox" data-layer="flooded" checked> 积水检查井</label>
      <label><input type="checkbox" data-layer="inflow" checked> 外部入流节点</label>
      <label><input type="checkbox" data-layer="outfall" checked> 排口</label>
    </div>
    <h3>搜索节点或管道</h3>
    <input id="search" type="text" placeholder="例如 J11、J6、C1_1" />
    <div class="legend">
      <span><i class="dot green"></i>普通检查井</span><span><i class="dot red"></i>发生积水</span>
      <span><i class="dot orange"></i>外部入流</span><span><i class="dot blue"></i>排口</span><span><i class="dot gray"></i>管道</span>
    </div>
    <div id="detail" class="panel" style="box-shadow:none;border:1px solid #eee6da;margin-top:10px;">点击图上对象查看详情</div>
  </aside>
  <main>
    <section class="panel" id="mapWrap"><svg id="svg"></svg><div id="tip"></div></section>
    <section class="panel cat" id="categories"></section>
  </main>
</div>
<script>
const DATA = {payload};
const svg = document.getElementById('svg');
const tip = document.getElementById('tip');
const detail = document.getElementById('detail');
const vb = DATA.viewbox;
svg.setAttribute('viewBox', `${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`);
document.getElementById('cards').innerHTML = Object.entries(DATA.stats).map(([k,v]) => `<div class="card"><span class="num">${{v}}</span><span class="label">${{k}}</span></div>`).join('');
function cls(n) {{ return n.type === 'outfall' ? 'outfall' : n.category === '外部入流节点' ? 'inflow' : n.category === '积水检查井' ? 'flooded' : 'normal'; }}
function detailHtml(o, kind) {{
  const rows = Object.entries(o).filter(([k]) => !['x','y','x1','y1','x2','y2','flood'].includes(k)).map(([k,v]) => `<tr><td>${{k}}</td><td>${{typeof v==='object'?JSON.stringify(v):v}}</td></tr>`).join('');
  const flood = o.flood && Object.keys(o.flood).length ? '<h3>积水统计</h3><table>' + Object.entries(o.flood).map(([k,v])=>`<tr><td>${{k}}</td><td>${{v}}</td></tr>`).join('') + '</table>' : '';
  return `<b>${{kind}}：${{o.id}}</b><table>${{rows}}</table>${{flood}}`;
}}
DATA.links.forEach(l => {{
  const line = document.createElementNS('http://www.w3.org/2000/svg','line');
  line.setAttribute('x1', l.x1); line.setAttribute('y1', l.y1); line.setAttribute('x2', l.x2); line.setAttribute('y2', l.y2);
  line.setAttribute('class','link'); line.dataset.layer='link'; line.dataset.id=l.id;
  line.addEventListener('mousemove', e => showTip(e, `${{l.id}}：${{l.from}} → ${{l.to}}，长度 ${{l.length_m}} m`));
  line.addEventListener('mouseleave', hideTip);
  line.addEventListener('click', () => selectObject(line, detailHtml(l,'管道')));
  svg.appendChild(line);
}});
DATA.nodes.forEach(n => {{
  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  const c = document.createElementNS('http://www.w3.org/2000/svg', n.type === 'outfall' ? 'rect' : 'circle');
  const layer = cls(n);
  if (n.type === 'outfall') {{ c.setAttribute('x', n.x-18); c.setAttribute('y', n.y-18); c.setAttribute('width',36); c.setAttribute('height',36); }}
  else {{ c.setAttribute('cx', n.x); c.setAttribute('cy', n.y); c.setAttribute('r', layer==='inflow'?22:18); }}
  c.setAttribute('class', `node ${{layer}}`); c.dataset.layer=layer; c.dataset.id=n.id;
  c.addEventListener('mousemove', e => showTip(e, `${{n.id}}：${{n.category}}`));
  c.addEventListener('mouseleave', hideTip);
  c.addEventListener('click', () => selectObject(c, detailHtml(n,'节点')));
  g.appendChild(c); svg.appendChild(g);
}});
function showTip(e, text) {{ tip.style.display='block'; tip.textContent=text; tip.style.left=(e.offsetX+16)+'px'; tip.style.top=(e.offsetY+16)+'px'; }}
function hideTip() {{ tip.style.display='none'; }}
function selectObject(el, html) {{ document.querySelectorAll('.selected').forEach(x=>x.classList.remove('selected')); el.classList.add('selected'); detail.innerHTML=html; }}
document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.addEventListener('change', () => {{
  document.querySelectorAll(`[data-layer="${{cb.dataset.layer}}"]`).forEach(el => el.classList.toggle('hidden', !cb.checked));
}}));
document.getElementById('search').addEventListener('input', e => {{
  const q = e.target.value.trim().toUpperCase();
  document.querySelectorAll('[data-id]').forEach(el => el.classList.remove('selected'));
  if (!q) return;
  const hit = [...document.querySelectorAll('[data-id]')].find(el => el.dataset.id.toUpperCase() === q);
  if (hit) {{ hit.classList.add('selected'); hit.dispatchEvent(new Event('click')); }}
}});
document.getElementById('categories').innerHTML = Object.entries(DATA.categories).map(([name, items]) => `<h3>${{name}}（${{items.length}}）</h3><div class="chips">${{items.map(id=>`<span class="chip" onclick="document.getElementById('search').value='${{id}}';document.getElementById('search').dispatchEvent(new Event('input'))">${{id}}</span>`).join('')}}</div>`).join('');
</script>
</body>
</html>"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(html, encoding="utf-8")
    DATA_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    data = build_data()
    write_html(data)
    print(json.dumps({"html": str(HTML_OUT), "data": str(DATA_OUT), "stats": data["stats"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
