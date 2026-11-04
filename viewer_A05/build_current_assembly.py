"""Whole-set visualization from current saved A14 geometry; read-only CAD."""
from pathlib import Path
import json,struct,base64,hashlib,shutil,os
P=Path(__file__).resolve().parent;R=P.parent;C=R/'mechanical/assembly_A14_DRAFT'
D=Path(os.environ.get('RFCP_BUILD_DIR',str(P/'dist')));D.mkdir(parents=True,exist_ok=True)
v=json.loads((C/'build_report.json').read_text());assert v['pass_geometry']
assert hashlib.sha256((C/'RFCP_A14_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()==v['native_sha256']
assert hashlib.sha256((C/'mesh.json').read_bytes()).hexdigest()==v['mesh_sha256']
mesh=json.loads((C/'mesh.json').read_text());buf=bytearray();parts=[]
for n,p in mesh.items():
 vs=[c for q in p['vertices'] for c in q];tr=[c for q in p['triangles'] for c in q]
 vo=len(buf);buf.extend(struct.pack('<'+'f'*len(vs),*vs));io=len(buf);buf.extend(struct.pack('<'+'I'*len(tr),*tr))
 part={k:p[k] for k in p if k not in ['vertices','triangles']}|dict(name=n,vo=vo,vc=len(vs)//3,io=io,ic=len(tr))
 if n.startswith('Cable') and n.split('_')[-1] in ['LeadStud','HandKnob','TopJamNut','TopWasher']:part['local']=n.split('_')[-1]
 parts.append(part)
model=dict(printCount=v['printed_total'],printKinds=v['printed_unique'],parts=parts,data=base64.b64encode(buf).decode(),native_sha256=v['native_sha256'],summary='A14/C07 저장 CAD의 배치·개폐·장착 경로를 보여 줍니다. 코어·권선과 출력 체인의 실측 특성은 별도 검증 대상입니다.')
vendor='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
html=(P/'assembly_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->','<style>'+(P/'style.css').read_text(encoding='utf-8')+(P/'viewer_annotations.css').read_text(encoding='utf-8')+'</style>')
html=html.replace('<!--SCRIPTS-->','<script>'+vendor+'</script><script>window.A14_MODEL='+json.dumps(model,separators=(',',':'))+';</script><script>'+(P/'clamp_kinematics.js').read_text(encoding='utf-8')+'\n'+(P/'viewer_annotations.js').read_text(encoding='utf-8')+'\n'+(P/'assembly_viewer.js').read_text(encoding='utf-8')+'</script>')
(D/'assembly.html').write_text(html,encoding='utf-8')
(D/'assembly').mkdir(exist_ok=True)
shutil.copyfile(C/'RFCP_A14_Integrated_DRAFT.step',D/'assembly/RFCP_A14_Integrated_DRAFT.step')
print(json.dumps(dict(parts=len(parts),html_bytes=len(html.encode()),native_sha256=v['native_sha256'])))
