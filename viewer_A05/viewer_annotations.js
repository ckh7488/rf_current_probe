/* Shared RFCP annotation preference and text outside the 3D canvas. */
"use strict";
(()=>{
 const key='rfcp.viewer.annotations.visible.v1',views=new Set();
 let visible=true;
 try{visible=localStorage.getItem(key)!=='off';}catch(e){}
 const svgNS='http://www.w3.org/2000/svg';
 function svgElement(name){return document.createElementNS(svgNS,name);}
 function apply(value,save){
  visible=value;
  if(save)try{localStorage.setItem(key,value?'on':'off');}catch(e){}
  for(const view of views)view.refresh();
 }
 window.addEventListener('storage',e=>{if(e.key===key||e.key===null)apply(e.newValue!=='off',false);});
 window.RFCP_ANNOTATIONS={create({stage,camera,resetButton,extraText=[]}){
  const toggle=document.createElement('label'),input=document.createElement('input');
  toggle.className='annotation-toggle';toggle.title='다른 3D 페이지에서도 이 설정을 유지합니다.';
  input.type='checkbox';input.id='showAnnotations';input.checked=visible;
  input.addEventListener('change',()=>apply(input.checked,true));
  toggle.append(input,document.createTextNode('3D 글씨 표시'));
  const options=document.createElement('div');options.className='annotation-options';
  resetButton.before(options);options.append(toggle,resetButton);
  const dock=document.createElement('div');dock.id='annotationDock';dock.className='annotation-dock';
  dock.setAttribute('role','group');dock.setAttribute('aria-label','3D 위치 설명');stage.after(dock);
  const svg=svgElement('svg');svg.classList.add('annotation-lines');svg.setAttribute('aria-hidden','true');stage.append(svg);
  let entries=[],active=true,needsLayout=true,stageWidth=0,stageHeight=0;
  new ResizeObserver(()=>{needsLayout=true;}).observe(stage);
  new ResizeObserver(()=>{needsLayout=true;}).observe(dock);
  function refresh(){
   input.checked=visible;dock.hidden=!(visible&&active&&entries.length);svg.toggleAttribute('hidden',dock.hidden);
   for(const el of extraText)el.hidden=!visible;
   needsLayout=true;
  }
  const view={refresh};views.add(view);
  function set(items){
   dock.replaceChildren();svg.replaceChildren();
   entries=items.map(([text,pos],i)=>{
    const el=document.createElement('span');el.className='annotation-caption';
    const number=document.createElement('b');number.textContent=String(i+1);number.setAttribute('aria-hidden','true');
    el.append(number,document.createTextNode(text));dock.append(el);
    const group=svgElement('g'),path=svgElement('path'),point=svgElement('circle');
    point.setAttribute('r','3');group.append(path,point);svg.append(group);
    return{el,pos,group,path,point,x:0};
   });
   refresh();
  }
  function update(show=true){
   if(active!==show){active=show;refresh();}
   if(!visible||!active||!entries.length)return;
   if(needsLayout){
    const box=stage.getBoundingClientRect();stageWidth=box.width;stageHeight=box.height;
    svg.setAttribute('viewBox',`0 0 ${stageWidth} ${stageHeight}`);
    for(const e of entries){const r=e.el.getBoundingClientRect();e.x=r.left+r.width/2-box.left;}
    needsLayout=false;
   }
   for(const e of entries){
    const p=e.pos.clone().project(camera),on=p.z>=-1&&p.z<=1&&Math.abs(p.x)<=1&&Math.abs(p.y)<=1;
    e.group.style.display=on?'':'none';
    if(!on)continue;
    const x=(p.x+1)*stageWidth/2,y=(1-p.y)*stageHeight/2;
    e.path.setAttribute('d',`M ${x} ${y} L ${e.x} ${stageHeight-12} L ${e.x} ${stageHeight}`);
    e.point.setAttribute('cx',x);e.point.setAttribute('cy',y);
   }
  }
  refresh();return{set,update};
 }};
})();
