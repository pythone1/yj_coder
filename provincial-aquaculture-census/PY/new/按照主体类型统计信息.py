import os
import glob
import pandas as pd
import re

# 品种列表
yzpz = [
    "青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼",
    "黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳢", "乌鳗",
    "罗非鱼", "鲟鱼", "鳗鲡", "罗氏沼虾", "青虾", "克氏原螯虾", "南美白对虾", "河蟹",
    "河蚌", "螺", "蚬", "螺旋藻", "龟", "鳖", "蛙", "珍珠", "其他种类", "观赏鱼",
    "鲆鱼", "大黄鱼", "鲽鱼", "斑节对虾", "中国对虾", "日本对虾", "梭子蟹", "青蟹",
    "牡蛎", "蚶", "贻贝", "蛤", "蛏", "紫菜", "海参", "海蜇"
]

# 路径设置
pth = r'E:\全省养殖池溏上图入库普查\合规性检查\20250528'
files = glob.glob(os.path.join(pth, "*.csv"))

# 读取 CSV 文件
df_list = [pd.read_csv(f, skiprows=1, dtype='str', sep=',', usecols=range(54), index_col=False) for f in files]
ctxx = pd.concat(df_list, axis=0, ignore_index=True)

# 清洗数据
for c in ctxx.columns:
    ctxx.loc[ctxx[c] == '/', c] = ''
ctxx = ctxx.fillna('')
ctxx = ctxx[ctxx['状态'] != '未上报']
df = ctxx[ctxx['养殖状态'] == '养殖'].copy()

# 面积转化
df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")
df = df.dropna(subset=["图斑面积"])
df["养殖品种/预计亩产量"] = df["养殖品种/预计亩产量"].str.replace("乌鳗", "乌鳢", regex=False)
df["面积_亩"] = df["图斑面积"] * 0.0015

# 提取产量
def extract_main_yield(row):
    text = row["养殖品种/预计亩产量"]
    for variety in yzpz:
        if variety in text:
            match = re.search(fr"{variety}:(\d+\.?\d*)斤/亩", text)
            if match:
                return float(match.group(1))
    return None

df["主品种产量_斤每亩"] = df.apply(extract_main_yield, axis=1)
df["产量_吨"] = df["主品种产量_斤每亩"] * df["面积_亩"] / 2000
df = df.dropna(subset=["产量_吨"])

# 分组统计
group_stats = df.groupby(["市", "养殖主体类型"]).agg(
    主体数量=('图斑面积', 'count'),
    总养殖面积_亩=('面积_亩', 'sum'),
    总产量_吨=('产量_吨', 'sum')
).reset_index()

group_stats["平均占用面积_亩"] = group_stats["总养殖面积_亩"] / group_stats["主体数量"]
group_stats["平均产量_吨"] = group_stats["总产量_吨"] / group_stats["主体数量"]
group_stats["平均生产效率_吨每亩"] = group_stats["总产量_吨"] / group_stats["总养殖面积_亩"]

# 输出结果
output_excel_path = os.path.join(pth, "各市主体类型产量统计表.xlsx")
group_stats.to_excel(output_excel_path, index=False)

print(f"✅ 统计完成，已保存到：{output_excel_path}")
