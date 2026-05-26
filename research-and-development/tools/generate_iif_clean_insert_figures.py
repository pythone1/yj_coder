from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(r"D:\Users\Downloads\排水管网入渗入流_可插入示意图")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 2000, 1125
FONT = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

BLUE = "#1F86D1"
DEEP = "#0B3F63"
CYAN = "#1BB4D6"
GREEN = "#22A06B"
ORANGE = "#F39A2F"
RED = "#E55252"
GRAY = "#607587"
LIGHT = "#F3FAFF"
LINE = "#BFDCEF"
PIPE = "#579BC7"
WATER = "#1D91D0"


def ft(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def box(d, xy, fill="white", outline=LINE, width=4, r=28):
    d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=width)


def ctext(d, xy, s, size=44, color=DEEP, bold=True, gap=8):
    f = ft(size, bold)
    lines = s.split("\n")
    sizes = [d.textbbox((0, 0), t, font=f) for t in lines]
    ws = [b[2] - b[0] for b in sizes]
    hs = [b[3] - b[1] for b in sizes]
    total = sum(hs) + gap * (len(lines) - 1)
    y = (xy[1] + xy[3] - total) / 2
    for t, w, h in zip(lines, ws, hs):
        d.text(((xy[0] + xy[2] - w) / 2, y), t, font=f, fill=color)
        y += h + gap


def text(d, x, y, s, size=40, color=DEEP, bold=True):
    d.text((x, y), s, font=ft(size, bold), fill=color)


def arrow(d, a, b, color=BLUE, width=9):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    l = 34
    d.polygon([
        b,
        (b[0] - l * math.cos(ang - .45), b[1] - l * math.sin(ang - .45)),
        (b[0] - l * math.cos(ang + .45), b[1] - l * math.sin(ang + .45)),
    ], fill=color)


def canvas():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, W - 20, H - 20), 34, fill=(255, 255, 255, 255), outline=LINE, width=4)
    return img, d


