"use strict";
(() => {
const T=THREE, $=id=>document.getElementById(id), V=(x,y,z)=>new T.Vector3(x,y,z);
const model=window.RFCP_MODEL, source=atob(model.data), bytes=new Uint8Array(source.length);
for(let i=0;i<source.length;i++)bytes[i]=source.charCodeAt(i);
delete model.data;
const parts=new Map(), labels=[], host=$('stage'), scene=new T.Scene(); scene.background=new T.Color('#f8fafc');
const camera=new T.PerspectiveCamera(34,1,.1,3000), renderer=makeRenderer(); if(!renderer)return;
renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.outputEncoding=T.sRGBEncoding; host.prepend(renderer.domElement);
renderer.domElement.setAttribute('aria-label','실제 A07 CAD 3D 모델. 드래그로 회전하고 부품을 클릭해 설명을 확인하세요.');renderer.domElement.tabIndex=0;
const controls=new T.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.09;controls.minDistance=65;controls.maxDistance=1300;
scene.add(new T.HemisphereLight(0xffffff,0x8296a4,1.1));const light=new T.DirectionalLight(0xffffff,.7);light.position.set(50,160,220);scene.add(light);
const rig=new T.Group(),extras=new T.Group();scene.add(rig,extras);
for(const p of model.parts){
 const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(bytes.buffer,p.vo,p.vc*3),3));g.setIndex(new T.BufferAttribute(new Uint32Array(bytes.buffer,p.io,p.ic),1));g.computeVertexNormals();g.computeBoundingSphere();
 const m=new T.Mesh(g,new T.MeshStandardMaterial({color:p.color,roughness:.65,metalness:/SMA|Copper|Bolts|Nuts|Screws|Winding/.test(p.name)?.25:.02,flatShading:true,side:T.DoubleSide}));
 m.material.color.convertSRGBToLinear();m.name=p.name;m.userData=p;rig.add(m);parts.set(p.name,m);
}
const floor=new T.GridHelper(320,16,0xc7d6e0,0xe4ecf1);floor.position.y=-88;scene.add(floor);
let mode='mechanism',value=0,playing=false,started=0,selected=null,detachStep=0;
function makeRenderer(){try{return new T.WebGLRenderer({antialias:true})}catch(e){$('loading').classList.add('error');$('loading').textContent='3D 표시를 시작하지 못했습니다. 브라우저의 하드웨어 가속을 켜거나 다른 브라우저에서 열어주세요.';return null}}
function label(text,point,color='#14758e',offset=[0,0]){const el=document.createElement('div');el.className='label';el.textContent=text;el.style.setProperty('--color',color);const line=document.createElement('div');line.style.cssText='position:absolute;height:1px;transform-origin:0 0;opacity:.65;background:'+color;$('labels').append(line,el);labels.push({el,line,point,offset});}
function clearLabels(){labels.splice(0).forEach(x=>{x.el.remove();x.line.remove()});}
function applyPose(v){
 value=v;const k=window.RFCP_KINEMATICS;
 for(const m of parts.values()){const p=k.pose(m.userData,mode,v,detachStep);
  m.visible=p.visible;m.position.set(0,p.y,p.z);m.scale.set(1,p.sy,1);
 }
 const d=Math.max(0,(v-25)/75)*120;
 $('position').textContent=v<.1?'닫힘':v<=25?'손나사 두 개 빼기':`상부 ${(d).toFixed(1)} mm 분리`;
 if($('capTravel'))$('capTravel').textContent=d.toFixed(2)+' mm';

}
function transparent(){for(const m of parts.values()){const plastic=/Shell|Keeper$|Base$/.test(m.name);m.material.transparent=plastic&&$('inside').checked;m.material.opacity=m.material.transparent?.16:1;m.material.depthWrite=!m.material.transparent;}}
function reset(view){
 const target=V(0,mode==='detach'&&detachStep>=4?100:22,25);
 const distance=600*Math.max(1,1/camera.aspect);
 controls.target.copy(target);let d;
 if(view==='front')d=V(0,0,distance);
 else if(view==='top')d=V(0,distance,.01);
 else if(view==='side')d=V(distance,0,.01);
 else d=V(.48,.32,.7).normalize().multiplyScalar(distance);
 camera.position.copy(target).add(d);camera.up.set(0,1,0);controls.update();
}
function tube(points,color,radius=1.6){const path=new T.CatmullRomCurve3(points.map(a=>V(...a)));const mesh=new T.Mesh(new T.TubeGeometry(path,50,radius,9,false),new T.MeshStandardMaterial({color,roughness:.7}));extras.add(mesh);return mesh;}
function arrow(pos,dir,color,len=24){extras.add(new T.ArrowHelper(V(...dir),V(...pos),len,color,6,3));}
function clearExtras(){while(extras.children.length){const o=extras.children[0];extras.remove(o);o.traverse(x=>{x.geometry?.dispose();if(x.material){(Array.isArray(x.material)?x.material:[x.material]).forEach(m=>m.dispose());}});}}
function makeExtras(){clearExtras();
 if(mode==='calibration'||mode==='field'){
  // Straight coax through the real open saddle, curved only beyond the guard.
  const cable=new T.Mesh(new T.CylinderGeometry(1.6,1.6,61,18),new T.MeshStandardMaterial({color:'#267cc1'}));cable.rotation.x=Math.PI/2;cable.position.set(0,-49,47.5);extras.add(cable);
  tube([[0,-49,78],[0,-49,95],[65,-10,125],[125,-18,145]],'#267cc1');
  const plug=new T.Mesh(new T.CylinderGeometry(6,6,24,18),new T.MeshStandardMaterial({color:'#b7a77b',metalness:.3,roughness:.5}));plug.rotation.x=Math.PI/2;plug.position.set(0,-49,28);extras.add(plug);
  // Illustrative tie path through the two printed slots, not a force model.
  tube([[-8,-58.2,61],[-8,-43,61],[-5,-42.5,61],[0,-45.5,61],[5,-42.5,61],[8,-43,61],[8,-58.2,61],[-8,-58.2,61]],'#e58c34',.6);
 }
 if(mode==='calibration'){
  tube([[0,10,-28],[0,24,-28],[-90,35,-48],[-120,45,-60]],'#c07516');
  const load=new T.Mesh(new T.CylinderGeometry(4.5,4.5,18,24),new T.MeshStandardMaterial({color:'#8755ad'}));load.position.set(0,18.2,40.7);extras.add(load);
  arrow([0,2,-18],[0,0,1],0xd8891e,19);arrow([-62,2,20],[0,0,-1],0x17897e,26);arrow([62,2,20],[0,0,-1],0x17897e,26);
 }
 if(mode==='field'){
  tube([[0,0,-135],[0,0,-70],[0,0,45],[0,0,135]],'#6f5f96',4);
 }
}
function refreshLabels(){clearLabels();
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
function stop(){playing=false;$('play').textContent='▶ 움직임 보기';}
function setMode(next){mode=next;stop();detachStep=0;const c=window.RFCP_CONTENT[mode];$('sceneTag').textContent=c.tag;$('sceneTitle').textContent=c.title;$('explanation').innerHTML=c.body;
 document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);b.setAttribute('aria-pressed',String(b.dataset.mode===mode));});
 $('motionBox').hidden=mode==='detach';$('detachControls').hidden=mode!=='detach';
 if(selected)selected.material.emissive.set(0);selected=null;$('selection').textContent='부품을 클릭하면 역할을 볼 수 있어요.';
 $('motion').value=0;applyPose(0);makeExtras();refreshLabels();transparent();reset();if(mode==='detach')setDetachStep(0);
}
function setDetachStep(i,reframe=true){detachStep=i;applyPose(0);refreshLabels();$('detachMotion').value=i;
 const labelIndex=Math.min(5,Math.ceil(i));$('detachCaption').textContent=window.RFCP_DETACH[labelIndex][1];
 document.querySelectorAll('[data-step]').forEach(b=>{b.classList.toggle('active',+b.dataset.step===Math.round(i));b.setAttribute('aria-pressed',String(+b.dataset.step===Math.round(i)));});if(reframe)reset();}
