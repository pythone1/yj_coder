from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


W, H = 2626, 1600
OUT = Path(r"D:\Users\Downloads\smart_water_corrected_cn.png")
FONT_REG = r"C:\Windows\Fonts\simhei.ttf"
FONT_BOLD = r"C:\Windows\Fonts\simhei.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


img = Image.new("RGB", (W, H), "#061421")
d = ImageDraw.Draw(img)

for y in range(H):
    d.line(
        [(0, y), (W, y)],
        fill=(4 + int(3 * y / H), 14 + int(15 * y / H), 28 + int(35 * y / H)),
    )
for x in range(0, W, 80):
    d.line([(x, 150), (x, H - 100)], fill=(20, 55, 85), width=1)
for y in range(160, H - 100, 80):
    d.line([(0, y), (W, y)], fill=(15, 45, 70), width=1)

WHITE = (245, 250, 255)
MUTED = (190, 215, 235)
GREEN = (111, 205, 110)
BLUE = (67, 150, 255)
CYAN = (110, 220, 255)


def rr(xy, r, outline, fill, width=3):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def tc(x, y, s, f, fill=WHITE):
    b = d.textbbox((0, 0), s, font=f)
    d.text((x - (b[2] - b[0]) / 2, y - (b[3] - b[1]) / 2), s, font=f, fill=fill)


def label(x, y, s, color=CYAN):
    tw = d.textlength(s, font=font(24, True))
    rr((x, y, x + tw + 28, y + 42), 10, color, (5, 35, 45), 2)
    d.text((x + 14, y + 6), s, font=font(24, True), fill=WHITE)


def bullet_list(x, y, title, items, color, w=210, h=None):
    if h is None:
        h = 52 + len(items) * 42
    rr((x, y, x + w, y + h), 14, color, (8, 35, 35) if color == GREEN else (7, 27, 55), 2)
    d.text((x + 20, y + 18), title, font=font(30, True), fill=WHITE)
    yy = y + 68
    for it in items:
        d.ellipse((x + 22, yy + 11, x + 30, yy + 19), fill=color)
        d.text((x + 45, yy), it, font=font(24), fill=WHITE)
        yy += 42


def panel_title(x1, y1, x2, title, subtitle, color):
    rr((x1 + 300, y1 - 5, x2 - 230, y1 + 95), 18, color, (5, 25, 35), 3)
    tc((x1 + x2) / 2, y1 + 30, title, font(42, True))
    tc((x1 + x2) / 2, y1 + 72, subtitle, font(24, True), MUTED)


tc(W / 2, 54, "一厂一网 · 智慧水务系统全景图", font(62, True))
tc(W / 2, 125, "全面感知 · 智能决策 · 精准控制 · 低碳运行 · 韧性保障", font(30))

left = (0, 155, 1045, 1285)
center = (1075, 200, 1518, 1270)
right = (1530, 155, 2620, 1285)
rr(left, 28, GREEN, (4, 38, 24), 5)
rr(center, 28, (50, 130, 230), (4, 20, 42), 4)
rr(right, 28, BLUE, (4, 24, 55), 5)
panel_title(left[0], 170, left[2], "污水管网（感知神经系统）", "全域感知 · 智能诊断 · 精准养护", GREEN)
panel_title(right[0], 170, right[2], "污水处理厂（智慧中枢系统）", "精准控制 · 提质增效 · 低碳运行", BLUE)

bullet_list(18, 240, "感知层", ["液位监测", "流量监测", "水质监测", "气体监测", "视频监控", "井盖监测", "管道结构监测"], GREEN, 190, 370)
bullet_list(18, 650, "应用层", ["管网健康评估", "溢流污染监测", "内涝风险预警", "管道病害诊断", "养护计划优化"], GREEN, 220, 335)
bullet_list(18, 1035, "运维层", ["巡检调度", "工事管理", "养护作业", "绩效考核"], GREEN, 190, 250)

cx, cy = 510, 600
for x, y, t in [(360, 320, "居民区"), (330, 805, "商业区"), (690, 820, "工业园区"), (445, 930, "污水提升泵站")]:
    rr((x - 85, y - 45, x + 85, y + 45), 12, (70, 110, 90), (25, 55, 50), 2)
    tc(x, y, t, font(24, True))
