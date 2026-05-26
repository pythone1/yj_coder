from pathlib import Path
from zipfile import ZipFile


p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_文字版.pptx")
with ZipFile(p) as z:
    slide_xml = []
    bad = []
    for name in z.namelist():
        if name.startswith("ppt/slides/") and name.endswith(".xml"):
            data = z.read(name).decode("utf-8", errors="replace")
            slide_xml.append(data)
            if "????" in data or "�" in data or "Slide Number" in data:
                bad.append(name)

all_xml = "\n".join(slide_xml)
required = [
    "一厂一网",
    "智慧水务系统全景图",
    "污水管网",
    "污水处理厂",
    "管网健康评估",
    "曝气智能调控",
    "价值体系",
    "可持续发展",
]
print("pptx=", p)
print("size=", p.stat().st_size)
print("bad_markers=", bad)
for item in required:
    print(item, item in all_xml)
print("slide_count_xml=", len(slide_xml))
