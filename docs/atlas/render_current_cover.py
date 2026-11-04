"""Render the saved A13 CAD mesh for the requested ATLAS thumbnail."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'mechanical'))
from raster_cad import render
M=R/'mechanical/assembly_A13_DRAFT/mesh.json'
mesh=json.loads(M.read_text())
skip={'FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput','CalibrationScrews','CalibrationNuts'}
head={n:p for n,p in mesh.items() if p.get('group','').startswith('HEAD')}
print('Head parts:',list(head))
# Saved CAD is already in its assembled global pose. No new product geometry.
scene=[]
for n,p in mesh.items():
    if n in skip or n.startswith('Tool'):continue
    v=np.array(p['vertices']); v=np.column_stack([v[:,0],-v[:,2],v[:,1]])
    scene.append({**p,'vertices':v})
image=Image.fromarray(render(scene,width=1240,height=680,elevation=28,azimuth=60))
canvas=Image.new('RGB',(1600,880),'#f4f6f7')
canvas.paste(image,(330,120))
d=ImageDraw.Draw(canvas)
font='C:/Windows/Fonts/malgun.ttf'; bold='C:/Windows/Fonts/malgunbd.ttf'
f=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
d.text((140,142),'RFCP',font=f(70,True),fill='#172e33')
d.text((140,242),'RF 전류 프로브',font=f(32,True),fill='#172e33')
d.text((140,296),'A13 / C07 · 실제 CAD',font=f(23),fill='#5f737b')
d.line((140,346,412,346),fill='#197d71',width=5)
d.text((140,378),'개방형 프로브\n앞뒤 중심 클램프\n분리형 공통 바닥',font=f(24),fill='#5f737b',spacing=14)
d.text((140,807),'조립 · 교정 · 사용',font=f(24,True),fill='#197d71')
d.text((1110,807),'DRAFT · 실물 검증 전',font=f(20),fill='#5f737b')
out=R/'reviews/atlas_purchase_20260918';out.mkdir(exist_ok=True)
canvas.save(out/'cover-a13.png')
(out/'cover_provenance.json').write_text(json.dumps({'mesh_sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'renderer':'mechanical/raster_cad.py','omitted':'removable calibration fixture, no cable added','coordinate_transform':'CAD y-up to renderer z-up: x,-z,y','elevation':28,'azimuth':60},indent=2))
