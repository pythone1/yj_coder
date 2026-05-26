import pandas as pd

# ===== 参数配置 =====
a_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\原表\4个区县成品养殖信息表0703.xlsx"  # 表 A 路径
b_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\四个区县四条鱼主体0703.xlsx"  # 表 B 路径
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\原表\0703匹配结果.xlsx"  # 输出文件路径

# ===== 关键词列表 =====
keywords = ["鲫鱼", "鳊鲂", "泥鳅", "鲈鱼"]

# ===== 读取数据 =====
df_a = pd.read_excel(a_path)
df_b = pd.read_excel(b_path)

# ===== 筛选 A 表中品种字段包含关键词的数据 =====
mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
filtered_a = df_a[mask].copy()

# ===== 构建匹配键 =====
def make_key(df):
    return df[["养殖经营人名称", "联系方式", "身份证号", "统一社会信用代码", "地址"]].astype(str).agg("|".join, axis=1)

filtered_a["match_key"] = make_key(filtered_a)
df_b["match_key"] = make_key(df_b)

# ===== 匹配：从 A 中选出匹配 B 的数据 =====
matched_keys = set(df_b["match_key"])
matched_a = filtered_a[filtered_a["match_key"].isin(matched_keys)].copy()

# ===== 提取“乡镇”信息 =====
matched_a["乡镇"] = matched_a["地址"].astype(str).str.split("-").str[3]

# ===== 删除辅助列并保存结果 =====
matched_a.drop(columns=["match_key"], inplace=True)
matched_a.to_excel(output_path, index=False)
