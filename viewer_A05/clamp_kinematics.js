"use strict";
(function(root){
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
function pose(p,r,open,spread){const t=r-8,g=p.group;let x=0,y=0,z=0,visible=true;
 if(['DRIVE','TOP','TOPSCREW'].includes(g))y=t;
 if(g.startsWith('JAW')){const a=(g==='JAW1'?210:330)*Math.PI/180;x=Math.cos(a)*t;y=Math.sin(a)*t;}
 if(g==='TOPSCREW'){y+=clamp(open/.25)*25;visible=open<.25;}
 if(g==='TOP')y+=clamp((open-.25)/.75)*60;
 if(spread){if(p.name==='Frame')z-=35*spread;else if(g==='DRIVE')z+=32*spread;else if(g==='TOP'||g==='TOPSCREW')y+=65*spread;else if(g.startsWith('JAW')){const a=(g==='JAW1'?210:330)*Math.PI/180;x+=Math.cos(a)*18*spread;y+=Math.sin(a)*18*spread;if(p.name.startsWith('Follower'))z+=45*spread;else z-=18*spread;}else z+=65*spread;}
 if(spread&&/NutCover|NutCap/.test(p.name))z+=45*spread;
 return {x,y,z,visible};}
// Frictionless rigid circular cable, constrained by the three moving tangent planes.
// Closest feasible point to the initial placement; illustrative contact geometry.
function centerCable(apertureRadius,cableRadius,initial=[5,-3]){
 const g=apertureRadius-cableRadius;if(g<0)throw new RangeError('Cable larger than opening');
 const normals=[90,210,330].map(a=>[Math.cos(a*Math.PI/180),Math.sin(a*Math.PI/180)]);
 const feasible=p=>normals.every(n=>n[0]*p[0]+n[1]*p[1]<=g+1e-9),candidates=[];
 if(feasible(initial))candidates.push(initial);
 for(const n of normals){const d=n[0]*initial[0]+n[1]*initial[1]-g;const p=[initial[0]-d*n[0],initial[1]-d*n[1]];if(feasible(p))candidates.push(p);}
 for(let i=0;i<3;i++)for(let j=i+1;j<3;j++){const a=normals[i],b=normals[j],det=a[0]*b[1]-a[1]*b[0];const p=[g*(b[1]-a[1])/det,g*(a[0]-b[0])/det];if(feasible(p))candidates.push(p);}
 candidates.sort((a,b)=>(a[0]-initial[0])**2+(a[1]-initial[1])**2-(b[0]-initial[0])**2-(b[1]-initial[1])**2);return candidates[0];
}
root.C01_POSE=pose;root.C01_CENTER_CABLE=centerCable;if(typeof module!=='undefined')module.exports={pose,centerCable};
})(typeof window!=='undefined'?window:globalThis);
