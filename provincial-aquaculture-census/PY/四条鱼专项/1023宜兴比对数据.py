import pandas as pd
import geopandas as gpd
import os

# --- 配置文件路径 ---
EXCEL_FILE_PATH = r"E:\全省养殖池溏上图入库普查\PY\宜兴市\业主信息.xlsx"
GPKG_FILE_PATH = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市池塘图斑库.gpkg'
OUTPUT_EXCEL_PATH = r'E:\全省养殖池溏上图入库普查\PY\宜兴市\output_with_analysis.xlsx'


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

    # 标准化列名去除空格
    df.columns = df.columns.str.strip()

    # --- 步骤 2: 检查塘口面积填写不一致的问题 ---
    print("\n--- 步骤 2: 检查塘口面积填写不一致 ---")

    town_col = "所在镇村（镇街+村）"
    name_col = "养殖主体姓名（名称）"
    area_col = "塘口面积（亩）"

    # 初始化问题描述列
    if "问题描述" not in df.columns:
        df["问题描述"] = ""

    # 清洗面积列（去掉非数字）
    df[area_col + "_原始"] = df[area_col].astype(str)
    df[area_col] = (
        df[area_col].astype(str)
        .str.replace(r"[^\d.]", "", regex=True)
        .replace("", pd.NA)
        .astype(float)
    )

    # 分组计算每组内的面积集合
    area_group = (
        df.groupby([town_col, name_col])[area_col]
        .apply(lambda s: set(s.dropna()))
        .reset_index(name="面积集合")
    )

    # 判断是否存在多个不同的面积值
    problem_groups = area_group[area_group["面积集合"].apply(lambda x: len(x) > 1)]

    if not problem_groups.empty:
        print(f"⚠️ 发现 {len(problem_groups)} 组存在塘口面积填写不一致的问题。")
        print(problem_groups.head())

        # 构建问题组合集合
        problem_set = set(tuple(x) for x in problem_groups[[town_col, name_col]].values)

        # 在原始数据中标记
        df["问题描述"] = df.apply(
            lambda r: "同镇同名养殖主体塘口面积填写不一致"
            if (r[town_col], r[name_col]) in problem_set else r["问题描述"],
            axis=1,
        )
    else:
        print("✅ 未发现塘口面积填写不一致的问题。")

    # --- 步骤 3: 读取GPKG文件并计算面积 ---
    print("\n--- 步骤 3: 读取GPKG文件并计算面积 ---")
    try:
        gdf = gpd.read_file(gpkg_path)
        print(f"✅ 成功读取GPKG文件，共 {len(gdf)} 个图斑。")
        print("GPKG列名:", gdf.columns.tolist())
    except FileNotFoundError:
        print(f"❌ 错误：找不到GPKG文件 '{gpkg_path}'。")
        return

    # 投影到 EPSG:32650 (单位: 米)
    print("正在将GPKG数据投影到 EPSG:32650...")
    gdf_projected = gdf.to_crs('EPSG:32650')

    # 计算面积（平方米 → 亩）
    gdf_projected['单个图斑面积'] = gdf_projected.geometry.area * 0.0015
    print("✅ 已计算所有图斑的面积（亩）。")

    # --- 步骤 4: 合并Excel和GPKG数据 ---
    print("\n--- 步骤 4: 合并数据 ---")
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

    # --- 步骤 5: 计算养殖户在当前镇的总图斑面积 ---
    print("\n--- 步骤 5: 计算累计面积 ---")
    merged_df['该养殖户在当前镇总图斑面积'] = merged_df.groupby(
        [name_col, town_col]
    )['单个图斑面积'].transform('sum')
    print("✅ 累计面积计算完成。")

    # --- 步骤 6: 保存最终结果到新的Excel文件 ---
    print("\n--- 步骤 6: 保存结果 ---")
    if 'tbid' in merged_df.columns:
        merged_df.drop('tbid', axis=1, inplace=True)

    try:
        merged_df.to_excel(output_excel, index=False, engine='openpyxl')
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
