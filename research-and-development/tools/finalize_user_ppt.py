from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image
SRC = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_文字版_editable.pptx")
OUT = Path(r"D:\Users\Downloads\一厂一网_智慧水务系统全景图_最终版.pptx")
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def remove_star_logo(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    if img.size != (2626, 1600):
        return image_bytes

    arr = np.array(img)
    # Bottom-right star logo area in the 2626x1600 template.
    x1, y1, x2, y2 = 2460, 1350, 2608, 1535
    roi = arr[y1:y2, x1:x2]

    # Mask the bright gray star, leaving darker background untouched.
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[(gray > 80)] = 255

    # Expand mask so antialiased edges disappear too.
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)
    _, mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

    bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
    arr[y1:y2, x1:x2] = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)

    out = BytesIO()
    Image.fromarray(arr).save(out, format="PNG")
    return out.getvalue()


def patch_media():
    with ZipFile(SRC, "r") as zin, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.startswith("ppt/slides/") and info.filename.endswith(".xml"):
                root = ET.fromstring(data)
                text_nodes = [node for node in root.iter(f"{NS_A}t")]
                values = [node.text or "" for node in text_nodes]
                for idx, value in enumerate(values):
                    if value == "决策" and idx > 0 and idx + 1 < len(values):
                        if "低碳运行" in values[idx - 1] and values[idx + 1] == "保障":
                            text_nodes[idx].text = "韧性"
                    if value == "曝气" and idx + 2 < len(values):
                        if values[idx + 1] == "沉淀" and values[idx + 2] == "池":
                            text_nodes[idx].text = "曝气沉砂池"
                            text_nodes[idx + 1].text = ""
                            text_nodes[idx + 2].text = ""
                    if value == "曝气沉淀池":
                        text_nodes[idx].text = "曝气沉砂池"
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            if info.filename.startswith("ppt/media/") and info.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                try:
                    data = remove_star_logo(data)
                except Exception:
                    pass
            zout.writestr(info, data)


if __name__ == "__main__":
    patch_media()
    print(OUT)
