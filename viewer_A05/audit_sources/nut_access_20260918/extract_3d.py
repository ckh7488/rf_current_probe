"""Compare stored A11/C05 and A12/C06 CAD; preserve the 14 earlier comparisons."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
old=json.loads((R/'reviews/visual_revision_20260918/comparison_3d.json').read_text())
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
 ('head_nut','프로브 개폐 · 너트 탈락 방지','A11','A12',[-169,-44,-23,94,82,74],'사각 너트의 조립 여유와 체결 받침면은 유지하고, 나사를 완전히 뺄 때 너트가 빠지는 입구를 덮었습니다. 덮개는 체결 하중을 받는 부품이 아닙니다. 손으로 누를 공간을 위해 덮개 위치를 1 mm 낮추고 받이의 아래 창을 넓혔습니다.',['옆으로 열린 너트 입구','너트 삽입 후 덮개로 유지'],[-1,.4,1]),
 ('cal_nut','교정 PCB · 반대쪽 공구 없이 조임','A11','A12',[48,-43,19,74,49,61],'작은 육각 너트를 스패너로 잡던 방식을 바꿨습니다. 나일론 날개 너트가 받침 안에서 회전하지 않도록 하고, 탈락 방지 부품을 추가했습니다. 너트를 먼저 설치한 뒤 PCB를 올립니다.',['스패너로 육각 너트 붙잡기','날개 너트와 회전 방지 받침'],[1,.18,.8]),
 ('base_nut','바닥 · 모듈을 빼도 너트 유지','A11','A12',[27,-90,55,55,40,54],'바닥 밑 너트에 탈락 방지를 추가했습니다. 책상에 닿는 기준면과 나사 끝 돌출도 함께 다시 확인합니다.',['바닥 아래로 열린 포켓','바닥 안에 너트 유지'],[.5,-1,1]),
 ('bridge_nut','케이블 가로대 · 너트를 매번 잡지 않기','C05','C06',[30,6,9,46,48,71],'기존 사각 너트를 넣고 덮개를 닫습니다. 가로대를 열기 위해 손나사를 완전히 빼도 너트는 연결틀에 남습니다. 덮개는 손으로 해제하는 정비 부품입니다.',['열린 사각 너트 포켓','너트 포켓과 손으로 여는 덮개'],[.8,.3,1]),
 ('lead_nut','구경 노브 축 · 스패너 하나로 초도 조립','C05','C06',[65,27,7,35,25,39],'얇은 너트 두 개를 서로 잠그는 대신 M6 풀림 방지 너트 하나를 사용합니다. 너트를 스패너로 잡고 큰 노브를 돌려 처음 조립합니다. 와셔와 너트는 축을 넣기 전에 놓습니다. 축을 꽉 조여 회전을 막는 체결이 아닙니다.',['얇은 잠금너트 두 개','M6 풀림 방지 너트 한 개'],[1,.3,1]),
 ('base_panel','공통 바닥 · 너트 여섯 개를 한 장으로 유지','A11','A12',[-131,-91,-140,262,32,324],'별도 M4 나사 두 개로 격자 밑판을 처음 한 번 고정합니다. 모듈용 나사를 풀어도 밑판은 남습니다. 긴 출력물의 간격 차이를 흡수하도록 한쪽 고정 홀에 길이 방향 여유를 둡니다.',['밑면으로 열린 너트 포켓','하나의 밑판과 별도 고정 나사'],[.2,-1,.35]),
]
cases=old['cases']+[case(*s) for s in specs]
payload=dict(classification='CALCULATED_CAD_VISUALIZATION',cropping='Bounded actual solids, not fabrication cuts.',sources=inputs,cases=cases)
(O/'comparison_3d.json').write_text(json.dumps(payload,separators=(',',':')))
print(json.dumps(dict(cases=len(cases),sources=len(inputs))))
