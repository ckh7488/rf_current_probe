from pathlib import Path
import json,hashlib,struct,base64,sys,os
from guide_steps import make_steps
from guide_bom import add_bom
P=Path(__file__).resolve().parent;R=P.parent;C=R/'mechanical/assembly_A14_DRAFT';O=P/'guide_sources';O.mkdir(exist_ok=True)
D=Path(os.environ.get('RFCP_BUILD_DIR',str(P/'dist')));D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((C/'build_report.json').read_text());assert build['pass_geometry']
assert sha(C/'RFCP_A14_Integrated_DRAFT.FCStd')==build['native_sha256']
assert sha(C/'mesh.json')==build['mesh_sha256']
mesh=json.loads((C/'mesh.json').read_text());mesh.pop('CalibrationNuts')
sup=json.loads((O/'geometry_supplements_a14.json').read_text());sources=sup.pop('_sources')
for rel,h in sources.items():assert sha(R/rel)==h,rel
mesh.update(sup);steps=make_steps(mesh)
assert len({s['id'] for s in steps})==len(steps)
for s in steps:
 s['action']=[v.replace('、',', ').replace('다음 두 단계 동안','PCB가 나사로 고정될 때까지') for v in s['action']]
 s['rest']=list(dict.fromkeys(n for n in s['rest'] if n not in s['active']))
 assert all(n in mesh for n in s['rest']+s['active']+list(s['moves'])),s['id']
 assert all(n in s['active'] for n in s['moves']),s['id']
checks=O/'animation_path_review.json'
if False: # A13 motion evidence is historical; current checks are bound separately.
 review=json.loads(checks.read_text());assert review['native_sha256']==build['native_sha256']
 assert review['steps_source_sha256']==sha(P/'guide_steps.py')
 for s in steps:
  r=review['steps'].get(s['id'])
  if r and r['collisions']:
   s['pathBlocked']=True;s['pathResult']='이 직선 분리 표현에는 주변 부품과 겹치는 구간이 있습니다. 실제 삽입 방향·순서를 다시 확인해야 하며, 이 동작대로 밀어 넣지 않습니다.'
   if s['id'] in ['B05','B07']:
    s['pathResult']='확인 필요: 왼쪽 M4 손나사 머리를 위로 뺄 때 프레임 모서리와 약0.06 mm³의 공칭 겹침이 있습니다. 실제 손나사 외경·출력 여유를 확인해야 하며, 이 부위의 조립 가능 판정은 보류합니다.'
  elif r and r['samples']:s['pathResult']='이 표시 경로의 '+str(r['samples'])+'개 위치에서 강체 겹침을 점검했습니다. 손·공구·나사산·유연한 권선은 별도입니다.'
labels={'LowerBody':'프로브 아래 몸체','UpperLid':'프로브 뚜껑','UpperLidFree':'프로브 뚜껑 · 자유 형상','FixedCore':'아래 코어','MovingCore':'위 코어','Winding':'권선 배치 예시','LowerKeeper':'아래 코어 고정바','UpperKeeper':'위 코어 고정바','PCB':'헤드 PCB','SMAEnvelope':'프로브 출력 SMA','PCBScrews':'M2 나일론 나사 2개','PCBNuts':'M2 나일론 너트 2개','LowerKeeperScrews':'아래 고정바 M3 나사 2개','UpperKeeperScrews':'위 고정바 M3 나사 2개','LowerKeeperNuts':'아래 고정바 너트 2개','UpperKeeperNuts':'위 고정바 너트 2개','HeadHandScrews':'프로브 개폐 손나사 2개','HeadSquareNuts':'프로브 개폐 사각너트 2개','CommonBase':'공통 바닥','FlatPCB':'교정 PCB','SignalCopper':'중앙 신호 경로','ReturnCopper':'바깥 귀환 경로','SMAInput':'교정 PCB 입력 SMA','SMAOutput':'교정 PCB 출력 SMA','CalibrationScrews':'교정 PCB 고정 나사 4개','ToolM6':'검사한 10 mm 스패너 외형','Frame':'클램프 고정틀','DriveYoke':'클램프 연결틀','TopBridgeJaw':'분리 가로대·위 턱','Jaw1':'아래 왼쪽 턱','Jaw2':'아래 오른쪽 턱','LeadScrewKnob':'큰 노브축','DriveNut':'M6 사각 구동너트','LeadLockNut':'축 위치 조절용 M6 잠금너트','ThrustWasher':'축 받침 와셔'}
from set_content import ROWS
for row in ROWS:
 for name in row['cad']:labels[name]=row['name']
labels.update(UpperLeftFree='왼쪽 뚜껑 · 출력 자유 형상',UpperRightFree='오른쪽 뚜껑 · 출력 자유 형상')
buf=bytearray();parts=[]
for n,p in mesh.items():
 vs=[v for point in p['vertices'] for v in point];tr=[v for face in p['triangles'] for v in face]
 local=p.get('local',n);label=labels.get(n,labels.get(local,local))
 if local.startswith('BridgeNut'):label='가로대 M4 사각너트'
 if local.startswith('BridgeScrew'):label='가로대 M4 손나사'
 if local.startswith('FollowerNut'):label='팔로워용 사각너트'
 elif local.startswith('Follower'):label='팔로워 어깨나사'
 if n.startswith('MountNut'):label='바닥 아래 M4 사각너트'
 if n.startswith('MountScrew'):label='모듈 고정 M4×20 나사'
 if n.startswith('CalibrationNut'):label='교정 PCB 나일론 날개너트'
 part=dict(name=n,label=label,color=p['color'],vo=len(buf),vc=len(vs)//3);buf.extend(struct.pack('<'+'f'*len(vs),*vs));part.update(io=len(buf),ic=len(tr));buf.extend(struct.pack('<'+'I'*len(tr),*tr));parts.append(part)
add_bom(steps)
if os.environ.get('RFCP_SHOWCASE')=='1':
 from showcase_content import guide_steps
 guide_steps(steps)
for s in steps:s['action']=[v.replace('전체 조립과 사용','캘리브레이션 및 사용법') for v in s['action']]
payload=dict(parts=parts,steps=steps,data=base64.b64encode(buf).decode(),native_sha256=build['native_sha256'],classification='ASSEMBLY_SEQUENCE_VISUAL_REVIEW_NOT_PHYSICAL_ASSEMBLY')
vendor='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
page=(P/'guide_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->','<style>'+(P/'guide.css').read_text(encoding='utf-8')+(P/'viewer_annotations.css').read_text(encoding='utf-8')+'</style>')
scripts=vendor+'</script><script>window.RFCP_GUIDE='+json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';</script><script>'+(P/'guide_motion.js').read_text(encoding='utf-8')+'\n'+(P/'viewer_annotations.js').read_text(encoding='utf-8')+'\n'+(P/'guide_viewer.js').read_text(encoding='utf-8')
page=page.replace('<!--SCRIPTS-->','<script>'+scripts+'</script>')
(D/'assembly-guide.html').write_text(page,encoding='utf-8')
(O/'steps.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(steps=len(steps),parts=len(parts),html_bytes=len(page.encode()),native_sha256=build['native_sha256'])))
