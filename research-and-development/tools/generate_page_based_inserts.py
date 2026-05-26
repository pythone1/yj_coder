from pathlib import Path
from PIL import Image, ImageDraw
import math

OUT = Path(r"D:\Users\Downloads\基于原页_可插入图片")
OUT.mkdir(parents=True, exist_ok=True)

BLUE = (35, 139, 211, 255)
DEEP = (17, 96, 125, 255)
TEAL = (31, 110, 132, 255)
LIGHT = (232, 247, 255, 255)
WHITE = (255, 255, 255, 255)
GREEN = (33, 159, 112, 255)
ORANGE = (243, 151, 43, 255)
RED = (229, 82, 82, 255)
GRID = (188, 220, 238, 255)


def save(img, name):
    img.save(OUT / name)


def arrow(d, a, b, color=BLUE, width=8):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    l = 28
    d.polygon([
        b,
        (b[0] - l * math.cos(ang - .45), b[1] - l * math.sin(ang - .45)),
        (b[0] - l * math.cos(ang + .45), b[1] - l * math.sin(ang + .45)),
    ], fill=color)


def dot(d, x, y, color, r=18):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=WHITE, width=5)


def triangle_insert():
    w, h = 1400, 980
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    tri = [(700, 55), (90, 905), (1310, 905)]
    d.polygon(tri, fill=(31, 110, 132, 235), outline=(13, 60, 80, 255))

    # inner layer lines
    d.line((420, 445, 980, 445), fill=(255, 255, 255, 170), width=5)
    d.line((255, 675, 1145, 675), fill=(255, 255, 255, 170), width=5)

    # bottom: drainage pipe network and sensors
    pts = [(315, 790), (520, 735), (700, 800), (900, 720), (1085, 800)]
    d.line(pts, fill=(162, 217, 241, 255), width=24, joint="curve")
    d.line(pts, fill=(46, 156, 218, 255), width=8, joint="curve")
    branch = [(520, 735), (545, 860), (800, 870), (900, 720)]
    d.line(branch, fill=(162, 217, 241, 255), width=20, joint="curve")
    d.line(branch, fill=(46, 156, 218, 255), width=7, joint="curve")
    for i, (x, y) in enumerate(pts + [(545, 860), (800, 870)]):
        dot(d, x, y, [GREEN, GREEN, ORANGE, RED, RED, GREEN, ORANGE][i], 22)

    # middle: AI core
    cx, cy = 700, 565
    hexagon = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        hexagon.append((cx + 120 * math.cos(a), cy + 120 * math.sin(a)))
    d.polygon(hexagon, fill=(238, 249, 255, 235), outline=(116, 201, 237, 255))
    for i in range(9):
        x = cx - 85 + (i % 3) * 85
        y = cy - 65 + (i // 3) * 65
        dot(d, x, y, BLUE, 14)
    for a in [(615, 500), (700, 500), (785, 500), (615, 565), (700, 565), (785, 565), (615, 630), (700, 630)]:
        for b in [(700, 565), (785, 630)]:
            d.line([a, b], fill=(70, 154, 202, 150), width=3)

    # top: model output icons
    d.rounded_rectangle((555, 190, 845, 315), 24, fill=(245, 252, 255, 235), outline=(116, 201, 237, 255), width=4)
    d.line((590, 280, 645, 245, 700, 260, 760, 220, 815, 235), fill=BLUE, width=8)
    for x, y in [(590, 280), (645, 245), (700, 260), (760, 220), (815, 235)]:
        dot(d, x, y, BLUE, 10)
    arrow(d, (700, 675), (700, 445), (220, 240, 250, 230), 8)
    arrow(d, (700, 445), (700, 315), (220, 240, 250, 230), 8)
    return img


def result_insert():
    w, h = 760, 560
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, w - 20, h - 20), 30, fill=(255, 255, 255, 245), outline=GRID, width=5)

    # mini network heat map
    d.rounded_rectangle((55, 70, 355, 315), 22, fill=(243, 250, 255, 255), outline=GRID, width=3)
    nodes = [(105, 220), (170, 155), (255, 190), (310, 130), (285, 255)]
    d.line(nodes[:4], fill=(91, 166, 210, 255), width=14, joint="curve")
    d.line([nodes[1], nodes[4], nodes[2]], fill=(91, 166, 210, 255), width=12, joint="curve")
    for i, (x, y) in enumerate(nodes):
        dot(d, x, y, [GREEN, ORANGE, RED, RED, GREEN][i], 16)

    # charts
    d.rounded_rectangle((405, 70, 705, 315), 22, fill=(243, 250, 255, 255), outline=GRID, width=3)
    d.line((435, 250, 490, 225, 545, 170, 600, 205, 665, 135), fill=BLUE, width=7)
    d.line((435, 275, 490, 260, 545, 245, 600, 235, 665, 230), fill=GREEN, width=7)
    d.rectangle((455, 120, 500, 255), fill=(33, 159, 112, 230))
    d.rectangle((545, 170, 590, 255), fill=(243, 151, 43, 230))
    d.rectangle((635, 105, 680, 255), fill=(229, 82, 82, 230))

    # output cards without text
    for i, color in enumerate([RED, ORANGE, BLUE, GREEN]):
        x = 80 + i * 160
        d.rounded_rectangle((x, 385, x + 100, 470), 18, fill=(248, 252, 255, 255), outline=color, width=4)
        d.ellipse((x + 30, 405, x + 70, 445), fill=color)
    return img


tri = triangle_insert()
res = result_insert()
save(tri, "01_大三角模型层插图_透明.png")
save(res, "02_右侧模型结果插图_透明.png")

preview = Image.new("RGB", (1700, 900), "white")
preview.paste(tri.resize((900, 630)), (60, 120), tri.resize((900, 630)))
preview.paste(res.resize((560, 413)), (1080, 220), res.resize((560, 413)))
preview.save(OUT / "00_预览.png", quality=95)

print(OUT)
print(OUT / "01_大三角模型层插图_透明.png")
print(OUT / "02_右侧模型结果插图_透明.png")
