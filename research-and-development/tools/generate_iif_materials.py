from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(r"D:\Users\Downloads\排水管网技术方案_具体内容素材")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 2560, 1440

BLUE = "#2F8ED8"
DEEP = "#0E4F78"
TEAL = "#126B7F"
LIGHT = "#EAF5FF"
GRID = "#D9EAF6"
TEXT = "#152536"
MUTED = "#5E7488"
GREEN = "#22A071"
ORANGE = "#F39C35"
RED = "#E85D5D"

FONT_REG = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]


def rounded(draw, box, fill, outline=None, width=2, r=22):
    draw.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def center_text(draw, box, s, f, fill=TEXT, spacing=8):
    lines = s.split("\n")
    sizes = [text_size(draw, line, f) for line in lines]
    total_h = sum(h for _, h in sizes) + spacing * (len(lines) - 1)
    y = (box[1] + box[3] - total_h) / 2
    for line, (tw, th) in zip(lines, sizes):
        x = (box[0] + box[2] - tw) / 2
        draw.text((x, y), line, font=f, fill=fill)
        y += th + spacing


def draw_wrapped(draw, xy, text, f, fill=TEXT, max_width=520, line_gap=12):
    x, y = xy
    line = ""
    for ch in text:
        test = line + ch
        if text_size(draw, test, f)[0] <= max_width:
            line = test
        else:
            draw.text((x, y), line, font=f, fill=fill)
            y += f.size + line_gap
            line = ch
    if line:
        draw.text((x, y), line, font=f, fill=fill)
    return y + f.size


def arrow(draw, start, end, color=BLUE, width=8):
    draw.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    l = 28
    pts = [
        end,
        (end[0] - l * math.cos(ang - 0.45), end[1] - l * math.sin(ang - 0.45)),
        (end[0] - l * math.cos(ang + 0.45), end[1] - l * math.sin(ang + 0.45)),
    ]
    draw.polygon(pts, fill=color)


def draw_check(draw, box, color="white", width=8):
    x1, y1, x2, y2 = box
    p1 = (x1 + (x2 - x1) * 0.28, y1 + (y2 - y1) * 0.55)
    p2 = (x1 + (x2 - x1) * 0.44, y1 + (y2 - y1) * 0.72)
    p3 = (x1 + (x2 - x1) * 0.74, y1 + (y2 - y1) * 0.34)
    draw.line([p1, p2, p3], fill=color, width=width, joint="curve")


def base(title, subtitle):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for x in range(0, W, 80):
        d.line([(x, 230), (x, H)], fill="#F2F7FB", width=1)
    for y in range(250, H, 80):
        d.line([(0, y), (W, y)], fill="#F2F7FB", width=1)
    d.rectangle((0, 0, W, 150), fill="white")
    d.text((140, 54), "02", font=font(82, True), fill=BLUE)
    d.text((295, 54), "技术方案", font=font(58, True), fill=BLUE)
    d.text((302, 120), "Technical scheme", font=font(30), fill=MUTED)
    d.rectangle((130, 190, W - 130, 295), fill=BLUE)
    d.text((170, 213), title, font=font(48, True), fill="white")
    d.text((170, 318), subtitle, font=font(34, True), fill=TEXT)
    return img, d


def tag(draw, xy, s, color=BLUE):
    x, y = xy
    tw, th = text_size(draw, s, font(28, True))
    rounded(draw, (x, y, x + tw + 42, y + 54), "#FFFFFF", color, 3, 16)
    draw.text((x + 21, y + 8), s, font=font(28, True), fill=color)


