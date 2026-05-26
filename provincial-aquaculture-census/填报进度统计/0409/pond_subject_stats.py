from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(r"E:\temp_pond_info_0409_ascii")
OUTPUT_DIR = BASE_DIR / "output"

CITY_FILE_MAP = {
    "nanjing": "南京市",
    "wuxi": "无锡市",
    "suzhou": "苏州市",
    "changzhou": "常州市",
    "zhenjiang": "镇江市",
    "nantong": "南通市",
    "suqian": "宿迁市",
    "xuzhou": "徐州市",
    "yangzhou": "扬州市",
    "taizhou": "泰州市",
    "huaian": "淮安市",
    "yancheng": "盐城市",
    "lianyungang": "连云港市",
}

KEY_COLS = ["养殖经营人名称", "身份证号", "统一社会信用代码", "地址", "联系方式"]
AREA_COL = "图斑面积"
STATUS_COL = "养殖状态"


def normalize_value(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"} or text in {"/", "／"}:
        return ""
    return text


def load_all_data() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for file_stem, city_name in CITY_FILE_MAP.items():
        file_path = BASE_DIR / f"{file_stem}.xlsx"
        df = pd.read_excel(file_path, sheet_name=0)
        df["城市"] = city_name
        df[AREA_COL] = pd.to_numeric(df[AREA_COL], errors="coerce")
        df["面积_亩"] = df[AREA_COL] * 0.0015
        df[STATUS_COL] = df[STATUS_COL].map(normalize_value)
        for col in KEY_COLS:
            df[col] = df[col].map(normalize_value)
        df["主体字段全空"] = (df[KEY_COLS] == "").all(axis=1)
        df["主体去重键"] = df[KEY_COLS].agg("|".join, axis=1)
        frames.append(df[["城市", AREA_COL, "面积_亩", STATUS_COL, "主体字段全空", "主体去重键", *KEY_COLS]])
    return pd.concat(frames, ignore_index=True)


def build_region_table(
    all_data: pd.DataFrame, region_name: str, cities: list[str], min_mu: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered = all_data[
        (all_data["城市"].isin(cities))
        & (all_data["面积_亩"] >= min_mu)
        & (all_data[STATUS_COL] == "养殖")
    ].copy()
    valid_subjects = filtered.loc[~filtered["主体字段全空"]].copy()

    city_rows = []
    for city in cities:
        city_filtered = filtered.loc[filtered["城市"] == city]
        city_valid = valid_subjects.loc[valid_subjects["城市"] == city]
        city_rows.append(
            {
                "区域": region_name,
                "城市": city,
                "面积门槛(亩)": min_mu,
                "养殖状态筛选": "养殖",
                "符合条件池塘数": int(len(city_filtered)),
                "主体字段全空池塘数": int(city_filtered["主体字段全空"].sum()),
                "涉及养殖主体数": int(city_valid["主体去重键"].nunique()),
            }
        )

    city_rows.append(
        {
            "区域": region_name,
            "城市": "合计(跨市去重)",
            "面积门槛(亩)": min_mu,
            "养殖状态筛选": "养殖",
            "符合条件池塘数": int(len(filtered)),
            "主体字段全空池塘数": int(filtered["主体字段全空"].sum()),
            "涉及养殖主体数": int(valid_subjects["主体去重键"].nunique()),
        }
    )

    table = pd.DataFrame(city_rows)

    subject_list = (
        valid_subjects.drop_duplicates(subset=["主体去重键"])
        .loc[:, ["城市", *KEY_COLS]]
        .sort_values(["城市", "养殖经营人名称", "身份证号", "统一社会信用代码", "地址", "联系方式"])
        .reset_index(drop=True)
    )
    return table, subject_list


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_data = load_all_data()

    suxichang_table, suxichang_subjects = build_region_table(
        all_data,
        region_name="苏锡常",
        cities=["苏州市", "无锡市", "常州市"],
        min_mu=6,
    )
    sunan_table, sunan_subjects = build_region_table(
        all_data,
        region_name="苏南",
        cities=["苏州市", "无锡市", "常州市", "南京市", "镇江市"],
        min_mu=5,
    )

    workbook_path = OUTPUT_DIR / "pond_subject_stats.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        suxichang_table.to_excel(writer, sheet_name="苏锡常6亩以上", index=False)
        sunan_table.to_excel(writer, sheet_name="苏南5市5亩以上", index=False)
        suxichang_subjects.to_excel(writer, sheet_name="苏锡常主体明细", index=False)
        sunan_subjects.to_excel(writer, sheet_name="苏南主体明细", index=False)

    suxichang_table.to_csv(OUTPUT_DIR / "suxichang_6mu_stats.csv", index=False, encoding="utf-8-sig")
    sunan_table.to_csv(OUTPUT_DIR / "sunan_5mu_stats.csv", index=False, encoding="utf-8-sig")

    print("RESULT_WORKBOOK", workbook_path)
    print("\n[苏锡常6亩以上]")
    print(suxichang_table.to_string(index=False))
    print("\n[苏南5市5亩以上]")
    print(sunan_table.to_string(index=False))


if __name__ == "__main__":
    main()
