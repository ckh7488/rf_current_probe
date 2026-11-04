"""Publishable A14 actual-CAD patch review; keep A13 manufacturing history separate."""
from pathlib import Path
import json,struct,base64,zipfile,hashlib,shutil,re
P=Path(__file__).resolve().parent;R=P.parent;O=R/'mechanical/assembly_A14_DRAFT';D=P/'dist'
b=json.loads((O/'build_report.json').read_text());v=json.loads((O/'verification.json').read_text())
assert b['pass_geometry'] and v['pass']
if v['native_sha256']!=b['native_sha256']:
 delta=json.loads((O/'catalogue_delta_verification.json').read_text())
 assert delta.get('pass') or delta.get('pass_scoped'), 'Current hardware delta must be verified'
 assert delta['native_sha256']==b['native_sha256']
 for ref in delta['references'].values():
  assert hashlib.sha256((R/ref['path']).read_bytes()).hexdigest()==ref['sha256']
scan=json.loads((R/'reviews/functionality_20260918/wall_scan_A14/summary.json').read_text())
assert all(p['watertight'] and p['below_1p5mm_samples']==0 for p in scan['parts'])
assert all(hashlib.sha256((O/'parts'/p['part']).read_bytes()).hexdigest()==p['stl_sha256'] for p in scan['parts'])
assert hashlib.sha256((O/'RFCP_A14_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()==b['native_sha256']
out=D/'split-a14';out.mkdir(exist_ok=True)
audit=R/'reviews/a14_recheck_20260921'
review=out/'recheck';review.mkdir(exist_ok=True)
for f in ['README.md','PHYSICAL_ACCEPTANCE.md']:
 shutil.copy2(audit/f,review/f)
for folder in ['structure','independent','hardware']:
 target=review/folder;target.mkdir(exist_ok=True)
 for p in (audit/folder).iterdir():
  if p.is_file() and p.suffix in ['.md','.json','.py','.png','.step'] and 'before' not in p.name and not (folder=='hardware' and p.suffix=='.png'):
   shutil.copy2(p,target/p.name)
for name in ['build_report.json','verification.json','README.md','catalogue_delta_verification.json']:
 if (O/name).exists():shutil.copy2(O/name,out/name)
shutil.copy2(R/'reviews/functionality_20260918/wall_scan_A14/summary.json',out/'wall-sampling.json')
sync=out/'document-sync'; sync.mkdir(exist_ok=True)
src=R/'reviews/a14_document_sync_20260921'
if (src/'README.md').exists():
 text=(src/'README.md').read_text(encoding='utf-8').replace('../../mechanical/assembly_A14_DRAFT/catalogue_delta_verification.json','../catalogue_delta_verification.json').replace('../../procurement/jlc_refresh_20260921/README.md','jlc_submission_history.md')
 (sync/'README.md').write_text(text,encoding='utf-8')
shutil.copy2(src/'jlc_observed_status.json',sync/'jlc_observed_status.json')
shutil.copy2(R/'procurement/jlc_refresh_20260921/README.md',sync/'jlc_submission_history.md')
for folder in ['cad_hardware','independent','hardware']:
 for p in (src/folder).rglob('*'):
  if p.is_file() and p.name!='mesh.json' and p.suffix in ['.json','.md','.py','.pdf','.png','.jpg']:
   target=sync/folder/p.relative_to(src/folder);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
closure=R/'reviews/technical_closure_20260921'
if (closure/'m2x12_result.json').exists():
 for name in ['README.md','m2x12_result.json','adopt_m2x12.py','before_m2/catalogue_delta_verification.json']:
  target=out/'technical-closure'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(closure/name,target)
with zipfile.ZipFile(out/'RFCP_A14_SPLIT_REVIEW.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in O.glob('*'):
  if p.is_file() and p.suffix in ['.FCStd','.step','.md','.json'] and p.name!='mesh.json':z.write(p,p.name)
 for p in (O/'parts').glob('*'):z.write(p,'parts/'+p.name)
 for name in ['build_assembly_A14.py','verify_assembly_A14.py']:z.write(R/'mechanical'/name,'source/mechanical/'+name)
 for name in ['RFCP_A13_Integrated_DRAFT.FCStd','mesh.json']:
  z.write(R/'mechanical/assembly_A13_DRAFT'/name,'source/mechanical/assembly_A13_DRAFT/'+name)
 for p in (R/'mechanical/assembly_A13_DRAFT/parts').glob('*'):z.write(p,'source/mechanical/assembly_A13_DRAFT/parts/'+p.name)
 for name in ['CarrierLoaded_INTERNAL.step']:z.write(R/'mechanical/assembly_A13_DRAFT'/name,'source/mechanical/assembly_A13_DRAFT/'+name)
 z.write(R/'mechanical/build_assembly_A13.py','source/mechanical/build_assembly_A13.py')
 z.write(R/'reviews/functionality_20260918/scan_walls.py','source/reviews/functionality_20260918/scan_walls.py')
 z.write(out/'wall-sampling.json','wall-sampling.json')
 for p in review.rglob('*'):
  if p.is_file():z.write(p,'recheck/'+p.relative_to(review).as_posix())
 for p in sync.rglob('*'):
  if p.is_file():z.write(p,'document-sync/'+p.relative_to(sync).as_posix())
 for p in (out/'technical-closure').rglob('*'):
  if p.is_file():z.write(p,'technical-closure/'+p.relative_to(out/'technical-closure').as_posix())
 for rel in ['cad_hardware/before_f05/mesh.json','cad_hardware/before_f05/RFCP_A14_Integrated_DRAFT.FCStd','before_cad/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.FCStd']:
  z.write(src/rel,'document-sync/'+rel)
buf=bytearray();versions=[];shared={};original_geometry={}
for revision in ['A13','A14']:
 data=json.loads((R/f'mechanical/assembly_{revision}_DRAFT/mesh.json').read_text());parts=[]
 for n,p in data.items():
  if revision=='A14' and n in shared and original_geometry[n]==(p['vertices'],p['triangles']):
   q={k:val for k,val in p.items() if k not in ['vertices','triangles']};q.update(shared[n]);parts.append(q);continue
  vs=[a for xyz in p['vertices'] for a in xyz];tr=[a for xyz in p['triangles'] for a in xyz]
  q={k:val for k,val in p.items() if k not in ['vertices','triangles']};q.update(name=n,vo=len(buf),vc=len(vs)//3)
  buf.extend(struct.pack('<'+'f'*len(vs),*vs));q.update(io=len(buf),ic=len(tr));buf.extend(struct.pack('<'+'I'*len(tr),*tr));parts.append(q)
  if revision=='A13' and n not in ['CommonBase','LowerBody','UpperLid']:
   shared[n]={k:q[k] for k in ['name','vo','vc','io','ic']};original_geometry[n]=(p['vertices'],p['triangles'])
 versions.append(parts)
payload=dict(versions=versions,data=base64.b64encode(buf).decode(),dimensions={n:[round(x,1) for x in q['bbox_mm']] for n,q in b['parts'].items()},native_sha256=b['native_sha256'])
vendor='\n'.join((P/'vendor'/n).read_text() for n in ['three.min.js','OrbitControls.js'])
page=(P/'split_review_template.html').read_text(encoding='utf-8')
page=page.replace('<!--SCRIPTS-->','<script>'+vendor+'</script><script>window.SPLIT_MODEL='+json.dumps(payload,separators=(',',':')).replace('</','<\\/')+';</script><script>'+(P/'split_review_viewer.js').read_text(encoding='utf-8')+'</script>')
(D/'split-review.html').write_text(page,encoding='utf-8')
banner='<aside id="a14-patch-notice" style="padding:12px 24px;background:#fff0cd;color:#573e12;border-bottom:1px solid #d6b265;font:15px/1.6 system-ui"><b>9/21 A14 재검증·JLC 재검토 접수</b> · 나사·기성 노브·PCB 받침 보강까지 반영했습니다. 이 페이지 본문·견적은 A13 이력입니다. <a style="color:#075c75;font-weight:700" href="split-review.html">현행 3D · 조립 변경 · 검증 결과 →</a></aside>'
for name in ['compare.html']:
 p=D/name;s=p.read_text(encoding='utf-8');s=re.sub(r'<aside id="a14-patch-notice".*?</aside>','',s,flags=re.S)
 s=s.replace('</header>','</header>'+banner,1);p.write_text(s,encoding='utf-8')
source=P/'split_sources';source.mkdir(exist_ok=True)
for f in [R/'mechanical/build_assembly_A14.py',R/'mechanical/verify_assembly_A14.py',O/'README.md',O/'build_report.json',O/'verification.json']:shutil.copy2(f,source/f.name)
print(json.dumps(dict(html_bytes=len(page.encode()),parts=[len(x) for x in versions],native_sha256=b['native_sha256'])))
