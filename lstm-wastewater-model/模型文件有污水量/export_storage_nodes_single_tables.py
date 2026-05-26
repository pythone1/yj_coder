from pathlib import Path
import re
import pandas as pd
import os
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute


WORKDIR = Path(r"E:\PY\LSTM\模型文件有污水量")
OUTDIR = WORKDIR / "节点时序导出"
INP = WORKDIR / "盱眙污水管3（入渗点有雨水量）.inp"
ASCII_OUT_DIR = Path(r"C:\swmm_temp")
ASCII_OUT = ASCII_OUT_DIR / "model_with_rain.out"
TARGET_NODES = ["J231", "J232", "J41"]


def read_sections(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    sections = {}
    current = None
    buf = []
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            if current is not None:
                sections[current] = buf
            current = s.strip("[]")
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = buf
    return sections


def clean_lines(lines):
    return [x.strip() for x in lines if x.strip() and not x.strip().startswith(";")]


def get_storage_info(sections, node):
    for line in clean_lines(sections.get("STORAGE", [])):
        parts = re.split(r"\s+", line)
        if parts[0] == node:
            return {
                "节点名称": parts[0],
                "节点类型": "Storage",
                "井底高程": float(parts[1]),
                "最大水深": float(parts[2]),
                "初始水深": float(parts[3]),
                "形状类型": parts[4],
                "库容曲线": parts[5] if len(parts) > 5 else "",
                "地表积水深": float(parts[6]) if len(parts) > 6 else 0.0,
                "蒸发系数": float(parts[7]) if len(parts) > 7 else 0.0,
            }
    return {"节点名称": node, "节点类型": "Storage"}


def get_coord_info(sections, node):
    for line in clean_lines(sections.get("COORDINATES", [])):
        parts = re.split(r"\s+", line)
        if parts[0] == node:
            return {"X坐标": float(parts[1]), "Y坐标": float(parts[2])}
    return {}


def get_tag_info(sections, node):
    for line in clean_lines(sections.get("TAGS", [])):
        parts = re.split(r"\s+", line)
        if len(parts) >= 3 and parts[0] == "Node" and parts[1] == node:
            return {"标签类型": parts[0], "标签值": parts[2]}
    return {}


def get_link_info(sections, node):
    upstream = []
    downstream = []
    for sec in ["CONDUITS", "PUMPS"]:
        for line in clean_lines(sections.get(sec, [])):
            parts = re.split(r"\s+", line)
            if len(parts) >= 3:
                link, from_node, to_node = parts[0], parts[1], parts[2]
                if to_node == node:
                    upstream.append(link)
                if from_node == node:
                    downstream.append(link)
    return {
        "上游连接": ",".join(upstream),
        "下游连接": ",".join(downstream),
        "上游连接数量": len(upstream),
        "下游连接数量": len(downstream),
    }


def get_node_timeseries(node):
    attrs = [
        ("水深(m)", NodeAttribute.INVERT_DEPTH),
        ("水力水头(m)", NodeAttribute.HYDRAULIC_HEAD),
        ("节点贮水量", NodeAttribute.PONDED_VOLUME),
        ("侧向流量", NodeAttribute.LATERAL_INFLOW),
        ("总入流量", NodeAttribute.TOTAL_INFLOW),
        ("溢流损失", NodeAttribute.FLOODING_LOSSES),
    ]
    old_cwd = os.getcwd()
    os.chdir(str(ASCII_OUT_DIR))
    try:
        with Output(ASCII_OUT.name) as out:
            df = None
            for col_name, attr in attrs:
                s = pd.Series(out.node_series(node, attr), name=col_name)
                if df is None:
                    df = s.to_frame()
                else:
                    df = df.join(s, how="outer")
    finally:
        os.chdir(old_cwd)
    return df.reset_index().rename(columns={"index": "时间"})


def export_one(sections, node):
    static_info = {"模型版本": "有雨水量版"}
    static_info.update(get_storage_info(sections, node))
    static_info.update(get_coord_info(sections, node))
    static_info.update(get_tag_info(sections, node))
    static_info.update(get_link_info(sections, node))
    static_info.setdefault("标签类型", "")
    static_info.setdefault("标签值", "")

    df = get_node_timeseries(node)
    df.insert(0, "节点名称", node)
    for key, value in static_info.items():
        df[key] = value

    ordered_cols = [
        "模型版本",
        "节点名称",
        "节点类型",
        "井底高程",
        "最大水深",
        "初始水深",
        "形状类型",
        "库容曲线",
        "地表积水深",
        "蒸发系数",
        "X坐标",
        "Y坐标",
        "标签类型",
        "标签值",
        "上游连接",
        "下游连接",
        "上游连接数量",
        "下游连接数量",
        "时间",
        "水深(m)",
        "水力水头(m)",
        "节点贮水量",
        "侧向流量",
        "总入流量",
        "溢流损失",
    ]
    df = df[ordered_cols]

    xlsx_path = OUTDIR / f"{node}_调蓄点单表.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=f"{node}调蓄点", index=False)
    return xlsx_path


def main():
    sections = read_sections(INP)
    for node in TARGET_NODES:
        print(export_one(sections, node))


if __name__ == "__main__":
    main()
