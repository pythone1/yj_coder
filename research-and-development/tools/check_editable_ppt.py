from pathlib import Path
from zipfile import ZipFile

p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_文字版_editable.pptx")
with ZipFile(p) as z:
    slides = [n for n in z.namelist() if n.startswith("ppt/slides/") and n.endswith(".xml")]
    xml = "\n".join(z.read(n).decode("utf-8", errors="replace") for n in slides)
print("pptx=", p)
print("size=", p.stat().st_size)
print("slides=", len(slides))
print("bad_markers=", any(x in xml for x in ["????", "�", "Slide Number"]))
print("has_text_nodes=", "<a:t>" in xml)
for s in ["污水管网", "感知层", "液位监测", "污水处理厂", "AI优化控制", "价值体系"]:
    print(s, s in xml)
