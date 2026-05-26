import os
import glob
import pandas as pd
import re

yzpz = [
    "青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼",
    "黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳢", "乌鳗",
    "罗非鱼", "鲟鱼", "鳗鲡", "罗氏沼虾", "青虾", "克氏原螯虾", "南美白对虾", "河蟹",
    "河蚌", "螺", "蚬", "螺旋藻", "龟", "鳖", "蛙", "珍珠", "其他种类", "观赏鱼",
    "鲆鱼", "大黄鱼", "鲽鱼", "斑节对虾", "中国对虾", "日本对虾", "梭子蟹", "青蟹",
    "牡蛎", "蚶", "贻贝", "蛤", "蛏", "紫菜", "海参", "海蜇"
]

pth = r'E:\全省养殖池溏上图入库普查\合规性检查\20250528'
files = glob.glob(os.path.join(pth, "*.csv"))

df_list = [pd.read_csv(f, skiprows=1, dtype='str', sep=',', usecols=range(54), index_col=False) for f in files]
ctxx = pd.concat(df_list, axis=0, ignore_index=True)

for c in ctxx.columns:
    ctxx.loc[ctxx[c] == '/', c] = ''
ctxx = ctxx.fillna('')
ctxx = ctxx[ctxx['状态'] != '未上报']
df = ctxx[ctxx['养殖状态'] == '养殖'].copy()

df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")
df = df.dropna(subset=["图斑面积"])
df["面积_亩"] = df["图斑面积"] * 0.0015
df["养殖品种/预计亩产量"] = df["养殖品种/预计亩产量"].str.replace("乌鳗", "乌鳢", regex=False)

# 拆解市和区县
def extract_city_district(addr):
    parts = str(addr).split('-')
    return pd.Series([parts[1], parts[2]]) if len(parts) >= 3 else pd.Series(["未知市", "未知区县"])
df[['市', '区县']] = df['地址'].apply(extract_city_district)

final_result = []

for variety in yzpz:
    sub_df = df[df["养殖品种/预计亩产量"].str.contains(variety, na=False)].copy()
    if sub_df.empty:
        continue

    def extract_yield(text):
        match = re.search(fr"{variety}:(\d+\.?\d*)斤/亩", text)
        return float(match.group(1)) if match else None

    sub_df["亩产量_斤"] = sub_df["养殖品种/预计亩产量"].apply(extract_yield)
    sub_df = sub_df.dropna(subset=["亩产量_斤"])
    sub_df["产量_吨"] = sub_df["亩产量_斤"] * sub_df["面积_亩"] / 2000

    # 创建一个唯一主体标识列
    sub_df["主体标识"] = (
        sub_df["养殖经营人名称"].astype(str).str.strip() + "_" +
        sub_df["身份证号"].astype(str).str.strip() + "_" +
        sub_df["统一社会信用代码"].astype(str).str.strip()
    )

    # 分组计算面积、产量
    grouped = sub_df.groupby(["市", "养殖主体类型"]).agg(
        总养殖面积_亩=('面积_亩', 'sum'),
        总产量_吨=('产量_吨', 'sum')
    ).reset_index()

    # 统计每组唯一主体数量
    unique主体 = sub_df.drop_duplicates(subset=["市", "养殖主体类型", "主体标识"])
    count_df = unique主体.groupby(["市", "养殖主体类型"]).size().reset_index(name="主体数量")

    # 合并主体数量
    grouped = pd.merge(grouped, count_df, on=["市", "养殖主体类型"], how='left')

    # 计算平均指标
    grouped["平均占用面积_亩"] = grouped["总养殖面积_亩"] / grouped["主体数量"]
    grouped["平均产量_吨"] = grouped["总产量_吨"] / grouped["主体数量"]
    grouped["平均生产效率_吨每亩"] = grouped["总产量_吨"] / grouped["总养殖面积_亩"]
    grouped["品种"] = variety

    final_result.append(grouped)

# 合并所有品种结果
total_df = pd.concat(final_result, axis=0, ignore_index=True)

# 列顺序整理
total_df = total_df[[
    "品种", "市", "养殖主体类型", "主体数量",
    "总养殖面积_亩", "总产量_吨",
    "平均占用面积_亩", "平均产量_吨", "平均生产效率_吨每亩"
]]

# 保存结果
output_path = os.path.join(pth, "各品种_市_主体类型_统计汇总_去重主体数量.xlsx")
total_df.to_excel(output_path, index=False)

print(f"✅ 成功完成并保存：{output_path}")
