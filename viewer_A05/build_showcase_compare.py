"""Generate a single A13/A14 comparison, without copying historical packages."""
from pathlib import Path
import os, json, struct, base64, re, hashlib
P=Path(__file__).resolve().parent; R=P.parent
D=Path(os.environ.get('RFCP_BUILD_DIR',str(P/'dist'))); D.mkdir(parents=True,exist_ok=True)
C=R/'mechanical/assembly_A14_DRAFT'
b=json.loads((C/'build_report.json').read_text())
assert hashlib.sha256((C/'RFCP_A14_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()==b['native_sha256']
buf=bytearray();versions=[];shared={};original={}
for revision in ['A13','A14']:
    data=json.loads((R/f'mechanical/assembly_{revision}_DRAFT/mesh.json').read_text());parts=[]
    for name,p in data.items():
        q={k:v for k,v in p.items() if k not in ['vertices','triangles']}
        if revision=='A14' and name in shared and original[name]==(p['vertices'],p['triangles']):
            q.update(shared[name]);parts.append(q);continue
        vs=[v for xyz in p['vertices'] for v in xyz];tr=[v for xyz in p['triangles'] for v in xyz]
        q.update(name=name,vo=len(buf),vc=len(vs)//3)
        buf.extend(struct.pack('<'+'f'*len(vs),*vs));q.update(io=len(buf),ic=len(tr))
        buf.extend(struct.pack('<'+'I'*len(tr),*tr));parts.append(q)
        if revision=='A13' and name not in ['CommonBase','LowerBody','UpperLid']:
            shared[name]={k:q[k] for k in ['name','vo','vc','io','ic']};original[name]=(p['vertices'],p['triangles'])
    versions.append(parts)
payload=dict(versions=versions,data=base64.b64encode(buf).decode(),dimensions={n:[round(x,1) for x in q['bbox_mm']] for n,q in b['parts'].items()},native_sha256=b['native_sha256'])
style=re.search(r'<style>(.*?)</style>',(P/'split_review_template.html').read_text(encoding='utf-8'),re.S)[1]
style+=(P/'viewer_annotations.css').read_text(encoding='utf-8')
vendor='\n'.join((P/'vendor'/name).read_text(encoding='utf-8') for name in ['three.min.js','OrbitControls.js'])
script=(P/'viewer_annotations.js').read_text(encoding='utf-8')+'\n'+(P/'split_review_viewer.js').read_text(encoding='utf-8').replace('이번 재검토에서 고친 세 가지','A14의 세 가지 구조 변경')
page=(P/'showcase_compare_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->',style)
page=page.replace('<!--SCRIPTS-->','<script>'+vendor+'</script><script>window.SPLIT_MODEL='+json.dumps(payload,separators=(',',':'))+';</script><script>'+script+'</script>')
(D/'compare.html').write_text(page,encoding='utf-8')
print(json.dumps(dict(page='compare.html',parts=[len(v) for v in versions],native_sha256=b['native_sha256'])))
