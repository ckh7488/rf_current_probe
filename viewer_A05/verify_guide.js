const fs=require('fs'),assert=require('assert/strict'),crypto=require('crypto');
const {state}=require('./guide_motion');
const html=fs.readFileSync(__dirname+'/dist/assembly-guide.html','utf8');
const model=JSON.parse(html.match(/window\.RFCP_GUIDE=(.*?);<\/script>/s)[1]);
const names=new Set(model.parts.map(p=>p.name));const data=Buffer.from(model.data,'base64');
assert.equal(model.steps.length,36);assert.equal(new Set(model.steps.map(s=>s.id)).size,36);
const source=fs.readFileSync(__dirname+'/../mechanical/assembly_A13_DRAFT/RFCP_A13_Integrated_DRAFT.FCStd');
assert.equal(crypto.createHash('sha256').update(source).digest('hex'),model.native_sha256);
for(const p of model.parts){assert(p.vo%4===0&&p.io%4===0);assert(p.vo+p.vc*12<=data.length);assert(p.io+p.ic*4<=data.length);for(let i=0;i<p.ic;i++)assert(data.readUInt32LE(p.io+4*i)<p.vc);}
for(const step of model.steps){for(const n of [...step.rest,...step.active,...Object.keys(step.moves)])assert(names.has(n),[step.id,n]);assert(step.action.length&&step.hold&&step.tool&&step.check&&step.proof);for(let i=0;i<=20;i++)for(const n of names){const q=state(step,n,i/20);assert(q.pos.every(Number.isFinite));assert(Number.isFinite(q.lidRelax));if(q.visible)assert(step.rest.includes(n)||step.active.includes(n));}}
const end=model.steps.at(-1),visible=new Set([...end.rest,...end.active]);assert.equal(visible.size,74);assert(![...visible].some(n=>/NutCover|Retainer|BasePanel/.test(n)));
const head=model.steps.find(s=>s.id==='H13');assert.equal(state(head,'MovingCore',1).pos[1],118.2);assert.equal(state(head,'UpperLid',1).pos[1],120);
const pcm=model.steps.find(s=>s.id==='H05');assert(state(pcm,'PCBScrews',.5).pos[2]===90);assert(Math.abs(state(pcm,'PCB',.5).rx+Math.PI/6)<1e-10);
// Nuts cannot leave sideways until the lead shaft has cleared them.
for(const id of ['C05','C06']){const s=model.steps.find(s=>s.id===id);assert(state(s,'Cable1_LeadScrewKnob',.45).pos[1]===120);for(const n of s.active.filter(n=>n!=='Cable1_LeadScrewKnob'))assert.deepEqual(state(s,n,.4).pos,[0,0,0]);assert(s.previewOnly.includes('Cable1_LeadScrewKnob'));}
const washers=model.steps.find(s=>s.id==='C06');assert.equal(state(washers,'Cable1_LeadLockNut',.7).pos[2],50);assert.equal(state(washers,'Cable1_ThrustWasher',.7).pos[2],0);
for(const s of model.steps.filter(s=>/^C0[1-7]$/.test(s.id)))assert(![...s.rest,...s.active].some(n=>n.includes('BridgeNut')),'bridge nuts must wait until C08');
assert.deepEqual(model.steps.filter(s=>s.group==='케이블 클램프').map(s=>s.id),Array.from({length:11},(_,i)=>'C'+String(i+1).padStart(2,'0')));
const guideIds=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]));const js=fs.readFileSync(__dirname+'/guide_viewer.js','utf8');for(const [,id]of js.matchAll(/\$\('([^']+)'\)/g))assert(guideIds.has(id),id);
assert(!html.includes('src="http'));assert(html.includes('OrbitControls'));assert(!html.includes('<!--SCRIPTS-->'));
const report={classification:'STATIC_ROUTE_PAYLOAD_AND_MOTION_CHECK_NOT_BROWSER_QA',steps:36,parts:model.parts.length,complete_state_parts:visible.size,embedded_geometry:true,native_sha256:model.native_sha256,pass:true};
fs.writeFileSync(__dirname+'/guide_sources/static_verification.json',JSON.stringify(report,null,2));console.log(report);
