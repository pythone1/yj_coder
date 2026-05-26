"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: draw.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

# --- 全局样式设置 ---
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(1, figsize=(14, 20))
ax.set_xlim(0, 10)
ax.set_ylim(0, 100)
ax.axis('off')  # 隐藏坐标轴
# 颜色定义
color_stage_bg = '#EAEAF2'
color_input = '#C5E1A5'  # 浅绿色
color_output = '#FFCCBC'  # 浅橙色
color_process = '#BBDEFB'  # 浅蓝色
color_parallel = '#FFF9C4'  # 浅黄色
color_final = '#E1BEE7'  # 浅紫色


# --- 辅助函数：绘制带文字的框 ---
def draw_box(ax, x, y, width, height, text, color=color_process, text_color='black', fontsize=9,
             style="round,pad=0.05"):
	"""绘制一个带文字的圆角矩形框"""
	box = patches.FancyBboxPatch((x, y), width, height, boxstyle=style,
	                             facecolor=color, edgecolor='black', linewidth=1.2)
	ax.add_patch(box)
	ax.text(x + width / 2, y + height / 2, text, ha='center', va='center',
	        fontsize=fontsize, color=text_color, wrap=True)
	return box


# --- 辅助函数：绘制箭头 ---
def draw_arrow(ax, start, end, style="->", lw=1.5, color='black'):
	"""绘制从起点到终点的箭头"""
	arrow = patches.FancyArrowPatch(start, end, connectionstyle="arc3",
	                                arrowstyle=style, lw=lw, color=color, mutation_scale=20)
	ax.add_patch(arrow)
	return arrow


# --- 第一阶段：数据收集与预处理 ---
stage1_y = 80
draw_box(ax, 1, stage1_y + 8, 8, 3, "【输入】\n农业部公告、历史数据、高分辨率卫星影像、规划图件", color_input, fontsize=10)
draw_box(ax, 1, stage1_y, 8, 7, "", color=color_stage_bg)  # 背景框
ax.text(5, stage1_y + 6, "第一阶段：数据收集与预处理 (奠定基础)", ha='center', fontsize=12, weight='bold')
draw_box(ax, 1.5, stage1_y + 4, 7, 1.5, "1. 数据普查与收集", fontsize=10)
draw_box(ax, 1.5, stage1_y + 2, 7, 1.5, "2. 数据标准化与整合 (统一坐标系、影像校正)", fontsize=10)
draw_box(ax, 1.5, stage1_y, 7, 1.5, "3. 构建基础数据库", fontsize=10)
draw_arrow(ax, (5, stage1_y + 7.5), (5, stage1_y + 5.5))
draw_arrow(ax, (5, stage1_y + 4), (5, stage1_y + 3.5))
draw_arrow(ax, (5, stage1_y + 2), (5, stage1_y + 1.5))
draw_box(ax, 1, stage1_y - 2, 8, 2, "【输出】\n标准化基础数据库", color_output, fontsize=10)
draw_arrow(ax, (5, stage1_y), (5, stage1_y - 0.5))
# --- 第二阶段：内业信息提取与上图 (核心内业) ---
stage2_y = 60
draw_box(ax, 1, stage2_y, 8, 15, "", color=color_stage_bg)  # 背景框
ax.text(5, stage2_y + 13.5, "第二阶段：内业信息提取与上图 (核心内业)", ha='center', fontsize=12, weight='bold')
draw_box(ax, 1.5, stage2_y + 11, 7, 1.5, "并行流程", color=color_parallel, fontsize=10)
# 并行流程 A
draw_box(ax, 1.2, stage2_y + 8.5, 3.6, 2, "流程A: 保护区边界勘定", color='white', fontsize=9)
draw_box(ax, 1.2, stage2_y + 6.5, 3.6, 1.5, "公告信息解析", fontsize=8)
draw_box(ax, 1.2, stage2_y + 5, 3.6, 1.5, "多源数据交叉验证", fontsize=8)
draw_box(ax, 1.2, stage2_y + 3.5, 3.6, 1.5, "边界数字化与功能区划分", fontsize=8)
draw_arrow(ax, (3, stage2_y + 9.5), (3, stage2_y + 8))
draw_arrow(ax, (3, stage2_y + 7.5), (3, stage2_y + 6.5))
draw_arrow(ax, (3, stage2_y + 5.75), (3, stage2_y + 5))
# 并行流程 B
draw_box(ax, 5.2, stage2_y + 8.5, 3.6, 2, "流程B: 涉渔工程遥感智能识别", color='white', fontsize=9)
draw_box(ax, 5.2, stage2_y + 6.5, 3.6, 1.5, "建立/优化AI识别模型", fontsize=8)
draw_box(ax, 5.2, stage2_y + 5, 3.6, 1.5, "AI初步解译", fontsize=8)
draw_box(ax, 5.2, stage2_y + 3.5, 3.6, 1.5, "人机交互解译与精修", fontsize=8)
draw_arrow(ax, (7, stage2_y + 9.5), (7, stage2_y + 8))
draw_arrow(ax, (7, stage2_y + 7.5), (7, stage2_y + 6.5))
draw_arrow(ax, (7, stage2_y + 5.75), (7, stage2_y + 5))
draw_box(ax, 1.5, stage2_y + 1, 7, 1.5, "【输出】内业初步成果 (工作底图+工程数据集)", color_output, fontsize=10)
draw_arrow(ax, (3, stage2_y + 4.25), (3, stage2_y + 2.5))  # A流程输出
draw_arrow(ax, (7, stage2_y + 4.25), (7, stage2_y + 2.5))  # B流程输出
draw_arrow(ax, (5, stage2_y + 2.5), (5, stage2_y + 1.75))
# --- 第三阶段：外业抽样核验与数据修正 (闭环验证) ---
stage3_y = 38
draw_box(ax, 1, stage3_y, 8, 12, "", color=color_stage_bg)  # 背景框
ax.text(5, stage3_y + 10.5, "第三阶段：外业抽样核验与数据修正 (闭环验证)", ha='center', fontsize=12, weight='bold')
draw_box(ax, 1.5, stage3_y + 8, 7, 1.5, "1. 抽样方案制定 (抽取13个保护区)", fontsize=10)
draw_box(ax, 1.5, stage3_y + 6, 7, 1.5, "2. 外业现场核验 (GPS定位、拍照、记录)", fontsize=10)
draw_box(ax, 1.5, stage3_y + 4, 7, 1.5, "3. 内业数据修正与完善", fontsize=10)
draw_arrow(ax, (5, stage3_y + 8.75), (5, stage3_y + 7.5))
draw_arrow(ax, (5, stage3_y + 6.75), (5, stage3_y + 5.5))
draw_arrow(ax, (5, stage3_y + 4.75), (5, stage3_y + 4.5))
# 反馈循环
feedback_arrow = patches.FancyArrowPatch((3, stage3_y + 4.5), (7, stage2_y + 5),
                                         connectionstyle="arc3,rad=.4",
                                         arrowstyle="->", lw=2, color='red', mutation_scale=20)
