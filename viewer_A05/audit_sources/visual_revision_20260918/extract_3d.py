"""Extract bounded, real CAD solids for the interactive change review.
FreeCAD 1.0.2. Crops are viewing windows, not manufacturing cuts.
"""
from pathlib import Path
import json, hashlib
import FreeCAD as A, Part
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
V=A.Vector
docs={}; inputs={}
def source(rev):
    if rev.startswith('A'): p=R/f'mechanical/assembly_{rev}_DRAFT/RFCP_{rev}_Integrated_DRAFT.FCStd'
    else:p=R/f'mechanical/cable_clamp_{rev}_DRAFT/Cable_Clamp_{rev}_DRAFT.FCStd'
    if rev not in docs:
        docs[rev]=A.openDocument(str(p)); inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return docs[rev]
def case(key,title,before,after,names,bounds,why,labels,angle=0,direction=(.8,.55,1)):
    out={'key':key,'title':title,'before':before,'after':after,'why':why,'labels':labels,'direction':direction,'models':[],'bounds':bounds}
    crop=Part.makeBox(bounds[3],bounds[4],bounds[5],V(*bounds[:3]))
    solids=[]
    for rev in [before,after]:
        parts=[]
        shapes={}
        for name in names:
            obj=source(rev).getObject(name)
            if obj is None: raise KeyError((rev,name))
            q=obj.Shape.copy()
            if name=='UpperLid':
                # Historical CLOSED display geometry was invalid; compare the
                # valid, actual FREE printable shapes on both sides instead.
                p=R/f'mechanical/assembly_{rev}_DRAFT/parts/UpperLid_FREE_DRAFT.step'
                q=Part.read(str(p));assert q.isValid()
                inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
                out['lid_state']='FREE printable shape on both sides'
            if angle:q.rotate(V(),V(0,0,1),angle)
            s=q.common(crop)
            if s.isNull() or s.Volume<1e-8:continue
            shapes[name]=s
            vertices,triangles=s.tessellate(.07)
            parts.append({'name':name,'vertices':[list(p) for p in vertices],'triangles':triangles,'volume_mm3':s.Volume})
        assert parts,(key,rev)
        out['models'].append(parts)
        solids.append(shapes)
    out['changes']=[]
    for i in [0,1]:
        delta=[]
        for name,s in solids[i].items():
            other=solids[1-i].get(name)
            q=s.cut(other) if other is not None else s
            if q.isNull() or q.Volume<1e-5:continue
            vs,ts=q.tessellate(.07)
            delta.append({'name':name,'vertices':[list(v) for v in vs],'triangles':ts,'volume_mm3':q.Volume})
        out['changes'].append(delta)
    return out