def page_1():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "技术路线总览")
    steps = [
        ("多源数据接入", "雨量、水位、流量、水质、泵站运行、管网拓扑"),
        ("数据治理", "异常清洗、时间对齐、缺失补全、工况标记"),
        ("特征构建", "旱天基线、雨天响应、滞后时长、峰值增量"),
        ("模型识别", "入渗入流分解、异常管段定位、风险评分"),
        ("诊断应用", "治理优先级、工程核查清单、调度优化建议"),
    ]
    x0, y, gap, bw, bh = 180, 520, 46, 410, 250
    for i, (h, b) in enumerate(steps):
        x = x0 + i * (bw + gap)
        rounded(d, (x, y, x + bw, y + bh), "white", GRID, 4, 28)
        d.ellipse((x + 28, y + 28, x + 86, y + 86), fill=BLUE)
        center_text(d, (x + 28, y + 28, x + 86, y + 86), str(i + 1), font(30, True), "white")
        d.text((x + 110, y + 36), h, font=font(34, True), fill=DEEP)
        draw_wrapped(d, (x + 34, y + 118), b, font(26), MUTED, max_width=bw - 68)
        if i < len(steps) - 1:
            arrow(d, (x + bw + 8, y + bh // 2), (x + bw + gap - 10, y + bh // 2), BLUE, 6)
    rounded(d, (260, 900, 2300, 1195), LIGHT, "#B9D9EF", 3, 26)
    d.text((320, 940), "核心输出", font=font(38, True), fill=DEEP)
    outputs = ["入渗入流量化结果", "异常来源识别", "重点管段清单", "风险分区图", "治理优先级"]
    for i, s in enumerate(outputs):
        x = 575 + i * 325
        d.ellipse((x, 1000, x + 76, 1076), fill=[GREEN, BLUE, ORANGE, RED, TEAL][i])
        draw_check(d, (x, 1000, x + 76, 1076), "white", 8)
        d.text((x - 70, 1100), s, font=font(28, True), fill=TEXT)
    return img


def page_2():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "排水管网数据输入与融合")
    left = (170, 420, 1060, 1180)
    right = (1500, 420, 2390, 1180)
    rounded(d, left, "#F8FCFF", "#B9D9EF", 4, 26)
    rounded(d, right, "#F8FCFF", "#B9D9EF", 4, 26)
    d.text((220, 460), "输入数据", font=font(42, True), fill=DEEP)
    data = [
        ("监测数据", "水位、流量、雨量、液位、泵站启停"),
        ("管网资料", "管径、坡度、埋深、检查井、汇水分区"),
        ("运行数据", "泵站工况、闸门状态、溢流记录"),
        ("外部数据", "降雨预报、地形高程、道路与河道"),
    ]
    y = 545
    for h, b in data:
        d.rounded_rectangle((240, y, 980, y + 120), 18, fill="white", outline=GRID, width=3)
        d.rectangle((240, y, 254, y + 120), fill=BLUE)
        d.text((285, y + 18), h, font=font(31, True), fill=DEEP)
        d.text((285, y + 68), b, font=font(25), fill=MUTED)
        y += 150
    d.text((1550, 460), "融合结果", font=font(42, True), fill=DEEP)
    res = [
        "统一时间序列库",
        "监测点-管段映射关系",
        "降雨事件样本集",
        "旱天基准流量曲线",
        "异常工况标记库",
    ]
    for i, s in enumerate(res):
        yy = 555 + i * 110
        d.ellipse((1570, yy, 1618, yy + 48), fill=GREEN)
        draw_check(d, (1570, yy, 1618, yy + 48), "white", 6)
        d.text((1645, yy + 4), s, font=font(31, True), fill=TEXT)
    for i in range(4):
        arrow(d, (1060, 555 + i * 150), (1500, 610 + i * 110), BLUE, 6)
    tag(d, (1120, 755), "清洗")
    tag(d, (1165, 850), "对齐")
    tag(d, (1210, 945), "融合")
    return img


def page_3():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "AI 入渗入流识别模型")
    cx, cy = 1250, 780
    levels = [
        ((520, 1000), (1980, 1000), (1780, 1180), (720, 1180), "基础层：旱天基线与雨天响应样本"),
        ((680, 760), (1820, 760), (1600, 960), (900, 960), "特征层：峰值、滞后、衰减、持续时间"),
        ((850, 520), (1650, 520), (1450, 720), (1050, 720), "模型层：时序预测 + 异常分解 + 风险评分"),
    ]
    colors = ["#DFF2FF", "#BEE4FA", "#79C4EA"]
    for pts, col in zip(levels, colors):
        poly = pts[:4]
        d.polygon(poly, fill=col, outline=DEEP)
        center_text(d, (poly[0][0], poly[0][1], poly[1][0], poly[2][1]), pts[4], font(32, True), TEXT)
    d.polygon([(1040, 430), (1460, 430), (1360, 510), (1140, 510)], fill=BLUE, outline=DEEP)
    center_text(d, (1040, 430, 1460, 510), "目标：识别入渗入流来源与贡献量", font(30, True), "white")
    side = [
        ("输入", "降雨过程\n管网拓扑\n监测序列"),
        ("训练", "样本切片\n参数校准\n交叉验证"),
        ("输出", "异常概率\n贡献率\n风险等级"),
    ]
    xs = [230, 220, 2040]
    ys = [540, 860, 700]
    for (h, b), x, y in zip(side, xs, ys):
        rounded(d, (x, y, x + 330, y + 220), "white", GRID, 4, 24)
        d.text((x + 35, y + 25), h, font=font(35, True), fill=BLUE)
        d.text((x + 35, y + 86), b, font=font(28), fill=TEXT, spacing=12)
    arrow(d, (560, 650), (760, 690), BLUE, 6)
    arrow(d, (550, 965), (740, 1045), BLUE, 6)
    arrow(d, (1820, 820), (2040, 810), BLUE, 6)
    return img


