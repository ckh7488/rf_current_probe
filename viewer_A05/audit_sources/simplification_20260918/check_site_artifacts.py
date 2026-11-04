"""Static artifact identity/link checks; no browser rendering claim."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import base64,json,re,hashlib,zipfile
R=Path(__file__).resolve().parents[2];P=R/'viewer_A05';D=P/'dist'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for key,val in attrs:
   if key in ('href','src') and val:self.links.append(val)
pages=['index.html','clamp.html','compare.html','audit/latest-review.html'];checked=[]
for name in pages:
 p=D/name;s=p.read_text(encoding='utf-8');a=Links();a.feed(s)
 for link in a.links:
  u=urlsplit(link)
  if u.scheme or u.netloc or not u.path:continue
  path=(D/unquote(u.path.lstrip('/'))) if u.path.startswith('/') else p.parent/unquote(u.path)
  assert path.exists() or path.with_suffix('.html').exists(),(name,link)
  checked.append([name,link])
 for var in ['A13_MODEL','C07_MODEL','RFCP_COMPARE']:
  m=re.search(r'window\.'+var+r'=(.*?);</script>',s,re.S)
  if not m:continue
  data=json.loads(m[1]);buf=base64.b64decode(data['data'],validate=True)
  if 'parts' in data:parts=data['parts']
  else:parts=[p for c in data['cases'] for k in ['models','changes'] for collection in c[k] for p in collection]
  for q in parts:
   assert q['vo']%4==0 and q['io']%4==0
   assert q['vo']+q['vc']*12<=len(buf) and q['io']+q['ic']*4<=len(buf),(name,q['name'])
  if var=='A13_MODEL':assert(data['printKinds'],data['printCount'])==(10,15)
  if var=='C07_MODEL':assert data['printCount']==5
  if var=='RFCP_COMPARE':assert len(data['cases'])==24
zpath=D/'assembly/A13_REVIEW_PACKAGE.zip'
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for f in (R/'mechanical/assembly_A13_DRAFT/parts').glob('*'):
  assert z.read('parts/'+f.name)==f.read_bytes()
 for f in ['mechanical/build_assembly_A13.py','mechanical/build_cable_clamp_C07.py']:
  assert z.read('source/'+f)==(R/f).read_bytes()
report=dict(classification='STATIC_SITE_LINK_PAYLOAD_AND_PACKAGE_IDENTITY',pages=pages,local_links_checked=len(checked),comparison_cases=24,pass_=True,
 sha256={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/n for n in pages]+[zpath]})
report['pass']=report.pop('pass_')
(Path(__file__).parent/'site_artifact_check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
