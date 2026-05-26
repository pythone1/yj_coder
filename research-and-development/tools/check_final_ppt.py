from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from PIL import Image

p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_最终版.pptx")
extract_dir = Path(r"D:\Users\Downloads\ppt_final_check")
extract_dir.mkdir(exist_ok=True)
ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

with ZipFile(p) as z:
    slide_text = []
    media_out = []
    for name in z.namelist():
        if name.startswith("ppt/slides/") and name.endswith(".xml"):
            data = z.read(name).decode("utf-8", errors="replace")
            root = ET.fromstring(data)
            slide_text.extend(node.text or "" for node in root.findall(".//a:t", ns))
        if name.startswith("ppt/media/") and name.lower().endswith((".png", ".jpg", ".jpeg")):
            data = z.read(name)
            out = extract_dir / Path(name).name
            out.write_bytes(data)
            try:
                im = Image.open(out)
                media_out.append((str(out), im.size))
            except Exception:
                media_out.append((str(out), None))

joined = "\n".join(slide_text)
print("pptx=", p)
print("size=", p.stat().st_size)
print("text_count=", len([t for t in slide_text if t.strip()]))
print("bad_markers=", any(x in joined for x in ["????", "�", "Slide Number"]))
print("fixed_subtitle=", "韧性" in slide_text and "决策保障" not in joined)
print("fixed_process=", "曝气沉砂池" in joined and "曝气沉淀池" not in joined)
print("media=", media_out)
