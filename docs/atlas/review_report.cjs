const { chromium } = require('C:/Users/artzy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const audit = path.join(__dirname, 'review', process.env.RFCP_REVIEW_URL ? 'live' : '');
fs.mkdirSync(audit,{recursive:true});
const report = 'C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe';
const base = process.env.RFCP_REVIEW_URL || 'http://127.0.0.1:8766/';
(async()=>{
 const browser = await chromium.launch({channel:'chrome',headless:true});
 const page = await browser.newPage({viewport:{width:1365,height:960},deviceScaleFactor:1});
 const errors=[], requests=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('requestfailed',r=>requests.push({url:r.url(),reason:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)requests.push({url:r.url(),status:r.status()});});
 await page.goto(base,{waitUntil:'networkidle'});
 const card=page.locator('a[href="reports/rf-current-probe/"]').first();
 await card.click(); await page.waitForURL('**/reports/rf-current-probe/');
 await page.waitForLoadState('networkidle');
 assert.match(await page.title(),/RF 전류 프로브.*ATLAS/);
 const expected=[['교정 표준 / Thru','SOLT용'],['지그 OUT','사용하지 않음'],['지그 OUT','프로브 SMA'],['프로브 SMA','지그 OUT']];
 for(let i=0;i<4;i++){
  await page.locator(`[data-step="${i}"]`).click();
  assert.match(await page.locator('#step-p2').innerText(),new RegExp(expected[i][0]));
  assert.match(await page.locator('#step-load').innerText(),new RegExp(expected[i][1]));
  assert.equal(await page.locator(`[data-step="${i}"]`).getAttribute('aria-pressed'),'true');
  await page.locator('#step-image').evaluate(img=>img.decode());
  assert.match(await page.locator('#step-image').getAttribute('src'),new RegExp(`step-${i}.svg$`));
  await page.locator('#step-image').screenshot({path:path.join(audit,`step-${i}.png`)});
 }
 assert.equal(await page.locator('#next-step').isDisabled(),true);
 await page.locator('#previous-step').focus(); await page.keyboard.press('Enter');
 assert.equal(await page.locator('#step-count').innerText(),'3 / 4');
 await page.locator('#next-step').click();
 await page.locator('.calibration-panel').screenshot({path:path.join(audit,'calibration-desktop.png')});
 if(!process.env.RFCP_REVIEW_URL) await page.locator('.calibration-panel').screenshot({path:path.join(report,'cover.png')});
 await page.locator('#step-image').screenshot({path:path.join(audit,'step-3.png')});
 for(const mode of ['signal','return','all']){
  await page.locator(`[data-path="${mode}"]`).click();
  await page.locator('#topology-diagram img').evaluate(img=>img.decode());
  assert.equal(await page.locator(`[data-path="${mode}"]`).getAttribute('aria-pressed'),'true');
 }
 await page.locator('.topology-panel').screenshot({path:path.join(audit,'topology-desktop.png')});
 await page.locator('#topology-diagram img').screenshot({path:path.join(audit,'pcb-current-path.png')});
 await page.locator('.cad-details summary').click();
 await page.locator('.cad-details img').evaluateAll(imgs=>Promise.all(imgs.map(img=>img.decode())));
 await page.locator('.cad-details').screenshot({path:path.join(audit,'pcb-cad.png')});
 await page.locator('.cad-details summary').click();
 assert.equal(await page.locator('#zt-value').innerText(),'5.000 Ω');
 assert.equal(await page.locator('#current-value').innerText(),'1.000 mA RMS');
 await page.locator('#s21-db').fill('-40');
 assert.equal(await page.locator('#zt-value').innerText(),'0.500 Ω');
 assert.equal(await page.locator('#current-value').innerText(),'10.000 mA RMS');
 await page.locator('#voltage-mv').fill('');
 assert.equal(await page.locator('#current-value').innerText(),'—');
 await page.locator('#voltage-mv').fill('5'); await page.locator('#s21-db').fill('-20');
 const responsive=[];
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  await page.locator('[data-step="3"]').click();
  const sizes=await page.evaluate(()=>({viewport:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}));
  assert.ok(sizes.doc<=width,`page overflow at ${width}: ${JSON.stringify(sizes)}`);
  const broken=await page.locator('img:not([loading="lazy"])').evaluateAll(imgs=>imgs.filter(img=>!img.complete||!img.naturalWidth).map(i=>i.src));
  assert.deepEqual(broken,[]);
  responsive.push(sizes);
  await page.locator('.calibration-panel').screenshot({path:path.join(audit,`calibration-${width}.png`)});
  await page.locator('.topology-panel').screenshot({path:path.join(audit,`topology-${width}.png`)});
 }
 await page.locator('.site-header > a').click(); await page.waitForURL(base);
 await page.setViewportSize({width:1365,height:960});
 await page.screenshot({path:path.join(audit,'catalog.png')});
 const result={base,step_states:4,keyboard_navigation:true,topology_modes:3,calculator_examples:3,responsive,back_to_catalog:true,page_errors:errors,failed_requests:requests};
 fs.writeFileSync(path.join(audit,'browser-checks.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));
 await browser.close(); assert.deepEqual(errors,[]); assert.deepEqual(requests,[]);
})().catch(e=>{console.error(e);process.exitCode=1});
