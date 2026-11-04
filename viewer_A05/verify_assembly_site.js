const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const pages=[];
for(const file of ['index.html','clamp.html','compare.html','compare-history.html','audit/latest-review.html']){
const html=fs.readFileSync(path.join(__dirname,'dist',file),'utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
for(const s of scripts)new vm.Script(s);
const refs=[...html.matchAll(/(?:href|src)="([^"]+)"/g)].map(x=>x[1]).filter(x=>!/^https?:|^data:|^#/.test(x));
for(const r of refs)assert(fs.existsSync(path.resolve(__dirname,'dist',path.dirname(file),r.split('?')[0])),r);
if(file==='compare-history.html')assert.equal((html.match(/data-card="/g)||[]).length,8);
if(['index.html','clamp.html'].includes(file))assert.equal((html.match(/data-mode="/g)||[]).length,4);
if(file==='compare.html'){
 const match=html.match(/window.RFCP_COMPARE=(.*?);<\/script>/s);assert(match,'Embedded CAD comparison');
 const model=JSON.parse(match[1]);assert.equal(model.cases.length,14);
 for(const c of model.cases){assert.equal(c.models.length,2);assert(c.models.every(p=>p.length>0));assert(c.changes.some(p=>p.length>0),'No actual change: '+c.key);}
}
assert(!/file:\/\/|localhost|127\.0\.0\.1|cdn\./.test(html));
pages.push({file,syntax_scripts:scripts.length,local_links:refs,four_sections:['index.html','clamp.html'].includes(file),comparison_pairs:file==='compare.html'?14:file==='compare-history.html'?8:null,external_runtime_dependencies:false});
}
const report={pages,classification:'STATIC_ARTIFACT_CHECK',browser_checks_reported_separately:true};
fs.writeFileSync(path.join(__dirname,'assembly_sources/viewer_verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