cases=[]
# Earlier changes retain their actual A09/C03 -> A10/C04 provenance.
specs=[
('jaw','아래 턱 · 너트 홈','C03','C04',['Jaw1'],(6,-10,-1,40,20,13),'비스듬한 너트 홈이 턱 옆면을 뚫던 부분을 정렬하고 몸체를 넓혔습니다.',['폭 8 mm · 옆으로 열린 홈','폭 14 mm · 옆벽 2.6 mm'],-210),
('lug','위 가로대 · 체결부','C03','C04',['DriveYoke'],(38,11,14,23,28,22),'손나사를 조일 때 힘을 받는 너트 주변을 보강했습니다.',['옆벽 1.1 mm','옆벽 3.1 mm · 뒷벽 2.4 mm'],0),
('guide','아래 턱 · 이탈 방지턱','C03','C04',['Frame'],(25,-15,-5,23,30,24),'미끄러지는 턱을 앞에서 받치는 얇은 턱을 두껍게 했습니다.',['앞턱 1.2 mm','앞턱 2.4 mm'], -210),
('catch','코어 고정바 · 안쪽 턱','A09','A10',['LowerKeeper'],(3,-20,-2,14,15,25),'코어 이탈 방지턱의 두께를 늘렸습니다.',['두께 1 mm','두께 2 mm'],0),
('boss','프로브 · 고정바 나사 받침','A09','A10',['UpperLid'],(28,11,-6,19,24,25),'나사를 코어 바깥쪽으로 옮기고 나사 주변 받침을 넓혔습니다.',['안쪽 벽 1.4 mm','안쪽 벽 2.4 mm'],0),
('post','교정 PCB · 기둥 보강','A09','A10',['CommonBase'],(55,-19,33,21,20,24),'너트 홈 가장자리의 얇은 부분을 없애도록 기둥을 사각형으로 키웠습니다.',['둥근 기둥의 얇은 모서리','14 × 14 mm 사각 기둥'],0),
('lead','큰 노브 · 축 주변 보강','C03','C04',['DriveYoke'],(70,-40,13,22,22,24),'구동축과 구동너트 주변 벽을 두껍게 했습니다.',['축 구멍 위·아래 벽 1.5 mm','위 3.5 mm · 아래 4.5 mm'],0),
('wire','권선 출구 · 얇은 막벽 제거','A09','A10',['LowerBody'],(-8,-43,2,16,15,22),'권선 출구의 남은 얇은 막벽을 제거하고 PCB 받침을 보강했습니다.',['출구에 1 mm 막벽','출구 개방 · 지붕 2.4 mm'],0),
]
for s in specs:cases.append(case(*s))
# This turn: nominal new geometry. Text is checked against the fresh reports.
new=[
('mount','바닥 나사 · 책상 돌출 제거','A10','A11',['CommonBase','MountScrew1','MountNut1','LowerBody'],(37,-90,63,23,37,26),'나사 길이를 줄이고 너트를 받는 면에 맞췄습니다. 책상에 닿던 끝부분을 바닥 안으로 넣었습니다.',['M4 × 25 · 밑으로 돌출','M4 × 20 · 바닥 안쪽'],0,(.7,-.6,1)),
('access','고정바 · SMA와 납땜 공간','A10','A11',['LowerKeeper','LowerBody','PCB','SMAEnvelope','Winding'],(-46,-70,1,92,68,35),'고정바를 위로 옮겨 SMA 플러그와 S+ / S− 패드 앞의 작업 공간을 열었습니다. 고정바의 코어 접촉부는 유지했습니다.',['SMA와 패드 앞을 가림','고정바 이동 · 작업 공간 개방'],0,(.25,.08,1)),
('register','뚜껑 · 다시 닫을 때 위치 기준','A10','A11',['LowerBody','UpperLid','HeadHandScrews'],(-134,-16,-20,42,70,59),'왼쪽 아래 몸체에 ㄱ자 위치 기준을 추가했습니다. 뚜껑 기둥을 이 모서리에 가볍게 맞대고 나사를 조입니다. 자동 정밀 정렬이 아니며, 출력 오차와 맞댐 반복성은 시제품에서 확인해야 합니다.',['평평한 받침 + 나사 여유','눈에 보이는 ㄱ자 기준에 맞대기'],0,(-1,.5,-.8)),
('postaccess','교정 PCB · 너트 조립 접근','A10','A11',['CommonBase','CalibrationNuts','CalibrationScrews','FlatPCB'],(53,-23,31,31,30,31),'기둥 바깥쪽에 공구 창을 열었습니다. 두께 3 mm 이하인 5.5 mm 스패너로 나일론 너트를 잡고 위에서 나사를 조입니다. 너트가 저절로 고정되는 홈은 아닙니다.',['너트를 잡기 어려운 홈','바깥쪽 창으로 스패너 접근'],0,(1,.2,.65)),
('backlash','큰 노브 · 방향 전환 여유','C04','C05',['DriveYoke','DriveNut','LeadScrewKnob'],(70,-39,16,22,18,23),'구동너트 홈 높이를 6.8 → 6.0 mm로 줄였습니다. 공칭 여유는 1.8 → 1.0 mm이며, 출력 공차가 있으므로 무유격 구조는 아닙니다.',['공칭 축방향 여유 1.8 mm','공칭 축방향 여유 1.0 mm'],0,(.8,.3,1)),
('exitcleanup','권선 출구 · 남은 얇은 조각','A10','A11',['LowerBody'],(-8,-42,-3,16,15,21),'기존 PCB 공간과 권선 통로가 만나는 곳에 남아 있던 아주 얇은 조각을 제거했습니다. 가운데 통로를 열고 뒤쪽 벽 2.5 mm와 나사 받침은 유지했습니다.',['통로에 남은 얇은 조각','가운데 통로 개방'],0,(.65,.3,1)),
]
for s in new:cases.append(case(*s))
payload={'classification':'CALCULATED_CAD_VISUALIZATION','cropping':'Actual solid common with stated rectangular viewing window; no invented surfaces except crop boundaries.','sources':inputs,'cases':cases}
(O/'comparison_3d.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
print(json.dumps({'cases':len(cases),'sources':inputs,'bytes':(O/'comparison_3d.json').stat().st_size}))
