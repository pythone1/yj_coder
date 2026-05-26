import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================
# 中文 & 符号
# =====================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# =====================
# 路径
# =====================
area_file = r"E:\哨兵影像\20251229\片区1统计.xlsx"
water_file = r"E:\哨兵影像\20251229\片区1自动站监测数据 .xls"
out_dir = r"E:\PIC\PIC"

# =====================
# 1. 读取
# =====================
area_df = pd.read_excel(area_file)
water_df = pd.read_excel(water_file)

# =====================
# 2. 面积表（月尺度，缺失补 0）
# =====================
area_df["year_month"] = pd.to_datetime(area_df["year_month"], errors="coerce")
area_df["total_area"] = pd.to_numeric(area_df["total_area"], errors="coerce")
area_df = area_df.dropna(subset=["year_month"])

area_df["month"] = area_df["year_month"].dt.to_period("M").dt.to_timestamp()

# 补全月份
full_months = pd.date_range(
    start=area_df["month"].min(),
    end=area_df["month"].max(),
    freq="MS"
)

area_month = (
    area_df
    .set_index("month")
    .reindex(full_months)
    .fillna({"total_area": 0})
    .reset_index()
    .rename(columns={"index": "month"})
)

# =====================
# 3. 自动站基础时间清洗（一次即可）
# =====================
water_df["监测时间"] = pd.to_datetime(water_df["监测时间"], errors="coerce")
water_df = water_df.dropna(subset=["监测时间"])

# =====================
# 4. 作图函数（逐指标单独清洗）
# =====================
def plot_area_vs_index(index_col, save_name):

    # ---- 针对“单个指标”的独立清洗
    df = water_df[["监测时间", index_col]].copy()

    # 去掉各种 "-"
    df[index_col] = (
        df[index_col]
        .astype(str)
        .replace(["-", "–", "—", ""], np.nan)
    )

    # 强制转数值
    df[index_col] = pd.to_numeric(df[index_col], errors="coerce")

    # 去空
    df = df.dropna(subset=[index_col])

    if df.empty:
        print(f"⚠️ {index_col} 无有效数据，跳过")
        return

    # =====================
    # 作图
    # =====================
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # ---- 左轴：面积（月柱状图）
    ax1.bar(
        area_month["month"],
        area_month["total_area"],
        width=20,
        alpha=0.6,
        label="面积（亩）"
    )
    ax1.set_ylabel("排水面积（亩）")

    # ---- 右轴：水质（原始自动站数据）
    ax2 = ax1.twinx()
    ax2.plot(
        df["监测时间"],
        df[index_col],
        linewidth=1.5,
        label=index_col
    )
    ax2.set_ylabel(index_col)

    # ---- X 轴：只显示月份
    ax1.set_xticks(area_month["month"])
    ax1.set_xticklabels(
        area_month["month"].dt.strftime("%Y-%m"),
        rotation=45
    )

    ax1.set_xlabel("年月")
    ax1.set_title(f"排水面积 与 {index_col}")

    # ---- 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    plt.savefig(f"{out_dir}\\{save_name}.png", dpi=300)
    plt.close()

# =====================
# 5. 批量绘图
# =====================
plot_area_vs_index("浊度(NTU)", "排水面积_浊度")
plot_area_vs_index("溶解氧(mg/L)", "排水面积_溶解氧")
plot_area_vs_index("高锰酸盐指数(mg/L)", "排水面积_高锰酸盐指数")
plot_area_vs_index("氨氮(mg/L)", "排水面积_氨氮")
plot_area_vs_index("总磷(mg/L)", "排水面积_总磷")
plot_area_vs_index("总氮(mg/L)", "排水面积_总氮")

print("✅ 图件生成完成（逐指标清洗，原始自动站数据）")
