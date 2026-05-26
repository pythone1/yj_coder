import os, glob,re
import pandas as pd
yzpz = [
"青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼",
"黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳢","乌鳗",
"罗非鱼", "鲟鱼", "鳗鲡", "罗氏沼虾", "青虾", "克氏原螯虾", "南美白对虾", "河蟹",
"河蚌", "螺", "蚬", "螺旋藻", "龟", "鳖", "蛙", "珍珠", "其他种类", "观赏鱼",
"鲆鱼", "大黄鱼", "鲽鱼", "斑节对虾", "中国对虾", "日本对虾", "梭子蟹", "青蟹",
"牡蛎", "蚶", "贻贝", "蛤", "蛏", "紫菜", "海参", "海蜇"
]
# yzpz=["青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂"]
if __name__ == "__main__":
    pth = r'E:\全省养殖池溏上图入库普查\合规性检查\20250516'
    os.chdir(pth)
    files = glob.glob(r"*.csv")
    df_list = []
    for f in files:
        df_list.append(pd.read_csv(f,dtype='str',sep=',',usecols=range(54),index_col=False))
    ctxx = pd.concat(df_list, axis=0,ignore_index=True)
    for c in ctxx.columns:
        ctxx.loc[ctxx[c] == '/', c] = ''
    ctxx = ctxx.fillna('')
    ctxx = ctxx[ctxx['状态']!='未上报']
    df = ctxx[ctxx['养殖状态'] == '养殖']
    df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")
    df = df.dropna(subset=["图斑面积"])
    df["养殖品种/预计亩产量"] = df["养殖品种/预计亩产量"].str.replace("乌鳗", "乌鳢", regex=False)
    results = []
    for variety in yzpz:
        # 过滤包含该品种的行
        matched_df = df[df["养殖品种/预计亩产量"].str.contains(variety, na=False)]
        for _, row in matched_df.iterrows():
            text = row["养殖品种/预计亩产量"]
            area = float(row["图斑面积"])
            address = row["地址"]
            # 使用正则表达式提取该品种对应的产量数字
            match = re.search(fr"{variety}:(\d+\.?\d*)斤/亩", text)
            if match:
                yield_per_mu = float(match.group(1))
                total_yield_tons = yield_per_mu * area / 2000  # 斤 -> 吨
                # 解析市和区县
                address_parts = str(address).split("-")
                if len(address_parts) >= 3:
                    city = address_parts[1]
                    district = address_parts[2]
                else:
                    city = "未知市"
                    district = "未知区县"
                results.append({
                    "品种": variety,
                    "市": city,
                    "区县": district,
                    "产量（吨）": total_yield_tons
                })
    # 转换为 DataFrame
    results_df = pd.DataFrame(results)

    # 按市、品种汇总产量
    summary = results_df.groupby(["市", "品种"], as_index=False)["产量（吨）"].sum()

    # 计算每个品种在全省的总产量
    variety_total = summary.groupby("品种", as_index=False)["产量（吨）"].sum().rename(
        columns={"产量（吨）": "全省该品种总产量"})

    # 合并总产量信息到 summary 表
    summary = summary.merge(variety_total, on="品种", how="left")

    # 计算占比并生成描述
    summary["占比"] = summary["产量（吨）"] / summary["全省该品种总产量"]
    summary["产量描述"] = summary.apply(
        lambda row: f"{row['市']}产量{row['产量（吨）']:.2f}吨（{row['占比']:.2%}）", axis=1
    )

    # 保存为 Excel 表格
    summary.to_excel(r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\所有品种产量统计结果（市）.xlsx", index=False)


