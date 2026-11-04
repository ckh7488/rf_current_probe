from pathlib import Path
import json,re,base64,struct,math,zipfile
from html.parser import HTMLParser
P=Path(__file__).resolve().parent;D=P/'dist';s=(D/'split-review.html').read_text(encoding='utf-8')
data=json.loads(re.search(r'window.SPLIT_MODEL=(.*?);</script>',s,re.S)[1]);raw=base64.b64decode(data['data'])
count=0
for version in data['versions']:
 assert len({p['name'] for p in version})==len(version)
 for p in version:
  assert p['vo']%4==p['io']%4==0
  xyz=struct.unpack_from('<'+str(p['vc']*3)+'f',raw,p['vo']);tri=struct.unpack_from('<'+str(p['ic'])+'I',raw,p['io'])
  assert all(math.isfinite(x) for x in xyz) and min(tri)>=0 and max(tri)<p['vc'] and p['ic']%3==0
  count+=1
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ['href','src']:
   if k not in a:continue
   val=a[k]
   if ':' in val or val.startswith('#'):continue
   assert (D/val.split('?')[0].split('#')[0]).exists(),val
Links().feed(s)
assert len(s.encode())<25*1024*1024
with zipfile.ZipFile(D/'split-a14/RFCP_A14_SPLIT_REVIEW.zip') as z:
 assert z.testzip() is None
 assert len([n for n in z.namelist() if n.startswith('parts/') and n.endswith('.stl')])==15
for name in ['index.html','assembly.html','assembly-guide.html','bom.html','manual.html','purchase.html']:
 assert 'id="a14-patch-notice"' not in (D/name).read_text(encoding='utf-8')
assert (D/'compare.html').read_text(encoding='utf-8').count('id="a14-patch-notice"')==1
import hashlib
native=P.parent/'mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.FCStd'
assert data['native_sha256']==hashlib.sha256(native.read_bytes()).hexdigest()
mesh=json.loads((native.parent/'mesh.json').read_text())
assert len(data['versions'][1])==len(mesh)==125
for part in data['versions'][1]:
 p=mesh[part['name']];vs=[a for xyz in p['vertices'] for a in xyz];tr=[a for xyz in p['triangles'] for a in xyz]
 assert raw[part['vo']:part['vo']+part['vc']*12]==struct.pack('<'+'f'*len(vs),*vs)
 assert raw[part['io']:part['io']+part['ic']*4]==struct.pack('<'+'I'*len(tr),*tr)
result=dict(classification='STATIC_ARTIFACT_VALIDATION_NOT_BROWSER_TEST',parts_decoded=count,html_bytes=len(s.encode()),zip_integrity=True,entrypoints=7,pass_checks=True,native_sha256=data['native_sha256'])
(D/'split-a14/site-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
