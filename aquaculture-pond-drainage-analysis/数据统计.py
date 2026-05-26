import pandas as pd
import glob
import os

""""统计"""
# -----------------------------
# 1. 配置路径（你的excel所在文件夹）
# # -----------------------------
# folder = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\新建镇养殖区\去重叠\统计"  # 改成你的路径
# # 支持 xlsx 和 xls
# excel_files = glob.glob(os.path.join(folder, "*.xlsx")) + glob.glob(os.path.join(folder, "*.xls"))
#
# if not excel_files:
#     raise FileNotFoundError(f"在 {folder} 没有找到 xlsx/xls 文件。")
#
# # -----------------------------
# # 处理每个 Excel 文件
# # -----------------------------
# for file in excel_files:
#     df = pd.read_excel(file)
#
#     # 必要字段检查
#     required = ["序号", "规划面积（公顷）", "行政区划"]
#     for col in required:
#         if col not in df.columns:
#             raise ValueError(f"文件 {os.path.basename(file)} 缺少必要字段：{col}")
#
#     # ------ 关键：取前两段作为序号组（例如 '1-1-1' -> '1-1'） ------
#     def take_first_two(s):
#         if pd.isna(s):
#             return ""
#         parts = str(s).split("-")
#         if len(parts) >= 2:
#             return f"{parts[0].strip()}-{parts[1].strip()}"
#         else:
#             return parts[0].strip()  # 没有 '-' 的情况，返回原样（去空格）
#
#     df["序号组"] = df["序号"].apply(take_first_two)
#
#     # 确保 规划面积 列为数值，可以处理字符串或空值
#     df["规划面积（公顷）"] = pd.to_numeric(df["规划面积（公顷）"], errors="coerce").fillna(0)
#
#     # 分组汇总：按 行政区划 + 序号组 累加面积
#     grouped = (
#         df.groupby(["行政区划", "序号组"], as_index=False)["规划面积（公顷）"]
#         .sum()
#         .rename(columns={"规划面积（公顷）": "规划面积汇总（公顷）"})
#     )
#
#     # 计算每个行政区划的合计面积
#     total_area = (
#         grouped.groupby("行政区划", as_index=False)["规划面积汇总（公顷）"]
#         .sum()
#         .rename(columns={"规划面积汇总（公顷）": "行政区划合计（公顷）"})
#     )
#
#     # 合并合计列到分组表
#     result = pd.merge(grouped, total_area, on="行政区划", how="left")
#
#     # 可选：按 行政区划、序号组 排序（便于查看）
#     result = result.sort_values(["行政区划", "序号组"]).reset_index(drop=True)
#
#     # 输出文件名 = 原名 + _统计.xlsx
#     base = os.path.splitext(os.path.basename(file))[0]
#     out_name = base + "_统计.xlsx"
#     out_path = os.path.join(folder, out_name)
#
#     result.to_excel(out_path, index=False)
#     print(f"✅ 已生成：{out_path}")
#
# print("全部处理完成 ✅")
#
# """行政区汇总"""
#
# # 匹配所有 *_统计.xlsx 文件
# import pandas as pd
# import glob
# import os
#
# def get_col_name(filename):
# 	base = os.path.splitext(os.path.basename(filename))[0]
# 	if "禁养区" in base:
# 		return "养殖现状位于禁养区（公顷）"
# 	elif "限养区" in base:
# 		return "养殖现状位于限养区（公顷）"
# 	elif "养殖区" in base:
# 		return "养殖现状位于养殖区（公顷）"
# 	else:
# 		return "养殖现状位于未知区（公顷）"
# # 文件夹路径，可修改
# folder = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\新建镇养殖区\去重叠"
# os.chdir(folder)
# files = glob.glob("*_统计.xlsx")
# print(files)
# for f in files:
# 	col_name = get_col_name(f)
# 	df = pd.read_excel(f)
#
# 	# 按行政区划分组累加
# 	df_grouped = df.groupby("行政区划", as_index=False)["规划面积（公顷）"].sum()
# 	df_grouped.rename(columns={"规划面积（公顷）": col_name}, inplace=True)
#
# 	# 添加总计行
# 	total = df_grouped[col_name].sum()
# 	total_row = pd.DataFrame({
# 		"行政区划": ["总计"],
# 		col_name: [total]
# 	})
# 	df_final = pd.concat([df_grouped, total_row], ignore_index=True)
#
# 	# 输出文件名 = 原文件名 + "_最终统计.xlsx"
# 	out_file = os.path.splitext(f)[0] + "_最终统计.xlsx"
# 	print(out_file)
# 	df_final.to_excel(out_file, index=False)
# 	print(f"✅ 已生成：{out_file}")

"""实际养殖面积"""
import pandas as pd
import glob
import os

# === 输入输出文件夹 ===
folder = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\新建镇养殖区\去重叠\统计"  # ⚠️改成你的文件夹路径

for file in glob.glob(os.path.join(folder, "*.xlsx")):
	# 读取表格
	df = pd.read_excel(file)
	
	# 检查必须的字段
	if not {"行政区划", "规划面积（公顷）"}.issubset(df.columns):
		print(f"⚠️ 跳过 {os.path.basename(file)}：缺少必要列")
		continue
	
	# 按行政区划分组求和
	result = (
		df.groupby("行政区划", as_index=False)["规划面积（公顷）"]
		.sum()
		.sort_values("行政区划")
		.reset_index(drop=True)
	)
	
	# 添加总计行
	total = pd.DataFrame({
		"行政区划": ["总计"],
		"规划面积（公顷）": [result["规划面积（公顷）"].sum()]
	})
	result = pd.concat([result, total], ignore_index=True)
	
	# 输出新表
	out_path = os.path.splitext(file)[0] + "_统计.xlsx"
	result.to_excel(out_path, index=False)
	print(f"✅ 输出完成：{os.path.basename(out_path)}")
