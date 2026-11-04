"""Check generated routes, archive portability, source provenance and frozen 3D payloads."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,zipfile,hashlib,subprocess,posixpath
P=Path(__file__).resolve().parent;D=P/'dist';S=P/'set_sources'
names=['index.html','assembly.html','assembly-guide.html','bom.html','manual.html']
extras=['purchase.html','impedance-review.html']
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.ids=[];self.runtime=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if 'href' in a:self.links.append(a['href'])
  if 'src' in a:self.links.append(a['src'])
  if (tag=='script' and 'src' in a) or (tag=='link' and a.get('rel')=='stylesheet'):self.runtime.append(a.get('src',a.get('href')))
def check(pages,files):
 checked=0
 for name,text in pages.items():
  p=Page(text)
  assert len(set(p.ids))==len(p.ids),(name,'duplicate ids')
  assert not p.runtime,(name,'external runtime',p.runtime)
  for u in p.links:
   q=urlsplit(u)
   assert q.scheme!='file' and q.hostname not in ['localhost','127.0.0.1'],(name,u)
   if q.scheme or q.netloc:continue
   target=posixpath.normpath(unquote(q.path)) if q.path else name
   assert target in files,(name,u,'missing file')
   if q.fragment and target in pages:assert unquote(q.fragment) in Page(pages[target]).ids,(name,u,'missing anchor')
   checked+=1
  for other in names:assert any(urlsplit(u).path.split('/')[-1]==other for u in p.links),(name,'missing navigation',other)
 return checked
pages={n:(D/n).read_text(encoding='utf-8') for n in names+extras}
links=check(pages,{f.relative_to(D).as_posix() for f in D.rglob('*') if f.is_file()})
with zipfile.ZipFile(D/'RFCP_A13_DOCUMENT_SET.zip') as z:
 assert z.testzip() is None
 offline=check({n:z.read(n).decode() for n in names+extras},set(z.namelist()))
 for name in z.namelist():
  if name.startswith(('files/','purchase-files/','impedance-files/')):assert z.read(name)==(D/name).read_bytes()
for rel,sha in json.loads((S/'source_manifest.json').read_text()).items():assert hashlib.sha256((P.parent/rel).read_bytes()).hexdigest()==sha,rel
baseline='bbefbc10560f117a01369d1a1e56d99d984b8884'
def old(name):return subprocess.check_output(['git','show',baseline+':dist/'+name],cwd=P).decode('utf-8')
def payload(text,key):return re.search(r'window\.'+key+r'=(.*?);</script>',text,re.S)[1]
for current,previous,key in [('assembly.html','index.html','A13_MODEL'),('assembly-guide.html','assembly-guide.html','RFCP_GUIDE')]:
 a=json.loads(payload(pages[current],key));b=json.loads(payload(old(previous),key))
 if key=='RFCP_GUIDE':
  for step in a['steps']:
   assert step.pop('bom'),step['id']
   step['action']=[v.replace('캘리브레이션 및 사용법','전체 조립과 사용') for v in step['action']]
 assert a==b,key+' geometry or motion changed'
rows=json.loads((S/'bom.json').read_text(encoding='utf-8'))
assert len(rows)==43 and len({r['id'] for r in rows})==43
by_id={r['id']:r for r in rows}
guide=json.loads(payload(pages['assembly-guide.html'],'RFCP_GUIDE'))
for step in guide['steps']:
 for item in step['bom']:
  assert item['id'] in by_id
  if item['qty'] is not None:assert 0<item['qty']<=by_id[item['id']]['qty'],(step['id'],item)
for name,s in pages.items():
 menu=re.search(r'<nav[^>]*aria-label="문서 세트"[^>]*>(.*?)</nav>',s,re.S)[1]
 assert [urlsplit(u).path.split('/')[-1] for u in re.findall(r'href="([^"]+)"',menu)[:5]]==['index.html','manual.html','assembly-guide.html','bom.html','assembly.html'],name
 assert '전체 조립과 사용' not in menu
assert 'MSO4054' not in pages['bom.html'] and 'LibreVNA' not in pages['bom.html']
assert sum(r['qty'] for r in rows if r['group']=='3D 출력')==15
cad=json.loads((S/'bom_cad_check.json').read_text(encoding='utf-8'));assert cad['pass']
cart=json.loads((D/'purchase-files/purchase_items.json').read_text(encoding='utf-8'))
assert len(cart)==9 and sum(r['line_krw'] for r in cart)==348513
assert len((D/'purchase-files/DigiKey_9_items.txt').read_text().splitlines())==9
assert by_id['E03']['status']=='보류'
for name in extras:
 assert not re.search(r'(?:[CE]:[/\\]|file:///|accessId=|invoiceId=)',pages[name],re.I),name
for u in Page(pages['purchase.html']).links:
 assert u.startswith(('https:','data:','#')),u
report=dict(classification='STATIC_DOCUMENT_AND_ARCHIVE_CHECK_NOT_BROWSER_QA',pass_=True,documents=names+extras,bom_rows=43,printed_types=10,printed_pieces=15,local_links_checked=links,offline_links_checked=offline,existing_3d_payloads_unchanged=True,cad_quantity_rows_checked=len(cad['rows']),native_sha256=cad['native_sha256'],cart_rows=9,cart_krw=348513,fixture_A02_on_hold=True)
(S/'static_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
