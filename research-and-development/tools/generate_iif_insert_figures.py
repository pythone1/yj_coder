from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(r"D:\Users\Downloads\排水管网入渗入流_AI示意图")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 2400, 1350
FONT = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

BLUE = "#2487D1"
DEEP = "#0A4165"
CYAN = "#19A7CE"
GREEN = "#1E9F72"
ORANGE = "#F39B2F"
RED = "#E85B5B"
TEXT = "#162536"
MUTED = "#5B7083"
LIGHT = "#EEF8FF"
GRID = "#D7E9F5"
PIPE = "#5FA8D3"
WATER = "#2B91D1"


def f(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def rounded(d, box, fill, outline=GRID, width=3, r=28):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def text_center(d, box, text, font, fill=TEXT, spacing=8):
    lines = text.split("\n")
    sizes = [d.textbbox((0, 0), line, font=font) for line in lines]
    heights = [b[3] - b[1] for b in sizes]
    widths = [b[2] - b[0] for b in sizes]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = (box[1] + box[3] - total) / 2
    for line, w, h in zip(lines, widths, heights):
        d.text(((box[0] + box[2] - w) / 2, y), line, font=font, fill=fill)
        y += h + spacing


def arrow(d, a, b, color=BLUE, width=8):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    l = 32
    pts = [
        b,
        (b[0] - l * math.cos(ang - .45), b[1] - l * math.sin(ang - .45)),
        (b[0] - l * math.cos(ang + .45), b[1] - l * math.sin(ang + .45)),
    ]
    d.polygon(pts, fill=color)


def base(title):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill="#F4F9FD", width=1)
    for y in range(0, H, 80):
        d.line((0, y, W, y), fill="#F4F9FD", width=1)
    d.text((90, 58), title, font=f(54, True), fill=DEEP)
    d.line((90, 135, W - 90, 135), fill=BLUE, width=6)
    return img, d


def pipe_network(d, nodes, hot=None):
    hot = set(hot or [])
    for i in range(len(nodes) - 1):
        d.line([nodes[i], nodes[i + 1]], fill=PIPE, width=24)
        d.line([nodes[i], nodes[i + 1]], fill=WATER, width=8)
    branches = [(1, 5), (2, 6), (3, 7)]
    for a, b in branches:
        d.line([nodes[a], nodes[b]], fill=PIPE, width=20)
        d.line([nodes[a], nodes[b]], fill=WATER, width=7)
    for i, (x, y) in enumerate(nodes):
        col = RED if i in hot else ORANGE if i in {2, 6} else GREEN
        d.ellipse((x - 38, y - 38, x + 38, y + 38), fill=col, outline="white", width=6)


def fig1():
    img, d = base("排水管网 AI 诊断总体示意")
    nodes = [(260, 760), (520, 650), (820, 720), (1110, 600), (1420, 700), (560, 930), (920, 980), (1210, 900)]
    rounded(d, (130, 230, 1530, 1160), "#F8FCFF", "#B8D9ED")
    pipe_network(d, nodes, hot=[3, 4])
    rounded(d, (1620, 300, 2220, 520), "white")
    rounded(d, (1620, 620, 2220, 840), "white")
    rounded(d, (1620, 940, 2220, 1160), "white")
    text_center(d, (1620, 300, 2220, 520), "监测数据\n水位 / 流量 / 降雨", f(38, True), DEEP)
    text_center(d, (1620, 620, 2220, 840), "AI 识别模型\n入渗入流分解", f(38, True), DEEP)
    text_center(d, (1620, 940, 2220, 1160), "诊断结果\n异常位置 / 风险等级", f(38, True), DEEP)
    arrow(d, (1530, 570), (1620, 410))
    arrow(d, (1920, 520), (1920, 620))
    arrow(d, (1920, 840), (1920, 940))
    return img


def fig2():
    img, d = base("入渗入流来源示意")
    d.rectangle((0, 660, W, H), fill="#F2F6F8")
    d.rectangle((0, 660, W, 760), fill="#DDE8EE")
    d.line((250, 820, 2150, 820), fill=PIPE, width=56)
    d.line((250, 820, 2150, 820), fill=WATER, width=18)
    for x in [450, 930, 1410, 1880]:
        d.rectangle((x - 35, 620, x + 35, 820), fill="#B5C8D6")
        d.ellipse((x - 80, 570, x + 80, 650), fill="#D9E6ED", outline="#8099AA", width=4)
    for x in [740, 1220, 1680]:
        d.line((x, 350, x, 780), fill=CYAN, width=7)
        d.polygon([(x - 26, 760), (x + 26, 760), (x, 820)], fill=CYAN)
    for x in range(260, 2200, 120):
        d.line((x, 250, x - 22, 310), fill=BLUE, width=5)
    rounded(d, (200, 930, 680, 1110), "white")
    rounded(d, (780, 930, 1260, 1110), "white")
    rounded(d, (1360, 930, 1840, 1110), "white")
    text_center(d, (200, 930, 680, 1110), "雨水错接\n进入污水管", f(36, True), DEEP)
    text_center(d, (780, 930, 1260, 1110), "地下水渗入\n管道破损接口", f(36, True), DEEP)
    text_center(d, (1360, 930, 1840, 1110), "检查井入流\n井盖与井壁缺陷", f(36, True), DEEP)
    d.text((260, 285), "降雨", font=f(34, True), fill=BLUE)
    d.text((990, 860), "污水主干管", font=f(34, True), fill=DEEP)
    return img


