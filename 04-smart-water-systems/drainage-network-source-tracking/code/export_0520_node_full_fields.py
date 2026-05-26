"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: export_0520_node_full_fields.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
import math
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "analysis_0520"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INP_PATH = max(DATA_DIR.glob("*.inp"), key=lambda p: p.stat().st_mtime)
RPT_PATH = max(DATA_DIR.glob("*.rpt"), key=lambda p: p.stat().st_mtime)


def as_float(value: object, default: float = math.nan) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def split_sections(path: Path) -> dict[str, list[dict[str, object]]]:
    sections: dict[str, list[dict[str, object]]] = defaultdict(list)
    section = ""
    for line_no, raw in enumerate(path.read_text(encoding="gbk", errors="ignore").splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            continue
        if not section or not stripped or stripped.startswith(";"):
            continue
        sections[section].append({"line_no": line_no, "raw": raw, "parts": stripped.split()})
    return sections


def rpt_section(text: str, title: str, next_titles: tuple[str, ...]) -> str:
    start = text.find(title)
    if start < 0:
        return ""
    end = len(text)
    for next_title in next_titles:
        idx = text.find(next_title, start + len(title))
        if idx > start:
            end = min(end, idx)
    return text[start:end]


def parse_rpt_tables(path: Path) -> dict[str, pd.DataFrame]:
    text = path.read_text(encoding="gbk", errors="ignore")

    depth_rows = []
    for line in rpt_section(text, "Node Depth Summary", ("Node Inflow Summary", "Node Surcharge Summary")).splitlines():
        p = line.split()
        if len(p) >= 8 and p[1] in {"JUNCTION", "STORAGE", "OUTFALL"}:
            depth_rows.append(
                {
                    "node": p[0],
                    "rpt_node_type": p[1],
                    "rpt_avg_depth_m": as_float(p[2]),
                    "rpt_max_depth_m": as_float(p[3]),
                    "rpt_max_hgl_m": as_float(p[4]),
                    "rpt_depth_time_of_max": f"{p[5]} {p[6]}",
                    "rpt_reported_max_depth_m": as_float(p[7]),
                }
            )

    inflow_rows = []
    for line in rpt_section(text, "Node Inflow Summary", ("Node Surcharge Summary", "Node Flooding Summary")).splitlines():
        p = line.split()
        if len(p) >= 9 and p[1] in {"JUNCTION", "STORAGE", "OUTFALL"}:
            inflow_rows.append(
                {
                    "node": p[0],
                    "rpt_max_lateral_inflow_cms": as_float(p[2]),
                    "rpt_max_total_inflow_cms": as_float(p[3]),
                    "rpt_inflow_time_of_max": f"{p[4]} {p[5]}",
                    "rpt_lateral_inflow_volume_10e6_ltr": as_float(p[6]),
                    "rpt_total_inflow_volume_10e6_ltr": as_float(p[7]),
                    "rpt_flow_balance_error_percent": as_float(p[8]),
                }
            )

    flooding_rows = []
    for line in rpt_section(text, "Node Flooding Summary", ("Storage Volume Summary",)).splitlines():
        p = line.split()
        if len(p) >= 7 and re.match(r"^\d", p[1]):
            flooding_rows.append(
                {
                    "node": p[0],
                    "rpt_hours_flooded": as_float(p[1]),
                    "rpt_flood_max_rate_cms": as_float(p[2]),
                    "rpt_flood_time_of_max": f"{p[3]} {p[4]}",
                    "rpt_total_flood_volume_10e6_ltr": as_float(p[5]),
                    "rpt_total_flood_volume_m3": as_float(p[5]) * 1000,
                    "rpt_max_ponded_depth_m": as_float(p[6]),
                    "rpt_max_ponded_depth_cm": as_float(p[6]) * 100,
                }
            )

    storage_rows = []
    for line in rpt_section(text, "Storage Volume Summary", ("Outfall Loading Summary",)).splitlines():
        p = line.split()
        if len(p) >= 10 and re.match(r"^\d|^J", p[0]):
            storage_rows.append(
                {
                    "node": p[0],
                    "rpt_storage_avg_volume_1000m3": as_float(p[1]),
                    "rpt_storage_avg_pct_full": as_float(p[2]),
                    "rpt_storage_evap_pct_loss": as_float(p[3]),
                    "rpt_storage_exfil_pct_loss": as_float(p[4]),
                    "rpt_storage_max_volume_1000m3": as_float(p[5]),
                    "rpt_storage_max_pct_full": as_float(p[6]),
                    "rpt_storage_time_of_max": f"{p[7]} {p[8]}",
                    "rpt_storage_max_outflow_cms": as_float(p[9]),
                }
            )

    outfall_rows = []
    for line in rpt_section(text, "Outfall Loading Summary", ("Link Flow Summary",)).splitlines():
        p = line.split()
        if len(p) >= 7 and p[0] not in {"Outfall", "System"} and re.match(r"^\d|^J", p[0]):
            outfall_rows.append(
                {
                    "node": p[0],
                    "rpt_outfall_flow_freq_pct": as_float(p[1]),
                    "rpt_outfall_avg_flow_cms": as_float(p[2]),
                    "rpt_outfall_max_flow_cms": as_float(p[3]),
                    "rpt_outfall_total_volume_10e6_ltr": as_float(p[4]),
                    "rpt_outfall_total_volume_m3": as_float(p[4]) * 1000,
                    "rpt_outfall_total_COD_kg": as_float(p[5]),
                    "rpt_outfall_total_NH3_kg": as_float(p[6]),
                }
            )

    return {
        "depth": pd.DataFrame(depth_rows),
        "inflow": pd.DataFrame(inflow_rows),
        "flooding": pd.DataFrame(flooding_rows),
        "storage": pd.DataFrame(storage_rows),
        "outfall": pd.DataFrame(outfall_rows),
    }


def join_values(values: list[object]) -> str:
    return ";".join(str(v) for v in values if str(v) != "")


def build_node_table(sections: dict[str, list[dict[str, object]]], rpt: dict[str, pd.DataFrame]) -> pd.DataFrame:
    coords = {r["parts"][0]: r["parts"] for r in sections.get("COORDINATES", []) if len(r["parts"]) >= 3}
    rows: list[dict[str, object]] = []

    for r in sections.get("JUNCTIONS", []):
        p = r["parts"]
        c = coords.get(p[0], [])
        rows.append(
            {
                "node_id": p[0],
                "inp_node_type": "junction",
                "inp_section": "JUNCTIONS",
                "inp_line_no": r["line_no"],
                "inp_raw_line": r["raw"],
                "junction_invert_elev_m": as_float(p[1] if len(p) > 1 else None),
                "junction_max_depth_m": as_float(p[2] if len(p) > 2 else None),
                "junction_init_depth_m": as_float(p[3] if len(p) > 3 else None),
                "junction_surcharge_depth_m": as_float(p[4] if len(p) > 4 else None),
                "junction_ponded_area_m2": as_float(p[5] if len(p) > 5 else None),
                "coord_x": as_float(c[1] if len(c) > 1 else None),
                "coord_y": as_float(c[2] if len(c) > 2 else None),
            }
        )

    for r in sections.get("STORAGE", []):
        p = r["parts"]
        c = coords.get(p[0], [])
        rows.append(
            {
                "node_id": p[0],
                "inp_node_type": "storage",
                "inp_section": "STORAGE",
                "inp_line_no": r["line_no"],
                "inp_raw_line": r["raw"],
                "storage_invert_elev_m": as_float(p[1] if len(p) > 1 else None),
                "storage_max_depth_m": as_float(p[2] if len(p) > 2 else None),
                "storage_init_depth_m": as_float(p[3] if len(p) > 3 else None),
                "storage_shape": p[4] if len(p) > 4 else "",
                "storage_curve_or_coefficient": p[5] if len(p) > 5 else "",
                "storage_fe_ratio_or_a1": as_float(p[6] if len(p) > 6 else None),
                "storage_seepage_or_a2": as_float(p[7] if len(p) > 7 else None),
                "coord_x": as_float(c[1] if len(c) > 1 else None),
                "coord_y": as_float(c[2] if len(c) > 2 else None),
            }
        )

    for r in sections.get("OUTFALLS", []):
        p = r["parts"]
        c = coords.get(p[0], [])
        rows.append(
            {
                "node_id": p[0],
                "inp_node_type": "outfall",
                "inp_section": "OUTFALLS",
                "inp_line_no": r["line_no"],
                "inp_raw_line": r["raw"],
                "outfall_invert_elev_m": as_float(p[1] if len(p) > 1 else None),
                "outfall_type": p[2] if len(p) > 2 else "",
                "outfall_stage_data": p[3] if len(p) > 3 else "",
                "outfall_gated": p[4] if len(p) > 4 else "",
                "outfall_route_to": p[5] if len(p) > 5 else "",
                "coord_x": as_float(c[1] if len(c) > 1 else None),
                "coord_y": as_float(c[2] if len(c) > 2 else None),
            }
        )

    df = pd.DataFrame(rows)

    # Tags.
    tag_by_node: dict[str, list[str]] = defaultdict(list)
    tag_by_object: dict[str, list[str]] = defaultdict(list)
    for r in sections.get("TAGS", []):
        p = r["parts"]
        if len(p) >= 3:
            tag_by_object[f"{p[0]}:{p[1]}"].append(" ".join(p[2:]))
            if p[0].lower() == "node":
                tag_by_node[p[1]].append(" ".join(p[2:]))
    df["inp_node_tags"] = df["node_id"].map(lambda x: join_values(tag_by_node.get(str(x), [])))

    # Links.
    link_rows = []
    for section, link_type in (("CONDUITS", "conduit"), ("PUMPS", "pump")):
        for r in sections.get(section, []):
            p = r["parts"]
            if len(p) >= 3:
                link_rows.append(
                    {
                        "link_id": p[0],
                        "link_type": link_type,
                        "from_node": p[1],
                        "to_node": p[2],
                        "link_raw_line": r["raw"],
                    }
                )
    links = pd.DataFrame(link_rows)
    if not links.empty:
        for direction, node_col in (("incoming", "to_node"), ("outgoing", "from_node")):
            grouped = links.groupby(node_col)
            df[f"{direction}_link_count"] = df["node_id"].map(grouped.size().to_dict()).fillna(0).astype(int)
            df[f"{direction}_links"] = df["node_id"].map(grouped["link_id"].apply(list).map(join_values).to_dict()).fillna("")
            df[f"{direction}_conduit_links"] = df["node_id"].map(
                links[links["link_type"] == "conduit"].groupby(node_col)["link_id"].apply(list).map(join_values).to_dict()
            ).fillna("")
            df[f"{direction}_pump_links"] = df["node_id"].map(
                links[links["link_type"] == "pump"].groupby(node_col)["link_id"].apply(list).map(join_values).to_dict()
            ).fillna("")

        reverse_graph: dict[str, list[str]] = defaultdict(list)
        for _, row in links.iterrows():
            reverse_graph[str(row["to_node"])].append(str(row["from_node"]))
        outfall_nodes = set(df[df["inp_node_type"] == "outfall"]["node_id"].astype(str))
        reachable = set(outfall_nodes)
        queue = deque(outfall_nodes)
        while queue:
            node = queue.popleft()
            for upstream in reverse_graph.get(node, []):
                if upstream not in reachable:
                    reachable.add(upstream)
                    queue.append(upstream)
        df["can_reach_outfall"] = df["node_id"].astype(str).isin(reachable)

    # Direct subcatchments and pollutant/loaduse data by outlet node.
    sub_rows = []
    for r in sections.get("SUBCATCHMENTS", []):
        p = r["parts"]
        if len(p) >= 7:
            sub_rows.append(
                {
                    "subcatchment": p[0],
                    "raingage": p[1],
                    "outlet": p[2],
                    "area_ha": as_float(p[3]),
                    "imperv_pct": as_float(p[4]),
                    "width_m": as_float(p[5]),
                    "slope_pct": as_float(p[6]),
                }
            )
    subs = pd.DataFrame(sub_rows)
    if not subs.empty:
        df["direct_subcatchment_count"] = df["node_id"].map(subs.groupby("outlet").size().to_dict()).fillna(0).astype(int)
        df["direct_subcatchments"] = df["node_id"].map(subs.groupby("outlet")["subcatchment"].apply(list).map(join_values).to_dict()).fillna("")
        df["direct_subcatchment_area_ha"] = df["node_id"].map(subs.groupby("outlet")["area_ha"].sum().to_dict()).fillna(0.0)
        df["direct_subcatchment_avg_imperv_pct"] = df["node_id"].map(subs.groupby("outlet")["imperv_pct"].mean().to_dict()).fillna(math.nan)
        df["direct_subcatchment_avg_width_m"] = df["node_id"].map(subs.groupby("outlet")["width_m"].mean().to_dict()).fillna(math.nan)
        df["direct_subcatchment_avg_slope_pct"] = df["node_id"].map(subs.groupby("outlet")["slope_pct"].mean().to_dict()).fillna(math.nan)
        df["direct_subcatchment_raingages"] = df["node_id"].map(subs.groupby("outlet")["raingage"].apply(lambda s: sorted(set(s))).map(join_values).to_dict()).fillna("")

        loading_rows = []
        for r in sections.get("LOADINGS", []):
            p = r["parts"]
            if len(p) >= 3:
                loading_rows.append({"subcatchment": p[0], "pollutant": p[1], "loading": as_float(p[2])})
        load = pd.DataFrame(loading_rows)
        if not load.empty:
            load = load.merge(subs[["subcatchment", "outlet"]], on="subcatchment", how="left")
            pivot = load.pivot_table(index="outlet", columns="pollutant", values="loading", aggfunc="sum")
            for pollutant in pivot.columns:
                df[f"direct_subcatchment_loading_{pollutant}"] = df["node_id"].map(pivot[pollutant].to_dict()).fillna(0.0)

        cover_rows = []
        for r in sections.get("COVERAGES", []):
            p = r["parts"]
            if len(p) >= 3:
                cover_rows.append({"subcatchment": p[0], "landuse": p[1], "coverage_value": as_float(p[2])})
        cover = pd.DataFrame(cover_rows)
        if not cover.empty:
            cover = cover.merge(subs[["subcatchment", "outlet"]], on="subcatchment", how="left")
            cover_text = (
                cover.groupby("outlet")
                .apply(lambda g: join_values([f"{r.landuse}:{r.coverage_value:g}" for r in g.itertuples()]))
                .to_dict()
            )
            df["direct_subcatchment_coverages"] = df["node_id"].map(cover_text).fillna("")

    # External inflows.
    inflow_rows = []
    for r in sections.get("INFLOWS", []):
        p = r["parts"]
        if len(p) >= 8:
            inflow_rows.append(
                {
                    "node_id": p[0],
                    "external_inflow_constituent": p[1],
                    "external_inflow_timeseries": p[2],
                    "external_inflow_type": p[3],
                    "external_inflow_m_factor": p[4],
                    "external_inflow_s_factor": p[5],
                    "external_inflow_baseline": p[6],
                    "external_inflow_pattern": p[7],
                }
            )
    inflow = pd.DataFrame(inflow_rows)
    if not inflow.empty:
        inflow_text = inflow.groupby("node_id").apply(
            lambda g: join_values(
                [
                    f"{r.external_inflow_constituent}|{r.external_inflow_type}|baseline={r.external_inflow_baseline}|pattern={r.external_inflow_pattern}|ts={r.external_inflow_timeseries}"
                    for r in g.itertuples()
                ]
            )
        )
        df["external_inflow_records"] = df["node_id"].map(inflow_text.to_dict()).fillna("")

    for table in rpt.values():
        if not table.empty:
            df = df.merge(table, on="node", how="left") if "node" in df.columns else df

    df = df.rename(columns={"node_id": "node"})
    for table in rpt.values():
        if not table.empty:
            df = df.merge(table, on="node", how="left")

    df["has_ponding_area"] = df.get("junction_ponded_area_m2", 0).fillna(0).astype(float) > 0
    df["is_actual_ponding_depth_gt0"] = df.get("rpt_max_ponded_depth_m", 0).fillna(0).astype(float) > 0
    return df


def build_dictionary(columns: list[str]) -> pd.DataFrame:
    meaning = {
        "node": "节点编号",
        "inp_node_type": "INP节点类型，junction为检查井，storage为调蓄/泵站相关节点，outfall为排口",
        "inp_section": "该节点来自INP的哪个段落",
        "inp_line_no": "该节点在INP文件中的原始行号",
        "inp_raw_line": "INP中该节点对应的原始文本行",
        "junction_invert_elev_m": "检查井井底高程，单位m",
        "junction_max_depth_m": "检查井最大井深，单位m",
        "junction_init_depth_m": "检查井初始水深，单位m",
        "junction_surcharge_depth_m": "检查井超载深度，单位m",
        "junction_ponded_area_m2": "检查井地表积水面积，单位m2；大于0表示允许ponding",
        "storage_invert_elev_m": "调蓄节点底部高程，单位m",
        "storage_max_depth_m": "调蓄节点最大深度，单位m",
        "storage_init_depth_m": "调蓄节点初始水深，单位m",
        "storage_shape": "调蓄节点形状或曲线类型",
        "storage_curve_or_coefficient": "调蓄曲线名或形状参数",
        "storage_fe_ratio_or_a1": "调蓄节点后续参数，按SWMM格式保留",
        "storage_seepage_or_a2": "调蓄节点后续参数，按SWMM格式保留",
        "outfall_invert_elev_m": "排口底部高程，单位m",
        "outfall_type": "排口边界类型，如FREE自由出流",
        "outfall_stage_data": "排口水位或潮位数据字段",
        "outfall_gated": "排口是否设置闸门",
        "outfall_route_to": "排口转输目标",
        "coord_x": "节点X坐标",
        "coord_y": "节点Y坐标",
        "inp_node_tags": "INP TAGS中节点标签",
        "incoming_link_count": "进入该节点的管段/泵数量",
        "incoming_links": "进入该节点的全部连接编号",
        "incoming_conduit_links": "进入该节点的管道编号",
        "incoming_pump_links": "进入该节点的泵编号",
        "outgoing_link_count": "从该节点流出的管段/泵数量",
        "outgoing_links": "从该节点流出的全部连接编号",
        "outgoing_conduit_links": "从该节点流出的管道编号",
        "outgoing_pump_links": "从该节点流出的泵编号",
        "can_reach_outfall": "沿管网拓扑是否可到达排口",
        "direct_subcatchment_count": "直接汇入该节点的子汇水区数量",
        "direct_subcatchments": "直接汇入该节点的子汇水区编号",
        "direct_subcatchment_area_ha": "直接汇入该节点的子汇水区总面积，单位ha",
        "direct_subcatchment_avg_imperv_pct": "直接汇入该节点子汇水区平均不透水率，单位%",
        "direct_subcatchment_avg_width_m": "直接汇入该节点子汇水区平均宽度，单位m",
        "direct_subcatchment_avg_slope_pct": "直接汇入该节点子汇水区平均坡度，单位%",
        "direct_subcatchment_raingages": "直接汇入该节点子汇水区使用的雨量计",
        "direct_subcatchment_coverages": "直接汇入该节点子汇水区的土地利用覆盖信息",
        "external_inflow_records": "节点外部入流/污染物输入记录；当前主要是污染物COD记录，不是水量FLOW",
        "rpt_node_type": "RPT节点类型",
        "rpt_avg_depth_m": "RPT模拟期平均水深，单位m",
        "rpt_max_depth_m": "RPT模拟期最大水深，单位m",
        "rpt_max_hgl_m": "RPT模拟期最大水力坡线高程，单位m",
        "rpt_depth_time_of_max": "RPT最大水深出现时间",
        "rpt_reported_max_depth_m": "RPT报告步长下最大水深，单位m",
        "rpt_max_lateral_inflow_cms": "RPT最大侧向入流，单位m3/s",
        "rpt_max_total_inflow_cms": "RPT最大总入流，单位m3/s",
        "rpt_inflow_time_of_max": "RPT最大入流出现时间",
        "rpt_lateral_inflow_volume_10e6_ltr": "RPT侧向入流体积，单位10^6 L",
        "rpt_total_inflow_volume_10e6_ltr": "RPT总入流体积，单位10^6 L",
        "rpt_flow_balance_error_percent": "RPT节点流量平衡误差，单位%",
        "rpt_hours_flooded": "RPT溢流/积水持续小时数",
        "rpt_flood_max_rate_cms": "RPT最大溢流速率，单位m3/s",
        "rpt_flood_time_of_max": "RPT最大溢流速率出现时间",
        "rpt_total_flood_volume_10e6_ltr": "RPT总溢流/积水体积，单位10^6 L",
        "rpt_total_flood_volume_m3": "RPT总溢流/积水体积，单位m3",
        "rpt_max_ponded_depth_m": "RPT井盖以上最大积水深度，单位m",
        "rpt_max_ponded_depth_cm": "RPT井盖以上最大积水深度，单位cm",
        "rpt_storage_avg_volume_1000m3": "RPT调蓄节点平均体积，单位1000m3",
        "rpt_storage_avg_pct_full": "RPT调蓄节点平均充满比例，单位%",
        "rpt_storage_evap_pct_loss": "RPT调蓄节点蒸发损失比例，单位%",
        "rpt_storage_exfil_pct_loss": "RPT调蓄节点下渗损失比例，单位%",
        "rpt_storage_max_volume_1000m3": "RPT调蓄节点最大体积，单位1000m3",
        "rpt_storage_max_pct_full": "RPT调蓄节点最大充满比例，单位%",
        "rpt_storage_time_of_max": "RPT调蓄节点最大体积出现时间",
        "rpt_storage_max_outflow_cms": "RPT调蓄节点最大出流，单位m3/s",
        "rpt_outfall_flow_freq_pct": "RPT排口有流频率，单位%",
        "rpt_outfall_avg_flow_cms": "RPT排口平均流量，单位m3/s",
        "rpt_outfall_max_flow_cms": "RPT排口最大流量，单位m3/s",
        "rpt_outfall_total_volume_10e6_ltr": "RPT排口总出流体积，单位10^6 L",
        "rpt_outfall_total_volume_m3": "RPT排口总出流体积，单位m3",
        "rpt_outfall_total_COD_kg": "RPT排口COD总量，单位kg",
        "rpt_outfall_total_NH3_kg": "RPT排口氨氮总量，单位kg",
        "has_ponding_area": "模型中是否设置了Ponding Area",
        "is_actual_ponding_depth_gt0": "本次模拟是否出现井上最大积水深度大于0",
    }
    rows = []
    for col in columns:
        col_meaning = meaning.get(col)
        if col_meaning is None and col.startswith("direct_subcatchment_loading_"):
            pollutant = col[len("direct_subcatchment_loading_") :]
            col_meaning = f"直接汇入该节点子汇水区的{pollutant}加载量汇总"
        if col_meaning is None:
            col_meaning = "未单独解释的保留字段"
        source = "INP/RPT/派生"
        if col.startswith("junction_") or col.startswith("storage_") or col.startswith("outfall_") or col.startswith("inp_") or col.startswith("coord_"):
            source = "INP"
        elif col.startswith("rpt_"):
            source = "RPT"
        elif col.startswith("direct_subcatchment"):
            source = "INP SUBCATCHMENTS/LOADINGS/COVERAGES聚合"
        elif "link" in col or col == "can_reach_outfall":
            source = "INP CONDUITS/PUMPS拓扑派生"
        rows.append({"field": col, "中文含义": col_meaning, "来源": source})
    return pd.DataFrame(rows)


def main() -> None:
    sections = split_sections(INP_PATH)
    rpt = parse_rpt_tables(RPT_PATH)
    all_nodes = build_node_table(sections, rpt)
    ponding_nodes = all_nodes[all_nodes["is_actual_ponding_depth_gt0"]].sort_values("rpt_max_ponded_depth_cm", ascending=False)
    dictionary = build_dictionary(list(all_nodes.columns))

    all_path = OUT_DIR / "0520_all_nodes_full_fields.csv"
    ponding_path = OUT_DIR / "0520_ponding_nodes_full_fields.csv"
    dict_path = OUT_DIR / "0520_node_field_dictionary.csv"
    xlsx_path = OUT_DIR / "0520_node_full_fields_with_dictionary.xlsx"

    all_nodes.to_csv(all_path, index=False, encoding="utf-8-sig")
    ponding_nodes.to_csv(ponding_path, index=False, encoding="utf-8-sig")
    dictionary.to_csv(dict_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path) as writer:
        ponding_nodes.to_excel(writer, sheet_name="井上高度大于0节点", index=False)
        all_nodes.to_excel(writer, sheet_name="全部节点完整字段", index=False)
        dictionary.to_excel(writer, sheet_name="字段中文对照表", index=False)

    print(f"all_nodes={all_path}")
    print(f"ponding_nodes={ponding_path}")
    print(f"dictionary={dict_path}")
    print(f"xlsx={xlsx_path}")
    print(f"all_node_count={len(all_nodes)}")
    print(f"ponding_node_count={len(ponding_nodes)}")
    print(f"field_count={len(all_nodes.columns)}")


if __name__ == "__main__":
    main()
