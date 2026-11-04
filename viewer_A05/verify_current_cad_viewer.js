// Verify the actual latest CAD payload and motion grouping, not historical C01.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {pose,centerCable}=require('./clamp_kinematics');
const R=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const C=path.join(R,'mechanical/cable_clamp_C07_DRAFT'),A=path.join(R,'mechanical/assembly_A13_DRAFT');
const cr=read(path.join(C,'verification.json')),ar=read(path.join(A,'build_report.json'));
assert(cr.pass);assert(ar.pass);assert.equal(hash(path.join(C,'Cable_Clamp_C07_DRAFT.FCStd')),cr.native_sha256);assert.equal(hash(path.join(A,'RFCP_A13_Integrated_DRAFT.FCStd')),ar.native_sha256);
const cm=read(path.join(C,'mesh.json')),am=read(path.join(A,'mesh.json'));assert(Object.keys(am).length===71);assert(Object.values(cm).filter(x=>x.printed).length===5);
for(const [name,p]of Object.entries(cm)){for(const r of [3,8,13])for(const opening of [0,.25,.5,1])for(const explode of [0,.5,1]){const q=pose({...p,name},r,opening,explode);assert([q.x,q.y,q.z].every(Number.isFinite));if(name==='BridgeScrew1'&&opening>.25)assert(!q.visible);}}
const assemblySource=fs.readFileSync(path.join(__dirname,'assembly_viewer.js'),'utf8');
const poseSource=assemblySource.slice(assemblySource.indexOf('function pose(p,'),assemblySource.indexOf('function update()'));
const assemblyPose=new Function('clamp',poseSource+';return pose;')(x=>Math.max(0,Math.min(1,x)));
assert(!Object.keys(am).some(n=>/NutCover|NutCap|Retainer|BasePanel/.test(n)));
for(const offset of [-118.65,121.35])for(const [name,p]of Object.entries(cm)){
 const hit=Object.entries(am).find(([n,x])=>x.local===name&&x.offset_z===offset);assert(hit);const q=hit[1];assert.equal(q.subgroup,p.group);assert.equal(q.vertices.length,p.vertices.length);
 // BRep import can reorder tessellation vertices without changing geometry.
 const canonical=(vs,z)=>vs.map(v=>v.map((x,i)=>Math.round((x-(i===2?z:0))*1e5)).join(',')).sort();
 assert.deepEqual(canonical(q.vertices,offset),canonical(p.vertices,0));
}
for(let i=0;i<=100;i++){const r=13-7*i/100,c=centerCable(r,6);for(const a of [90,210,330])assert(Math.cos(a*Math.PI/180)*c[0]+Math.sin(a*Math.PI/180)*c[1]+6<=r+1e-8);}
const before=read(path.join(R,'reviews/simplification_20260918/comparison_3d.json'));for(const [p,h]of Object.entries(before.sources))assert.equal(hash(path.join(R,p)),h);
const report={classification:'STATIC_CAD_PAYLOAD_AND_IDEAL_MOTION_CHECK',assembly_revision:'A13',clamp_revision:'C07',parts:Object.keys(am).length,clamp_instances_verified:2,vertex_comparison_rounding_mm:1e-5,comparison_pairs:before.cases.length,pass:true};
fs.writeFileSync(path.join(__dirname,'assembly_sources/current_cad_viewer_verification.json'),JSON.stringify(report,null,2));console.log(report);
