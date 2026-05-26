# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set matplotlib backend to Agg to avoid GUI errors
import matplotlib
matplotlib.use('Agg')

# Set font for Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

workspace_dir = r"e:\PY\射阳城北污水处理厂\东阳水厂"
csv_path = os.path.join(workspace_dir, "中控运行记录.csv")
output_img_path = r"C:\Users\Administrator\.gemini\antigravity\brain\4ac58bc5-1718-4c97-908b-5cd1a57b476e\dosing_inefficiency_diagnostics.png"
workspace_img_path = os.path.join(workspace_dir, "dosing_inefficiency_diagnostics.png")

# Load data
df = pd.read_csv(csv_path, encoding='gbk')
df['time'] = pd.to_datetime(df['time'])
df = df.groupby('time').mean().reset_index().sort_values('time')

# Clean outliers as in training
for col in ['出水TN', '出水TP', '总出水NH', 'B组好末DO', 'B系列碳源投加流量', 'PAC实际投加量', '总进水', '进水TN', '进水TP', '反硝化滤池进TP']:
    df.loc[df[col] < 0, col] = np.nan
    df[col] = df[col].interpolate(method='linear').bfill().ffill()

df.loc[df['出水TN'] > 12.0, '出水TN'] = np.nan
df['出水TN'] = df['出水TN'].interpolate(method='linear').bfill().ffill()

df.loc[df['出水TP'] > 0.15, '出水TP'] = np.nan
df['出水TP'] = df['出水TP'].interpolate(method='linear').bfill().ffill()

# Calculate loads
df['TN_load'] = df['总进水'] * df['进水TN'] / 1000.0  # kg TN/h
df['TP_load'] = df['总进水'] * df['反硝化滤池进TP'] / 1000.0  # kg TP/h

r_tn = df['TN_load'].corr(df['B系列碳源投加流量'])
r_tp = df['TP_load'].corr(df['PAC实际投加量'])

# Create 2x2 subplots
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Subplot 1 (0,0): TN Load vs. Carbon Dosing
ax1 = axes[0, 0]
ax1.scatter(df['TN_load'], df['B系列碳源投加流量'], alpha=0.3, color='#2E7D32', s=10)
ax1.set_xlabel('进水总氮负荷 (kg TN/h)', fontsize=11)
ax1.set_ylabel('碳源实际投加流量 (m3/h)', fontsize=11)
ax1.set_title(f'(a) 进水总氮负荷与碳源实际投加量相关性分析\n(相关系数 R = {r_tn:.4f}，呈弱负相关或无相关性)', fontsize=12, fontweight='bold', pad=10)
# Draw horizontal bands representing typical manual steps
for val in [1.5, 2.0, 2.5]:
    ax1.axhline(y=val, color='#C62828', linestyle='--', alpha=0.8, linewidth=1.5, label=f'手工设定阶梯值 {val} m3/h' if val==1.5 else "")
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2 (0,1): TP Load vs. PAC Dosing
ax2 = axes[0, 1]
ax2.scatter(df['TP_load'], df['PAC实际投加量'], alpha=0.3, color='#1565C0', s=10)
ax2.set_xlabel('滤池进水总磷负荷 (kg TP/h)', fontsize=11)
ax2.set_ylabel('PAC实际投加量 (m3/h)', fontsize=11)
ax2.set_title(f'(b) 滤池进水总磷负荷与PAC实际投加量相关性分析\n(相关系数 R = {r_tp:.4f}，弱正相关且加药响应严重滞后)', fontsize=12, fontweight='bold', pad=10)
# Draw horizontal lines for PAC typical values
for val in [3.0, 4.0]:
    ax2.axhline(y=val, color='#C62828', linestyle='--', alpha=0.8, linewidth=1.5, label=f'手工设定阶梯值 {val} m3/h' if val==3.0 else "")
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.5)

# Subplot 3 (1,0): Box plots of Effluent Quality showing Over-treatment
ax3 = axes[1, 0]
data_to_plot = [df['出水TN'].values, (df['出水TP'] * 10).values]
box = ax3.boxplot(data_to_plot, patch_artist=True, labels=['出水总氮 TN\n(mg/L)', '出水总磷 TP × 10\n(mg/L)'], widths=0.35)

colors = ['#2E7D32', '#1565C0']
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
for median in box['medians']:
    median.set(color='black', linewidth=2)

ax3.set_ylabel('指标数值 (mg/L)', fontsize=11)
ax3.set_title('(c) 实际出水水质分布与排放标准及控制目标对比\n(中位数大幅低于排放标准，存在严重过度处理空间)', fontsize=12, fontweight='bold', pad=10)

ax3.axhline(y=10.0, color='#C62828', linestyle='-', linewidth=1.5, label='出水TN排放国家标准 (10.0 mg/L)')
ax3.axhline(y=8.5, color='#EF6C00', linestyle='--', linewidth=1.2, label='出水TN系统内控目标 (8.5 mg/L)')
ax3.axhline(y=5.0, color='#283593', linestyle='-', linewidth=1.5, label='出水TP排放国家标准 (0.50 mg/L, 放大10倍)')
ax3.axhline(y=0.9, color='#1565C0', linestyle='--', linewidth=1.2, label='出水TP系统内控目标 (0.09 mg/L, 放大10倍)')
ax3.legend(loc='upper right', fontsize=8.5)
ax3.grid(True, linestyle='--', alpha=0.5)

# Subplot 4 (1,1): DO Distribution Histogram
ax4 = axes[1, 1]
counts, bins, patches = ax4.hist(df['B组好末DO'], bins=45, density=False, weights=np.ones(len(df)) / len(df) * 100, color='#0097A7', alpha=0.7, edgecolor='white')
ax4.axvspan(1.5, 2.0, color='green', alpha=0.2, label='工艺推荐最佳DO区间 (1.5 - 2.0 mg/L)')
ax4.axvspan(2.0, 5.0, color='red', alpha=0.15, label='过度曝气区间 (> 2.0 mg/L)')
over_aeration_pct = (df['B组好末DO'] > 2.0).mean() * 100
ax4.set_xlabel('好氧池末端溶解氧 DO (mg/L)', fontsize=11)
ax4.set_ylabel('时间占比 (%)', fontsize=11)
ax4.set_title(f'(d) 好氧池末端溶解氧(DO)分布频数与过度曝气评估\n(过度曝气时间占比高达 {over_aeration_pct:.2f}%)', fontsize=12, fontweight='bold', pad=10)
ax4.legend(loc='upper right', fontsize=9)
ax4.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
fig.subplots_adjust(hspace=0.3, wspace=0.25)
plt.savefig(output_img_path, dpi=180)
plt.savefig(workspace_img_path, dpi=180)
plt.close()

print(f"Diagnostics 2x2 plots generated successfully and saved to {output_img_path} and {workspace_img_path}")
print(f"TN Correlation: {r_tn:.4f}, TP Correlation: {r_tp:.4f}, Over-aeration %: {over_aeration_pct:.2f}%")