nodes = [(410, 420), (640, 420), (345, 600), (690, 600), (520, 780), (520, 1045)]
for nx, ny in nodes:
    d.line([(cx, cy), (nx, ny)], fill=(102, 150, 120), width=18)
    d.line([(cx, cy), (nx, ny)], fill=(160, 205, 210), width=8)
    d.ellipse((nx - 22, ny - 22, nx + 22, ny + 22), fill=(35, 95, 95), outline=WHITE, width=2)
d.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), fill=(40, 110, 110), outline=WHITE, width=3)
tc(cx, cy, "泵站", font(22, True))
for y in range(650, 1180, 80):
    d.line([(cx, y), (cx, y + 60)], fill=(160, 205, 210), width=12)
d.rectangle((cx - 30, 1160, cx + 30, 1215), fill=(50, 130, 170), outline=WHITE, width=2)
d.arc((410, 1190, 610, 1285), 0, 180, fill=(80, 220, 255), width=4)
rr((360, 895, 530, 985), 12, (70, 110, 90), (25, 55, 50), 2)
tc(445, 940, "污水提升泵站", font(24, True))
for args in [
    (285, 410, "流量监测"),
    (635, 462, "水质监测"),
    (260, 505, "液位监测"),
    (700, 570, "气体监测"),
    (645, 690, "井盖监测"),
    (640, 1040, "管道结构监测"),
    (410, 1090, "干线管网"),
    (525, 1185, "排放口"),
]:
    label(*args, GREEN)
d.text((840, 1212), "自然水体", font=font(22), fill=MUTED)
rr((825, 300, 1020, 600), 16, GREEN, (8, 45, 30), 2)
d.text((865, 320), "关键指标", font=font(26, True), fill=(160, 255, 160))
for i, s in enumerate(["流量：12,580 m3/h", "液位：2.45 m", "COD：28 mg/L", "氨氮：3.2 mg/L", "温度：18.6℃", "井盖状态：正常"]):
    d.text((845, 370 + i * 36), s, font=font(22), fill=WHITE)
rr((845, 875, 1025, 1110), 16, (190, 190, 70), (45, 45, 15), 2)
d.text((885, 895), "风险预警", font=font(26, True), fill=(255, 220, 80))
for i, s in enumerate(["溢流风险：低", "内涝风险：中", "管道缺陷：2处", "设备告警：1处"]):
    d.text((865, 945 + i * 38), s, font=font(22), fill=WHITE)

for e in [(1155, 250, 1465, 380), (1110, 315, 1515, 450), (1190, 200, 1390, 400)]:
    d.ellipse(e, fill=(8, 55, 100), outline=(90, 190, 255), width=3)
tc(1315, 310, "智慧水务云平台", font(34, True))
tc(1315, 365, "（AI中枢大脑）", font(30, True))
for i, s in enumerate(["数据汇聚", "模型训练", "智能诊断"]):
    d.text((1088, 455 + i * 70), s, font=font(24), fill=WHITE)
for i, s in enumerate(["决策优化", "数字孪生", "可视化呈现"]):
    d.text((1370, 455 + i * 70), s, font=font(22), fill=WHITE)
rr((1200, 450, 1425, 735), 20, (50, 170, 255), (10, 45, 95), 3)
tc(1312, 590, "AI", font(82, True), (120, 230, 255))
rr((1070, 745, 1505, 940), 16, (70, 150, 230), (5, 30, 62), 3)
tc(1288, 775, "数据中台", font(30, True), (150, 230, 255))
for i, s in enumerate(["数据接入", "数据治理", "数据存储", "数据服务"]):
    x = 1120 + i * 95
    d.ellipse((x, 820, x + 52, 872), outline=(100, 190, 255), width=3)
    tc(x + 26, 910, s, font(19))
    if i < 3:
        d.line([(x + 55, 846), (x + 88, 846)], fill=(90, 150, 210), width=3)
rr((1080, 985, 1500, 1168), 16, (70, 150, 230), (5, 30, 62), 3)
tc(1290, 1018, "统一标准与安全体系", font(28, True), (160, 230, 255))
for i, s in enumerate(["物联感知标准化", "数据安全", "权限管理"]):
    x = 1160 + i * 140
    d.ellipse((x, 1065, x + 50, 1115), outline=(100, 190, 255), width=3)
    tc(x + 25, 1140, s, font(18))
