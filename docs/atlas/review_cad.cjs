const {chromium}=require('C:/Users/artzy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const base=process.env.RFCP_REVIEW_URL||'http://127.0.0.1:8766/';
const audit=path.join(__dirname,'review',process.env.RFCP_REVIEW_URL?'split-a02-live':'split-a02');fs.mkdirSync(audit,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1365,height:960},deviceScaleFactor:1});
 const errors=[],failed=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failed.push(r.url()+': '+r.failure()?.errorText));
 page.on('response',r=>{if(r.status()>=400)failed.push(r.url()+': '+r.status());});
 await page.goto(base,{waitUntil:'networkidle'});await page.locator('a[href="reports/rf-current-probe/"]').first().click();
 await page.waitForFunction(()=>document.querySelectorAll('.cad-stage[data-ready="true"]').length===1,{},{timeout:60000});
 const geometry=await page.evaluate(()=>Object.fromEntries(Object.entries(window.rfcpViewers).map(([name,v])=>[name,{parts:v.parts.size,triangles:[...v.parts.values()].reduce((n,m)=>n+m.geometry.index.count/3,0)}])));
 assert.equal(geometry.structure.parts,35);assert.equal(geometry.structure.triangles,456702);
 assert.ok(await page.evaluate(()=>window.rfcpViewers.structure.parts.has('FlatPCB')&&!window.rfcpViewers.structure.parts.has('InputPCB')));
 for(const revision of ['A01','A02']){
  await page.locator(`[data-revision-choice="${revision}"]`).click();
  await page.waitForFunction(rev=>document.querySelector('#structure-cad').dataset.revision===rev,revision);
  assert.equal(await page.evaluate(()=>window.rfcpViewers.structure.parts.size),revision==='A02'?35:44);
  await page.locator('#structure-cad').screenshot({path:path.join(audit,`revision-${revision}.png`)});
 }
 for(const mode of ['closed','pcb','head','open']){
  await page.locator(`[data-assembly="${mode}"]`).click();assert.equal(await page.locator('#structure-cad').getAttribute('data-mode'),mode);
  await page.locator('#structure-cad').screenshot({path:path.join(audit,`structure-${mode}.png`)});
 }
 for(const route of ['signal','return','all']){
  await page.locator(`[data-path="${route}"]`).click();assert.equal(await page.locator('#structure-cad').getAttribute('data-active-path'),route);
  await page.locator('#structure-cad').screenshot({path:path.join(audit,`path-${route}.png`)});
 }
 await page.locator('[data-assembly="head"]').click();
 assert.ok(await page.evaluate(()=>[...window.rfcpViewers.structure.parts.values()].filter(m=>m.visible).every(m=>m.name.startsWith('Head_'))));
 await page.locator('[data-path="signal"]').click();
 assert.equal(await page.locator('#structure-cad').getAttribute('data-mode'),'pcb');
 await page.locator('[data-assembly="open"]').click();
 await page.locator('.topology-panel').screenshot({path:path.join(audit,'structure-desktop.png')});
 await page.locator('#a04').screenshot({path:path.join(audit,'head-assembly-step.png')});
 await page.screenshot({path:path.join(audit,'assembly-full-desktop.png'),fullPage:true});
 const responsive=[];
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  const sizes=await page.evaluate(()=>({page:document.body.dataset.document,viewport:innerWidth,document:document.documentElement.scrollWidth}));assert.ok(sizes.document<=width,JSON.stringify(sizes));responsive.push(sizes);
  await page.locator('.topology-panel').screenshot({path:path.join(audit,`structure-${width}.png`)});
  await page.locator('#a07').screenshot({path:path.join(audit,`assembly-step-${width}.png`)});
 }
 await page.setViewportSize({width:1365,height:960});
 const assemblyID=await page.evaluate(()=>window.RFCP_DESIGN.document.design_id);
 await page.locator('.document-tabs a[href="testing.html"]').first().click();
 await page.waitForFunction(()=>document.querySelector('#calibration-cad')?.dataset.ready==='true',{},{timeout:60000});
 assert.equal(await page.evaluate(()=>window.RFCP_DESIGN.document.design_id),assemblyID);
 assert.equal(await page.locator('#calibration-cad').getAttribute('data-revision'),'A02');
 geometry.calibration=await page.evaluate(()=>{const v=window.rfcpViewers.calibration;return {parts:v.parts.size,triangles:[...v.parts.values()].reduce((n,m)=>n+m.geometry.index.count/3,0)};});
 assert.equal(geometry.calibration.parts,35);
 for(let i=0;i<4;i++){
  await page.locator(`[data-step="${i}"]`).click();
  const state=await page.evaluate(()=>{const v=window.rfcpViewers.calibration;return {p2:v.host.dataset.p2,load:v.host.dataset.load,head:v.parts.get('Head_FixedTray').visible,fixture:v.fixture.visible,cables:v.accessories.children.map(m=>m.name).filter(Boolean)};});
  assert.equal(state.p2,['standard','output','output','probe'][i]);assert.equal(state.load,['standard','none','probe','output'][i]);
  assert.equal(state.fixture,i!==0);if(i===1)assert.equal(state.head,false);if(i>=2)assert.equal(state.head,true);
  if(i===3)assert.ok(state.cables.includes('Probe-to-P2'));if(i===1||i===2)assert.ok(state.cables.includes('OUT-to-P2'));
  if(i>0){const start=await page.evaluate(()=>window.rfcpViewers.calibration.accessories.getObjectByName('P1-to-IN').geometry.parameters.path.points[0].toArray());assert.deepEqual(start,[0,29.2,-28]);}
  await page.locator('#calibration-cad').screenshot({path:path.join(audit,`step-${i}.png`)});
 }
 await page.locator('[data-step="0"]').click();
 for(const standard of ['open','short','load','thru']){
  await page.locator(`[data-standard="${standard}"]`).click();
  if(standard!=='thru')for(const port of [2,1]){await page.locator(`[data-standard-port="${port}"]`).click();assert.equal(await page.locator('#calibration-cad').getAttribute('data-active-port'),String(port));}
  assert.equal(await page.locator('#calibration-cad').getAttribute('data-active-standard'),standard);
  await page.locator('#calibration-cad').screenshot({path:path.join(audit,`standard-${standard}.png`)});
 }
 await page.locator('[data-step="3"]').click();
 const before=await page.evaluate(()=>window.rfcpViewers.calibration.camera.position.toArray());
 await page.locator('#calibration-cad canvas').focus();await page.keyboard.press('ArrowRight');
 const after=await page.evaluate(()=>window.rfcpViewers.calibration.camera.position.toArray());assert.notDeepEqual(before,after);
 await page.keyboard.press('+');assert.ok(await page.evaluate(()=>window.rfcpViewers.calibration.camera.zoom>1));
 await page.keyboard.press('Home');assert.equal(await page.evaluate(()=>window.rfcpViewers.calibration.camera.zoom),1);
 for(const camera of ['top','front','overview']){await page.locator(`[data-for="calibration"][data-camera="${camera}"]`).click();await page.locator('#calibration-cad').screenshot({path:path.join(audit,`camera-${camera}.png`)});}
 await page.locator('.calibration-panel').screenshot({path:path.join(audit,'calibration-desktop.png')});

 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  const sizes=await page.evaluate(()=>({page:document.body.dataset.document,viewport:innerWidth,document:document.documentElement.scrollWidth}));assert.ok(sizes.document<=width);responsive.push(sizes);
  await page.locator('.calibration-panel').screenshot({path:path.join(audit,`calibration-${width}.png`)});
 }
 assert.equal(await page.locator('#zt-value').innerText(),'5.000 Ω');await page.locator('#s21-db').fill('-40');assert.equal(await page.locator('#current-value').innerText(),'10.000 mA RMS');
 await page.locator('#voltage-mv').fill('');assert.equal(await page.locator('#current-value').innerText(),'—');
 await page.goto(base+'reports/rf-current-probe/?step=3#calibration',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>document.querySelector('#calibration-cad')?.dataset.ready==='true',{},{timeout:60000});
 assert.ok(page.url().includes('testing.html?step=3#calibration'));
 assert.equal(await page.locator('#calibration-cad').getAttribute('data-active-step'),'3');
 await page.locator('.document-tabs a[href="index.html"]').first().click();
 await page.waitForFunction(()=>document.querySelector('#structure-cad')?.dataset.ready==='true',{},{timeout:60000});
 assert.equal(await page.locator('#a08').count(),1);
 await page.locator('.site-header > a').click();await page.waitForURL(base);
 const result={url:base,geometry,revision_comparison:2,calibration_always_A02:true,upward_SMA_cable_alignment:true,step_states:4,standards:4,standard_ports:2,assembly_modes:4,head_only_isolation:true,shared_design_id:true,legacy_redirect:true,two_document_navigation:true,path_modes:3,keyboard_camera:true,camera_presets:3,responsive,back_to_catalog:true,errors,failed};
 fs.writeFileSync(path.join(audit,'browser-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
 await browser.close();assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
})().catch(e=>{console.error(e);process.exitCode=1});
