"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto'),vm=require('vm'),assert=require('assert/strict'),{pose,centerCable}=require('./clamp_kinematics');
const root=__dirname,mech=path.join(root,'../mechanical/cable_clamp_C01_DRAFT'),read=n=>fs.readFileSync(n,'utf8'),hash=n=>crypto.createHash('sha256').update(fs.readFileSync(n)).digest('hex');
const report=JSON.parse(read(path.join(mech,'verification.json'))),assembly=JSON.parse(read(path.join(mech,'assembly_verification.json'))),manifest=JSON.parse(read(path.join(root,'clamp_manifest.json')));
assert(report.pass);assert(assembly.pass);assert.equal(report.native_sha256,assembly.native_sha256);assert.equal(hash(path.join(mech,'Cable_Clamp_C01_DRAFT.FCStd')),report.native_sha256);assert.equal(hash(path.join(mech,'mesh.json')),manifest.mesh_sha256);
const model=JSON.parse(read(path.join(mech,'mesh.json')));assert.equal(Object.values(model).filter(p=>p.printed).length,5);
for(let r=3;r<=13;r+=.25){
 const t=r-8;assert(Math.abs(pose({...model.TopBridgeJaw,name:'TopBridgeJaw'},r,0,0).y-t)<1e-9);
 for(const [n,a] of [['Jaw1',210],['Jaw2',330]]){const p=pose({...model[n],name:n},r,0,0),nx=Math.cos(a*Math.PI/180),ny=Math.sin(a*Math.PI/180);assert(Math.abs(p.x-nx*t)<1e-9);assert(Math.abs(p.y-ny*t)<1e-9);}
 for(let o=0;o<=1;o+=.05){const q=pose({...model.BridgeScrew1,name:'BridgeScrew1'},r,o,0),top=pose({...model.TopBridgeJaw,name:'TopBridgeJaw'},r,o,0);if(top.y>t+1e-7)assert(!q.visible,'Cap must lift only after screws removed');}
}
for(const p of Object.entries(model)){for(const r of [3,8,13])for(const open of [0,.25,1])for(const spread of [0,.5,1]){const q=pose({name:p[0],...p[1]},r,open,spread);assert([q.x,q.y,q.z].every(Number.isFinite));}}
const contact=[];
for(let i=0;i<=100;i++){const aperture=13-7*i/100,c=centerCable(aperture,6);assert(c.every(Number.isFinite));for(const a of [90,210,330])assert(Math.cos(a*Math.PI/180)*c[0]+Math.sin(a*Math.PI/180)*c[1]+6<=aperture+1e-8);contact.push({closing_percent:i,aperture_radius_mm:aperture,cable_center_mm:c});}
assert.deepEqual(contact[0].cable_center_mm,[5,-3]);assert(Math.hypot(...contact[100].cable_center_mm)<1e-8);
fs.writeFileSync(path.join(mech,'centering_contact_demo.json'),JSON.stringify({classification:'CALCULATED_IDEAL_CONTACT_GEOMETRY',initial:[5,-3],cable_radius_mm:6,assumptions:['Rigid circular cable','Frictionless tangent constraints','Zero guide/cam error; no force or physical validation','Reverse slider restores the illustrative initial placement, not spring recovery'],samples:contact},null,2)+'\n');
for(const page of ['index.html','clamp.html']){const html=read(path.join(root,'dist',page));assert(!/<script[^>]+src=|<link[^>]+(?:stylesheet|preload)/i.test(html),'Self-contained script/style expected');for(const [,script] of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script);for(const [,url] of html.matchAll(/href="([^"]+)"/g)){if(!/^(https?:|#)/.test(url))assert(fs.existsSync(path.resolve(root,'dist',url)),url);}}
assert(read(path.join(root,'dist/index.html')).includes('clamp.html'));assert(read(path.join(root,'dist/clamp.html')).includes('패드를 잘라'));
console.log('PASS C01: current CAD hashes, nominal/assembly checks, 5 prints, shared jaw motion, cap sequence, both HTML routes and downloads, embedded JS syntax.');
