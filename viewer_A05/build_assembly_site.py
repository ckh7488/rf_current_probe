from pathlib import Path
import json,struct,base64,hashlib,zipfile
P=Path(__file__).resolve().parent;R=P.parent;C=R/'mechanical/assembly_A13_DRAFT';v=json.loads((C/'build_report.json').read_text())
assert v['pass'],v['static_collisions']
assert hashlib.sha256((C/'RFCP_A13_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()==v['native_sha256']
assert hashlib.sha256((R/'mechanical/build_assembly_A13.py').read_bytes()).hexdigest()==v['source_sha256']
check=json.loads((C/'verification.json').read_text());assert check['pass'] and check['native_sha256']==v['native_sha256']
ret=json.loads((C/'retention_mount_verification.json').read_text());assert ret['pass'] and ret['native_sha256']==v['native_sha256']
c02=R/'mechanical/cable_clamp_C07_DRAFT';cv=json.loads((c02/'verification.json').read_text());assert cv['pass']
assert hashlib.sha256((R/'mechanical/build_cable_clamp_C07.py').read_bytes()).hexdigest()==cv['source_sha256']
assert hashlib.sha256((C/'mesh.json').read_bytes()).hexdigest()==v['mesh_sha256']
for rel,h in v.get('input_sha256',{}).items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,('stale assembly input',rel)
audit=json.loads((R/'reviews/simplification_20260918/simplification_verification.json').read_text());assert audit['pass']
for rel,h in audit['sources'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
scan=json.loads((R/'reviews/simplification_20260918/print_scan_A13/summary.json').read_text());assert scan['pass_identity_and_mesh'] and scan['below_1p5mm_samples']==0
mesh=json.loads((C/'mesh.json').read_text());buf=bytearray();parts=[]
for n,p in mesh.items():
 vs=[c for q in p['vertices'] for c in q];tr=[c for q in p['triangles'] for c in q];vo=len(buf);buf.extend(struct.pack('<'+'f'*len(vs),*vs));io=len(buf);buf.extend(struct.pack('<'+'I'*len(tr),*tr));parts.append({k:p[k] for k in p if k not in ['vertices','triangles']}|dict(name=n,vo=vo,vc=len(vs)//3,io=io,ic=len(tr)))
model={'printCount':v['printed_total'],'printKinds':v['printed_unique'],'parts':parts,'data':base64.b64encode(buf).decode(),'summary':'A13 / C07 원본에서 공칭 조립·개폐·탈착·코어 치수 민감도를 재확인했습니다. 분실방지 덮개10개와 바닥 유지판1개를 제거해 출력물을26개에서15개로 줄였습니다. 기존 보강 형상과 열린 너트 삽입 경로를 확인했습니다. 실제 출력·손조립·내구성·RF 시험은 미실행입니다. 세부 검사 범위와 남은 조건은 이번 재검토 결과에 기록했습니다.'}
vendor='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
html=(P/'assembly_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->','<style>'+(P/'style.css').read_text(encoding='utf-8')+'</style>')
html=html.replace('<!--SCRIPTS-->','<script>'+vendor+'</script><script>window.A13_MODEL='+json.dumps(model,separators=(',',':'))+';</script><script>'+(P/'clamp_kinematics.js').read_text(encoding='utf-8')+'\n'+(P/'assembly_viewer.js').read_text(encoding='utf-8')+'</script>')
(P/'dist/assembly.html').write_text(html,encoding='utf-8');out=P/'dist/assembly';out.mkdir(exist_ok=True)
for n in ['RFCP_A13_Integrated_DRAFT.step','README.md','build_report.json','verification.json','retention_mount_verification.json']:
 if (C/n).exists():(out/n).write_bytes((C/n).read_bytes())
with zipfile.ZipFile(out/'A13_REVIEW_PACKAGE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in C.glob('*'):
  if f.suffix in ['.md','.json','.py','.FCStd'] and f.name!='mesh.json':z.write(f,f.name)
 for f in (C/'parts').glob('*'):z.write(f,'parts/'+f.name)
 for rel in ['mechanical/build_assembly_A13.py','mechanical/build_cable_clamp_C07.py','mechanical/clamp_A07_DRAFT/RFCP_Clamp_A07_DRAFT.FCStd','mechanical/clamp_A05_DRAFT/RFCP_A05_Fixture_REVIEW.FCStd','mechanical/cable_clamp_C07_DRAFT/Cable_Clamp_C07_DRAFT.FCStd','mechanical/cable_clamp_C07_DRAFT/mesh.json','mechanical/cable_clamp_C07_DRAFT/verification.json','mechanical/cable_clamp_C07_DRAFT/verify_assembly.py','mechanical/cable_clamp_C07_DRAFT/assembly_verification.json','mechanical/cable_clamp_C07_DRAFT/README.md']:
  z.write(R/rel,'source/'+rel)
 z.write(C/'verify_assembly.py','source/mechanical/assembly_A13_DRAFT/verify_assembly.py')
 z.write(C/'verify_retention_mount.py','source/mechanical/assembly_A13_DRAFT/verify_retention_mount.py')
 for n in ['RFCP_A13_Integrated_DRAFT.FCStd','mesh.json','build_report.json','verification.json','retention_mount_verification.json','CarrierLoaded_INTERNAL.step','UpperLid_UNLOADED_DRAFT.step']:
  z.write(C/n,'source/mechanical/assembly_A13_DRAFT/'+n)
 for f in (C/'parts').glob('*'):z.write(f,'source/mechanical/assembly_A13_DRAFT/parts/'+f.name)
 for f in (c02/'parts').glob('*'):z.write(f,'source/mechanical/cable_clamp_C07_DRAFT/parts/'+f.name)
 z.write(R/'reviews/a12_20260918/sources/SMO-3.pdf','source/reviews/a12_20260918/sources/SMO-3.pdf')
 z.writestr('REBUILD.txt','Open source/ as the project root. FreeCAD 1.0.2: run mechanical/build_cable_clamp_C07.py before mechanical/build_assembly_A13.py. The source/ tree contains the exact saved CAD, inputs and verification scripts. Printable lid: parts/UpperLid_FREE_DRAFT only; assembled/deflected lid is not a print file. Prototype review package, not production approval.\n')
 for f in (R/'reviews/simplification_20260918').glob('*.md'):z.write(f,'review/'+f.name)
 for f in (R/'reviews/simplification_20260918').glob('*.json'):
  if f.name not in ['comparison_3d.json','site_artifact_check.json']:z.write(f,'review/geometry/'+f.name)
 for rel in ['mechanical/assembly_A11_DRAFT/RFCP_A11_Integrated_DRAFT.FCStd','mechanical/cable_clamp_C05_DRAFT/Cable_Clamp_C05_DRAFT.FCStd']:
  z.write(R/rel,'source/'+rel)
 for folder in ['reviews/simplification_20260918']:
  for f in (R/folder).rglob('*'):
   if f.is_file() and f.suffix in ['.md','.json','.py','.csv'] and f.name not in ['comparison_3d.json','site_artifact_check.json'] and '__pycache__' not in f.parts:
    z.write(f,'source/'+str(f.relative_to(R)).replace('\\','/'))
 for f in C.glob('*.md'):z.write(f,'source/mechanical/assembly_A13_DRAFT/'+f.name)
source_out=P/'assembly_sources';source_out.mkdir(exist_ok=True)
for f in [R/'mechanical/build_assembly_A13.py',R/'mechanical/build_cable_clamp_C07.py',C/'verify_assembly.py',C/'verify_retention_mount.py',C/'README.md']:(source_out/f.name).write_bytes(f.read_bytes())
print(json.dumps({'parts':len(parts),'html_bytes':len(html.encode()),'native_sha256':v['native_sha256']}))
