"""Current A14 assembly steps, retaining prior H/C/B/Q links."""
from copy import deepcopy
import json
from pathlib import Path
from guide_steps_a13_history import make_steps as old_steps

def make_steps(mesh):
 lower=['LowerCenter','LowerArmLeft','LowerArmRight']+[n for n in mesh if n.startswith('LowerJoint')]
 upper=['UpperLeft','UpperRight']+[n for n in mesh if n.startswith('UpperJoint')]
 base=['BaseFront','BaseCenter','BaseRear']+[n for n in mesh if n.startswith('BaseJoint')]
 free=['UpperLeftFree','UpperRightFree']+[n for n in mesh if n.startswith('UpperJoint')]
 lead=lambda k:[f'Cable{k}_{s}' for s in ['LeadStud','HandKnob','TopJamNut','TopWasher']]
 headunit=['HeadHandScrews','HeadClosureKnobs','HeadClosureJamNuts','HeadClosureWashers']
 mapping={'LowerBody':lower,'UpperLid':upper,'UpperLidFree':free,'CommonBase':base,'HeadHandScrews':headunit,**{f'Cable{k}_LeadScrewKnob':lead(k) for k in [1,2]}}
 oldmesh={n:p for n,p in mesh.items() if n not in lead(1)+lead(2)}
 oldmesh.update({n:{} for n in mapping})
 expand=lambda ns:list(dict.fromkeys(a for n in ns for a in mapping.get(n,[n])))
 steps=old_steps(oldmesh)
 for s in steps:
  for field in ['rest','active','previewOnly']:
   if field in s:s[field]=expand(s[field])
  for field in ['moves','baseOffsets']:
   if field in s:s[field]={a:deepcopy(v) for n,v in s[field].items() for a in mapping.get(n,[n])}
  if s['id'] in ['H09','H10','H11']:
   s.setdefault('baseOffsets',{}).update({n:[0,-1.8,0] for n in free if n.startswith('UpperJoint')})
  if s['id'] in ['Q02','Q03']:
   for n in upper:
    if n.startswith('UpperJoint'):s['baseOffsets'][n]=[0,118.2,0]
  for field in ['action']:
   s[field]=[a.replace('위쪽 너트','아래쪽 축 위치 너트').replace('위 너트','아래쪽 축 위치 너트') for a in s[field]]
  if s['group']=='교정 준비':
   s['note']='화면의 교정 PCB는 A03과 외곽·고정홀이 같은 공통 장착 형상입니다. 실제 조립·제조에는 Fixture A03 원본을 사용합니다. '+s.get('note','')
 def get(i):return next(s for s in steps if s['id']==i)
 follower=get('C04')
 follower['tool']='F12 NBK SBSMS-M4-5-20용 2.5 mm 육각렌치.'
 follower['note']='F12는 NBK SBSMS-M4-5-20으로 선정했고 최대 어깨 길이 20.25 mm의 공칭 경로를 확인했습니다. 일반 M4 나사로 대체하지 않습니다. 실제 나사산·마찰·반복 고정은 첫 조립에서 확인합니다.'
 pcb=get('H05')
 for n in ['PCB','SMAEnvelope']:
  pcb['moves'][n]['keys']=[[0,[0,0,0],0],[.15,[0,0,.3],0],[.5,[0,0,.3],-45],[.65,[0,-4,0],-45],[1,[0,-4,40],-45]]
 pcb['action']=['PCB를 약45° 기울여 아랫변이 앞을 향하게 잡습니다.','최종 장착 위치보다 4 mm 아래에서 앞→뒤로 넣고 위로 올립니다. 장착면에 밀착시키지 않은 상태에서 기판을 세운 뒤 마지막에 앉힙니다. 슬라이더의 분해 동작을 역순으로 보세요.','뒤 너트를 받치면서 PA66 M2×12 나사 두 개를 차례로 걸어 고르게 조입니다.']
 pcb['check']='기판을 장착면에 누른 채 기울이지 않습니다. 탈착은 나사를 뺀 뒤 앞쪽으로 살짝 띄우고 기울입니다. 검증 모델은 +Z 0.3 mm를 먼저 띄우지만 손동작을0.3 mm로 계측하라는 뜻은 아닙니다. 현재45°/4 mm 경로를 사용하고 걸리면 억지로 누르지 않습니다.'
 pcb['note']='F01은 Essentra PA66 M2×12 두 개입니다. 최대 길이12.3 mm의 앞쪽 탈착61자세 무간섭. 입고 시 머리 아래11.7–12.3 mm, 체결 그립7.85–8.85 mm, 너트 높이1.46 mm 이하를 확인합니다. 이 범위에서 끝 돌출은 최소1.39 mm이며, 불완전 끝산0.6 mm 이하라는 수입검사 조건을 포함해도 완전산 여유0.79 mm가 남습니다. 공급자 보증공차가 아닌 설계 허용조건입니다. 체결 후 완전 나사산과 끝 간섭을 확인하고 플라스틱을 찌그러뜨릴 정도로 조이지 않습니다.'
 pcb['proof']='CALCULATED: 2026-09-22 독립 재검토. 외곽 각변+0.2 mm/두께1.76 mm PCB와 최대 SMA의 새 경로 각181자세, 합계362자세 무간섭. 공칭 출력물 기준이며 실물 시험 전.'
 pcb['action'].insert(0,'SMA만 PCB에 납땜된 상태로 작업합니다. 권선 끝선은 아직 납땜하지 말고 삽입 경로 밖으로 빼 둡니다.')
 pcb['note']+=' PCB를 다시 빼야 하면 먼저 권선 끝선 두 가닥을 납땜 제거하고 코어 쪽으로 빼 둡니다. 연결된 짧은 끝선을 당겨 PCB를 기울이지 않습니다.'
 get('H06')['note']+=' H05에서 PCB를 장착한 다음 이 단계에서 권선을 연결합니다. 캡을 분리한 현재 CAD에서 두 패드 위 Ø3×24 mm 인두 작업부의 접근 간섭은 없으며, 실제 팁/손잡이 외형·열 영향·납땜 품질은 별도 확인합니다.'
 def path(ns,v,w=(0,1)):return {n:dict(vector=v,window=list(w)) for n in ns}
 def fresh(id,group,title,rest,active,moves,action,check,note='',offsets=None):
  return dict(id=id,group=group,title=title,rest=rest,active=active,moves=moves,action=action,hold='두꺼운 접합면 가까이를 받칩니다. 얇은 탄성부·권선·SMA를 잡아당기지 않습니다.',tool='나사에 맞는 드라이버 + 7 mm 스패너/소켓',check=check,note=note,view=[.65,.35,1],proof='CALCULATED: A14 저장 CAD의 지정 연결·체결품·공구 경로 확인. 출력 휨·손 조립·체결력은 실물 확인.',baseOffsets=offsets or {})
 def insert_before(id,items):
  at=next(i for i,s in enumerate(steps) if s['id']==id);steps[at:at]=items
 def joint_steps(prefix,group,body,moving,joints,bodymoves,offsets=None):
  # Bolts out first, then their washers; nuts and front washers leave the opposite face.
  moves={}
  for n in joints:
   vector=[0,-40,0] if prefix=='B00' and (n.endswith('Screw') or n.endswith('RearWasher')) else [0,40,0] if prefix=='B00' else [0,0,-45] if n.endswith('Screw') or n.endswith('RearWasher') else [0,0,45]
   w=(0,.35) if n.endswith('Screw') else (.4,.6) if n.endswith('RearWasher') else (.65,.8) if n.endswith('Nut') else (.85,1)
   moves.update(path([n],vector,w))
  names=body+moving
  title={'L00':'아래 몸체 3조각','U00':'뚜껑 2조각','B00':'바닥 3조각'}[prefix]
  placement=fresh(prefix+'A',group,title+'을 받침면에 맞추기',body,moving,bodymoves,
   ['별도 조각의 맞닿는 면과 구멍을 확인합니다.','턱이 있는 넓은 면을 먼저 맞대고 구멍 중심을 손으로 맞춥니다.','틀어진 부품을 나사 힘으로 당겨 맞추지 않습니다.'],
   '손으로 놓은 상태에서 접합면이 앉고 나사가 무리 없이 통과해야 합니다.',offsets=offsets)
  fastening=fresh(prefix+'B',group,title+'을 연결 나사로 고정',names,joints,moves,
   ['바닥은 PA66 M4×20을 아래→위로, 몸체·뚜껑은 PA66 M4×30을 뒤→앞으로 넣습니다.','나사 머리 아래 와셔 1개, 반대편 와셔 1개와 육각너트를 댑니다.','모든 나사를 먼저 가볍게 걸고 접합면을 확인한 뒤 번갈아 조입니다.'],
   '와셔가 평평하고 너트 끝으로 나사산이 나오며, 접합부가 벌어지거나 휘지 않아야 합니다.',
   '정해진 체결 토크는 아직 없습니다. 나일론을 눌러 찌그러뜨리거나 힘으로 휨을 펴지 않습니다.',offsets=offsets)
  return [placement,fastening]
 lj=[n for n in lower if n.startswith('LowerJoint')]
 insert_before('H03',joint_steps('L00','프로브',['LowerCenter'],['LowerArmLeft','LowerArmRight'],lj,
  path(['LowerArmLeft','LowerArmRight'],[0,0,-60])))
 uj=[n for n in upper if n.startswith('UpperJoint')]
 insert_before('H09',joint_steps('U00','프로브',['UpperLeftFree'],['UpperRightFree'],uj,path(['UpperRightFree'],[0,0,-50]),{n:[0,-1.8,0] for n in uj}))
 bj=[n for n in base if n.startswith('BaseJoint')]
 insert_before('B01',joint_steps('B00','공통 바닥',['BaseFront','BaseRear'],['BaseCenter'],bj,path(['BaseCenter'],[0,60,0])))
 get('L00A')['action'][1]='양팔을 뒤에서 앞으로 가져와 아래 받침턱과 앞뒤 면에 앉힙니다. 옆에서 억지로 밀지 않습니다.'
 get('U00A')['action'][1]='오른쪽 뚜껑을 뒤에서 앞으로 가져와 중앙의 4 mm 아래 받침턱에 앉힙니다.'
 get('B00A')['action'][1]='앞·뒤 바닥 조각을 놓고 가운데 조각을 위에서 내려 겹침턱에 앉힙니다.'
 get('B00B')['action'].insert(0,'아직 체결하지 않은 세 조각을 통째로 뒤집지 않습니다. 두 조각을 접합부 가까이에서 함께 받쳐 나사 한 곳을 먼저 걸고, 나머지 위치를 차례로 체결합니다.')
 closure=fresh('H12A','프로브','개폐 손나사 두 개를 밖에서 선조립',['HeadHandScrews'],headunit[1:],
  {**path(['HeadClosureKnobs'],[0,160,0],[0,.35]),**path(['HeadClosureJamNuts'],[0,100,0],[.4,.7]),**path(['HeadClosureWashers'],[0,-80,0],[.75,1])},
  ['M4×70 스터드에 M4 잼너트를 넣고 관통형 노브를 돌려 끼웁니다.','스터드 끝이 노브 윗면과 평평해지도록 맞춘 뒤, 노브를 잡고 7 mm 스패너로 잼너트를 노브 아래에 조입니다.','아래쪽에 PA 와셔를 끼웁니다. 두 세트를 같은 방법으로 준비합니다. 이후에는 풀어 분해하지 않고 손나사 한 개처럼 사용합니다.'],
  '봉을 자르거나 표시할 필요가 없습니다. 역방향으로 돌려도 노브와 봉이 따로 풀리지 않는지 첫 조립에서 확인합니다.',
  '노브는 분실방지 부품이 아니라 기성 긴 손나사를 구성하는 손잡이입니다. 기존50 mm의 부족한 끝나사 여유를 확보합니다.')
 closure['hold']='노브를 손으로 잡고 잼너트만 스패너로 조입니다. 프린트 몸체에 끼우기 전 작업합니다.'
 closure['tool']='7 mm 스패너 + 평평한 끝 위치 육안 확인'
 closure['proof']='기성품 외형·너트 물림·지정 인출 경로 확인. 실제 조임력과 반복 풀림은 첫 제작 확인.'
 insert_before('H13',[closure])
 get('H14')['moves']=path(headunit,[0,75,0])
 get('H14')['action'][0]='선조립한 M4 개폐 손나사 두 개를 위에서 사각너트에 걸어 줍니다.'
 # Shaft and knob are assembled outside the frame: no hidden press-fit or custom machining.
 unit=lead(1);stud,knob,jam,top=unit
 a=fresh('C04A','케이블 클램프','스터드·잼너트·큰 노브를 밖에서 조립',[stud],[knob,jam],{**path([knob],[0,110,0],[0,.4]),**path([jam],[0,65,0],[.5,1])},
  ['M6×120 스터드 끝에서 10 mm를 표시합니다.','잼너트를 먼저 스터드에 넣고, 노브를 끝에서 10 mm 깊이까지 돌려 끼웁니다.','프레임 밖에서 노브를 잡고 10 mm 스패너로 잼너트를 노브의 금속 부싱에 밀착시킵니다.'],
  '역방향으로 돌려도 노브와 축이 풀리지 않아야 합니다. 실제 조임·반복 사용은 첫 조립 때 확인합니다.')
 a['tool']='10 mm 스패너 + 삽입 깊이 표시용 자';a['hold']='노브와 스터드를 작업대 밖에서 잡습니다. 나사산을 공구로 손상시키지 않습니다.'
 a['proof']='제조사 도면 외형·10 mm 삽입·공구 접근의 CAD 확인. 실제 풀림방지 성능 미측정.'
 b=fresh('C04B','케이블 클램프','노브축에 위쪽 와셔 끼우기',[stud,knob,jam],[top],path([top],[0,-135,0]),
  ['Ø12 / 두께1.6 mm 위쪽 와셔를 스터드 아래 끝으로 넣습니다.','와셔를 위로 올려 잼너트 아래에 둡니다. 이 면이 프레임 위쪽에 닿습니다.'],
  '위 F17과 아래 F11은 같은 1.6 mm 제품입니다. 축을 프레임에 넣기 전 작업입니다.')
 b['tool']='손으로 삽입';b['proof']='실제 기성품 외형·배치 확인. 화면은 나사 회전을 생략한 축 방향 설명.'
 insert_before('C05',[a,b])
 for id in ['C05','C06']:
  s=get(id);s['previewOnly']=list(dict.fromkeys(s.get('previewOnly',[])+unit))
  s['motionNote']=s['motionNote'].replace('노브축','선조립한 노브축 4부품').replace('위 너트','아래쪽 축 위치 너트')
 s=get('C07');s['action']=[a.replace('위쪽 너트','아래쪽 축 위치 너트').replace('위 너트','아래쪽 축 위치 너트') for a in s['action']]
 s['hold']='여유 조절 때만 프레임 아래 풀림방지 너트를 잡습니다. 정상 사용 때는 스패너를 빼고 노브만 돌립니다.'
 s['note']='위 잼너트는 노브와 축을 고정합니다. 프레임 아래 풀림방지 너트 F10은 축 여유를 약0.2 mm로 맞춥니다. 이를 꽉 조여 프레임을 압착하지 않습니다. 구동너트 홈의 1 mm 유격은 별개입니다.'
 s['proof']='CALCULATED: 새 기성 노브축 삽입·공구 지정 경로 확인. 회전 마찰·유격 유지·반복 내구성은 실물 확인.'
 s['tool']='10 mm 스패너: 머리폭18 / 두께4 mm 이내의 검토 외형 + 필러 게이지'
 s['toolModel']='spanner'
 s['anchors'][0][1][1]=37.2
 s['action'].append('아래 풀림방지 너트에는 프레임 바깥쪽(+X)에서 스패너를 넣고 고정한 채 노브를 돌립니다. 임의의 몽키스패너가 모두 맞는 것은 아닙니다.')
 get('C11')['action'][0]='C01~C10 및 C04A·C04B를 반복해 동일한 클램프 두 개를 만듭니다.'
 for id,i in [('B05',2),('B07',4)]:
  s=get(id);n=f'MountScrew{i}'
  s['moves'][n]=dict(pivot=[0,0,0],keys=[[0,[0,0,0],0],[.3,[0,25,0],0],[.5,[-35,25,0],0],[1,[-35,25,0],0]])
  s['action'].append('왼쪽 나사는 바깥쪽에서 구멍 위 25 mm 위치로 옮긴 다음 수직으로 내립니다. 분해는 25 mm 올림 → 왼쪽 바깥 인출입니다.')
  s['pathResult']='검사한 머리 외형의 지정 경로: 25 mm 상승 → 바깥 X 방향 인출. 40 mm 직선 상승 경로는 사용하지 않습니다.'
  s['proof']='CALCULATED: 현재 CAD의 지정 인출 경로 무간섭. 실제 공구·손·출력 공차는 별도 확인.'
 # Source review 2026-09-22: each joint step describes only its own fasteners.
 get('L00B')['action'][0]='PA66 M4×30을 좌우 팔에 각각2개씩, 뒤에서 앞으로 넣습니다.'
 get('U00B')['action'][0]='PA66 M4×30 두 개를 뚜껑 중앙 연결부에 뒤에서 앞으로 넣습니다.'
 get('B00B')['action'][1]='PA66 M4×20 네 개를 바닥 아래에서 위로 넣습니다.'
 get('H14')['proof']='CAD: 지정 손나사 인출 경로 확인 · 현행 노브 Ø16 · 실제 조임 미확인'
 get('H04')['tool']='M2 너트의 양쪽 평면을 잡을 수 있는 가는 평팁 공구'
 get('H04')['hold']='뒤쪽에서 가는 평팁으로 너트 양쪽 평면을 잡습니다. 앞쪽 나사가 걸릴 때까지 받칩니다.'
 get('H04')['check']='큰 원형 소켓을 밀어 넣지 않습니다. 실제 공구 끝이 뒤쪽 공간에 들어가고 너트를 놓치지 않는지 확인합니다.'
 get('H04')['note']='외경6.5 mm 관형 공구는 PCB 홀더에 걸렸습니다. 대신 각 끝단 단면0.6×1.5 mm, 가는 구간25 mm인 대향 평팁의 CAD 접근 공간을 확인했습니다. 실제 공구의 너트 잡는 힘과 나사물림은 첫 조립에서 확인합니다.'
 get('H04')['proof']='CALCULATED: 너트 AF3.64/3.90/4.16 mm, 좌우2곳, 뒤쪽 인출41위치씩 총246자세에서 지정 평팁/손잡이 포락 무간섭. 앞25 mm 이후 손잡이는 Ø14×80 mm 포락. 손·출력변형·파지력·상용공구 적합성은 미검증.'
 get('H05')['tool']='M2 나사 머리에 맞는 드라이버 + H04의 가는 평팁 너트 공구'
 for id in ['H08','H11']:
  get(id)['tool']='앞 드라이버 + M3 너트에 맞는 얇은 뒤쪽 공구'
  get(id)['check']='뒤쪽에서 너트를 받치고 앞 나사를 조입니다. 공구로 코어·플라스틱을 밀어내거나 과도하게 조이지 않습니다.'
  get(id)['note']='뒤쪽 관형 공구의 외경8 mm·길이25 mm 포락을 확인했습니다. 실제 육각 맞물림·공구 몸통·손 공간·조임력은 별도입니다. 단순 외경 통과를 실제 소켓의 적합성 보증으로 사용하지 않습니다.'
  get(id)['proof']='CALCULATED: 뒤쪽 Ø8 mm 관형 공구 포락, 좌우2곳×41위치 무간섭. H08은 하부 단독, H11은 자유 형상 뚜껑 단독 조립 상태. 실물 공차·손·토크는 미검증.'
 for s in steps:
  s['rest']=[n for n in dict.fromkeys(s['rest']) if n not in s['active']]
 # Reviewed public corrections from main 2b937fc; retain them on local rebuild.
 corrections=json.loads((Path(__file__).parent/'guide_sources/reviewed_steps_20260928.json').read_text(encoding='utf-8'))
 for id,fields in corrections.items():
  if id=='Q00':insert_before('Q01',[deepcopy(fields)])
  else:get(id).update(deepcopy(fields))
 return steps
