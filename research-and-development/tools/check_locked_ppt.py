from pathlib import Path
from zipfile import ZipFile

p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_文字版.pptx")
with ZipFile(p) as z:
    names = z.namelist()
    slides = [n for n in names if n.startswith("ppt/slides/") and n.endswith(".xml")]
    media = [n for n in names if n.startswith("ppt/media/")]
    all_xml = "\n".join(z.read(n).decode("utf-8", errors="replace") for n in slides)
print("pptx=", p)
print("size=", p.stat().st_size)
print("slides=", len(slides))
print("media_count=", len(media))
print("bad_markers=", any(x in all_xml for x in ["????", "�", "Slide Number"]))
print("has_text_nodes=", "<a:t>" in all_xml)