def fig3():
    img, d = base("监测数据到诊断结果流程")
    steps = [
        ("数据接入", "降雨、水位、流量、管网拓扑"),
        ("数据治理", "清洗、对齐、缺失补全"),
        ("特征构建", "旱天基线、雨天响应、滞后特征"),
        ("模型识别", "入渗入流分解、异常识别"),
        ("结果输出", "风险区域、核查清单、治理建议"),
    ]
    x, y, bw, bh, gap = 130, 500, 380, 260, 55
    for i, (h, b) in enumerate(steps):
        xx = x + i * (bw + gap)
        rounded(d, (xx, y, xx + bw, y + bh), "white")
        d.ellipse((xx + 30, y + 35, xx + 100, y + 105), fill=BLUE)
        text_center(d, (xx + 30, y + 35, xx + 100, y + 105), str(i + 1), f(34, True), "white")
        d.text((xx + 125, y + 42), h, font=f(36, True), fill=DEEP)
        d.text((xx + 35, y + 135), b, font=f(28), fill=MUTED)
        if i < len(steps) - 1:
            arrow(d, (xx + bw + 8, y + bh / 2), (xx + bw + gap - 8, y + bh / 2), BLUE, 7)
    return img


def fig4():
    img, d = base("AI 模型识别逻辑示意")
    rounded(d, (160, 270, 660, 1080), "white")
    rounded(d, (870, 270, 1530, 1080), LIGHT, "#9ED0EE")
    rounded(d, (1740, 270, 2240, 1080), "white")
    text_center(d, (160, 300, 660, 420), "输入变量", f(42, True), DEEP)
    for i, t in enumerate(["降雨过程", "水位变化", "流量响应", "管网属性", "运行工况"]):
        rounded(d, (245, 465 + i * 105, 575, 535 + i * 105), "#F8FCFF")
        text_center(d, (245, 465 + i * 105, 575, 535 + i * 105), t, f(30, True), TEXT)
    text_center(d, (870, 315, 1530, 460), "AI 诊断模型", f(46, True), DEEP)
    for i, t in enumerate(["时序预测", "异常检测", "贡献分解", "风险评分"]):
        d.ellipse((1010 + i * 115, 650, 1100 + i * 115, 740), fill=[BLUE, CYAN, ORANGE, RED][i])
        text_center(d, (970 + i * 115, 780, 1140 + i * 115, 850), t, f(27, True), TEXT)
    text_center(d, (1740, 300, 2240, 420), "模型输出", f(42, True), DEEP)
    for i, t in enumerate(["入渗入流量化", "异常管段定位", "风险等级判断", "治理优先级"]):
        rounded(d, (1815, 500 + i * 120, 2165, 580 + i * 120), "#F8FCFF")
        text_center(d, (1815, 500 + i * 120, 2165, 580 + i * 120), t, f(30, True), TEXT)
    arrow(d, (660, 675), (870, 675))
    arrow(d, (1530, 675), (1740, 675))
    return img


def fig5():
    img, d = base("管网异常风险定位示意")
    rounded(d, (160, 250, 2240, 1140), "#F8FCFF", "#B8D9ED")
    nodes = [(350, 720), (640, 610), (920, 690), (1220, 540), (1510, 670), (1800, 810), (620, 920), (1020, 1010), (1450, 960)]
    pipe_network(d, nodes, hot=[3, 5])
    d.rounded_rectangle((1150, 465, 1420, 555), 20, fill="#FFEDED", outline=RED, width=4)
    text_center(d, (1150, 465, 1420, 555), "高风险", f(34, True), RED)
    d.rounded_rectangle((1690, 735, 1970, 825), 20, fill="#FFEDED", outline=RED, width=4)
    text_center(d, (1690, 735, 1970, 825), "疑似入流", f(34, True), RED)
    legend = [("正常", GREEN), ("关注", ORANGE), ("异常", RED)]
    for i, (t, c) in enumerate(legend):
        x = 1740 + i * 160
        d.ellipse((x, 1010, x + 40, 1050), fill=c)
        d.text((x + 52, 1008), t, font=f(28, True), fill=TEXT)
    return img


