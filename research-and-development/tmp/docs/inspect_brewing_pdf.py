from pathlib import Path

import fitz

pdf = Path(r"D:\Users\Downloads\Brewing_Digital_Intelligence.pdf")
out_dir = Path(r"E:\PY\research\tmp\brewing_pdf_preview")
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(str(pdf))
print("pages", len(doc))
for i in range(min(10, len(doc))):
    page = doc[i]
    text = page.get_text("text").strip().replace("\n", " ")
    print(f"PAGE {i+1}: {text[:300]}")
    pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    pix.save(str(out_dir / f"page_{i+1}.png"))
