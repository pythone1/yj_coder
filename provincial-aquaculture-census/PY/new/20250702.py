import pandas as pd

# 读取 Excel 表格
file_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250702\高邮市四鱼养殖主体（含品种乡镇）.xlsx'  # 修改为你的文件路径
df = pd.read_excel(file_path)

# 目标品种关键词
species_list = ["鲫鱼", "鳊鲂", "鲈鱼", "泥鳅"]
# 初始化结果字典
result = {}
# 遍历每种品种
for species in species_list:
    # 筛选包含该品种的记录
    filtered = df[df["养殖品种"].astype(str).str.contains(species, na=False)]
    # 按“乡镇”字段分组统计数量
    count_by_town = filtered.groupby("乡镇").size()
    # 存入结果
    result[species] = count_by_town
# 将结果字典转换为DataFrame（行是品种，列是乡镇）
stat_table = pd.DataFrame(result).T.fillna(0).astype(int)
# 输出结果
print(stat_table)
# 保存到 Excel
stat_table.to_excel(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250702\高邮市品种统计表.xlsx")
