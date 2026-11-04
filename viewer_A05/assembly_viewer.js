"use strict";
(()=>{
const T=THREE,$=id=>document.getElementById(id),V=(x,y,z)=>new T.Vector3(x,y,z),data=window.A14_MODEL,clamp=(x)=>Math.max(0,Math.min(1,x));
const content={
structure:`<span class="eyebrow">구조 · 개폐</span><h2>세 모듈을 한 바닥에</h2><p>가운데 프로브가 전류를 보고, 앞뒤 클램프가 선을 잡습니다.</p><div class="callout"><b>선 넣기</b> 위 나사를 풀고 상부를 들어냅니다.<br><b>닫기</b> 왼쪽 바깥 기둥을 ㄱ자 기준에 대고 양쪽 나사를 조입니다.<br><b>중심 맞추기</b> 앞뒤 큰 노브를 조입니다.</div>`,
calibration:'',
detach:`<span class="eyebrow">지그 · 분리</span><h2>기본은 탁상용, 헤드만 분리도 가능</h2><p>슬라이더 순서대로 프로브를 열고, 교정 PCB를 위로 빼고, 바닥 체결 나사 두 개를 풀어 헤드를 분리합니다.</p><p>케이블 측정은 교정 PCB만 뺀 공통 바닥에서 하는 것이 기본입니다. 앞뒤 클램프가 선을 잡아주므로 코어·권선·SMA가 선 무게를 받지 않습니다.</p><div class="callout">헤드만 떼어 이미 연결된 선에 끼울 수도 있습니다. 그때는 선을 중심에 두고 출력 동축의 무게를 별도로 받쳐야 합니다.</div><p class="fine">나사는 관통 홀과 별도 너트를 사용합니다. 반복 개폐용 나사산을 출력 플라스틱 몸체에 직접 만들지 않습니다.</p>`,
measurement:`<span class="eyebrow">케이블 측정</span><h2>앞뒤에서 모으고, 가운데에서 측정</h2><p>교정 PCB 없이 선 전체를 코어 안에 넣습니다. 앞뒤 큰 노브가 각 클램프의 세 턱을 동시에 움직입니다. 개별 턱을 눈대중으로 조절하지 않습니다.</p><div class="callout">슬라이더는 두 노브를 함께 돌리는 원리 시연입니다. 실제로는 앞 노브·뒤 노브를 각각 돌립니다. 방향 전환 때 공칭1 mm의 너트 여유가 있어, 마지막은 조이는 방향으로 맞춥니다. 외피가 눌리기 전, 가볍게 닿으면 멈춥니다.</div><p><b>출력 연결: 프로브 SMA → R06 SMA–BNC 케이블 → 스코프 내부 50 Ω.</b> 새 현장·새 케이블의 첫 측정은 프로브 SMA 뒤에 R05 10 dB 감쇠기를 넣어 최대값을 확인한 뒤 빼기를 강력히 권고합니다. 현재 3D에는 감쇠기가 없으며 직접 체결 공간·하중은 검증 전입니다. <a href="manual.html#output-connection">커넥터 방향과 출력 연결안 →</a></p><p>확인된 주파수의 정현파 성분은 교정값으로 전류로 바꿀 수 있습니다. 광대역 잡음·과도파형 전체의 전류 복원은 아직 미완료입니다.</p><div class="metric"><span>예시 선의 중심 편차</span><b id="centerError">5.83 mm</b></div><p class="fine">Ø6–26 mm는 기구 검토 범위입니다. 휘거나 타원형인 선, 비대칭 다발은 중심이 달라질 수 있습니다. 마찰·유격·외피 변형을 생략한 시연이며, 압착력 제한 기능은 없습니다.</p>`};

// Connections and filenames follow G2_BENCH_PROCEDURE sections 4/6 and WP 11.6.
const calibrationSteps=[
 {id:'solt',label:'0 · VNA SOLT',title:'먼저 케이블 끝에서 VNA 교정',
  connections:['VNA PORT1 / PORT2 → 실제 사용할 테스트 케이블 2개','각 케이블 끝 → 교정키트 OPEN · SHORT · LOAD','두 케이블 끝 사이 → 교정키트 THROUGH'],
  file:'calibration/',value:'VNA 교정 원본 · 키트 정의 · 설정 · 교정 ID',
  purpose:'지그를 연결하기 전에 VNA와 두 테스트 케이블의 영향을 보정합니다. 실제 사용할 케이블·어댑터를 먼저 연결하고, DUT가 접속할 케이블 끝을 기준면으로 전체 2포트 SOLT를 수행합니다.',
  note:'교정 뒤 케이블은 그대로 둡니다. 교정 표준만 빼고 같은 끝에 지그를 연결합니다. 케이블·어댑터를 바꾸거나 크게 굽혔다면 교정 유효성을 재확인하고 필요하면 다시 교정합니다.'},
 {id:'empty',label:'1 · 빈 지그',title:'빈 지그 자체의 특성 저장',
  connections:['VNA PORT1 → J1 · IN','J2 · OUT → VNA PORT2','프로브 헤드 없음 · 외장 로드 미사용'],
  file:'fixture_through_empty.s2p',value:'지그 자체의 S11 · S21 · S12 · S22',
  purpose:'프로브가 없는 Fixture A03의 반사·전달 특성을 기준으로 보관합니다. 다음 단계와 비교해 프로브 장착으로 생긴 변화를 확인합니다.',
  note:'코어를 열어 둔 상태와 헤드가 없는 상태는 다릅니다. 빈 지그는 헤드 없이 측정합니다. 빈 지그 파일만으로 프로브 교정을 계산하지 않습니다.'},
 {id:'loaded',label:'2 · 장착 through',title:'프로브를 장착한 지그 특성 저장',
  connections:['VNA PORT1 → J1 · IN','J2 · OUT → VNA PORT2','프로브 출력 SMA → 외장 50 Ω 로드'],
  file:'fixture_through_head_loaded.s2p',value:'S21,thr · S22,thr 포함 전체 복소 S2P',
  purpose:'프로브를 정상 위치에 장착하고 코어를 닫습니다. 헤드 출력을 외장 50 Ω 로드로 종단한 채 지그 출구의 전달·반사를 측정합니다. 이 파일이 출력 포트 기준 교정의 기준값입니다.',
  note:'저장 후 RF OFF. 다음 단계에서는 PORT2 케이블 끝과 같은 외장 로드의 자리만 맞바꿉니다. 프로브·지그 위치와 나머지 케이블 배치를 유지합니다.'},
 {id:'transfer',label:'3 · 프로브 전달',title:'프로브 출력의 전달 특성 저장',
  connections:['VNA PORT1 → J1 · IN','J2 · OUT → 같은 외장 50 Ω 로드','프로브 출력 SMA → VNA PORT2'],
  file:'probe_transfer_5t_Lm30.s2p',value:'S21,tr 포함 전체 복소 S2P',
  purpose:'2단계와 같은 장착 상태에서 프로브 출력을 읽습니다. 장착 through 값과 이 전달값, 로드 반사와 코어→출구 보정 K를 함께 사용해 ZT를 구합니다.',
  note:'파일명은 초기 5턴·−30 dBm 예시입니다. 실제 턴 수·레벨·기준면을 함께 기록합니다. 빈 지그 S21로 대신 나누거나 dB 값만 단순히 빼지 않습니다.'},
 {id:'load',label:'4 · 로드 반사',title:'같은 외장 50 Ω 로드의 반사 저장',
  connections:['별도 SOL 교정한 VNA PORT2 · SMA 암 → 같은 외장 로드 · SMA 수','테스트 케이블·지그·프로브는 이 측정에서 분리'],
  file:'primary_load_s11.s1p',value:'외장 로드의 복소 반사계수 ΓL',
  purpose:'RF OFF 후 기존 2포트 교정과 배치를 저장하고 P2 테스트 케이블을 분리합니다. VNA의 SMA 암 포트에 모델이 확인된 수형 OPEN·SHORT·LOAD 표준을 차례로 연결해 별도 1포트 SOL 교정을 수행·적용·저장합니다. 그 암 기준면에 2·3단계에서 쓴 수형 외장 로드를 직접 연결해 복소 ΓL을 측정합니다. 보유 표준의 성별·모델을 먼저 확인합니다.',
  note:'M/M 케이블 끝과 수형 로드는 직접 연결되지 않습니다. F/F 어댑터만 추가하고 이전 교정을 적용하지 않습니다. 작업용 로드는 SOL 표준이 아닙니다. 물리 P2 반사(S22)를 선택해 1포트 S1P로 내보내면 파일 안에서는 S11입니다. 로드·암 기준면·표준 모델·물리 포트와 별도 1포트 교정 ID를 기록합니다. through/전달을 다시 측정할 때는 원래 2포트 배치를 복구하고 유효성을 재확인합니다.'}
];
const soltSteps=[
 {label:'P1 · OPEN',port:1,standard:'OPEN'},
 {label:'P1 · SHORT',port:1,standard:'SHORT'},
 {label:'P1 · LOAD',port:1,standard:'LOAD'},
 {label:'P2 · OPEN',port:2,standard:'OPEN'},
 {label:'P2 · SHORT',port:2,standard:'SHORT'},
 {label:'P2 · LOAD',port:2,standard:'LOAD'},
 {label:'P1 ↔ P2 · THROUGH',port:0,standard:'THROUGH'},
 {label:'적용 · 확인',port:0,standard:'VERIFY'}
];
let soltIndex=0;
let calibrationIndex=0;
function soltInstructions(){
 const x=soltSteps[soltIndex];
 const current=x.standard==='VERIFY'?'필요한 표준 측정을 마치면 SOLT_12를 적용하고 저장합니다. 알려진 THROUGH와 LOAD를 각각 다시 연결해 키트의 예상 응답과 일치하는지 확인합니다. 화면은 THROUGH 재확인 연결입니다.':x.standard==='THROUGH'?'두 케이블 끝을 키트 정의와 일치하는 THROUGH로 연결합니다. 이 연결의 양방향 전달·반사를 VNA 교정용으로 측정합니다.':`PORT${x.port} 케이블 끝에 교정키트의 ${x.standard} 표준을 연결하고, 해당 포트·표준의 교정 측정을 저장합니다. 다른 포트는 이번 표준 측정에 연결하지 않습니다.`;
 return `<div class="callout"><b>${x.label}</b><br>${current}</div><p>LOAD는 특성이 정의된 <b>SOLT 교정 표준</b>입니다. 나중에 ΓL을 측정할 임의의 외장 50 Ω 종단을 이상적인 교정 표준으로 가정하지 않습니다. OPEN·SHORT·THROUGH도 실제 키트 정의를 선택합니다.</p><p>교정 후에는 같은 케이블과 기준면을 유지하고, 표준을 지그로 교체합니다. 빈 지그 through는 SOLT의 THROUGH 표준을 대신하지 않습니다.</p><p class="fine">아래 버튼은 연결 안내를 바꿉니다. 장비 교정 실행·적용·저장은 LibreVNA에서 합니다. 표준 재측정은 교정 설정·재접속 점검이며, 독립적인 절대 정확도 검증은 별도입니다.</p>`;
}
function calibrationContent(){
 const step=calibrationSteps[calibrationIndex];
 const x=soltSteps[soltIndex];
 const connections=step.id==='solt'?(x.port?[`PORT${x.port} → 테스트 케이블 → 키트 ${x.standard}`]:['PORT1 케이블 끝 ↔ THROUGH ↔ PORT2 케이블 끝']):step.connections;
 const action=step.id==='solt'?(x.standard==='VERIFY'?'SOLT_12를 적용·저장하고 THROUGH와 LOAD를 재확인합니다.':x.port?`키트의 ${x.standard} 표준을 연결하고 PORT${x.port} 교정 항목을 측정합니다.`:'키트의 THROUGH로 두 케이블 끝을 연결해 측정합니다.'):{empty:'프로브 없이 지그 자체를 측정합니다.',loaded:'프로브를 장착하고 코어를 닫아 측정합니다.',transfer:'2단계와 같은 장착 상태에서 프로브 출력을 측정합니다.',load:'P2 암 포트에서 별도 1포트 SOL 교정을 한 뒤 수형 로드를 직접 연결합니다.'}[step.id];
 const reminder={solt:'교정 뒤 케이블은 유지하고, 표준만 지그로 바꿉니다.',empty:'연결을 바꿀 때는 RF OFF.',loaded:'RF OFF 후, 프로브·지그를 고정한 채 P2와 로드만 맞바꿉니다.',transfer:'2단계와 같은 외장 로드·케이블 배치를 유지합니다.',load:'별도 SOL 적용 후 P2 반사(S22)를 S1P로 저장합니다. 2포트 교정과 ID를 구분합니다.'}[step.id];
 return `<span class="eyebrow">${step.id==='solt'?'준비 · VNA와 테스트 케이블':'Fixture A03 · 측정 '+calibrationIndex+' / 4'}</span><h2>${step.title}</h2>
 <div class="connections">${connections.map((text,i)=>`<div class="connection" style="--c:${step.id==='solt'?(x.port===2?'#806fa2':'#ca8751'):step.id==='load'?'#806fa2':(step.id==='transfer'?['#ca8751','#c6a54a','#806fa2']:['#ca8751','#806fa2','#c6a54a'])[i]}">${text}</div>`).join('')}</div>
 <p>${action}</p><section class="cal-save"><h3>LibreVNA에서 저장</h3><code>${step.file}</code></section>
 <p class="fine">${reminder}</p>
 <details><summary>상세 절차 · 기록</summary>
 <p>${step.purpose}</p><p>${step.note}</p><p><b>저장할 값:</b> ${step.value}</p><p class="fine">이 화면은 연결 안내입니다. 측정·교정 실행과 원본 파일 저장은 LibreVNA에서 합니다.</p>
 ${step.id==='solt'?soltInstructions():''}
 <h3>시작 설정과 교정 기록</h3><p>케이블 끝을 기준면으로 전체 2포트 SOLT 교정을 하고, 교정 ID·키트·케이블·로드 ID와 장비 설정을 보관합니다. 초기에는 외부 에너지원 없는 VNA 벤치에서 시작합니다. 연결을 바꿀 때는 RF OFF로 둡니다.</p><p>각 구간은 같은 주파수 점을 사용합니다. through/전달용 케이블 끝 2포트 교정과 로드용 암 포트 1포트 교정은 별도입니다. 시작 설정안은 1–100 MHz, −30 dBm, IF BW 1 kHz, 평균 4회입니다. 실제 지원값과 변경 이력을 기록합니다.</p>
 <h3>원본 파일 보관</h3><p><code>measurements/raw/YYYYMMDD_runNN/</code> 아래 별도 실행 폴더에 복소 Touchstone 원본을 저장합니다.</p><ol>${calibrationSteps.map(x=>`<li><code>${x.file}</code><br>${x.value}</li>`).join('')}</ol><p>교정 원본·설정·배선 사진·head/fixture ID·방향·측정 시각을 함께 보관합니다. 이전 실행을 덮어쓰지 않습니다.</p>
 <h3>역방향과 반복성 확인</h3><p>지그 J1/J2 방향을 바꿔 2·3단계를 반복하고 <code>fixture_through_head_loaded_reverse.s2p</code>, <code>probe_transfer_5t_Lm30_reverse.s2p</code>를 저장합니다. 정/역방향 일치와 함께 재장착 5회·세 레벨·위치·직접 픽업·왕복 상쇄를 확인합니다.</p><p>같은 A03으로1–500 MHz 보정을 수행하고, 주파수별 ZT·불확도·유효성을 기록합니다. 300 MHz에서 일괄 참고 처리하지 않습니다. −6 dB 전달량 자체는500 MHz를 제외할 이유가 아닙니다. 깊은 null이나 큰 직접 픽업이 있는 구간을 자동으로 유효 처리하지 않습니다.</p><p>오프라인 분석기에 출력 기준 계산을 구현하고 합성 파일 시험을 통과했습니다. 장착 through·전달의 정/역방향 S2P, 로드 S1P, K와 주파수별 검토 기록을 함께 사용합니다. 기준면·개체·불확도·null·직접 픽업·반복성 조건이 충족된 구간만 절대 ZT를 출력합니다. 이 화면은 연결 안내이며 실물 교정 데이터는 아직 없습니다.</p>
 <p class="fine">실제 교정에는 Fixture A03를 사용합니다. 화면의 평판은 A03과 외곽·고정홀이 같은 공통 장착 형상입니다. 제조 기준은 A03 원본입니다. VNA·동축·교정 표준·로드는 연결 설명용 외형이며 실제 제품 치수가 아닙니다. 실측 교정 데이터는 아직 없습니다. <a href="design-review.html">A03 보정 원리와 수치 →</a> · <a href="https://github.com/jankae/LibreVNA/blob/master/Documentation/UserManual/manual.tex">LibreVNA 공식 교정 절차</a></p></details>`;
}
function updateAnnotations(){
 let labels=[['프로브',[0,60,6.35]],['앞 클램프',[0,80,-113.65]],['뒤 클램프',[0,80,126.35]],['88 mm · 공칭',[-110,-35,158]]];
 if(mode==='calibration'){
  const id=calibrationSteps[calibrationIndex].id;
  labels=id==='load'?[['VNA · 연결 개념도',[-150,12,0]],['PORT1 · 이 측정에서 미사용',[-94,0,-30]],['PORT2 · 별도 SOL 암 기준면',[-94,0,30]],['수형 외장 50 Ω 로드 · 직접 연결',[-68,0,30]]]:[
   ['VNA PORT1 → IN',[0,38,-28]],
   [id==='transfer'?'OUT → 50 Ω 로드':'OUT → VNA PORT2',[0,38,40.7]]
  ];
  if(id==='loaded'||id==='transfer')labels.push([id==='loaded'?'헤드 출력 → 50 Ω 로드':'헤드 출력 → VNA PORT2',[0,-49,37]]);
  if(id==='solt'){
   const x=soltSteps[soltIndex],thru=x.port===0,z=x.port===1?-30:30;
   labels=[['VNA · 연결 개념도',[-150,12,0]],['PORT1',[-94,0,-30]],['PORT2',[-94,0,30]]];
   if(thru)labels.push(['교정키트 THROUGH',[25,0,0]],['P1 기준면',[25,0,-8]],['P2 기준면',[25,0,8]]);
   else labels.push([`PORT${x.port} 케이블 끝 · 기준면`,[25,0,z]],[`교정키트 ${x.standard}`,[38,0,z]]);
  }
 }
 annotations.set(labels.map(([text,pos])=>[text,V(...pos)]));
}
function renderCalibration(){
 const step=calibrationSteps[calibrationIndex];
 $('explanation').innerHTML=calibrationContent();$('sceneTitle').textContent=step.title;
 $('calibrationSteps').innerHTML=calibrationSteps.map((x,i)=>`<button data-cal-step="${i}" aria-pressed="${i===calibrationIndex}" class="${i===calibrationIndex?'active':''}">${x.label}</button>`).join('');
 $('soltPanel').hidden=step.id!=='solt';
 $('soltSteps').innerHTML=soltSteps.map((x,i)=>`<button data-solt-step="${i}" aria-pressed="${i===soltIndex}" class="${i===soltIndex?'active':''}">${x.label}</button>`).join('');
 $('calibrationBenchNote').hidden=!['solt','load'].includes(step.id);
 $('calibrationBenchNote').textContent=step.id==='load'?'VNA PORT2 암 · 별도 1포트 SOL 기준면 → 수형 외장 로드 직접 연결':'VNA 본체와 케이블은 유지 · 표준만 교체 · 키트와 일치하는 SOLT 적용';
 $('opening').value=0;$('openLabel').hidden=true;
 renderer.domElement.setAttribute('aria-label',step.title+' · 3D 연결 안내');
 $('motionNote').textContent=step.id==='empty'?'헤드 없는 전기 연결을 보여 줍니다. 실물에서는 지그를 안정되게 지지합니다.':step.id==='load'?'로드 반사는 별도 SOL로 교정한 VNA 암 포트에서 측정합니다. 실제 제품 치수가 아닌 연결 개념도입니다.':step.id==='solt'?'VNA·표준은 연결 개념도입니다. 이 2포트 교정의 기준면은 케이블 끝입니다.':'커넥터 연결을 설명하는 장면입니다. 연결 변경은 RF OFF에서 진행합니다.';
 updateAnnotations();
}

const host=$('stage'),scene=new T.Scene();scene.background=new T.Color('#f8fafc');const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputEncoding=T.sRGBEncoding;host.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','RF 프로브와 앞뒤 중심 클램프 전체 3D 조립체');renderer.domElement.setAttribute('role','img');const camera=new T.PerspectiveCamera(36,1,.1,3000),orbit=new T.OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;scene.add(new T.HemisphereLight(0xffffff,0x77909f,1.15));for(const [x,y,z] of [[120,180,80],[-100,70,-100]]){const light=new T.DirectionalLight(0xffffff,.5);light.position.set(x,y,z);scene.add(light);}
const str=atob(data.data),bytes=new Uint8Array(str.length);for(let i=0;i<str.length;i++)bytes[i]=str.charCodeAt(i);const meshes=[];
for(const p of data.parts){const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(new Float32Array(bytes.buffer,p.vo,p.vc*3),3));geo.setIndex(new T.BufferAttribute(new Uint32Array(bytes.buffer,p.io,p.ic),1));geo.computeVertexNormals();const m=new T.Mesh(geo,new T.MeshStandardMaterial({color:p.color,roughness:.72,metalness:.07,side:T.DoubleSide,flatShading:true}));m.material.color.convertSRGBToLinear();m.userData=p;scene.add(m);meshes.push(m);}
const cable=new T.Mesh(new T.CylinderGeometry(6,6,430,48),new T.MeshStandardMaterial({color:'#8a79a8'}));cable.rotation.x=Math.PI/2;cable.position.z=6.35;scene.add(cable);
const line=new T.Line(new T.BufferGeometry().setFromPoints([V(0,0,-225),V(0,0,235)]),new T.LineDashedMaterial({color:'#2686a1',dashSize:5,gapSize:3}));line.computeLineDistances();scene.add(line);
const scaleLine=new T.Line(new T.BufferGeometry().setFromPoints([V(-110,-88,158),V(-110,0,158),V(0,0,158)]),new T.LineBasicMaterial({color:'#2686a1',transparent:true,opacity:.65}));scene.add(scaleLine);
function tube(points,color,r=2.5){const m=new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>V(...p))),48,r,10,false),new T.MeshStandardMaterial({color,roughness:.75}));scene.add(m);return m;}
const outputCoax=tube([[0,-49,16],[0,-49,40],[-25,-49,65],[-145,-49,75],[-170,-49,145]],'#817095');
const inputCoax=tube([[0,12,-28],[0,38,-28],[-40,52,-35],[-150,52,-75]],'#b57a4f');
const load=new T.Mesh(new T.CylinderGeometry(5.8,5.8,26,24),new T.MeshStandardMaterial({color:'#c6b06c'}));load.position.set(0,25,40.7);scene.add(load);
const fixtureOutputCoax=tube([[0,12,40.7],[0,40,40.7],[35,52,60],[150,52,105]],'#817095');
const headLoad=load.clone();headLoad.rotation.x=Math.PI/2;headLoad.position.set(0,-49,29);scene.add(headLoad);
const isolatedLoad=load.clone();isolatedLoad.rotation.z=Math.PI/2;isolatedLoad.position.set(-81,0,30);scene.add(isolatedLoad);
// Bench equipment is a connection diagram, not a dimensional LibreVNA model.
const vna=new T.Group();scene.add(vna);
function benchBox(size,pos,color){const m=new T.Mesh(new T.BoxGeometry(...size),new T.MeshStandardMaterial({color,roughness:.65,metalness:.15}));m.position.set(...pos);vna.add(m);return m;}
benchBox([100,22,90],[-150,0,0],'#496171');
benchBox([94,1,84],[-150,11.5,0],'#dbe5e9');
benchBox([62,1,8],[-156,12.2,0],'#16869c');
for(const z of [-30,30]){
 const port=new T.Mesh(new T.CylinderGeometry(5,5,6,24),new T.MeshStandardMaterial({color:'#c6b06c',metalness:.6,roughness:.4}));port.rotation.z=Math.PI/2;port.position.set(-97,0,z);vna.add(port);
}
const loadCoax=tube([[-94,0,30],[-62,0,38],[-20,0,38],[25,0,30]],'#817095');
const soltCoax1=tube([[-94,0,-30],[-62,0,-38],[-20,0,-38],[25,0,-30]],'#b57a4f');
const throughCoax1=tube([[-94,0,-30],[-40,0,-42],[25,0,-30],[25,0,-8]],'#b57a4f');
const throughCoax2=tube([[-94,0,30],[-40,0,42],[25,0,30],[25,0,8]],'#817095');
const soltThrough=new T.Mesh(new T.CylinderGeometry(5.5,5.5,16,24),new T.MeshStandardMaterial({color:'#16869c',roughness:.5}));soltThrough.rotation.x=Math.PI/2;soltThrough.position.set(25,0,0);scene.add(soltThrough);
const soltStandard=isolatedLoad.clone();soltStandard.material=isolatedLoad.material.clone();scene.add(soltStandard);
const referencePlanes=[-30,30].map(z=>{const ring=new T.Mesh(new T.RingGeometry(10,11.5,40),new T.MeshBasicMaterial({color:'#16869c',side:T.DoubleSide}));ring.rotation.y=Math.PI/2;ring.position.set(25,0,z);scene.add(ring);return ring;});
const benchObjects=[vna,isolatedLoad,loadCoax,soltCoax1,throughCoax1,throughCoax2,soltThrough,soltStandard,...referencePlanes];
const knobMarks=[-118.65,121.35].map(z=>{const p=new T.Group();p.position.set(80,76.8,26+z);const m=new T.Mesh(new T.BoxGeometry(2,.4,10),new T.MeshBasicMaterial({color:'#215d74'}));m.position.z=6;p.add(m);scene.add(p);return p;});
let mode='structure',selected=null,focusProbe=false;
const annotations=window.RFCP_ANNOTATIONS.create({stage:host,camera,resetButton:$('reset')});
annotations.set([['프로브',[0,60,6.35]],['앞 클램프',[0,80,-113.65]],['뒤 클램프',[0,80,126.35]],['88 mm · 공칭',[-110,-35,158]]].map(([text,pos])=>[text,V(...pos)]));
function pose(p,r,opening,explode){let x=0,y=0,z=0,visible=true;const g=p.group,headLift=120*clamp((opening-.25)/.75),release=75*clamp(opening/.25);
 if(g==='HEAD_SCREW'){y=release;visible=opening<=.25;}
 if(g==='HEAD_CAP')y=['UpperLeft','UpperRight'].includes(p.name)?headLift:Math.max(0,headLift-1.8);
 if(g==='CABLE'){
  const t=r-8,sg=p.subgroup;
  if(['DRIVE','TOP','TOPSCREW'].includes(sg))y=t;
  if(sg.startsWith('JAW')){const a=Number(sg.slice(-1))===1?210:330;x=Math.cos(a*Math.PI/180)*t;y=Math.sin(a*Math.PI/180)*t;}
  if(sg==='TOP')y+=65*clamp((opening-.25)/.75);
  if(sg==='TOPSCREW'){y+=25*clamp(opening/.25);visible=opening<=.25;}
  if(explode){if(sg==='DRIVE')z+=45*explode;if(sg==='TOP')y+=70*explode;if(sg.startsWith('JAW')){x+=Math.sign(x|| (sg==='JAW1'?-1:1))*30*explode;y-=20*explode;z-=25*explode;}}
 }
 if(explode&&g==='HEAD_CAP')y+=100*explode;
 if(explode&&p.explode){x+=p.explode[0]*explode;z+=p.explode[2]*explode;}
 if(explode&&p.name.startsWith('UpperJoint'))z+=(p.name.endsWith('Screw')||p.name.endsWith('RearWasher')?-35:35)*explode;
 if(explode&&p.name.startsWith('LowerJoint'))z+=(p.name.endsWith('Screw')||p.name.endsWith('RearWasher')?-35:35)*explode;
 if(explode&&p.name.startsWith('BaseJoint'))y+=(p.name.endsWith('Screw')||p.name.endsWith('RearWasher')?-30:30)*explode;
 if(explode&&/Keeper/.test(p.name)&&g!=='BASE')z+=50*explode;
 if(explode&&p.name==='PCB')z+=65*explode;
 if(explode&&p.name==='SMAEnvelope')z+=65*explode;
 return{x,y,z,visible};
}
function update(){const opening=Number($('opening').value)/100,exp=Number($('explode').value)/100,close=Number($('centering').value)/100,det=Number($('detach').value)/100,r=mode==='measurement'?13-7*close:8;const op=mode==='detach'?clamp(det/.2):opening;
 for(const m of meshes){const p=m.userData,q=pose(p,r,p.group==='CABLE'&&mode==='detach'?0:op,mode==='structure'?exp:0);m.position.set(q.x,q.y,q.z);m.visible=q.visible;
  if(['UpperLeft','UpperRight'].includes(p.name)){
   const a=m.geometry.attributes.position;if(!m.userData.original)m.userData.original=a.array.slice();const src=m.userData.original,relax=Math.min(1.8,120*clamp((op-.25)/.75));
   for(let i=0;i<a.count;i++){const u=clamp((103-Math.abs(src[i*3]))/63);a.array[i*3+1]=src[i*3+1]-relax*u*u*(3-2*u);}
   a.needsUpdate=true;m.geometry.computeVertexNormals();
  }
  if(p.group.startsWith('CALIBRATION'))m.visible=mode==='calibration'||mode==='detach';
  if(mode==='detach'){
   if(p.group==='CALIBRATION'){m.position.y=80*clamp((det-.3)/.2);m.position.x=200*clamp((det-.5)/.1);}
   if(p.group==='CALIBRATION_SCREW'){m.position.y=20*clamp((det-.2)/.1);m.visible=det<=.3;}
   if(p.group.startsWith('HEAD_')){m.position.y+=100*clamp((det-.7)/.3);m.position.x-=185*clamp((det-.7)/.3);}
   if(p.group==='MOUNT_Head'){m.position.y=30*clamp((det-.6)/.1);m.visible=det<.7;}
  }
  if(mode==='calibration'){const id=calibrationSteps[calibrationIndex].id;if(id==='load'||id==='solt'||(id==='empty'&&(p.group.startsWith('HEAD_')||p.group==='MOUNT_Head')))m.visible=false;}
  if(focusProbe&&(p.group==='CABLE'||p.group==='BASE'||p.group.startsWith('MOUNT_')))m.visible=false;
  const plastic=p.printed||p.group==='BASE'||(p.group==='CABLE'&&['Frame','DriveYoke','TopBridgeJaw','Jaw1','Jaw2'].includes(p.local));const tr=plastic&&$('transparent').checked;m.material.transparent=tr;m.material.opacity=tr?.2:1;m.material.depthWrite=!tr;
 }
 const cc=mode==='measurement'?window.C01_CENTER_CABLE(r,6):[0,0];cable.position.set(cc[0],cc[1],6.35);cable.visible=mode==='measurement'||(mode==='structure'&&!exp);const cal=mode==='calibration',id=calibrationSteps[calibrationIndex].id;
 const bench=cal&&(id==='solt'||id==='load'),solt=cal&&id==='solt',standard=soltSteps[soltIndex],thru=solt&&standard.port===0;
 outputCoax.visible=mode==='measurement'||(cal&&id==='transfer');inputCoax.visible=cal&&!bench;load.visible=cal&&id==='transfer';
 fixtureOutputCoax.visible=cal&&(id==='empty'||id==='loaded');headLoad.visible=cal&&id==='loaded';isolatedLoad.visible=cal&&id==='load';
 vna.visible=bench;loadCoax.visible=solt&&!thru;soltCoax1.visible=solt&&!thru;
 throughCoax1.visible=throughCoax2.visible=soltThrough.visible=thru;soltStandard.visible=solt&&!thru;
 soltStandard.position.set(38,0,standard.port===1?-30:30);
 soltStandard.material.color.set({OPEN:'#e0e9f0',SHORT:'#677680',LOAD:'#16869c'}[standard.standard]||'#16869c');
 referencePlanes.forEach((ring,i)=>{ring.visible=bench&&(thru||(!solt&&i===1)||(solt&&standard.port===i+1));ring.position.set(solt?25:-94,0,thru?(i===0?-8:8):(i===0?-30:30));ring.rotation.y=thru?0:Math.PI/2;});
 line.visible=scaleLine.visible=$('guides').checked&&!focusProbe&&!bench;for(const k of knobMarks){k.visible=!focusProbe&&!bench;k.rotation.y=-(r-13)*2*Math.PI;}$('openingOut').textContent=opening===0?'닫힘':opening<=.25?'나사 풀기':'상부 들어내기';$('centerOut').textContent=Math.round(close*100)+'%';if($('centerError'))$('centerError').textContent=Math.hypot(...cc).toFixed(2)+' mm';$('detachOut').textContent=det<.2?'프로브 상부 열기':det<.3?'PCB 나사 네 개 풀기':det<.6?'교정 PCB 빼기':det<.7?'바닥 나사 풀기':'헤드 분리';
}
function fit(direction){const box=new T.Box3();for(const m of [...meshes,...benchObjects])if(m.visible)box.union(new T.Box3().setFromObject(m));const sphere=box.getBoundingSphere(new T.Sphere()),target=sphere.center,dir=direction||camera.position.clone().sub(orbit.target).normalize();const fovy=camera.fov*Math.PI/180,fovx=2*Math.atan(Math.tan(fovy/2)*camera.aspect),d=sphere.radius/Math.sin(Math.min(fovy,fovx)/2)*1.06;orbit.target.copy(target);camera.position.copy(target).add(dir.normalize().multiplyScalar(d));orbit.update();}
function reset(view){if(!view||view==='all')focusProbe=false;if(view==='probe')focusProbe=true;update();fit(view==='front'?V(0,.03,1):view==='side'?V(1,.08,0):view==='top'?V(.01,1,.01):V(1,.62,.95));}
function setMode(v){mode=v;$('explanation').innerHTML=content[v];$('sceneTitle').textContent={structure:'같은 바닥, 같은 중심축',calibration:'교정 PCB를 넣고 VNA에 연결',detach:'PCB를 빼고, 필요하면 헤드만 분리',measurement:'앞뒤 클램프가 선을 중심으로'}[v];$('openLabel').hidden=v==='measurement'||v==='detach';$('centerLabel').hidden=v!=='measurement';$('detachLabel').hidden=v!=='detach';$('explodeLabel').hidden=v!=='structure';for(const id of ['opening','centering','detach','explode'])$(id).value=0;document.querySelectorAll('[data-mode]').forEach(b=>{const on=b.dataset.mode===v;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});$('calibrationPanel').hidden=v!=='calibration';
 $('motionNote').textContent='나사 제거 후 상부가 열립니다. 탄성부의 변형은 형상 설명이며 힘·마찰 시뮬레이션은 아닙니다.';
 if(v==='calibration')renderCalibration();else updateAnnotations();update();reset();}
