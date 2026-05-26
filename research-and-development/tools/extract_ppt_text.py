from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_文字版_editable.pptx")
ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
with ZipFile(p) as z:
    for name in z.namelist():
        if name.startswith("ppt/slides/") and name.endswith(".xml"):
            root = ET.fromstring(z.read(name))
            texts = [node.text or "" for node in root.findall(".//a:t", ns)]
            print(name)
            for text in texts:
                if text.strip():
                    print(text)
