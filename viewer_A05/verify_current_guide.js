const fs=require('fs'),assert=require('assert/strict');
const {state}=require('./guide_motion');
const html=fs.readFileSync(__dirname+'/dist/assembly-guide.html','utf8');
const model=JSON.parse(html.match(/window\.RFCP_GUIDE=(.*?);<\/script>/s)[1]);
const names=new Set(model.parts.map(p=>p.name)),data=Buffer.from(model.data,'base64');
assert.equal(model.steps.length,45);assert.equal(new Set(model.steps.map(s=>s.id)).size,45);
for(const p of model.parts){assert(p.vo%4===0&&p.io%4===0);assert(p.vo+p.vc*12<=data.length);assert(p.io+p.ic*4<=data.length);for(let i=0;i<p.ic;i++)assert(data.readUInt32LE(p.io+4*i)<p.vc);}
for(const step of model.steps){for(const n of [...step.rest,...step.active,...Object.keys(step.moves)])assert(names.has(n),[step.id,n]);assert(step.action.length&&step.hold&&step.tool&&step.check&&step.proof);for(let i=0;i<=20;i++)for(const n of names){const q=state(step,n,i/20);assert(q.pos.every(Number.isFinite));assert(Number.isFinite(q.lidRelax));if(q.visible)assert(step.rest.includes(n)||step.active.includes(n));}}
const end=model.steps.at(-1),visible=new Set([...end.rest,...end.active]);assert.equal(visible.size,128);
assert(![...visible].some(n=>/NutCover|Retainer|BasePanel|UpperLid|LowerBody|CommonBase|LeadScrewKnob/.test(n)));
const step=id=>model.steps.find(s=>s.id===id);
assert.equal(state(step('H13'),'MovingCore',1).pos[1],118.2);
for(const n of ['UpperLeft','UpperRight'])assert.equal(state(step('H13'),n,1).pos[1],120);
assert(Math.abs(state(step('H05'),'PCB',.5).rx+Math.PI/4)<1e-10);
assert.deepEqual(step('H05').moves.PCB.keys.at(-1),[1,[0,-4,40],-45]);
for(const [id,n] of [['B05','MountScrew2'],['B07','MountScrew4']]){assert.deepEqual(state(step(id),n,.3).pos,[0,25,0]);assert.deepEqual(state(step(id),n,.5).pos,[-35,25,0]);}
for(const id of ['C05','C06'])for(const suffix of ['LeadStud','HandKnob','TopJamNut','TopWasher'])assert.equal(state(step(id),'Cable1_'+suffix,.45).pos[1],120);
assert.equal(state(step('C04A'),'Cable1_HandKnob',1).pos[1],110);
for(const s of model.steps.filter(s=>/^C0[1-7][AB]?$/.test(s.id)))assert(![...s.rest,...s.active].some(n=>n.includes('BridgeNut')),'bridge nuts must wait until C08');
const ids=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]));const js=fs.readFileSync(__dirname+'/guide_viewer.js','utf8');for(const [,id]of js.matchAll(/\$\('([^']+)'\)/g))assert(ids.has(id),id);
const result={classification:'STATIC_ANIMATION_STATE_NOT_COLLISION_OR_BROWSER_QA',pass:true,steps:45,parts:model.parts.length,complete_parts:visible.size};
fs.writeFileSync(__dirname+'/guide_sources/current_static_verification.json',JSON.stringify(result,null,2));console.log(result);
