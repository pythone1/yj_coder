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


def parse_junction_j1(sections):
    for line in clean_lines(sections.get("JUNCTIONS", [])):
        parts = re.split(r"\s+", line)
        if parts[0] == "J1":
            return {
                "节点名称": parts[0],
                "井底高程": float(parts[1]),
                "最大水深": float(parts[2]),
                "初始水深": float(parts[3]),
                "地表积水深": float(parts[4]),
                "积水面积": float(parts[5]),
            }
    return {}


def parse_coord_j1(sections):
    for line in clean_lines(sections.get("COORDINATES", [])):
        parts = re.split(r"\s+", line)
        if parts[0] == "J1":
            return {"X坐标": float(parts[1]), "Y坐标": float(parts[2])}
    return {}


def parse_tags_j1(sections):
    for line in clean_lines(sections.get("TAGS", [])):
        parts = re.split(r"\s+", line)
        if len(parts) >= 3 and parts[0] == "Node" and parts[1] == "J1":
            return {"标签类型": parts[0], "标签值": parts[2]}
    return {}


def parse_links_j1(sections):
    upstream = []
    downstream = []
    for line in clean_lines(sections.get("CONDUITS", [])):
        parts = re.split(r"\s+", line)
        if len(parts) >= 3:
            link, from_node, to_node = parts[0], parts[1], parts[2]
            if to_node == "J1":
                upstream.append(link)
            if from_node == "J1":
                downstream.append(link)
    return {
        "上游管段": ",".join(upstream),
        "下游管段": ",".join(downstream),
        "上游管段数量": len(upstream),
        "下游管段数量": len(downstream),
    }


def main():
    sections = read_sections(INP)
    static_info = {}
    static_info.update(parse_junction_j1(sections))
    static_info.update(parse_coord_j1(sections))
    static_info.update(parse_tags_j1(sections))
    static_info.update(parse_links_j1(sections))
    static_info["模型版本"] = "有雨水量版"

    old_cwd = os.getcwd()
    os.chdir(str(ASCII_OUT_DIR))
    try:
        with Output(ASCII_OUT.name) as out:
            attrs = [
                ("水深(m)", NodeAttribute.INVERT_DEPTH),
                ("水力水头(m)", NodeAttribute.HYDRAULIC_HEAD),
                ("节点贮水量", NodeAttribute.PONDED_VOLUME),
                ("侧向流量", NodeAttribute.LATERAL_INFLOW),
                ("总入流量", NodeAttribute.TOTAL_INFLOW),
                ("溢流损失", NodeAttribute.FLOODING_LOSSES),
            ]
            j1 = None
            for col_name, attr in attrs:
                s = pd.Series(out.node_series("J1", attr), name=col_name)
                if j1 is None:
                    j1 = s.to_frame()
                else:
                    j1 = j1.join(s, how="outer")
    finally:
        os.chdir(old_cwd)

    j1 = j1.reset_index().rename(columns={"index": "时间"})
    j1.insert(0, "节点名称", "J1")

    for key, value in static_info.items():
        j1[key] = value

    ordered_cols = [
        "模型版本",
        "节点名称",
        "井底高程",
        "最大水深",
        "初始水深",
        "地表积水深",
        "积水面积",
        "X坐标",
        "Y坐标",
        "标签类型",
        "标签值",
        "上游管段",
        "下游管段",
        "上游管段数量",
        "下游管段数量",
        "时间",
        "水深(m)",
        "水力水头(m)",
        "节点贮水量",
        "侧向流量",
        "总入流量",
        "溢流损失",
    ]
    j1 = j1[ordered_cols]

    csv_path = OUTDIR / "J1_全部信息单表.csv"
    xlsx_path = OUTDIR / "J1_全部信息单表.xlsx"
    j1.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        j1.to_excel(writer, sheet_name="J1单表", index=False)

    print(csv_path)
    print(xlsx_path)
    print(j1.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
