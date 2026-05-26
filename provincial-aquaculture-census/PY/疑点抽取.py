import geopandas as gpd
import pandas as pd

# 读取池塘shp文件
ponds_shp = r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250331江阴市疑点选取\池塘信息-1743399406935-无锡市江阴市-池塘图斑.gpkg"  # 请替换为实际文件路径
ponds = gpd.read_file(ponds_shp)

# 从“已填报养殖”类别中随机抽取200个用于电话核查
phone_check_samples = ponds[ponds["填报状态"] == "已填报养殖"].sample(n=200, random_state=42)
phone_check_samples["核查方式"] = "电话核查"

# 从“已填报非养殖”类别中随机抽取20个用于现场核查
field_check_samples = ponds[ponds["填报状态"] == "已填报非养殖"].sample(n=20, random_state=42)
field_check_samples["核查方式"] = "现场核查"

# 合并两类核查样本
samples = pd.concat([phone_check_samples, field_check_samples])

# 选择需要保存的字段（去除geometry等不必要字段）
columns_to_save = [col for col in samples.columns if col != "geometry"]

# 保存到 Excel
output_excel = r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250331江阴市疑点选取\20250331江阴核查点位选取.xlsx"
samples[columns_to_save].to_excel(output_excel, index=False)

print(f"抽样结果已保存至 {output_excel}")
