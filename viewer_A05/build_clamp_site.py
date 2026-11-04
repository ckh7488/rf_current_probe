"""Build the current C07 detail page alongside integrated A13."""
from pathlib import Path
import json,hashlib,struct,base64,zipfile,subprocess
P=Path(__file__).resolve().parent;R=P.parent;C=R/'mechanical/cable_clamp_C07_DRAFT'
v=json.loads((C/'verification.json').read_text());assert v['pass']
a=json.loads((C/'assembly_verification.json').read_text());assert a['pass'];assert a['native_sha256']==v['native_sha256']
assert v['native_sha256']==hashlib.sha256((C/'Cable_Clamp_C07_DRAFT.FCStd').read_bytes()).hexdigest()
mesh=json.loads((C/'mesh.json').read_text());buf=bytearray();parts=[]
for n,p in mesh.items():
 vs=[c for q in p['vertices'] for c in q];tr=[c for q in p['triangles'] for c in q];vo=len(buf);buf.extend(struct.pack('<'+'f'*len(vs),*vs));io=len(buf);buf.extend(struct.pack('<'+'I'*len(tr),*tr));parts.append({k:p[k] for k in ['color','group','printed']}|dict(name=n,vo=vo,vc=len(vs)//3,io=io,ic=len(tr)))
model={'printCount':sum(p.get('print_quantity',1) for p in mesh.values() if p['printed']),'parts':parts,'data':base64.b64encode(buf).decode(),'verificationSummary':'공칭 구경 21위치·상부 제거 21위치: 강체 겹침 0. 분실방지 덮개를 제거했습니다. 출력용 솔리드와 열린 가이드 조립 경로를 검사했습니다. 실제 조립·RF 시험은 미실행.'}
code='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
html=(P/'clamp_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->','<style>'+(P/'style.css').read_text(encoding='utf-8')+'</style>')
html=html.replace('<!--SCRIPTS-->','<script>'+code.replace('</script','<\\/script')+'</script><script>window.C07_MODEL='+json.dumps(model,separators=(',',':'))+';</script><script>'+(P/'clamp_kinematics.js').read_text(encoding='utf-8')+'\n'+(P/'clamp_viewer.js').read_text(encoding='utf-8')+'</script>')
(P/'dist/clamp.html').write_text(html,encoding='utf-8')
out=P/'dist/clamp';out.mkdir(exist_ok=True)
for n in ['Cable_Clamp_C07_DRAFT.step','verification.json','assembly_verification.json','README.md']:(out/n).write_bytes((C/n).read_bytes())
with zipfile.ZipFile(out/'C07_print_parts_DRAFT.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((C/'parts').glob('*')):
  if p.suffix in ['.step','.stl']:z.write(p,p.name)
 z.write(C/'README.md','README.md')
 z.write(R/'mechanical/build_cable_clamp_C07.py','source/mechanical/build_cable_clamp_C07.py')
 z.write(C/'verify_assembly.py','source/mechanical/cable_clamp_C07_DRAFT/verify_assembly.py')
print(json.dumps({'parts':len(parts),'html_bytes':len(html.encode()),'source_checks':'pass'}))