$('detachMotion').addEventListener('input',e=>setDetachStep(+e.target.value,false));
window.RFCP_DETACH.forEach((s,i)=>{const b=document.createElement('button');b.dataset.step=i;b.textContent=s[0];b.onclick=()=>setDetachStep(i);$('detachSteps').append(b)});
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
$('motion').addEventListener('input',e=>{playing=false;$('play').textContent='▶ 움직임 보기';applyPose(+e.target.value)});
$('play').onclick=()=>{playing=!playing;started=performance.now();$('play').textContent=playing?'Ⅱ 멈춤':'▶ 움직임 보기'};
$('inside').onchange=()=>{transparent();refreshLabels()};$('reset').onclick=()=>reset();document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>reset(b.dataset.view));
const ray=new T.Raycaster();let down=null;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY]});
renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=ray.intersectObjects([...parts.values()].filter(x=>x.visible&&x.material.opacity>.2),false)[0];if(selected)selected.material.emissive.set(0);selected=hit?.object;if(selected){selected.material.emissive.set('#16485c');const d=window.RFCP_PARTS[selected.userData.base];$('selection').textContent=d?d[0]+' — '+d[1]:selected.userData.base+' · '+(/Keeper/.test(selected.name)?'코어를 받침에 고정하는 부품입니다. 일상 개폐 때 풀지 않습니다.':/Guide/.test(selected.name)?'움직이는 받침의 위치와 이탈을 제어하는 부품입니다.':'실제 CAD의 기구 부품입니다.');}});
new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}).observe(host);
renderer.domElement.addEventListener('keydown',e=>{const rel=camera.position.clone().sub(controls.target);if(e.key==='Home'){reset();e.preventDefault();return;}if(['ArrowLeft','ArrowRight'].includes(e.key))rel.applyAxisAngle(V(0,1,0),e.key==='ArrowLeft'?.1:-.1);else if(['ArrowUp','ArrowDown'].includes(e.key))rel.y+=e.key==='ArrowUp'?15:-15;else if(['+','=','-'].includes(e.key))rel.multiplyScalar(e.key==='-'?1.1:.9);else return;camera.position.copy(controls.target).add(rel);controls.update();e.preventDefault();});
function drawLabels(){const occupied=[];for(const l of labels){const p=l.point().clone().project(camera),on=$('annotations').checked&&p.z<1&&p.z>-1&&Math.abs(p.x)<.96&&Math.abs(p.y)<.96;l.el.style.display=on?'block':'none';l.line.style.display=on?'block':'none';if(!on)continue;
 const ax=(p.x+1)*host.clientWidth/2,ay=(-p.y+1)*host.clientHeight/2,w=l.el.offsetWidth,h=l.el.offsetHeight;
 let x=Math.max(w/2+6,Math.min(host.clientWidth-w/2-6,ax+l.offset[0])),y=Math.max(h/2+6,Math.min(host.clientHeight-h/2-6,ay+l.offset[1]));
 for(let attempt=0;attempt<8&&occupied.some(r=>Math.abs(r.x-x)<(r.w+w)/2+4&&Math.abs(r.y-y)<(r.h+h)/2+4);attempt++)y=Math.max(h/2+6,y-h-7);
 occupied.push({x,y,w,h});l.el.style.left=x+'px';l.el.style.top=y+'px';const dx=x-ax,dy=y-ay;l.line.style.left=ax+'px';l.line.style.top=ay+'px';l.line.style.width=Math.hypot(dx,dy)+'px';l.line.style.transform=`rotate(${Math.atan2(dy,dx)}rad)`;
 }}
function frame(t){requestAnimationFrame(frame);if(document.hidden)return;if(playing){let v=(1-Math.cos((t-started)/6500*Math.PI))*50;if(t-started>=13000){v=0;stop();}$('motion').value=v;applyPose(v);}controls.update();drawLabels();renderer.render(scene,camera);}
// Initial sizing precedes camera framing, including narrow mobile screens.
camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight,false);
setMode('mechanism');$('loading').classList.add('hidden');requestAnimationFrame(frame);
})();