def fig6():
    img, d = base("模型结果可视化看板示意")
    rounded(d, (130, 230, 2270, 1160), "#F8FCFF", "#B8D9ED")
    cards = [
        (220, 330, 680, 560, "入渗入流识别", "识别雨天异常增量"),
        (760, 330, 1220, 560, "异常区域定位", "输出重点核查片区"),
        (1300, 330, 1760, 560, "风险等级判断", "区分高、中、低风险"),
        (1840, 330, 2180, 560, "治理建议", "形成工程核查方向"),
    ]
    for x1, y1, x2, y2, h, b in cards:
        rounded(d, (x1, y1, x2, y2), "white")
        d.text((x1 + 35, y1 + 38), h, font=f(34, True), fill=DEEP)
        d.text((x1 + 35, y1 + 112), b, font=f(28), fill=MUTED)
    d.line((280, 930, 1030, 720), fill=BLUE, width=8)
    d.line((280, 995, 1030, 910), fill=GREEN, width=8)
    d.text((280, 670), "流量响应曲线", font=f(34, True), fill=DEEP)
    for i, c in enumerate([GREEN, ORANGE, RED]):
        d.rectangle((1260 + i * 180, 970 - i * 110, 1390 + i * 180, 1030), fill=c)
    d.text((1240, 670), "风险分布结果", font=f(34, True), fill=DEEP)
    d.ellipse((1870, 790, 2110, 1030), outline=BLUE, width=26)
    d.arc((1870, 790, 2110, 1030), 205, 335, fill=RED, width=26)
    d.text((1830, 670), "诊断置信度", font=f(34, True), fill=DEEP)
    return img


def fig7():
    img, d = base("诊断成果应用闭环示意")
    items = [
        ("监测预警", "发现异常水量"),
        ("模型诊断", "识别入渗入流来源"),
        ("现场核查", "确认问题井段"),
        ("工程治理", "修复缺陷与错接"),
        ("效果评估", "回灌数据优化模型"),
    ]
    center = (1200, 720)
    r = 390
    pts = []
    for i in range(len(items)):
        ang = -math.pi / 2 + i * 2 * math.pi / len(items)
        pts.append((center[0] + r * math.cos(ang), center[1] + r * math.sin(ang)))
    for i in range(len(pts)):
        arrow(d, pts[i], pts[(i + 1) % len(pts)], "#80BDE0", 7)
    d.ellipse((center[0] - 190, center[1] - 190, center[0] + 190, center[1] + 190), fill=LIGHT, outline=BLUE, width=6)
    text_center(d, (center[0] - 170, center[1] - 120, center[0] + 170, center[1] + 120), "AI 辅助\n排水管网诊断", f(38, True), DEEP)
    for (h, b), (x, y) in zip(items, pts):
        rounded(d, (x - 185, y - 90, x + 185, y + 90), "white")
        text_center(d, (x - 170, y - 70, x + 170, y - 15), h, f(30, True), DEEP)
        text_center(d, (x - 170, y + 0, x + 170, y + 60), b, f(24), MUTED)
    return img


def fig8():
    img, d = base("入渗入流定量分析输出示意")
    rounded(d, (150, 270, 2250, 1110), "white", "#B8D9ED")
    sections = [
        ("定量结果", ["雨天异常增量", "旱天基准流量", "入渗入流占比"]),
        ("空间结果", ["异常检查井", "疑似问题管段", "重点汇水片区"]),
        ("诊断结果", ["主要来源判断", "风险等级划分", "现场核查顺序"]),
    ]
    for i, (h, rows) in enumerate(sections):
        x = 260 + i * 690
        rounded(d, (x, 390, x + 560, 970), "#F8FCFF")
        d.rectangle((x, 390, x + 560, 470), fill=[BLUE, GREEN, ORANGE][i])
        text_center(d, (x, 390, x + 560, 470), h, f(36, True), "white")
        for j, row in enumerate(rows):
            yy = 550 + j * 125
            d.ellipse((x + 60, yy, x + 110, yy + 50), fill=[BLUE, GREEN, ORANGE][i])
            d.text((x + 140, yy + 4), row, font=f(31, True), fill=TEXT)
    arrow(d, (820, 690), (950, 690))
    arrow(d, (1510, 690), (1640, 690))
    return img


figs = [
    ("01_排水管网AI诊断总体示意.png", fig1),
    ("02_入渗入流来源示意.png", fig2),
    ("03_监测数据到诊断结果流程.png", fig3),
    ("04_AI模型识别逻辑示意.png", fig4),
    ("05_管网异常风险定位示意.png", fig5),
    ("06_模型结果可视化看板示意.png", fig6),
    ("07_诊断成果应用闭环示意.png", fig7),
    ("08_入渗入流定量分析输出示意.png", fig8),
]

for name, make in figs:
    make().save(OUT / name, quality=95)

thumbs = []
for name, _ in figs:
    im = Image.open(OUT / name).convert("RGB")
    im.thumbnail((520, 292))
    thumbs.append((name, im.copy()))
sheet = Image.new("RGB", (1160, 1400), "white")
d = ImageDraw.Draw(sheet)
for idx, (name, im) in enumerate(thumbs):
    x = 40 + (idx % 2) * 560
    y = 30 + (idx // 2) * 335
    sheet.paste(im, (x, y))
    d.text((x, y + 300), Path(name).stem, font=f(24), fill=TEXT)
sheet.save(OUT / "00_总览预览.png", quality=95)

print(OUT)
for name, _ in figs:
    print(OUT / name)
