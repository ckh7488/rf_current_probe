"use strict";
(()=>{
 const $=id=>document.getElementById(id),D=window.RFCP_GUIDE,T=THREE,V=(...x)=>new T.Vector3(...x),motion=window.GUIDE_MOTION;
 if(location.protocol==='file:')$('downloadHtml').href=location.href.split('?')[0];
 const host=$('stage'),scene=new T.Scene();scene.background=new T.Color('#f8fafc');
 let renderer;try{renderer=new T.WebGLRenderer({antialias:true});}catch(e){$('loading').textContent='이 브라우저에서는 3D를 시작하지 못했습니다. WebGL을 사용할 수 있는 브라우저에서 열어 주세요.';return;}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputEncoding=T.sRGBEncoding;host.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','현재 조립 단계의 실제 A14 C07 부품');renderer.domElement.setAttribute('role','img');
 const camera=new T.PerspectiveCamera(35,1,.1,4000),orbit=new T.OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;scene.add(new T.HemisphereLight(0xffffff,0x758da0,1.15));
 for(const [x,y,z] of [[100,160,160],[-100,50,-160]]){const l=new T.DirectionalLight(0xffffff,.65);l.position.set(x,y,z);scene.add(l);}
 const annotations=window.RFCP_ANNOTATIONS.create({stage:host,camera,resetButton:$('reset'),extraText:[$('viewHint')]});
 const bytes=Uint8Array.from(atob(D.data),c=>c.charCodeAt(0)),meshes=new Map();
 for(const p of D.parts){const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(bytes.buffer,p.vo,p.vc*3).slice(),3));g.setIndex(new T.BufferAttribute(new Uint32Array(bytes.buffer,p.io,p.ic),1));g.computeVertexNormals();g.computeBoundingBox();
  const m=new T.Mesh(g,new T.MeshStandardMaterial({color:p.color,roughness:.72,metalness:.03,side:T.DoubleSide,flatShading:true}));m.userData={...p,sourceVertices:g.attributes.position.array.slice(),normalColor:new T.Color(p.color).convertSRGBToLinear()};m.material.color.copy(m.userData.normalColor);meshes.set(p.name,m);scene.add(m);
 }
 const driver=new T.Mesh(new T.CylinderGeometry(4,4,60,24),new T.MeshStandardMaterial({color:'#778da0',transparent:true,opacity:.62}));driver.rotation.x=Math.PI/2;scene.add(driver);
 let index=0,step=D.steps[0],selected=null,focusActive=false;
 function update(){const t=Number($('separation').value)/100,transparent=$('transparent').checked;
  for(const [name,m] of meshes){const q=motion.state(step,name,t);m.visible=q.visible;m.position.set(...q.pos);m.rotation.x=q.rx;m.material.color.copy(q.active?new T.Color('#e9b35e').convertSRGBToLinear():m.userData.normalColor);m.material.emissive.set(selected===m?'#4b3720':'#000000');m.material.transparent=transparent&&!q.active;m.material.opacity=m.material.transparent?.19:1;m.material.depthWrite=!m.material.transparent;
   if(['UpperLeft','UpperRight'].includes(name)){const a=m.geometry.attributes.position,src=m.userData.sourceVertices;for(let i=0;i<src.length;i+=3){const x=Math.abs(src[i]),u=Math.max(0,Math.min(1,(103-x)/63));const f=x<=40?1:x<103?u*u*(3-2*u):0;a.array[i+1]=src[i+1]-q.lidRelax*f;}a.needsUpdate=true;}
  }
  const tool=meshes.get('ToolM6');tool.visible=step.toolModel==='spanner'&&$('showTool').checked;tool.position.set(0,-.8,-118.65);tool.material.color.copy(tool.userData.normalColor);tool.material.transparent=true;tool.material.opacity=.62;tool.material.depthWrite=false;
  driver.visible=/Driver$/.test(step.toolModel||'')&&$('showTool').checked;driver.position.set(-37,step.toolModel==='upperDriver'?21.2:-23,54);
  $('separationOut').textContent=step.kind==='inspect'?'작업 위치':t===0?'조립 위치':t===1?'분리 위치':step.phases?.find(p=>t<=p[0])?.[1]||Math.round(t*100)+'% 꺼냄';
 }
 function bounds(activeOnly=false){const box=new T.Box3();for(const n of activeOnly?step.active:[...step.rest,...step.active]){const m=meshes.get(n);if(!m)continue;for(const t of [0,1]){const q=motion.state(step,n,t);if(!q.visible)continue;const b=m.geometry.boundingBox.clone().applyMatrix4(new T.Matrix4().makeRotationX(q.rx)).translate(V(...q.pos));box.union(b);}}
  if(step.toolModel==='spanner'&&!activeOnly)box.union(meshes.get('ToolM6').geometry.boundingBox.clone().translate(V(0,-.8,-118.65)));
  if(box.isEmpty())return new T.Box3(V(-50,-50,-50),V(50,50,50));return box;
 }
 function fit(direction){const b=bounds(focusActive),c=b.getCenter(V()),sz=b.getSize(V());const dist=Math.max(sz.length(),35)*1.85/Math.max(.4,Math.min(1,camera.aspect));orbit.target.copy(c);camera.position.copy(c).addScaledVector(V(...(direction||step.view)).normalize(),dist);orbit.update();}
 function renderList(){const group=step.group;$('steps').replaceChildren();D.steps.forEach((s,i)=>{if(s.group!==group)return;const b=document.createElement('button');b.className='step-button';b.setAttribute('aria-current',i===index?'step':'false');b.innerHTML='<small>'+s.id+'</small><span></span>';b.lastChild.textContent=s.title;b.onclick=()=>show(i);$('steps').append(b);});$('listCount').textContent=D.steps.filter(s=>s.group===group).length+'단계';document.querySelectorAll('[data-group]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.group===group)));}
 function show(i){index=Math.max(0,Math.min(D.steps.length-1,i));step=D.steps[index];selected=null;focusActive=false;$('separation').value=step.id==='Q01'?100:0;$('separation').disabled=step.kind==='inspect';$('assembled').disabled=$('separated').disabled=step.kind==='inspect';$('transparent').checked=false;
  $('stepNumber').textContent=step.id+' · '+step.group;$('stepTitle').textContent=step.title;$('sectionName').textContent=step.group;$('actions').replaceChildren();for(const line of step.action){const li=document.createElement('li');li.textContent=line;$('actions').append(li);}for(const id of ['hold','tool','check','note','proof'])$(id).textContent=step[id]||'';
  $('pathResult').textContent=step.pathResult||'';$('pathResult').className=step.pathBlocked?'path-bad':'';$('selection').textContent='주황: 이번에 움직이는 부품 · 부품을 누르면 이름을 볼 수 있습니다.';
  $('motionNote').textContent=step.motionNote||(step.kind==='inspect'?'이 단계는 이동 없이 권선·배선의 작업 위치를 살펴봅니다.':step.kind==='headOpen'?'왼쪽: 닫힘 · 오른쪽: 손나사를 빼고 뚜껑을 연 상태.':'맞물린 위치에서 해당 부품만 꺼내 봅니다. 실제 조립은 오른쪽 → 왼쪽 순서입니다. 나사산과 손의 움직임은 생략했습니다.');
  $('bomParts').replaceChildren();for(const part of step.bom||[]){const li=document.createElement('li'),a=document.createElement('a');a.href='bom.html#'+part.id;a.textContent=part.id+' · '+part.name;const qty=document.createElement('span');qty.textContent=part.qty===null?part.unit:part.qty+' '+part.unit;li.append(a,qty);$('bomParts').append(li);}
  $('proofDetails').open=false;
  $('sources').replaceChildren();for(const [label,url]of step.sources||[]){const a=document.createElement('a');a.href=url;a.textContent=label;a.target='_blank';a.rel='noopener noreferrer';$('sources').append(a);}
  $('pageCount').textContent=(index+1)+' / '+D.steps.length;$('previous').disabled=index===0;$('next').disabled=index===D.steps.length-1;$('toolOption').hidden=!step.toolModel;$('focus').textContent='현재 부품 확대';
  annotations.set((step.anchors||[]).map(([name,pos])=>[name,V(...pos)]));
  renderList();update();fit();const url=new URL(location.href);url.searchParams.set('step',step.id);try{history.replaceState(null,'',url);}catch(e){}
 }
 for(const [i,g]of [...new Set(D.steps.map(s=>s.group))].entries()){const b=document.createElement('button');b.textContent=String(i+1).padStart(2,'0')+' '+g;b.dataset.group=g;b.onclick=()=>show(D.steps.findIndex(s=>s.group===g));$('groups').append(b);}
 $('previous').onclick=()=>show(index-1);$('next').onclick=()=>show(index+1);$('separation').oninput=update;$('transparent').onchange=update;$('showTool').onchange=update;
 $('assembled').onclick=()=>{$('separation').value=0;update();};$('separated').onclick=()=>{$('separation').value=100;update();};$('reset').onclick=()=>{focusActive=false;$('focus').textContent='현재 부품 확대';fit();};$('focus').onclick=()=>{focusActive=!focusActive;$('focus').textContent=focusActive?'작업 전체 보기':'현재 부품 확대';fit();};
 document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>fit({front:[0,0,1],back:[0,0,-1],bottom:[.25,-1,.2]}[b.dataset.view]));
 const ray=new T.Raycaster();let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),camera);selected=ray.intersectObjects([...meshes.values()].filter(m=>m.visible),false)[0]?.object||null;$('selection').textContent=selected?selected.userData.label+(step.previewOnly?.includes(selected.userData.name)?' · 분해 순서 참고용, 이후 단계에서 장착':''):'부품을 누르면 이름을 볼 수 있습니다.';update();});
 let hadSize=false;new ResizeObserver(()=>{camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight,false);if(!hadSize){hadSize=true;fit();}}).observe(host);camera.aspect=host.clientWidth/host.clientHeight;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.updateProjectionMatrix();
 const q=new URLSearchParams(location.search).get('step'),start=D.steps.findIndex(s=>s.id===q);show(start<0?0:start);$('loading').hidden=true;
 function tick(){requestAnimationFrame(tick);if(document.hidden)return;orbit.update();annotations.update(Number($('separation').value)<=5);renderer.render(scene,camera);}tick();
})();
