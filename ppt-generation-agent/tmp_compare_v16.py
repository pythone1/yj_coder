from pathlib import Path
import re

from PIL import Image, ImageDraw


BASE = Path(r"E:\PY\research\0424")
SRC_DIR = BASE / "_check_source_png"
NEW_DIR = BASE / "_check_v16_png"
OUT = BASE / "_check_compare_source_vs_v16.jpg"


def slide_no(path):
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0


src_files = sorted(SRC_DIR.glob("*.png"), key=slide_no)
new_files = sorted(NEW_DIR.glob("*.PNG"), key=slide_no)
thumb_w = 480
pad = 24
label_h = 36
rows = []

for idx, (src_path, new_path) in enumerate(zip(src_files, new_files), 1):
    src = Image.open(src_path).convert("RGB")
    new = Image.open(new_path).convert("RGB")
    src_h = int(src.height * thumb_w / src.width)
    new_h = int(new.height * thumb_w / new.width)
    src = src.resize((thumb_w, src_h))
    new = new.resize((thumb_w, new_h))
    row_h = max(src_h, new_h) + label_h + pad
    row = Image.new("RGB", (thumb_w * 2 + pad * 3, row_h), (245, 247, 250))
    draw = ImageDraw.Draw(row)
    draw.text((pad, 8), f"Slide {idx} source", fill=(20, 45, 80))
    draw.text((thumb_w + pad * 2, 8), f"Slide {idx} v16", fill=(20, 45, 80))
    row.paste(src, (pad, label_h))
    row.paste(new, (thumb_w + pad * 2, label_h))
    rows.append(row)

canvas = Image.new("RGB", (rows[0].width, sum(row.height for row in rows)), "white")
y = 0
for row in rows:
    canvas.paste(row, (0, y))
    y += row.height

canvas.save(OUT, quality=90)
print(OUT)
