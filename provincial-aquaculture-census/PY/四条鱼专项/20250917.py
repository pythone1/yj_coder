# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


font_path = r"C:\Windows\Fonts\simkai.ttf"
my_font = font_manager.FontProperties(fname=font_path)

# ------------------------------
# 2. 读取 Excel 文件
# ------------------------------
file_path = r"E:\渔业\天气直方图.xlsx"   # <-- 改成你的实际路径
df = pd.read_excel(file_path, dtype=str)          # 以字符串读取，避免类型问题

# 检查列是否存在
col = '天气状况'
if col not in df.columns:
    raise KeyError(f"找不到列 '{col}'，请检查你的 Excel 表头：{df.columns.tolist()}")

# 缺失值处理
df[col] = df[col].fillna('未知').astype(str)

# 按天气分组统计
counts = df[col].value_counts()
counts = counts.sort_values(ascending=False)   # 按出现次数排序

# ------------------------------
# 3. 绘制直方图
# ------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(counts))
bars = ax.bar(x, counts.values, color='skyblue', edgecolor='black')

# 横轴
ax.set_xticks(x)
ax.set_xticklabels(counts.index, fontproperties=my_font, fontsize=11)

# 在柱子上方标注数值
for xi, val in zip(x, counts.values):
    ax.text(xi, val + 0.3, str(int(val)),
            ha='center', va='bottom', fontsize=10, fontproperties=my_font)

# 标题和坐标轴
ax.set_title("各类天气状况出现天数统计", fontsize=14, fontweight='bold', fontproperties=my_font)
ax.set_xlabel("天气状况", fontsize=12, fontproperties=my_font)
ax.set_ylabel("天数", fontsize=12, fontproperties=my_font)

# 美化：去掉上、右边框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()

# ------------------------------
# 4. 保存图片
# ------------------------------
output_path = r"E:\渔业\天气直方图统计.png"   # <-- 改成你要保存的路径
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.show()

print(f"图片已保存到：{output_path}")
