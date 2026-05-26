import fitz
from pathlib import Path
pdf=Path(r'E:\PY\research\PPT模版.pdf')
out=Path(r'E:\PY\research\tmp\template_preview')
out.mkdir(parents=True,exist_ok=True)
doc=fitz.open(str(pdf))
print('pages',doc.page_count)
for i,p in enumerate(doc):
    pix=p.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False)
    path=out/f'page_{i+1}.png'
    pix.save(str(path))
    print(path)