ax.add_patch(feedback_arrow)
ax.text(6.5, stage3_y + 6, "数据反馈\n与修正", ha='center', color='red', fontsize=9, weight='bold')
draw_box(ax, 1, stage3_y + 1.5, 8, 2, "【输出】经过核验的最终矢量数据集", color_output, fontsize=10)
draw_arrow(ax, (5, stage3_y + 4.5), (5, stage3_y + 3))
draw_arrow(ax, (5, stage3_y + 3), (5, stage3_y + 2.5))
# --- 第四阶段：成果汇总与上图入库 (成果交付) ---
stage4_y = 16
draw_box(ax, 1, stage4_y, 8, 15, "", color=color_stage_bg)  # 背景框
ax.text(5, stage4_y + 13.5, "第四阶段：成果汇总与上图入库 (成果交付)", ha='center', fontsize=12, weight='bold')
draw_box(ax, 1.5, stage4_y + 11, 7, 1.5, "1. 数据库建设与上图入库", fontsize=10)
draw_box(ax, 1.5, stage4_y + 9, 7, 1.5, "2. 涉渔工程档案建立", fontsize=10)
draw_box(ax, 1.5, stage4_y + 7, 7, 1.5, "3. 图集与图册编制", fontsize=10)
draw_box(ax, 1.5, stage4_y + 5, 7, 1.5, "4. 总结报告撰写", fontsize=10)
draw_arrow(ax, (5, stage4_y + 11.75), (5, stage4_y + 10.5))
draw_arrow(ax, (5, stage4_y + 9.75), (5, stage4_y + 8.5))
draw_arrow(ax, (5, stage4_y + 7.75), (5, stage4_y + 6.5))
draw_arrow(ax, (5, stage4_y + 5.75), (5, stage4_y + 4.5))
draw_box(ax, 0.5, stage4_y + 1, 9, 3,
         "【最终成果交付】\n- 全省保护区“一张图”数据库\n- 涉渔工程档案库及图册\n- 39个保护区要素信息矢量图集\n- 上图入库总结报告",
         color=color_final, fontsize=10)
draw_arrow(ax, (5, stage4_y + 5), (5, stage4_y + 4))
# --- 阶段间连接箭头 ---
draw_arrow(ax, (5, stage1_y - 2), (5, stage2_y + 14.5))  # 1 -> 2
draw_arrow(ax, (5, stage2_y + 1), (5, stage3_y + 12))  # 2 -> 3
draw_arrow(ax, (5, stage3_y + 1.5), (5, stage4_y + 15))  # 3 -> 4
# 设置标题
plt.title("江苏省水产种质资源保护区“上图入库”项目技术路线图", fontsize=18, weight='bold', pad=20)
plt.tight_layout()
plt.show()