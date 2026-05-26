import geopandas as gpd
import pandas as pd
import re
import os

# 品种列表
yzpz = [
    "青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼",
    "黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳢", "乌鳗",
    "罗非鱼", "鲟鱼", "鳗鲡", "罗氏沼虾", "青虾", "克氏原螯虾", "南美白对虾", "河蟹",
    "河蚌", "螺", "蚬", "螺旋藻", "龟", "鳖", "蛙", "珍珠", "其他种类", "观赏鱼",
    "鲆鱼", "大黄鱼", "鲽鱼", "斑节对虾", "中国对虾", "日本对虾", "梭子蟹", "青蟹",
    "牡蛎", "蚶", "贻贝", "蛤", "蛏", "紫菜", "海参", "海蜇"
]

# 输入输出路径
gpkg_path = r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\填报养殖点.gpkg"
output_dir = r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\产量热图"

os.makedirs(output_dir, exist_ok=True)

# 读取文件
gdf = gpd.read_file(gpkg_path)

# 替换误写的品种名
gdf["养殖品种/预计亩产量"] = gdf["养殖品种/预计亩产量"].str.replace("乌鳗", "乌鳢", regex=False)

# 转换图斑面积为数值
gdf["图斑面积_x"] = pd.to_numeric(gdf["图斑面积_x"], errors="coerce")

# 遍历每个品种
for variety in yzpz:
    产量列名 = f"{variety}产量"
    产量值 = []

    for idx, row in gdf.iterrows():
        text = str(row["养殖品种/预计亩产量"])
        area = row["图斑面积_x"]

        match = re.search(fr"{variety}:(\d+\.?\d*)斤/亩", text)
        if match and pd.notnull(area):
            yield_per_mu = float(match.group(1))
            yield_tons = yield_per_mu * area * 0.0015
        else:
            yield_tons = 0.0

        产量值.append(yield_tons)

    # 临时复制一份gdf，只保留地址、图斑面积、产量
    temp_gdf = gdf.copy()
    temp_gdf[产量列名] = 产量值
    temp_gdf = temp_gdf[temp_gdf[产量列名] > 0]

    # 只保留三列：地址、图斑面积_x、{品种}产量
    if not temp_gdf.empty:
        output_gdf = temp_gdf[["地址", "图斑面积_x", 产量列名,"geometry"]]
        out_path = os.path.join(output_dir, f"{variety}_产量结果.gpkg")
        output_gdf.to_file(out_path, driver="GPKG", encoding="utf-8")
        print(f"✅ 导出：{variety} → {out_path}")
    else:
        print(f"⚠️ 跳过：{variety}（无产量记录）")

print("🎉 所有品种导出完成。")

