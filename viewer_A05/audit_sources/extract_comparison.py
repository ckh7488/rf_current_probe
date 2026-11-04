"""Actual BRep sections for before/after illustrations; no invented geometry."""
from pathlib import Path
import json
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
def sh(rel):return Part.read(str(R/rel))
def rotate(s,a):q=s.copy();q.rotate(V(),V(0,0,1),a);return q
def box(a):return Part.makeBox(a[3],a[4],a[5],V(*a[:3]))
cases=[]
for title,key,fn,cut,proj,bounds in [
 ('아래 턱 · 너트 홈','jaw',lambda rev:rotate(sh('mechanical/cable_clamp_'+('C03' if rev==0 else 'C04')+'_DRAFT/parts/Jaw1_DRAFT.step'),-210),(6,-10,4,40,20,.05),(0,1),[6,46,-10,10]),
 ('위 가로대 · 너트 고정부','lug',lambda rev:sh('mechanical/cable_clamp_'+('C03' if rev==0 else 'C04')+'_DRAFT/parts/DriveYoke_DRAFT.step'),(39,18.5,16,20,.05,17),(0,2),[39,59,16,33]),
 ('슬라이딩 턱 · 앞쪽 이탈 방지턱','guide',lambda rev:rotate(sh('mechanical/cable_clamp_'+('C03' if rev==0 else 'C04')+'_DRAFT/parts/Frame_DRAFT.step'),-210),(34,-14,-5,.05,28,23),(1,2),[-14,14,-5,18]),
 ('코어 고정바 · 안쪽 이탈 방지턱','catch',lambda rev:sh('mechanical/assembly_'+('A09' if rev==0 else 'A10')+'_DRAFT/parts/LowerKeeper_FREE_DRAFT.step'),(10,-16,-2,.05,8,25),(2,1),[-2,23,-16,-8]),
 ('프로브 · 고정바 나사 주변','boss',lambda rev:sh('mechanical/assembly_'+('A09' if rev==0 else 'A10')+'_DRAFT/parts/UpperLid_FREE_DRAFT.step'),(30,13,5,15,19,.05),(0,1),[30,45,13,32]),
 ('교정 PCB 기둥 · 너트 홈','post',lambda rev:sh('mechanical/assembly_'+('A09' if rev==0 else 'A10')+'_DRAFT/parts/CommonBase_FREE_DRAFT.step'),(56,-9,35,18,.05,20),(0,2),[56,74,35,55]),
 ('큰 노브 · 구동축 주변','lead',lambda rev:sh('mechanical/cable_clamp_'+('C03' if rev==0 else 'C04')+'_DRAFT/parts/DriveYoke_DRAFT.step'),(73,-34.5,16,17,.05,20),(0,2),[73,90,16,36]),
 ('권선 출구 · 불필요한 얇은 벽','wire',lambda rev:sh('mechanical/assembly_'+('A09' if rev==0 else 'A10')+'_DRAFT/parts/LowerBody_FREE_DRAFT.step'),(0,-40,3,.05,11,15),(1,2),[-40,-29,3,18]),
]:
 models=[]
 for i in [0,1]:
  s=fn(i).common(box(cut));vs,ts=s.tessellate(.02)
  # Keep only triangles whose projected area is nonzero (section front/back).
  pts=[[v[proj[0]],v[proj[1]]] for v in vs];tri=[]
  for t in ts:
   p,q,r=[pts[k] for k in t];area=(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
   if abs(area)>1e-7:tri.append(t)
  models.append(dict(vertices=pts,triangles=tri))
 cases.append(dict(key=key,title=title,bounds=bounds,models=models,method='CAD solid sliced at the same plane and projected at equal scale'))
(O/'comparison_geometry.json').write_text(json.dumps(cases)+'\n');print('Actual CAD sections',len(cases))