def page_4():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "模型结果看板")
    cards = [
        (170, 440, 760, 720, "入渗入流总量", "32h 事件累计", "18.6 万 m³", BLUE),
        (830, 440, 1420, 720, "峰值贡献率", "降雨峰后 2.5h", "41.8%", GREEN),
        (1490, 440, 2080, 720, "异常管段", "高风险优先核查", "12 处", ORANGE),
    ]
    for x1, y1, x2, y2, h, sub, val, col in cards:
        rounded(d, (x1, y1, x2, y2), "white", GRID, 4, 28)
        d.text((x1 + 40, y1 + 35), h, font=font(35, True), fill=DEEP)
        d.text((x1 + 40, y1 + 92), sub, font=font(25), fill=MUTED)
        d.text((x1 + 40, y1 + 155), val, font=font(64, True), fill=col)
    rounded(d, (170, 810, 1180, 1220), "#F8FCFF", "#B9D9EF", 4, 28)
    d.text((220, 850), "时间序列拟合结果", font=font(36, True), fill=DEEP)
    pts1, pts2 = [], []
    for i in range(15):
        x = 260 + i * 58
        pts1.append((x, 1110 - int(110 * math.sin(i / 2.2)) - i * 5))
        pts2.append((x, 1130 - int(80 * math.sin(i / 2.0 + .6)) - i * 3))
    d.line(pts1, fill=BLUE, width=8)
    d.line(pts2, fill=GREEN, width=8)
    d.text((930, 875), "实测流量", font=font(24), fill=BLUE)
    d.text((930, 918), "模型预测", font=font(24), fill=GREEN)
    rounded(d, (1280, 810, 2390, 1220), "#F8FCFF", "#B9D9EF", 4, 28)
    d.text((1330, 850), "诊断结论", font=font(36, True), fill=DEEP)
    items = [
        ("高风险区域", "老旧合流管段、低洼汇水片区"),
        ("主要诱因", "雨天外水进入、地下水持续渗入"),
        ("建议措施", "优先排查 12 处节点，复核 4 条主干管"),
    ]
    y = 930
    for h, b in items:
        d.ellipse((1340, y + 6, 1382, y + 48), fill=BLUE)
        d.text((1405, y), h, font=font(29, True), fill=TEXT)
        d.text((1600, y), b, font=font(29), fill=MUTED)
        y += 82
    return img


