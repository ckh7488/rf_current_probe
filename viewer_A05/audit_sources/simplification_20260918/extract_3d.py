"""Compare stored A11/C05 and A12/C06 CAD; preserve the 14 earlier comparisons."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
old=json.loads((R/'reviews/nut_access_20260918/comparison_3d.json').read_text())
inputs=old['sources'].copy();docs={};V=A.Vector
def source(rev):
 p=R/(f'mechanical/assembly_{rev}_DRAFT/RFCP_{rev}_Integrated_DRAFT.FCStd' if rev.startswith('A') else f'mechanical/cable_clamp_{rev}_DRAFT/Cable_Clamp_{rev}_DRAFT.FCStd')
 if rev not in docs:
  docs[rev]=A.openDocument(str(p));inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return docs[rev]
def case(key,title,before,after,bounds,why,labels,direction):
 crop=Part.makeBox(*bounds[3:],V(*bounds[:3]));models=[];ss=[]
 for rev in [before,after]:
  shapes={};parts=[]
  for obj in source(rev).Objects:
   if not hasattr(obj,'Shape') or obj.Shape.isNull() or not obj.Shape.BoundBox.intersect(crop.BoundBox):continue
   q=obj.Shape.common(crop)
   if q.isNull() or q.Volume<1e-6:continue
   vs,ts=q.tessellate(.09);shapes[obj.Name]=q
   parts.append(dict(name=obj.Name,vertices=[list(v) for v in vs],triangles=ts,volume_mm3=q.Volume))
  assert parts,(rev,key)
  models.append(parts);ss.append(shapes)
 changes=[]
 for i in [0,1]:
  parts=[]
  for n,s in ss[i].items():
   q=s.cut(ss[1-i][n]) if n in ss[1-i] else s
   if q.isNull() or q.Volume<1e-5:continue
   vs,ts=q.tessellate(.09);parts.append(dict(name=n,vertices=[list(v) for v in vs],triangles=ts,volume_mm3=q.Volume))
  changes.append(parts)
 print(key, [len(p) for p in models],flush=True)
 return dict(key=key,title=title,before=before,after=after,bounds=bounds,why=why,labels=labels,direction=direction,models=models,changes=changes)
specs=[
 ('remove_head_covers','프로브 · 덮개와 긴 받이 제거','A12','A13',[-162,-44,-23,84,82,74],'덮개와 긴 받이를 없애고 원래의 짧고 열린 사각너트 홈으로 돌아갑니다. 나사를 뺄 때는 너트를 직접 챙깁니다. 코어 받침과 얇은 벽 보강은 유지합니다.',['너트 덮개와 돌출 받이','열린 너트 홈'],[-1,.4,1]),
 ('remove_cal_covers','교정 PCB · 열린 받침만 남김','A12','A13',[48,-43,19,74,49,61],'나일론 날개너트와 하중을 받는 지지대는 남기고, 긴 받이와 덮개를 제거했습니다. 받침의 바깥쪽에서 너트를 넣고 위에서 조입니다.',['날개너트와 덮개','날개너트와 열린 받침'],[1,.18,.8]),
 ('remove_base_panel','바닥 · 노란 판과 전용 나사 제거','A12','A13',[-131,-91,-140,262,32,324],'노란 너트 유지판과 그 판을 고정하는 나사·너트 두 쌍을 없앴습니다. 바닥을 뒤집어 기존 모듈 너트를 잡고 체결합니다. 출력물은 전체26개에서15개로 줄었습니다.',['별도 노란 유지판','공통 바닥 한 개'],[.2,-1,.35]),
 ('remove_bridge_covers','케이블 클램프 · 기존 다섯 부품으로','C06','C07',[30,6,9,46,48,71],'가로대 너트 덮개와 받이를 제거했습니다. 경사 홈 위3.7mm 보강과 세 턱의 연동은 유지하며, 나사를 완전히 뺄 때 너트는 직접 챙깁니다.',['너트 덮개 두 개 추가','기존 열린 사각너트 홈'],[.8,.3,1]),
]
cases=old['cases']+[case(*s) for s in specs]
payload=dict(classification='CALCULATED_CAD_VISUALIZATION',cropping='Bounded actual solids, not fabrication cuts.',sources=inputs,cases=cases)
(O/'comparison_3d.json').write_text(json.dumps(payload,separators=(',',':')))
print(json.dumps(dict(cases=len(cases),sources=len(inputs))))
