"""Current routes, offline bundle, BOM counts, CAD mesh identity and assembly motion."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,zipfile,hashlib,subprocess,posixpath,base64,struct
P=Path(__file__).resolve().parent;D=P/'dist';S=P/'set_sources';R=P.parent
names=['index.html','manual.html','assembly-guide.html','bom.html','assembly.html','purchase.html','impedance-review.html']
class Page(HTMLParser):
 def __init__(self,s):super().__init__();self.links=[];self.ids=[];self.feed(s)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
def check(pages,files):
 total=0
 for n,s in pages.items():
  page=Page(s);assert len(page.ids)==len(set(page.ids)),n
  for u in page.links:
   q=urlsplit(u);assert q.scheme!='file' and q.hostname not in ['localhost','127.0.0.1'],(n,u)
   if q.scheme or q.netloc:continue
   target=posixpath.normpath(unquote(q.path)) if q.path else n
   assert target in files,(n,u)
   if q.fragment and target in pages:assert unquote(q.fragment) in Page(pages[target]).ids,(n,u)
   total+=1
  menu=re.search(r'<nav[^>]*aria-label="문서 세트"[^>]*>(.*?)</nav>',s,re.S)[1]
  assert [urlsplit(u).path.split('/')[-1] for u in re.findall(r'href="([^"]+)"',menu)[:5]]==names[:5],n
  assert '<!--SCRIPTS-->' not in s
 return total
pages={n:(D/n).read_text(encoding='utf-8') for n in names}
readiness=json.loads((S/'readiness.json').read_text(encoding='utf-8'))
assert len(readiness['gates'])==9
for n,s in pages.items():
 assert s.count('id="readiness-banner"')==1,n
 assert readiness['overall'] in s,n
for gate in readiness['gates']:
 assert 'id="'+gate['id']+'"' in pages['bom.html'],gate['id']
assert (D/'purchase-files/full-audit/README.md').is_file()
audit=json.loads((D/'purchase-files/full-audit/procurement.json').read_text(encoding='utf-8'))
links=check(pages,{f.relative_to(D).as_posix() for f in D.rglob('*') if f.is_file()})
with zipfile.ZipFile(D/'RFCP_A14_DOCUMENT_SET.zip') as z:
 assert z.testzip() is None
 offline=check({n:z.read(n).decode() for n in names},set(z.namelist()))
 assert len([n for n in z.namelist() if n.startswith('files/parts/') and n.endswith('.stl')])==15
 assert not any('LowerBody_FREE' in n or 'UpperLid_FREE' in n or 'CommonBase_FREE' in n for n in z.namelist())
rows=json.loads((S/'bom.json').read_text(encoding='utf-8'));assert len(rows)==58 and len({r['id'] for r in rows})==58
assert sum(r['qty'] for r in rows if r['group']=='3D 출력')==20
cad=json.loads((S/'bom_cad_check.json').read_text(encoding='utf-8'));assert cad['pass']
native=hashlib.sha256((R/'mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()
assert native==cad['native_sha256']
def payload(text,key):return json.loads(re.search(r'window\.'+key+r'=(.*?);</script>',text,re.S)[1])
guide=payload(pages['assembly-guide.html'],'RFCP_GUIDE');assembly=payload(pages['assembly.html'],'A14_MODEL')
assert guide['native_sha256']==assembly['native_sha256']==native
mesh=json.loads((R/'mechanical/assembly_A14_DRAFT/mesh.json').read_text());raw=base64.b64decode(assembly['data'])
assert len(assembly['parts'])==125
for part in assembly['parts']:
 n=part['name'];p=mesh[n];values=[a for v in p['vertices'] for a in v];tri=[a for v in p['triangles'] for a in v]
 assert raw[part['vo']:part['vo']+part['vc']*12]==struct.pack('<'+'f'*len(values),*values),n
 assert raw[part['io']:part['io']+part['ic']*4]==struct.pack('<'+'I'*len(tri),*tri),n
assert len(guide['steps'])==45
known={r['id']:r for r in rows}
from readiness_content import purchase_state
for row in rows:assert purchase_state(row) in pages['bom.html'],row['id']
c04=next(step for step in guide['steps'] if step['id']=='C04')
assert 'SBSMS-M4-5-20' in json.dumps(c04,ensure_ascii=False)
assert '팔로워 구매품 미확정' not in json.dumps(c04,ensure_ascii=False)
assert 'H05는 45°/4 mm' in pages['manual.html']
for step in guide['steps']:
 assert step['bom'],step['id']
 for item in step['bom']:
  assert item['id'] in known
  if item['qty'] is not None:assert 0<item['qty']<=known[item['id']]['qty'],(step['id'],item)
for rel,h in json.loads((S/'source_manifest.json').read_text()).items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
assert known['E03']['status']=='보류'
q=json.loads((S/'jlc_quote_status.json').read_text(encoding='utf-8'))
assert abs(sum(p['line_usd'] for p in q['parts'])-q['prints_usd'])<1e-6
assert round(q['total_usd']*1400)==q['total_krw']==560490
for n in ['bom.html','manual.html','index.html']:
 assert 'A13 / C07' not in pages[n] and '84 mm' not in pages[n],n
assert not any(x in pages['bom.html'] for x in ['MSO4054','LibreVNA'])
report=dict(classification='STATIC_ROUTE_OFFLINE_BUNDLE_CAD_IDENTITY_BOM_CHECK_NOT_PHYSICAL_ASSEMBLY',pass_=True,native_sha256=native,documents=names,steps=45,bom_rows=58,printed_types=15,printed_pieces=20,cad_quantity_rows=len(cad['rows']),actual_mesh_parts=125,local_links=links,offline_links=offline,fixture_A02_on_hold=True)
(S/'current_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
