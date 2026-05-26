import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = NS["w"]


def w_attr(name: str) -> str:
    return f"{{{W}}}{name}"


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS))


def main() -> None:
    docx = Path(sys.argv[1])
    with zipfile.ZipFile(docx) as z:
        comments_xml = z.read("word/comments.xml")
        document_xml = z.read("word/document.xml")

    comments_root = ET.fromstring(comments_xml)
    comments = {}
    for c in comments_root.findall("w:comment", NS):
        cid = c.attrib.get(w_attr("id"))
        comments[cid] = {
            "id": cid,
            "author": c.attrib.get(w_attr("author"), ""),
            "date": c.attrib.get(w_attr("date"), ""),
            "text": text_of(c),
            "anchors": [],
        }

    doc_root = ET.fromstring(document_xml)
    for idx, p in enumerate(doc_root.findall(".//w:p", NS), 1):
        ids = []
        for node in p.iter():
            local = node.tag.rsplit("}", 1)[-1]
            if local in {"commentRangeStart", "commentRangeEnd", "commentReference"}:
                cid = node.attrib.get(w_attr("id"))
                if cid is not None and cid not in ids:
                    ids.append(cid)
        if ids:
            p_text = text_of(p)
            for cid in ids:
                if cid in comments:
                    comments[cid]["anchors"].append({"paragraph": idx, "text": p_text})

    print(json.dumps(list(comments.values()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
