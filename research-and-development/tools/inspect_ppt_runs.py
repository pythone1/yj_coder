from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

p = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图.pptx")
ns = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

with ZipFile(p) as z:
    xml = z.read("ppt/slides/slide1.xml")
root = ET.fromstring(xml)
for r in root.findall(".//a:r", ns):
    t = r.find("a:t", ns)
    if t is None or not (t.text or "").strip():
        continue
    rpr = r.find("a:rPr", ns)
    color = None
    size = None
    bold = None
    if rpr is not None:
        size = rpr.attrib.get("sz")
        bold = rpr.attrib.get("b")
        srgb = rpr.find(".//a:srgbClr", ns)
        scheme = rpr.find(".//a:schemeClr", ns)
        if srgb is not None:
            color = "#" + srgb.attrib.get("val", "")
        elif scheme is not None:
            color = "scheme:" + scheme.attrib.get("val", "")
    if color and color != "scheme:tx1":
        print(repr(t.text), "size=", size, "bold=", bold, "color=", color)
