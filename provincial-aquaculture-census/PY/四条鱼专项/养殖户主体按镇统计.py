import pandas as pd


excel_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\四个区县四条鱼主体0703.xlsx"
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\0703四市主体_按市分.xlsx"

# 要统计的品种关键词与列名映射（用于识别品种）
species_map = {
    "鳊鲂": "鳊鲂",
    "鲫鱼": "鲫鱼",
    "鲈鱼": "淡水鲈鱼",
    "泥鳅": "泥鳅"
}

areas = ["金湖县", "高邮市", "丹阳市", "宝应县"]
df_all = pd.read_excel(excel_path, engine='openpyxl')
df_all["面积_亩"] = pd.to_numeric(df_all["面积_亩"], errors="coerce")

df_all["乡镇"] = df_all["地址"].astype(str).str.split("-").str[3]

# 创建 ExcelWriter，用于输出多个 sheet
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    for area in areas:
        # ===== 筛选包含该区域名的记录，面积不小于5亩 =====
        df = df_all[
            df_all["地址"].astype(str).str.contains(area) &
            (df_all["面积_亩"] >= 5)
        ].copy()

        # 获取所有乡镇列表
        towns = df["乡镇"].dropna().unique()
        result_df = pd.DataFrame({"乡镇、园区": sorted(towns)})

        # 逐品种统计每个乡镇的记录数量
        for keyword, col_name in species_map.items():
            filtered = df[df["养殖品种"].astype(str).str.contains(keyword, na=False)].copy()
            count_series = filtered.groupby("乡镇").size().rename(col_name)
            result_df = result_df.merge(count_series, how="left", left_on="乡镇、园区", right_index=True)

        # 确保所有鱼种列存在
        for col in species_map.values():
            if col not in result_df:
                result_df[col] = 0

        # 转换为整数，填补空值
        species_cols = list(species_map.values())
        result_df[species_cols] = result_df[species_cols].fillna(0).astype(int)

        # 重新计算“小计”：只要包含任一品种就算入一条
        pattern = '|'.join(species_map.keys())
        filtered_df_for_subtotal = df[df["养殖品种"].astype(str).str.contains(pattern, na=False)]
        subtotal_series = filtered_df_for_subtotal.groupby("乡镇").size().rename("小计")

        result_df = result_df.merge(subtotal_series, how="left", left_on="乡镇、园区", right_index=True)
        result_df["小计"] = result_df["小计"].fillna(0).astype(int)

        # 添加序号
        result_df.insert(0, "序号", range(1, len(result_df) + 1))

        # ===== 合计行：每个品种的总数量，小计为四种鱼总记录数（不分类镇） =====
        total_row = {
            "序号": "",
            "乡镇、园区": "合计"
        }
        for keyword, col_name in species_map.items():
            total_row[col_name] = df[df["养殖品种"].astype(str).str.contains(keyword, na=False)].shape[0]
        total_row["小计"] = df[df["养殖品种"].astype(str).str.contains(pattern, na=False)].shape[0]

        result_df.loc[len(result_df)] = total_row

        # 写入对应 sheet
        sheet_name = area[:31]  # Excel sheet 名不能超过31字符
        result_df.to_excel(writer, index=False, sheet_name=sheet_name)

print(f"四地市统计完成，结果已保存至：{output_path}")
