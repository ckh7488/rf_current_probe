"use strict";
const fs=require('fs'),assert=require('assert/strict'),vm=require('vm'),crypto=require('crypto'),{pose}=require('./kinematics');
const model=JSON.parse(fs.readFileSync(__dirname+'/mesh_manifest.json','utf8'));
const review=JSON.parse(fs.readFileSync(__dirname+'/../mechanical/clamp_A07_DRAFT/verification.json','utf8'));
assert.equal(model.revision,'A07');assert(review.pass,'Saved CAD nominal checks must pass before publishing');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(__dirname+'/../mechanical/clamp_A07_DRAFT/RFCP_A07_Fixture_REVIEW.FCStd')).digest('hex'),review.native_sha256,'CAD changed after verification; rerun the geometric checks');
for(const [n,sha] of Object.entries(model.source_sha256))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(__dirname+'/../mechanical/clamp_A07_DRAFT/'+n)).digest('hex'),sha);
const ctx={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/content.js','utf8'),ctx);
for(const p of model.parts)assert(ctx.window.RFCP_PARTS[p.base],`Missing description: ${p.name}`);
const byName=n=>model.parts.find(p=>p.name===n),visible=(mode,v=0,step=0)=>model.parts.filter(p=>pose(p,mode,v,step).visible);
for(const mode of ['mechanism','field']){
 assert(visible(mode).some(p=>p.name==='Base'),'Bench is default');assert(!visible(mode).some(p=>p.name==='FlatPCB'));
 assert(visible(mode).some(p=>p.name==='Head_PCB'));assert(visible(mode).some(p=>p.name==='Head_PCBScrews'));
}
assert.equal(visible('calibration').length,model.parts.length);
assert.equal(pose(byName('Head_UpperShell'),'mechanism',100).y,120);
assert.equal(pose(byName('Head_MovingCore'),'mechanism',100).y,120);
for(let s=0;s<=5;s+=.01){
 const pcb=pose(byName('Head_PCB'),'detach',0,s),screws=pose(byName('Head_PCBScrews'),'detach',0,s);
 assert(pcb.visible);assert.equal(pcb.y,screws.y);assert.equal(pcb.z,screws.z);
 for(const p of model.parts){const q=pose(p,'detach',0,s);assert(Number.isFinite(q.y)&&Number.isFinite(q.z));}
}
assert.equal(pose(byName('Head_LowerShell'),'detach',0,3.5).y,50);
assert.equal(pose(byName('BaseHandScrews'),'detach',0,2.5).y,14);
assert(!pose(byName('BaseHandScrews'),'detach',0,3).visible);
assert(visible('detach',0,5).every(p=>p.name.startsWith('Head_')));
assert.equal(pose(byName('Head_UpperShell'),'detach',0,5).y,100);
assert.equal(pose(byName('Head_LowerShell'),'detach',0,5).y,100);
console.log('PASS A07: CAD source hashes, part descriptions, bench default, continuous detachment, PCB retained, final closed standalone head.');
