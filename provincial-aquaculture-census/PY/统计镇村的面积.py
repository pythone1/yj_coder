import pandas as pd

# 读取 Excel 文件
excel_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250827\0827锡山区.xlsx"   # 修改为你的Excel路径
df = pd.read_excel(excel_path)

# 去重：按 图斑编号 保留第一条
df = df.drop_duplicates(subset=["图斑编号"], keep="first")

# 图斑面积换算成亩（确保是数值型）
df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")  # 转成数值，非法转NaN
df["图斑面积_亩"] = df["图斑面积"] * 0.0015

# 按 地址 + 填报状态 分组统计
result = df.groupby(["地址", "养殖状态"]).agg(
    数量=("图斑编号", "count"),
    总面积_亩=("图斑面积_亩", "sum")
).reset_index()

# 保留两位小数
result["总面积_亩"] = result["总面积_亩"].round(2)

# 保存到Excel
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250827\0827锡山区面积统计.xlsx"
result.to_excel(output_path, index=False)

print("统计完成，结果已保存：", output_path)
