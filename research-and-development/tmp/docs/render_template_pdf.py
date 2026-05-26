from pathlib import Path

import fitz

pdf = Path(r"E:\PY\research\PPT模版.pdf")
out_dir = Path(r"E:\PY\research\tmp\template_pdf_pages")
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(str(pdf))
for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    path = out_dir / f"template_page_{i}.png"
    pix.save(str(path))
    print(path)
print(f"pages={len(doc)}")