d.line([(1045, 360), (1120, 330)], fill=GREEN, width=12)
d.polygon([(1120, 330), (1088, 310), (1092, 355)], fill=GREEN)
d.line([(1518, 330), (1560, 330)], fill=BLUE, width=12)
d.polygon([(1560, 330), (1528, 310), (1532, 355)], fill=BLUE)

rr((1560, 280, 2235, 420), 14, (55, 120, 210), (8, 28, 60), 3)
tc(1895, 300, "进水监测", font(25, True), (140, 220, 255))
for i, s in enumerate(["流量", "水质", "水温", "pH", "氨氮", "重金属"]):
    x = 1620 + i * 92
    d.ellipse((x, 330, x + 40, 370), outline=(100, 190, 255), width=3)
    tc(x + 20, 392, s, font(19))


def process_box(y, title, items):
    rr((1560, y, 2280, y + 145), 14, (55, 120, 210), (8, 28, 60), 3)
    tc(1920, y + 24, title, font(25, True), (140, 220, 255))
    start = 1615
    gap = 610 // max(1, (len(items) - 1))
    last = None
    for i, it in enumerate(items):
        x = start + i * gap
        rr((x, y + 64, x + 95, y + 105), 5, (90, 160, 220), (35, 60, 85), 2)
        tc(x + 47, y + 125, it, font(18))
        if last is not None:
            d.line([(last + 95, y + 84), (x, y + 84)], fill=(90, 170, 255), width=4)
        last = x


process_box(460, "预处理系统", ["粗格栅", "细格栅", "曝气沉砂池"])
process_box(620, "生化处理系统", ["厌氧池", "缺氧池", "好氧池"])
process_box(775, "深度处理系统", ["沉淀池", "高效沉淀池", "滤布滤池", "消毒池"])
process_box(930, "污泥处理系统", ["浓缩池", "厌氧消化", "脱水机房", "干化/焚烧"])
rr((1560, 1105, 2280, 1205), 14, (55, 120, 210), (8, 28, 60), 3)
tc(1920, 1127, "出水监测", font(25, True), (140, 220, 255))
for i, s in enumerate(["COD", "氨氮", "总磷", "总氮", "浊度", "余氯"]):
    x = 1600 + i * 105
    d.ellipse((x, 1150, x + 36, 1186), outline=(100, 190, 255), width=3)
    tc(x + 18, 1198, s, font(18))
d.text((2385, 1194), "达标排放 / 回用利用", font=font(24), fill=WHITE)

bullet_list(2365, 265, "AI优化控制", ["曝气智能调控", "加药智能控制", "回流比优化", "能耗优化"], BLUE, 215, 260)
bullet_list(2365, 560, "能效管理", ["碳排监测", "能效分析", "碳绩效管理", "设备优化"], BLUE, 215, 245)
bullet_list(2365, 855, "生产运营", ["运行监控", "异常预警", "报表管理", "绩效分析"], BLUE, 215, 245)

rr((545, 1300, 2025, 1425), 18, (55, 130, 220), (5, 30, 60), 3)
tc(1285, 1308, "一厂一网协同联动", font(34, True))
for i, s in enumerate(["水量水质协同调度", "风险预警联动", "应急响应联动", "调度策略优化"]):
    x = 660 + i * 330
    d.ellipse((x - 45, 1350, x + 5, 1400), outline=(90, 180, 255), width=3)
    d.text((x + 25, 1358), s, font=font(26), fill=WHITE)
    if i < 3:
        d.line([(x + 260, 1375), (x + 315, 1375)], fill=(60, 140, 220), width=5)

rr((235, 1460, 2390, 1575), 18, (50, 135, 220), (6, 34, 66), 3)
tc(1310, 1455, "价值体系", font(34, True))
vals = [
    ("环境效益", "减少污染排放"),
    ("社会效益", "提升履约保障"),
    ("经济效益", "降低运营成本"),
    ("管理效益", "提升决策效率"),
    ("安全效益", "保障系统安全"),
    ("可持续发展", "推动绿色低碳"),
]
for i, (a, b) in enumerate(vals):
    x = 360 + i * 300
    d.ellipse((x - 38, 1502, x + 8, 1548), outline=(90, 180, 255), width=3)
    d.text((x + 35, 1494), a, font=font(25, True), fill=WHITE)
    d.text((x + 35, 1532), b, font=font(18), fill=MUTED)

img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=2))
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)
