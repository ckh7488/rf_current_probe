"use strict";
(()=>{
const T=THREE,$=id=>document.getElementById(id),model=window.RFCP_COMPARE,vec=a=>new T.Vector3(...a);
const bin=atob(model.data),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
const scenes=[],views=[];let current=0,syncing=false;
for(const [i,id] of ['beforeStage','afterStage'].entries()){
 const host=$(id),scene=new T.Scene();scene.background=new T.Color('#f8fafc');scene.add(new T.HemisphereLight(0xffffff,0x607c91,1.2));
 for(const a of [[100,150,200],[-100,50,-150]]){const l=new T.DirectionalLight(0xffffff,.7);l.position.copy(vec(a));scene.add(l);}
 const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputEncoding=T.sRGBEncoding;host.append(renderer.domElement);renderer.domElement.setAttribute('aria-label',i?'수정 후 실제 CAD':'수정 전 실제 CAD');
 const camera=new T.PerspectiveCamera(34,1,.03,3000),orbit=new T.OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;
 const root=new T.Group();scene.add(root);views.push({host,scene,renderer,camera,orbit,root});
 orbit.addEventListener('change',()=>{if(syncing||views.length<2)return;syncing=true;const v=views[1-i];v.camera.position.copy(camera.position);v.camera.quaternion.copy(camera.quaternion);v.orbit.target.copy(orbit.target);v.orbit.update();syncing=false;});
 new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}).observe(host);
}
function mesh(p,color,delta){const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(new Float32Array(bytes.buffer,p.vo,p.vc*3),3));geo.setIndex(new T.BufferAttribute(new Uint32Array(bytes.buffer,p.io,p.ic),1));geo.computeVertexNormals();const mat=new T.MeshStandardMaterial({color,roughness:.8,metalness:0,side:T.DoubleSide,flatShading:true});mat.color.convertSRGBToLinear();const m=new T.Mesh(geo,mat);m.userData.delta=delta;m.userData.name=p.name;return m;}
function highlight(){for(const v of views)for(const m of v.root.children){const on=$('highlight').checked;if(m.userData.delta){m.visible=on;m.renderOrder=2;}else{m.material.transparent=on;m.material.opacity=on?.16:1;m.material.depthWrite=!on;m.renderOrder=0;}}}
function reset(direction){const c=model.cases[current],b=c.bounds,center=vec([b[0]+b[3]/2,b[1]+b[4]/2,b[2]+b[5]/2]),d=vec(direction||c.direction).normalize(),v=views[0];const dist=Math.hypot(b[3],b[4],b[5])*1.55*Math.max(1,1/v.camera.aspect);syncing=true;for(const w of views){w.orbit.target.copy(center);w.camera.position.copy(center).addScaledVector(d,dist);w.orbit.update();}syncing=false;}
function show(i){current=i;const c=model.cases[i];for(const [side,v] of views.entries()){for(const m of [...v.root.children]){m.geometry.dispose();m.material.dispose();v.root.remove(m);}for(const p of c.models[side]){const hardware=/Screw|Nut|SMA|Winding/.test(p.name),pcb=/PCB/.test(p.name);v.root.add(mesh(p,hardware?'#d1b976':pcb?'#498c66':side?'#62a9b9':'#9fadb4',false));}for(const p of c.changes[side])v.root.add(mesh(p,side?'#008d98':'#d65a48',true));}
 $('revision').textContent=c.before+' → '+c.after;$('caseTitle').textContent=c.title;$('beforeLabel').textContent=c.labels[0];$('afterLabel').textContent=c.labels[1];$('why').textContent=c.why;$('changeCount').textContent='이 창 안의 변경: 제거 '+c.changes[0].reduce((s,p)=>s+p.volume_mm3,0).toFixed(1)+' mm³ · 추가 '+c.changes[1].reduce((s,p)=>s+p.volume_mm3,0).toFixed(1)+' mm³ (CAD 부피)';document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.case===i)));highlight();reset();window.RFCP_COMPARE_STATE={case:c.key,loaded_parts:views.map(v=>v.root.children.length)};}
for(const [i,c] of model.cases.entries()){const b=document.createElement('button');b.textContent=c.title;b.dataset.case=i;b.onclick=()=>show(i);$(c.after==='A13'||c.after==='C07'?'latest':'earlier').append(b);}
for(const [id,d] of [['front',[0,0,1]],['back',[0,0,-1]],['bottom',[.1,-1,.15]]])$(id).onclick=()=>reset(d);$('reset').onclick=()=>reset();$('highlight').onchange=highlight;
const key=new URLSearchParams(location.search).get('part'),found=model.cases.findIndex(c=>c.key===key);show(found>=0?found:model.cases.findIndex(c=>c.after==='A13'||c.after==='C07'));
function frame(){requestAnimationFrame(frame);if(document.hidden)return;for(const v of views){v.orbit.update();v.renderer.render(v.scene,v.camera);}}frame();
})();