def pipe(d, pts, width=28):
    d.line(pts, fill=PIPE, width=width, joint="curve")
    d.line(pts, fill=WATER, width=max(8, width // 3), joint="curve")


def node(d, x, y, color=GREEN, r=36):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline="white", width=7)


def fig1():
    img, d = canvas()
    text(d, 85, 70, "排水管网 AI 入渗入流诊断", 58)
    pts = [(180, 650), (420, 540), (690, 610), (960, 500), (1250, 610)]
    pipe(d, pts)
    pipe(d, [(420, 540), (455, 820), (770, 845), (960, 500)], 24)
    pipe(d, [(690, 610), (890, 760), (1250, 610)], 24)
    for i, p in enumerate(pts + [(455, 820), (770, 845), (890, 760)]):
        node(d, *p, [GREEN, GREEN, ORANGE, RED, RED, GREEN, ORANGE, GREEN][i])
    box(d, (1380, 260, 1840, 430), LIGHT)
    box(d, (1380, 500, 1840, 670), LIGHT)
    box(d, (1380, 740, 1840, 910), LIGHT)
    ctext(d, (1380, 260, 1840, 430), "监测数据", 48)
    ctext(d, (1380, 500, 1840, 670), "AI 分析", 48)
    ctext(d, (1380, 740, 1840, 910), "风险定位", 48)
    arrow(d, (1250, 610), (1380, 345))
    arrow(d, (1610, 430), (1610, 500))
    arrow(d, (1610, 670), (1610, 740))
    ctext(d, (220, 880, 1160, 1000), "管网拓扑 + 传感器 + 异常区域", 44, GRAY)
    return img


def fig2():
    img, d = canvas()
    text(d, 85, 70, "入渗与入流来源", 58)
    d.rectangle((70, 625, W - 70, H - 70), fill="#EEF3F6")
    d.rectangle((70, 625, W - 70, 710), fill="#D9E5EC")
    pipe(d, [(230, 800), (1760, 800)], 56)
    for x in [420, 830, 1240, 1650]:
        d.rectangle((x - 34, 560, x + 34, 800), fill="#AFC5D4")
        d.ellipse((x - 80, 520, x + 80, 610), fill="#D8E8F2", outline="#849BAA", width=4)
    for x in [720, 1080, 1450]:
        arrow(d, (x, 290), (x, 760), CYAN, 8)
    d.line((500, 770, 650, 600), fill=RED, width=8)
    d.line((520, 800, 700, 630), fill=RED, width=8)
    box(d, (175, 885, 570, 1030), "white")
    box(d, (720, 885, 1115, 1030), "white")
    box(d, (1265, 885, 1660, 1030), "white")
    ctext(d, (175, 885, 570, 1030), "雨水入流", 46)
    ctext(d, (720, 885, 1115, 1030), "地下水入渗", 46)
    ctext(d, (1265, 885, 1660, 1030), "检查井入流", 46)
    text(d, 240, 265, "降雨进入", 42, BLUE)
    text(d, 520, 705, "破损接口", 42, RED)
    return img


def fig3():
    img, d = canvas()
    text(d, 85, 70, "监测数据融合", 58)
    left = [
        ("降雨", BLUE),
        ("水位", CYAN),
        ("流量", GREEN),
        ("水质", ORANGE),
        ("管网拓扑", DEEP),
    ]
    for i, (s, col) in enumerate(left):
        y = 235 + i * 155
        box(d, (110, y, 470, y + 105), "white")
        d.ellipse((145, y + 25, 200, y + 80), fill=col)
        text(d, 235, y + 25, s, 44)
        arrow(d, (470, y + 52), (820, 565), col, 7)
    box(d, (820, 400, 1180, 730), LIGHT, "#9ED0EE", 5)
    ctext(d, (820, 400, 1180, 730), "统一数据集", 54)
    arrow(d, (1180, 565), (1460, 565))
    box(d, (1460, 405, 1850, 725), "white")
    ctext(d, (1460, 405, 1850, 725), "特征工程\n旱天基线\n雨天响应", 46)
    return img


def fig4():
    img, d = canvas()
    text(d, 85, 70, "入渗入流定量分析", 58)
    box(d, (130, 320, 520, 760), "white")
    box(d, (805, 250, 1195, 830), LIGHT, "#9ED0EE", 5)
    box(d, (1480, 320, 1870, 760), "white")
    ctext(d, (130, 320, 520, 760), "旱天\n基准流量", 52)
    ctext(d, (805, 250, 1195, 830), "雨天响应\n分解模型", 56)
    ctext(d, (1480, 320, 1870, 760), "入渗入流\n贡献量", 52)
    arrow(d, (520, 540), (805, 540))
    arrow(d, (1195, 540), (1480, 540))
    d.line((170, 925, 680, 810), fill=BLUE, width=9)
    d.line((170, 970, 680, 960), fill=GREEN, width=9)
    text(d, 220, 1010, "雨天曲线", 38, BLUE)
    text(d, 470, 1010, "旱天基线", 38, GREEN)
    return img


def fig5():
    img, d = canvas()
    text(d, 85, 70, "分区诊断与风险定位", 58)
    zones = [
        (150, 270, 620, 750, "低风险", GREEN),
        (760, 220, 1230, 810, "中风险", ORANGE),
        (1370, 270, 1840, 750, "高风险", RED),
    ]
    for x1, y1, x2, y2, label, col in zones:
        box(d, (x1, y1, x2, y2), "#F8FCFF", col, 6)
        ctext(d, (x1, y1 + 30, x2, y1 + 120), label, 50, col)
        pts = [(x1 + 90, y2 - 130), (x1 + 210, y2 - 220), (x1 + 330, y2 - 145)]
        pipe(d, pts, 22)
        for p in pts:
            node(d, *p, col, 28)
    arrow(d, (620, 510), (760, 510))
    arrow(d, (1230, 510), (1370, 510))
    ctext(d, (440, 865, 1560, 1000), "按监测分区输出核查优先级", 52, DEEP)
    return img


def fig6():
    img, d = canvas()
    text(d, 85, 70, "诊断结果输出", 58)
    cards = [
        ("异常区域", RED),
        ("疑似管段", ORANGE),
        ("风险等级", BLUE),
        ("核查清单", GREEN),
    ]
    for i, (s, col) in enumerate(cards):
        x = 140 + i * 465
        box(d, (x, 285, x + 355, 520), "white", col, 5)
        d.ellipse((x + 130, 345, x + 225, 440), fill=col)
        ctext(d, (x, 555, x + 355, 640), s, 48, col)
    box(d, (220, 780, 1780, 980), LIGHT, "#9ED0EE", 5)
    ctext(d, (220, 780, 1780, 980), "用于现场复核、工程治理和模型更新", 52)
    return img


figures = [
    ("01_排水管网AI入渗入流诊断.png", fig1),
    ("02_入渗与入流来源.png", fig2),
    ("03_监测数据融合.png", fig3),
    ("04_入渗入流定量分析.png", fig4),
    ("05_分区诊断与风险定位.png", fig5),
    ("06_诊断结果输出.png", fig6),
]

for name, maker in figures:
    maker().save(OUT / name)

sheet = Image.new("RGB", (1120, 1080), "white")
sd = ImageDraw.Draw(sheet)
for idx, (name, _) in enumerate(figures):
    im = Image.open(OUT / name).convert("RGB")
    im.thumbnail((520, 292))
    x = 30 + (idx % 2) * 550
    y = 25 + (idx // 2) * 350
    sheet.paste(im, (x, y))
    sd.text((x, y + 300), Path(name).stem, font=ft(26), fill=DEEP)
sheet.save(OUT / "00_总览预览.png", quality=95)

print(OUT)
for name, _ in figures:
    print(OUT / name)
