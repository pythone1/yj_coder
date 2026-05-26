"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: process_yancheng_pond.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

﻿from collections import OrderedDict
from pathlib import Path
import re

import fiona
import pandas as pd
from pypinyin import lazy_pinyin, Style

BASE_DIR = Path(r"E:\全省养殖池溏上图入库普查\填报进度统计\0409")
INPUT_GPKG = BASE_DIR / "盐城市--池塘图斑.gpkg"
LAYER_NAME = "盐城市--池塘图斑"
OUTPUT_STEM = "盐城市_池塘图斑_地址含盐城市"
OUTPUT_DIR = BASE_DIR / f"{OUTPUT_STEM}_shp"
OUTPUT_SHP = OUTPUT_DIR / f"{OUTPUT_STEM}.shp"
MAPPING_XLSX = BASE_DIR / f"{OUTPUT_STEM}_字段对照表.xlsx"
MAPPING_CSV = BASE_DIR / f"{OUTPUT_STEM}_字段对照表.csv"


def contains_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def to_initials(name):
    letters = []
    for item in lazy_pinyin(name, style=Style.FIRST_LETTER, errors="ignore"):
        cleaned = re.sub(r"[^A-Za-z0-9]", "", item)
        if cleaned:
            letters.append(cleaned.lower())
    base = "".join(letters)
    if not base:
        ascii_only = re.sub(r"[^A-Za-z0-9]", "", name).lower()
        base = ascii_only or "fld"
    if base[0].isdigit():
        base = "f" + base
    return base


def make_unique_name(name, used):
    base = to_initials(name)
    candidate = base[:10]
    if candidate not in used:
        used.add(candidate)
        return candidate
    index = 1
    while True:
        suffix = str(index)
        trimmed = base[: max(1, 10 - len(suffix))]
        candidate = trimmed + suffix
        if candidate not in used:
            used.add(candidate)
            return candidate
        index += 1


def normalize_field_type(field_type):
    lower = field_type.lower()
    if lower.startswith("str"):
        match = re.search(r"str:(\d+)", lower)
        width = min(int(match.group(1)) if match else 254, 254)
        return "str:%s" % width
    if lower.startswith("int"):
        return "int"
    if lower.startswith("float"):
        return "float"
    if lower.startswith("date"):
        return "date"
    if lower.startswith("datetime"):
        return "str:254"
    return field_type


def cleanup_existing(stem):
    for suffix in [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix", ".fix"]:
        target = stem.with_suffix(suffix)
        if target.exists():
            target.unlink()


with fiona.open(INPUT_GPKG, layer=LAYER_NAME) as src:
    all_fields = list(src.schema["properties"].keys())
    field_types = src.schema["properties"]

    keep_fields = [field for field in all_fields if contains_chinese(field) or field == "TBID"]

    used_names = set()
    mapping_rows = []
    rename_map = OrderedDict()

    for field in keep_fields:
        if field == "TBID":
            source_name = "图斑编号"
            new_name = "tbbh"
            used_names.add(new_name)
            field_type = field_types[field]
        else:
            source_name = field
            new_name = make_unique_name(field, used_names)
            field_type = field_types[field]

        rename_map[field] = new_name
        mapping_rows.append(
            {
                "原字段名": source_name,
                "源字段": field,
                "新字段名": new_name,
                "原字段类型": field_type,
            }
        )

    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_excel(MAPPING_XLSX, index=False)
    mapping_df.to_csv(MAPPING_CSV, index=False, encoding="utf-8-sig")

    OUTPUT_DIR.mkdir(exist_ok=True)
    cleanup_existing(OUTPUT_SHP)

    out_schema = {
        "geometry": src.schema["geometry"],
        "properties": OrderedDict(
            (rename_map[field], normalize_field_type(field_types[field])) for field in keep_fields
        ),
    }

    matched_count = 0
    with fiona.open(
        OUTPUT_SHP,
        mode="w",
        driver="ESRI Shapefile",
        schema=out_schema,
        crs=src.crs,
        encoding="UTF-8",
    ) as dst:
        for feature in src:
            props = dict(feature["properties"])
            address = props.get("地址")
            if address is None or "盐城市" not in str(address):
                continue
            new_props = OrderedDict((rename_map[field], props.get(field)) for field in keep_fields)
            dst.write({"geometry": feature["geometry"], "properties": new_props})
            matched_count += 1

print("保留字段数:", len(keep_fields))
print("字段对照表:", MAPPING_XLSX)
print("字段对照表CSV:", MAPPING_CSV)
print("输出SHP:", OUTPUT_SHP)
print("筛选记录数:", matched_count)
