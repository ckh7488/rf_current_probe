"""Build a self-contained two-view CAD comparison, preserving previous figures."""
from pathlib import Path
import json,struct,base64,shutil,hashlib
P=Path(__file__).resolve().parent; R=P.parent; O=R/'reviews/simplification_20260918'
payload=json.loads((O/'comparison_3d.json').read_text());buf=bytearray()
for name,expected in payload['sources'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==expected,('stale comparison CAD',name)
for c in payload['cases']:
 for collection in ['models','changes']:
  for parts in c[collection]:
   for p in parts:
    vs=[v for point in p.pop('vertices') for v in point];tr=[i for t in p.pop('triangles') for i in t]
    p.update(vo=len(buf),vc=len(vs)//3);buf.extend(struct.pack('<'+'f'*len(vs),*vs));p.update(io=len(buf),ic=len(tr));buf.extend(struct.pack('<'+'I'*len(tr),*tr))
payload['data']=base64.b64encode(buf).decode()
vendor='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
page=(P/'compare_3d_template.html').read_text(encoding='utf-8').replace('<!--STYLE-->','<style>'+(P/'compare_3d.css').read_text()+'</style>')
page=page.replace('<!--SCRIPTS-->','<script>'+vendor+'</script><script>window.RFCP_COMPARE='+json.dumps(payload,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')+';</script><script>'+(P/'compare_3d_viewer.js').read_text(encoding='utf-8')+'</script>')
(P/'dist/compare.html').write_text(page,encoding='utf-8')
src=P/'audit_sources/simplification_20260918';src.mkdir(parents=True,exist_ok=True)
for p in O.glob('*.py'):shutil.copyfile(p,src/p.name)
(src/'cad_sources.json').write_text(json.dumps(payload['sources'],indent=2))
print(json.dumps({'cases':len(payload['cases']),'embedded_bytes':len(page.encode()),'source_hashes':len(payload['sources'])}))
