import glob
import pandas as pd

# ====== 配置部分 ====== #
folder_path = r"E:\全省养殖池溏上图入库普查\PY\七鱼疑点\无锡市\无锡市\无锡市七鱼质控"  # 你的Excel目录
sheet1 = "成品养殖七鱼相关"
sheet2 = "其他"

# ====== 初始化统计 ====== #
total_sheet1 = 0
total_sheet2 = 0

# ====== 遍历所有xlsx ====== #
for file in glob.glob(f"{folder_path}/**/*.xlsx", recursive=True):
    try:
        xls = pd.ExcelFile(file)
        if sheet1 in xls.sheet_names:
            df1 = pd.read_excel(file, sheet_name=sheet1)
            total_sheet1 += len(df1.dropna(how="all")) - 1  # 去掉表头，统计有效行
        if sheet2 in xls.sheet_names:
            df2 = pd.read_excel(file, sheet_name=sheet2)
            total_sheet2 += len(df2.dropna(how="all")) - 1  # 去掉表头，统计有效行
    except Exception as e:
        print(f"读取 {file} 出错: {e}")

# ====== 输出汇总结果 ====== #
print(f"七鱼相关总计 {total_sheet1} 条")
print(f"其他总计 {total_sheet2} 条")
