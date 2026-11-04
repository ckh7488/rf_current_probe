from pathlib import Path
P=Path(__file__).resolve().parent
q=P/'build.py';s=q.read_text(encoding='utf-8').replace('clamp_A06_DRAFT','clamp_A07_DRAFT').replace("'revision':'A06'","'revision':'A07'");q.write_text(s,encoding='utf-8')
q=P/'content.js';s=q.read_text(encoding='utf-8').replace('プロ브','프로브');q.write_text(s,encoding='utf-8')
q=P/'template.html';s=q.read_text(encoding='utf-8').replace('A06','A07')
s=s.replace('<b>분리 순서</b><div class="stepbuttons"', '<label for="detachMotion"><b>분리 순서</b></label><input id="detachMotion" type="range" min="0" max="5" step="0.01" value="0" aria-label="지그와 헤드 분리 순서"><div class="stepbuttons"')
s=s.replace('스프링은 실제 감긴 선 대신 외형으로 표시합니다.','패드의 눌림과 자동 중심 클램프는 아직 구현 전입니다.')
q.write_text(s,encoding='utf-8')
q=P/'viewer.js';s=q.read_text(encoding='utf-8').replace('A06','A07').replace('floor.position.y=-73','floor.position.y=-88')
s=s.replace('const d=Math.max(0,(v-25)/75)*80,fy=Math.max(0,d-3.95);','const d=Math.max(0,(v-25)/75)*120;')
s=s.replace(" if($('floatTravel'))$('floatTravel').textContent=fy.toFixed(2)+' mm';",'')
s=s.replace('/Tray|Cage|Cassette|Keeper[12]|Collar|Retainer|Bracket|FrontGuard/', '/Shell|Keeper$|Base$/')
a=s.index('function reset(view)');b=s.index('function tube(',a)
s=s[:a]+'''function reset(view){
 const target=V(0,mode==='detach'&&detachStep>=4?100:22,25);
 const distance=600*Math.max(1,1/camera.aspect);
 controls.target.copy(target);let d;
 if(view==='front')d=V(0,0,distance);
 else if(view==='top')d=V(0,distance,.01);
 else if(view==='side')d=V(distance,0,.01);
 else d=V(.48,.32,.7).normalize().multiplyScalar(distance);
 camera.position.copy(target).add(d);camera.up.set(0,1,0);controls.update();
}
'''+s[b:]
a=s.index('function refreshLabels()');b=s.index('function stop()',a)
s=s[:a]+'''function refreshLabels(){clearLabels();
 const cap=()=>parts.get('Head_UpperShell').position.y;
 const low=()=>parts.get('Head_LowerShell').position.y;
 if(mode==='mechanism'){
  label('상부: 완전히 분리',()=>V(34,30+cap(),17));
  label('잠금부: 코어에서 약 54 mm',()=>V(50,22,73),'#b1792d',[20,20]);
  label('바닥에 직접 닿는 발',()=>V(-48,-67,75));
  if($('inside').checked)label('실리콘 패드 · 눌림 미검증',()=>V(-9,-31,7),'#bd477e');
 }else if(mode==='calibration'){
  label('VNA Port 1',()=>V(-120,45,-60),'#c07516');
  label('50 Ω 로드',()=>V(0,26,40.7),'#8755ad',[0,-40]);
  label('VNA Port 2',()=>V(125,-18,145),'#267cc1');
  label('중앙: 코어 안',()=>V(0,8,-15),'#c07516',[55,30]);
  label('귀환: 코어 밖',()=>V(-63,4,15),'#17897e',[-35,0]);
 }else if(mode==='field'){
  label('케이블 Ø8 mm · 중심 배치 예시',()=>V(0,0,-95),'#735eb5');
  label('보호·감쇠 → 50 Ω 계측기',()=>V(125,-18,145),'#267cc1');
  label('바닥 고정 기본 · 헤드 분리 가능',()=>V(-55,-73,75));
 }else if(mode==='detach'){
  if(detachStep<5)label('바닥은 남김',()=>V(-65,-75,-32),'#596d83');
  if(detachStep<1)label('상부를 먼저 열기',()=>V(30,30+cap(),16));
  if(detachStep>=1&&detachStep<2)label('큰 교정 PCB 제거',()=>V(60,parts.get('FlatPCB').position.y,43),'#11897d');
  if(detachStep>=2&&detachStep<3)label('바닥 손나사 제거',()=>V(48,-60+parts.get('BaseHandScrews').position.y,75),'#bb771d');
  if(detachStep>=3)label('작은 PCB·권선은 함께 이동',()=>V(0,-49+low(),20));
 }
}
'''+s[b:]
a=s.index('function setDetachStep(');b=s.index('window.RFCP_DETACH.forEach',a)
s=s[:a]+'''function setDetachStep(i,reframe=true){detachStep=i;applyPose(0);refreshLabels();$('detachMotion').value=i;
 const labelIndex=Math.min(5,Math.ceil(i));$('detachCaption').textContent=window.RFCP_DETACH[labelIndex][1];
 document.querySelectorAll('[data-step]').forEach(b=>{b.classList.toggle('active',+b.dataset.step===Math.round(i));b.setAttribute('aria-pressed',String(+b.dataset.step===Math.round(i)));});if(reframe)reset();}
$('detachMotion').addEventListener('input',e=>setDetachStep(+e.target.value,false));
'''+s[b:]
q.write_text(s,encoding='utf-8')
print('A07 viewer integration applied')