def page_5():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "异常溯源与风险分区")
    rounded(d, (180, 430, 1450, 1190), "#F8FCFF", "#B9D9EF", 4, 28)
    d.text((240, 470), "管网风险分布示意", font=font(38, True), fill=DEEP)
    nodes = [(420, 700), (650, 610), (910, 690), (1150, 580), (1230, 850), (890, 980), (610, 920)]
    for a, b in zip(nodes, nodes[1:]):
        d.line([a, b], fill="#74B6E0", width=14)
    d.line([nodes[0], nodes[-1]], fill="#74B6E0", width=14)
    for i, (x, y) in enumerate(nodes):
        col = RED if i in (2, 4) else ORANGE if i in (1, 5) else GREEN
        d.ellipse((x - 38, y - 38, x + 38, y + 38), fill=col, outline="white", width=5)
    d.rounded_rectangle((975, 640, 1215, 735), 18, fill="#FFECEC", outline=RED, width=3)
    d.text((1002, 665), "重点核查区", font=font(30, True), fill=RED)
    rounded(d, (1540, 430, 2380, 1190), "white", GRID, 4, 28)
    d.text((1600, 470), "溯源判断", font=font(38, True), fill=DEEP)
    rows = [
        ("现象", "雨后流量持续高位，退水时间偏长"),
        ("判断", "外水入流与地下水渗入叠加"),
        ("位置", "上游支管、老旧接口、低洼检查井"),
        ("优先级", "红色区域先核查，黄色区域复测"),
        ("成果", "形成问题清单与治理排序"),
    ]
    y = 555
    for h, b in rows:
        rounded(d, (1600, y, 2310, y + 92), "#F8FCFF", "#D9EAF6", 2, 16)
        d.text((1630, y + 24), h, font=font(28, True), fill=BLUE)
        d.text((1745, y + 24), b, font=font(28), fill=TEXT)
        y += 118
    return img


def page_6():
    img, d = base("2. 基于人工智能的排水管网入渗入流定量分析与诊断方法", "诊断成果应用闭环")
    cx, cy, r = 1280, 780, 390
    items = [
        ("监测预警", "识别异常水量波动", 1280, 410, BLUE),
        ("现场核查", "定位问题井段", 1730, 780, ORANGE),
        ("工程治理", "修复错接破损渗漏", 1280, 1150, GREEN),
        ("模型更新", "回灌治理效果数据", 830, 780, TEAL),
    ]
    for i in range(len(items)):
        x1, y1 = items[i][2], items[i][3]
        x2, y2 = items[(i + 1) % len(items)][2], items[(i + 1) % len(items)][3]
        arrow(d, (x1, y1), (x2, y2), "#8FC6E8", 7)
    d.ellipse((cx - 230, cy - 230, cx + 230, cy + 230), fill=LIGHT, outline=BLUE, width=6)
    center_text(d, (cx - 200, cy - 170, cx + 200, cy + 170), "持续优化\n排水系统运行", font(42, True), DEEP)
    for h, b, x, y, col in items:
        rounded(d, (x - 220, y - 105, x + 220, y + 105), "white", GRID, 4, 28)
        d.ellipse((x - 190, y - 72, x - 122, y - 4), fill=col)
        d.text((x - 95, y - 72), h, font=font(34, True), fill=DEEP)
        d.text((x - 185, y + 18), b, font=font(26), fill=MUTED)
    rounded(d, (270, 1210, 2290, 1325), "#F8FCFF", "#B9D9EF", 3, 22)
    d.text((330, 1242), "交付成果：入渗入流量化报告、异常管段清单、风险分区图、治理优先级、运行调度建议", font=font(32, True), fill=TEXT)
    return img


pages = [page_1, page_2, page_3, page_4, page_5, page_6]
names = [
    "01_技术路线总览.png",
    "02_数据输入与融合.png",
    "03_AI入渗入流识别模型.png",
    "04_模型结果看板.png",
    "05_异常溯源与风险分区.png",
    "06_诊断成果应用闭环.png",
]

for fn, name in zip(pages, names):
    img = fn()
    img.save(OUT / name, quality=95)

thumbs = []
for name in names:
    im = Image.open(OUT / name).convert("RGB")
    im.thumbnail((720, 405))
    thumbs.append((name, im.copy()))

sheet = Image.new("RGB", (1500, 1400), "white")
sd = ImageDraw.Draw(sheet)
for idx, (name, im) in enumerate(thumbs):
    x = 40 + (idx % 2) * 730
    y = 40 + (idx // 2) * 450
    sheet.paste(im, (x, y))
    sd.text((x, y + 412), Path(name).stem, font=font(30), fill=TEXT)
sheet.save(OUT / "00_总览预览.png", quality=95)

print(str(OUT))
print(str(OUT / "00_总览预览.png"))
for name in names:
    print(str(OUT / name))