$('calibrationSteps').onclick=e=>{const button=e.target.closest('[data-cal-step]');if(!button)return;calibrationIndex=Number(button.dataset.calStep);renderCalibration();update();reset();};
$('soltSteps').onclick=e=>{const button=e.target.closest('[data-solt-step]');if(!button)return;soltIndex=Number(button.dataset.soltStep);renderCalibration();update();reset();};
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>reset(b.dataset.view));for(const id of ['opening','centering','detach','explode','guides','transparent'])$(id).oninput=()=>{if(id==='opening')$('explode').value=0;if(id==='explode')$('opening').value=0;update();if(['opening','detach','explode'].includes(id))fit();};$('reset').onclick=()=>reset();
const descriptions={LowerCenter:'프로브 중앙 몸체 — 코어 받침과 보강된 PCB 창을 유지합니다.',LowerArmLeft:'왼팔 — M4×30 2개와 양쪽 와셔로 중앙 몸체에 체결합니다.',LowerArmRight:'오른팔 — M4×30 2개와 양쪽 와셔로 중앙 몸체에 체결합니다.',UpperLeft:'왼쪽 뚜껑 — 오른쪽과 중앙 두꺼운 겹침부에서 M4×30 2개로 연결합니다. 자유 형상 STL만 출력합니다.',UpperRight:'오른쪽 뚜껑 — 별도 스프링 없이 기존2.4 mm 탄성부를 유지합니다.',BaseFront:'앞 바닥 — 아래에서 M4×20을 넣고 위에 와셔와 육각너트를 체결합니다.',BaseCenter:'가운데 바닥 — 바닥3조각을 조립한 뒤 모듈을 올립니다. 중심높이88 mm.',BaseRear:'뒤 바닥 — 아래에서 M4×20을 넣고 위에 와셔와 육각너트를 체결합니다.',LowerBody:'프로브 아래 몸체 — 왼쪽 바깥 기둥의 ㄱ자 기준에 뚜껑을 가볍게 맞대고 조입니다. 코어는 넓은 일체형 받침에 놓습니다.',UpperLid:'일체형 뚜껑 — 양옆 멈춤 기둥과 두 플라스틱 탄성부를 함께 출력합니다. 별도 스프링은 없지만 탄성 원리를 이용하므로 힘·피로 시험이 필요합니다.',LowerKeeper:'아래 코어 고정바 — 가로대를 위로 옮겨 SMA 플러그와 S+ / S− 앞을 열었습니다. 코어에 닿는 면과 안쪽 이탈 방지턱은 유지했습니다.',UpperKeeper:'위 코어 고정바 — 나사로 분리됩니다. 안쪽 두 턱은 이탈 방지용이며 케이블을 잡는 턱이 아닙니다.',CommonBase:'공통 바닥 — 프로브와 앞뒤 클램프가 동일한 Y=-72 면에 놓입니다. 정렬용 어깨는 억지 끼워맞춤을 하지 않습니다.',FixedCore:'아래 페라이트 코어 — 권선을 감는 실제 코어입니다.',MovingCore:'위 페라이트 코어 — 아래 코어와 깨끗한 면끼리 맞닿아야 합니다.',PCB:'프로브 헤드 PCB — 36×28 mm. M2 나일론 나사와 나일론 너트 두 쌍으로 고정합니다. 철 나사의 RF 무영향을 보증한 설계가 아닙니다.',FlatPCB:'교정용 PCB — 교정 때만 설치합니다.',HeadHandScrews:'프로브 개폐 손나사 — 양옆의 노출된 손잡이를 돌립니다. 끝까지 닫을 때 바깥 멈춤 기둥이 하중을 받습니다.'};
const ray=new T.Raycaster();let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const b=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new T.Vector2((e.clientX-b.left)/b.width*2-1,1-(e.clientY-b.top)/b.height*2),camera);const hit=ray.intersectObjects(meshes.filter(m=>m.visible),false)[0];if(selected)selected.material.emissive.set(0);selected=hit?.object;if(selected){$('selection').closest('details').open=true;selected.material.emissive.set('#244652');const p=selected.userData;$('selection').textContent=descriptions[p.name]||(['LeadStud','HandKnob','TopJamNut'].includes(p.local)?'큰 조절 노브 — 이 노브 하나가 세 턱을 동시에 움직입니다.':p.local==='DriveYoke'?'연결틀 — 대각선 홈 위쪽을 4 mm 높여 끝을 막았습니다. 홈 위 남는 두께는 공칭 3.7 mm이며 핀은 앞에서 조립합니다.':p.local==='TopBridgeJaw'?'위 가로대와 턱 — 작은 손나사 두 개를 빼고 들어내면 연결된 선을 넣을 수 있습니다.':p.group==='CABLE'?'케이블 중심 클램프 — 열린 가이드에 부품을 넣고 기성 체결품으로 연결합니다. 부품별 규격은 BOM에서 확인할 수 있습니다.':'체결품 / 연결부 — 형상 검토용입니다. 실제 규격과 조임은 조립 검토서를 따릅니다.');}});
new ResizeObserver(()=>{camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight,false);}).observe(host);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight,false);$('verification').textContent=data.summary;setMode('structure');$('loading').hidden=true;
function animate(){requestAnimationFrame(animate);if(document.hidden)return;orbit.update();annotations.update(mode!=='detach'&&(!focusProbe||mode==='calibration'));renderer.render(scene,camera);}animate();
})();
