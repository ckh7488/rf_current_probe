"use strict";
(function(root){
 const board=new Set(['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput','CornerPCBScrews']);
 const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
 function pose(p,mode,v,step=0){
  const head=p.name.startsWith('Head_'),isBoard=board.has(p.name),cap=p.group==='CAP',screw=p.group==='REMOVE';
  let visible=mode==='calibration'||mode==='detach'||!isBoard,y=0,z=0;
  const t=clamp(v/100),release=clamp(t/.25),dy=clamp((t-.25)/.75)*120;
  if(cap)y=dy;
  if(screw){y=release*40;visible=visible&&release<1;}
  if(mode==='detach'){
   const s=clamp(step,0,5);
   if(s<=1){if(cap)y=clamp((s-.25)/.75)*120;if(screw){y=clamp(s/.25)*40;visible=s<.25;}}
   if(s>1&&s<4){if(cap||screw)visible=false;}
   if(isBoard){y=clamp(s-1)*120;visible=s<2;}
   if(p.name==='BaseHandScrews'){y=clamp(s-2)*28;visible=s<3;}
   if(head&&p.group==='FIXED')y=clamp(s-3)*100;
   if(s>=4&&head){if(cap){visible=true;y=100+(5-s)*120;}if(screw){visible=s>=4.75;y=100+clamp((5-s)/.25)*40;}}
   if(s>=5&&!head)visible=false;
  }
  return {visible,y,z,sy:1,cap:dy};
 }
 root.RFCP_KINEMATICS={pose};if(typeof module!=='undefined')module.exports={pose};
})(typeof window!=='undefined'?window:globalThis);
