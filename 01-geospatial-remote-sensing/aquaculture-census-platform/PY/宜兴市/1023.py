"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 1023.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import pandas as pd
import geopandas as gpd
import os

# --- 配置文件路径 ---
EXCEL_FILE_PATH = r"E:\全省养殖池溏上图入库普查\PY\宜兴市\20251112\1211徐舍镇.xlsx"
GPKG_FILE_PATH = r'E:\全省养殖池溏上图入库普查\宜兴市池塘图斑数据库\宜兴市池塘图斑数据库.shp'
OUTPUT_EXCEL_PATH = r'E:\全省养殖池溏上图入库普查\PY\宜兴市\20251112\1211徐舍镇核查.xlsx'


def process_aquaculture_data(excel_path, gpkg_path, output_excel):
    """
    主处理函数，执行所有分析步骤。
    """
    print("--- 步骤 1: 读取Excel文件 ---")
    try:
        df = pd.read_excel(excel_path)
        print(f"✅ 成功读取Excel文件，共 {len(df)} 行数据。")
        print("Excel列名:", df.columns.tolist())
    except FileNotFoundError:
        print(f"❌ 错误：找不到Excel文件 '{excel_path}'。")
        return

    # 保存原始字段顺序
    original_cols = df.columns.tolist()

    # 标准化列名去除空格
    df.columns = df.columns.str.strip()

    town_col = "所在镇村（镇街+村）"
    name_col = "养殖主体姓名（名称）"
    area_col = "塘口面积（亩）"

    # 初始化问题描述列
    if "问题描述" not in df.columns:
        df["问题描述"] = ""

    # --- 步骤 2: 检查塘口面积填写不一致 ---
    print("\n--- 步骤 2: 检查塘口面积填写不一致 ---")

    df[area_col + "_原始"] = df[area_col].astype(str)
    df[area_col] = (
        df[area_col].astype(str)
        .str.replace(r"[^\d.]", "", regex=True)
        .replace("", pd.NA)
        .astype(float)
    )

    area_group = (
        df.groupby([town_col, name_col])[area_col]
        .apply(lambda s: set(s.dropna()))
        .reset_index(name="面积集合")
    )

    problem_groups = area_group[area_group["面积集合"].apply(lambda x: len(x) > 1)]

    if not problem_groups.empty:
        print(f"⚠️ 发现 {len(problem_groups)} 组存在塘口面积填写不一致的问题。")
        problem_set = set(tuple(x) for x in problem_groups[[town_col, name_col]].values)
        df["问题描述"] = df.apply(
            lambda r: "同镇同名养殖主体塘口面积填写不一致"
            if (r[town_col], r[name_col]) in problem_set else r["问题描述"],
            axis=1,
        )
    else:
        print("✅ 未发现塘口面积填写不一致的问题。")

    # --- 步骤 3: 读取GPKG并计算面积 ---
    print("\n--- 步骤 3: 读取GPKG文件并计算面积 ---")
    try:
        gdf = gpd.read_file(gpkg_path)
        print(f"✅ 成功读取GPKG文件，共 {len(gdf)} 个图斑。")
        print("GPKG列名:", gdf.columns.tolist())
    except FileNotFoundError:
        print(f"❌ 错误：找不到GPKG文件 '{gpkg_path}'。")
        return

    print("正在投影到 EPSG:32650...")
    gdf_projected = gdf.to_crs('EPSG:32650')
    gdf_projected['单个图斑面积'] = gdf_projected.geometry.area * 0.0015  # 平方米转亩
    print("✅ 已计算所有图斑的面积（亩）。")

    # --- 步骤 4: 合并数据 ---
    print("\n--- 步骤 4: 合并Excel与GPKG ---")
    df['图斑编号'] = df['图斑编号'].astype(str)
    gdf_projected['tbid'] = gdf_projected['tbid'].astype(str)

    merged_df = df.merge(
        gdf_projected[['tbid', '单个图斑面积']],
        left_on='图斑编号',
        right_on='tbid',
        how='left'
    )
    merged_df['单个图斑面积'].fillna(0, inplace=True)
    print("✅ 数据合并完成。")

    # --- 步骤 5: 计算累计面积和塘口数量（修正后的计算） ---
    print("\n--- 步骤 5: 计算累计面积和塘口数量 ---")

    # 计算该养殖户在当前镇的总图斑面积（亩）
    merged_df['该养殖户在当前镇总图斑面积'] = merged_df.groupby(
        [name_col, town_col]
    )['单个图斑面积'].transform('sum')

    # 计算养殖户在当前镇村的塘口数量（图斑数）
    merged_df['养殖户塘口数量（当前镇村）'] = merged_df.groupby(
        [name_col, town_col]
    )['图斑编号'].transform('count')

    # 为了计算分摊，需要保留“原始申报的塘口面积数值”（如果之前清洗过，则使用清洗后的 numeric 字段）
    # 注意：脚本上游已把原始文本保存在 area_col + "_原始"，并把 area_col 替换为清洗后的 float（如果存在）
    # 这里我们优先使用 merged_df[area_col] 作为“申报塘口面积数值”，若缺失则设为 0
    merged_df['申报塘口面积数值'] = merged_df[area_col].fillna(0).astype(float)

    # 计算占比 = 单个图斑面积 / 该养殖户在当前镇总图斑面积
    # 若分母为 0，则占比设为 0（避免除零）
    merged_df['占比'] = 0.0
    nonzero_mask = merged_df['该养殖户在当前镇总图斑面积'] > 0
    merged_df.loc[nonzero_mask, '占比'] = (
        merged_df.loc[nonzero_mask, '单个图斑面积'] /
        merged_df.loc[nonzero_mask, '该养殖户在当前镇总图斑面积']
    )

    # 最终塘口面积（亩） = 申报塘口面积数值 * 占比，保留两位小数
    merged_df[area_col] = (merged_df['申报塘口面积数值'] * merged_df['占比']).round(2)

    # 对于那些总图斑面积为0或者申报塘口面积数值为0的情况，塘口面积应为0（已经覆盖，但明确处理）
    merged_df.loc[
        (merged_df['该养殖户在当前镇总图斑面积'] == 0) | (merged_df['申报塘口面积数值'] == 0),
        area_col
    ] = 0.00

    # 清理临时列（如果不希望保留）
    # merged_df.drop(columns=['申报塘口面积数值', '占比'], inplace=True)


    # --- 步骤 6: 输出结果，保持原字段顺序 ---
    print("\n--- 步骤 6: 输出结果 ---")
    output_cols = [col for col in original_cols if col in merged_df.columns]
    output_cols.append("问题描述")  # 若新增此列则附加
    output_cols.append("养殖户塘口数量（当前镇村）")

    output_df = merged_df[output_cols]

    try:
        output_df.to_excel(output_excel, index=False, engine='openpyxl')
        print(f"🎉 处理完成！结果已保存到: {output_excel}")
    except Exception as e:
        print(f"❌ 保存Excel文件时出错: {e}")


if __name__ == '__main__':
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"⚠️ 警告: Excel文件 '{EXCEL_FILE_PATH}' 不存在。")
    if not os.path.exists(GPKG_FILE_PATH):
        print(f"⚠️ 警告: GPKG文件 '{GPKG_FILE_PATH}' 不存在。")

    if os.path.exists(EXCEL_FILE_PATH) and os.path.exists(GPKG_FILE_PATH):
        process_aquaculture_data(
            excel_path=EXCEL_FILE_PATH,
            gpkg_path=GPKG_FILE_PATH,
            output_excel=OUTPUT_EXCEL_PATH,
        )
    else:
        print("请确保输入文件存在后再运行脚本。")
