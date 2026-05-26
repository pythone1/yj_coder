from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw
ppt=Path(r'E:\PY\research\output\ppt\Jinshiyuan_AI_Production_Blueprint.pptx')
out=Path(r'E:\PY\research\tmp\jinshiyuan_input_media2')
out.mkdir(parents=True, exist_ok=True)
with ZipFile(ppt) as z:
    names=[n for n in z.namelist() if n.startswith('ppt/media/') and n.lower().endswith(('.png','.jpg','.jpeg'))]
    for n in names:
        (out/Path(n).name).write_bytes(z.read(n))
imgs=[]
for p in sorted(out.glob('image*.png'), key=lambda x:int(''.join(filter(str.isdigit,x.stem)) or 0)):
    im=Image.open(p).convert('RGB')
    im.thumbnail((384,216))
    canvas=Image.new('RGB',(384,246),'white')
    canvas.paste(im,(0,30))
    d=ImageDraw.Draw(canvas)
    d.text((8,6),p.stem,fill=(0,0,0))
    imgs.append(canvas)
w=384*2; h=246*((len(imgs)+1)//2)
sheet=Image.new('RGB',(w,h),(240,240,240))
for i,im in enumerate(imgs):
    sheet.paste(im,((i%2)*384,(i//2)*246))
sheet_path=Path(r'E:\PY\research\tmp\jinshiyuan_input_contact_sheet.png')
sheet.save(sheet_path)
print(sheet_path)
