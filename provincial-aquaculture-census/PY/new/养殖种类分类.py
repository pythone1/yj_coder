# import geopandas as gpd
#
# # 读取池塘数据
# gdf = gpd.read_file(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250609\南京\图斑.gpkg")  # 替换为你的文件路径
#
# # 鱼类关键词（注意包括观赏鱼等）
# fish_keywords = [
#     "青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "鲇鱼", "鮰鱼",
#     "黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼",
#     "乌鳢", "乌鳗", "罗非鱼", "鲟鱼", "鳗鲡", "观赏鱼", "鲆鱼", "大黄鱼", "鲽鱼"
# ]
#
# # 分类关键词字典
# type_keywords = {
#     "龟鳖": ["龟", "鳖"],
#     "鱼": fish_keywords,
#     "虾": ["虾"],
#     "蟹": ["蟹"],
#     "鳅": ["泥鳅"],
#     "蚌": ["蚌"],
#     "蛙": ["蛙"],
#     "其他": ["其他", "其它"]
# }
#
# # 分类函数
# def classify_type(value):
#     if not isinstance(value, str):
#         return "其他"
#
#     text = value.strip().replace("（", "(").replace("）", ")")
#
#     # 如果明确写了“其他”或“其它”，优先归为“其他”
#     if any(k in text for k in type_keywords["其他"]):
#         return "其他"
#
#     matched = set()
#
#     # 判断其他类型（除了“其他”）
#     for tname, keywords in type_keywords.items():
#         if tname == "其他":
#             continue
#         if any(k in text for k in keywords):
#             matched.add(tname)
#
#     # 分类组合判断（从复杂到简单）
#     if matched == {"鱼", "虾", "蟹"}:
#         return "鱼虾蟹"
#     elif matched == {"鱼", "蟹"}:
#         return "鱼蟹"
#     elif matched == {"鱼", "虾"}:
#         return "鱼虾"
#     elif matched == {"虾", "蟹"}:
#         return "虾蟹"
#     elif matched == {"鱼", "鳅"}:
#         return "鱼鳅"
#     elif "鱼" in matched:
#         return "鱼"
#     elif "虾" in matched:
#         return "虾"
#     elif "蟹" in matched:
#         return "蟹"
#     elif "鳅" in matched:
#         return "鱼鳅"
#     elif "龟鳖" in matched:
#         return "龟鳖"
#     elif "蛙" in matched:
#         return "蛙"
#     elif "蚌" in matched:
#         return "蚌"
#     else:
#         return "其他"
#
# # 应用分类
# gdf["养殖类型"] = gdf["养殖品种/预计亩产量"].apply(classify_type)
#
# # 写出到新文件
# gdf.to_file(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250609\南京\池塘分类.gpkg", driver="GPKG", encoding="utf-8")
# print("✅ 分类完成，文件已保存为 classified_ponds.gpkg")

import geopandas as gpd
import pandas as pd

# 读取已分类数据（确保已有 "养殖类型" 字段）
gdf = gpd.read_file(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250609\南京\池塘分类.gpkg")

# 确保为EPSG:32650投影，用于面积计算
if gdf.crs.to_epsg() != 32650:
    gdf = gdf.to_crs(epsg=32650)

# 提取区县字段
gdf["区县"] = gdf["地址"].str.split("-").str[2]

# 计算面积（平方米）
gdf["面积"] = gdf.geometry.area

# 按 区县 + 养殖类型 分组统计数量与总面积
grouped = gdf.groupby(["区县", "养殖类型"]).agg(
    池塘数量=("养殖类型", "count"),
    总面积平方米=("面积", "sum")
).reset_index()

# 添加总计行
total_row = pd.DataFrame({
    "区县": ["全省合计"],
    "养殖类型": ["全部"],
    "池塘数量": [grouped["池塘数量"].sum()],
    "总面积平方米": [grouped["总面积平方米"].sum()]
})

# 合并并导出
summary = pd.concat([grouped, total_row], ignore_index=True)
summary.to_excel(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250609\南京\池塘分类统计表.xlsx", index=False)

