from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(r"D:\Users\Downloads\入渗入流_架构结果汇总图")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 2600, 1500
FONT = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

BLUE = "#2389D7"
DEEP = "#073E63"
TEAL = "#126B7F"
LIGHT = "#EEF8FF"
MID = "#D9F0FF"
GREEN = "#1FA06E"
ORANGE = "#F39A2F"
RED = "#E95757"
GRAY = "#5D7082"
LINE = "#B8D9EE"


def ft(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def box(d, xy, fill="white", outline=LINE, width=4, r=28):
    d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=width)


def ctext(d, xy, s, size=42, color=DEEP, bold=True, gap=8):
    font = ft(size, bold)
    lines = s.split("\n")
    bbs = [d.textbbox((0, 0), t, font=font) for t in lines]
    ws = [b[2] - b[0] for b in bbs]
    hs = [b[3] - b[1] for b in bbs]
    total = sum(hs) + gap * (len(lines) - 1)
    y = (xy[1] + xy[3] - total) / 2
    for t, w, h in zip(lines, ws, hs):
        d.text(((xy[0] + xy[2] - w) / 2, y), t, font=font, fill=color)
        y += h + gap


def text(d, x, y, s, size=42, color=DEEP, bold=True):
    d.text((x, y), s, font=ft(size, bold), fill=color)


def arrow(d, a, b, color=BLUE, width=8):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    l = 32
    d.polygon([
        b,
        (b[0] - l * math.cos(ang - .45), b[1] - l * math.sin(ang - .45)),
        (b[0] - l * math.cos(ang + .45), b[1] - l * math.sin(ang + .45)),
    ], fill=color)


def dot(d, x, y, color, r=20):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline="white", width=5)


def draw_triangle_arch(d):
    tri = [(900, 255), (270, 1215), (1530, 1215)]
    d.polygon(tri, fill=TEAL, outline="#09394D")
    d.line((515, 850, 1285, 850), fill="#D9F0FF", width=6)
    d.line((650, 645, 1150, 645), fill="#D9F0FF", width=6)

    ctext(d, (690, 285, 1110, 410), "模型层", 50, "white")
    ctext(d, (650, 470, 1150, 585), "AI 识别\n入渗入流分解", 42, "white")
    ctext(d, (520, 700, 1280, 815), "特征层：旱天基线 / 雨天响应", 40, "white")
    ctext(d, (420, 970, 1380, 1085), "数据层：降雨 / 水位 / 流量 / 管网拓扑", 40, "white")

    pts = [(510, 1145), (680, 1070), (855, 1130), (1035, 1045), (1230, 1135)]
    d.line(pts, fill="#9DD8F2", width=22, joint="curve")
    d.line(pts, fill=BLUE, width=8, joint="curve")
    for i, (x, y) in enumerate(pts):
        dot(d, x, y, [GREEN, GREEN, ORANGE, RED, RED][i], 23)

    # AI core
    cx, cy = 900, 535
    for i in range(8):
        ang = i * math.pi / 4
        x, y = cx + 85 * math.cos(ang), cy + 85 * math.sin(ang)
        dot(d, x, y, BLUE, 12)
        d.line((cx, cy, x, y), fill="#BDE9FF", width=3)
    dot(d, cx, cy, "#FFFFFF", 18)


def draw_results(d):
    x0, y0 = 1675, 300
    box(d, (x0, y0, 2420, 1195), "white", LINE, 5, 34)
    text(d, x0 + 55, y0 + 45, "诊断结果输出", 56)

    items = [
        ("入渗入流量化", "分解异常增量", BLUE),
        ("异常管段定位", "识别疑似问题区", RED),
        ("风险分区", "高 / 中 / 低等级", ORANGE),
        ("治理核查清单", "支撑现场复核", GREEN),
    ]
    for i, (title, sub, color) in enumerate(items):
        y = y0 + 160 + i * 160
        box(d, (x0 + 65, y, x0 + 675, y + 115), LIGHT, color, 4, 22)
        d.ellipse((x0 + 95, y + 30, x0 + 150, y + 85), fill=color)
        text(d, x0 + 180, y + 20, title, 40, DEEP)
        text(d, x0 + 180, y + 68, sub, 30, GRAY, False)

    # small result chart
    chart = (x0 + 105, y0 + 830, x0 + 635, y0 + 850)
    d.line((x0 + 120, y0 + 805, x0 + 310, y0 + 745, x0 + 500, y0 + 775, x0 + 620, y0 + 700), fill=BLUE, width=8)
    d.rectangle((x0 + 155, y0 + 865, x0 + 215, y0 + 1010), fill=GREEN)
    d.rectangle((x0 + 285, y0 + 815, x0 + 345, y0 + 1010), fill=ORANGE)
    d.rectangle((x0 + 415, y0 + 755, x0 + 475, y0 + 1010), fill=RED)


img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

d.rounded_rectangle((45, 45, W - 45, H - 45), 36, fill="white", outline=LINE, width=4)
text(d, 105, 90, "基于人工智能的排水管网入渗入流定量分析与诊断方法", 60)
text(d, 110, 175, "架构与结果汇总示意", 42, GRAY, False)

draw_triangle_arch(d)
arrow(d, (1530, 735), (1675, 735), BLUE, 10)
draw_results(d)

box(d, (170, 1280, 2430, 1395), LIGHT, "#9ED0EE", 4, 24)
ctext(d, (170, 1280, 2430, 1395), "核心逻辑：多源监测数据 → AI 模型识别 → 入渗入流量化 → 风险定位与核查治理", 44, DEEP)

out = OUT / "01_架构与结果汇总示意.png"
img.save(out, quality=95)
print(out)
