"use strict";
((root)=>{
 const clamp=x=>Math.max(0,Math.min(1,x));
 function state(step,name,t){
  const visible=step.rest.includes(name)||step.active.includes(name);
  const pos=[...(step.baseOffsets?.[name]||[0,0,0])];
  const p=step.moves[name];let rx=0;
  if(p?.keys){let k=p.keys.findIndex((v,i)=>i&&v[0]>=t);if(k<1)k=p.keys.length-1;const a=p.keys[k-1],b=p.keys[k],f=clamp((t-a[0])/(b[0]-a[0]));a[1].forEach((v,i)=>pos[i]+=v+(b[1][i]-v)*f);rx=(a[2]+(b[2]-a[2])*f)*Math.PI/180;const [,py,pz]=p.pivot;pos[1]+=py-(py*Math.cos(rx)-pz*Math.sin(rx));pos[2]+=pz-(py*Math.sin(rx)+pz*Math.cos(rx));}
  else if(p){const w=p.window||[0,1],f=clamp((t-w[0])/(w[1]-w[0]));p.vector.forEach((v,i)=>pos[i]+=v*f);}
  let lidRelax=step.freeRaisedLid&&['UpperLeft','UpperRight'].includes(name)?1.8:0;
  if(['headLift','headOpen'].includes(step.kind)&&step.active.includes(name)){
   const both=step.kind==='headOpen',h=120*(both?clamp((t-.3)/.7):t);
   if((name==='HeadHandScrews'||name.startsWith('HeadClosure'))){pos[1]+=75*clamp(t/.3);return{visible:visible&&t<=.3,pos,rx,active:true,lidRelax:0};}
   if(['UpperLeft','UpperRight'].includes(name)){pos[1]+=h;lidRelax=Math.min(1.8,h);}
   else pos[1]+=Math.max(0,h-1.8);
  }
  return{visible,pos,rx,active:step.active.includes(name),lidRelax};
 }
 const api={state,clamp};if(typeof module!=='undefined')module.exports=api;root.GUIDE_MOTION=api;
})(typeof window!=='undefined'?window:globalThis);
