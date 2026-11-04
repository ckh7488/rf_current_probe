"""Release checks for public contents, nested ZIPs, links and actual CAD payloads."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re, json, zipfile, hashlib, io, posixpath, base64, struct
from showcase_content import ROWS
P=Path(__file__).resolve().parent;R=P.parent
BUNDLE='RFCP_A14_DOCUMENT_SET.zip'
PAGES={'index.html','manual.html','assembly-guide.html','bom.html','assembly.html','compare.html','design-review.html','impedance-review.html','testing.html','split-review.html'}
PUBLIC_FILES=PAGES|{BUNDLE,'cover-a14.png','vendor/LICENSE-three.txt','files/SMO-3.pdf','files/READ_FIRST_NOT_FOR_FABRICATION.txt','assembly/RFCP_A14_Integrated_DRAFT.step','files/RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip'}|{'files/'+r['file'] for r in ROWS if r['file']}
FORBIDDEN=['purchase-files/','purchase.html','split-a14/','audit/','QUOTE_ONLY','RFCP_PREARRIVAL_EVIDENCE','미결제','미제출','업체 승인','업체 파일 승인','구매팀','구매 카트','전포장','발룬','Molex','슬립링','17:10','readiness-banner','bom.html#readiness']

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.ids=[];self.tags=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if a.get('id'):self.ids.append(a['id'])
        for key in ['href','src','poster']:
            if a.get(key):self.links.append(a[key])

def payload(text,key):return json.loads(re.search(r'window\.'+key+r'=(.*?);</script>',text,re.S)[1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check_content(files,read,atlas=False):
    allowed=PUBLIC_FILES|({'document-set.css'} if atlas else set())
    assert files<=allowed, f'Unexpected public files: {sorted(files-allowed)}'
    assert PAGES<=files and 'vendor/LICENSE-three.txt' in files
    pages={n:read(n).decode('utf-8') for n in PAGES}
    parsed={n:Page(s) for n,s in pages.items()}
    count=0
    for name,text in pages.items():
        for word in FORBIDDEN:assert word not in text,(name,word)
        assert not re.search(r'(?:file://|[CE]:[\\/](?:Users|Current_Probe)|https?://(?:localhost|127\.0\.0\.1))',text,re.I),name
        assert len(parsed[name].ids)==len(set(parsed[name].ids)),name
        assert '<!--SCRIPTS-->' not in text
        for url in parsed[name].links:
            u=urlsplit(url)
            if u.scheme or u.netloc:continue
            target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(u.path))) if u.path else name
            if atlas and target in ['../..','../../assets/theme.v1.css','../../assets/favicon.svg']:continue
            assert target in files,(name,url)
            if u.fragment and target in parsed:assert unquote(u.fragment) in parsed[target].ids,(name,url)
            count+=1
    assert len(ROWS)==57 and sum(r['qty'] for r in ROWS if r['group']=='3D 출력')==20
    assert all(r['id'] in parsed['bom.html'].ids for r in ROWS)
    assert '상태</th>' not in pages['bom.html'] and 'id="readiness"' not in pages['bom.html']
    for needed in ['RP-SMA','코어 밖','단일 50 Ω','설치2개']:
        assert needed in pages['bom.html'],needed
    proof=[a for t,a in parsed['assembly-guide.html'].tags if t=='details' and a.get('id')=='proofDetails']
    assert len(proof)==1 and 'open' not in proof[0]
    for name in ['assembly-guide.html','assembly.html','compare.html']:
        assert '3D 글씨 표시' in pages[name] and 'annotationDock' in pages[name],name
        assert 'rfcp.viewer.annotations.visible.v1' in pages[name],name
    guide_js=(P/'guide_viewer.js').read_text(encoding='utf-8')
    for key in re.findall(r"\$\('([^']+)'\)",guide_js):assert key in parsed['assembly-guide.html'].ids,key
    assert 'DRAFT — NOT FOR FABRICATION' in pages['bom.html']
    for needed in ['Fixture A03','1–500 MHz','−6 dB','SIMULATED','보정량','불확도']:
        assert needed in pages['design-review.html'],needed
    assert '실측' in pages['manual.html'] and '광대역 펄스 전류 파형 복원은 구현하지 않았습니다' in pages['manual.html']
    assert '별도 SOL 교정한 VNA PORT2 · SMA 암' in pages['assembly.html']
    assert 'loadCoax.visible=solt&&!thru' in pages['assembly.html']
    assert '교정 기준면은 장비 본체가 아닌 케이블 끝입니다.' not in pages['assembly.html']
    assert '출력 기준 계산 모드는 아직 미구현' not in pages['assembly.html']
    assert '별도로 교정된 SMA 암 기준면' in pages['manual.html']
    return pages,count

def verify(folder,atlas=False):
    folder=Path(folder)
    files={f.relative_to(folder).as_posix() for f in folder.rglob('*') if f.is_file()}
    pages,links=check_content(files,lambda n:(folder/n).read_bytes(),atlas)
    assert len([n for n in files if n.endswith('.stl')])==15
    assert [n for n in files if n.endswith('.step')]==['assembly/RFCP_A14_Integrated_DRAFT.step']
    assert len([n for n in files if n.endswith('.zip')])==2
    for row in ROWS:
        if row['file']:assert sha(folder/'files'/row['file'])==sha(R/'mechanical/assembly_A14_DRAFT'/row['file'])
    for family,name in [('probe_head_A04_DRAFT','RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip')]:
        assert sha(folder/'files'/name)==sha(R/'hardware'/family/name)
        with zipfile.ZipFile(folder/'files'/name) as z:
            assert z.testzip() is None
            assert all(Path(n).suffix in ['.gbl','.gbs','.gbo','.gm1','.gtl','.gts','.gto','.gbrjob','.drl','.g1','.g2'] for n in z.namelist())
    with zipfile.ZipFile(folder/BUNDLE) as z:
        assert z.testzip() is None
        assert set(z.namelist())==files-{BUNDLE}
        _,offline_links=check_content(set(z.namelist()),z.read,atlas)
        for name in z.namelist():
            if name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:
                    assert nested.testzip() is None
                    assert all(not any(word in n for word in FORBIDDEN) for n in nested.namelist())
            if not name.endswith('.html'):assert z.read(name)==(folder/name).read_bytes(),name
    guide=payload(pages['assembly-guide.html'],'RFCP_GUIDE');assembly=payload(pages['assembly.html'],'A14_MODEL');comparison=payload(pages['compare.html'],'SPLIT_MODEL')
    native=sha(R/'mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.FCStd')
    assert guide['native_sha256']==assembly['native_sha256']==comparison['native_sha256']==native
    assert len(guide['steps'])==46 and len(assembly['parts'])==125
    assert any(s['id']=='Q00' and '다섯 핀' in ' '.join(s['action']) for s in guide['steps'])
    assert '45단계' not in pages['assembly-guide.html']
    assert all(s.get('proof') for s in guide['steps'])
    h05=next(s for s in guide['steps'] if s['id']=='H05')
    assert h05['moves']['PCB']['keys'][1]==[.15,[0,0,.3],0]
    assert '권선 끝선은 아직 납땜하지 말고' in ' '.join(h05['action'])
    assert '<meta http-equiv="refresh" content="0;url=compare.html">' in pages['split-review.html']
    # Every vertex and triangle of the live whole assembly remains exact float32/index data.
    mesh=json.loads((R/'mechanical/assembly_A14_DRAFT/mesh.json').read_text());raw=base64.b64decode(assembly['data'])
    for part in assembly['parts']:
        p=mesh[part['name']];vs=[v for xyz in p['vertices'] for v in xyz];tri=[i for t in p['triangles'] for i in t]
        assert raw[part['vo']:part['vo']+part['vc']*12]==struct.pack('<'+'f'*len(vs),*vs),part['name']
        assert raw[part['io']:part['io']+part['ic']*4]==struct.pack('<'+'I'*len(tri),*tri),part['name']
    assert 'RFCP_Fixture_Flat_A04' not in '\n'.join(pages.values())
    return dict(classification='PUBLIC_CONTENT_ARCHIVE_LINK_CAD_CHECK_NOT_PHYSICAL_VALIDATION',pass_=True,files=len(files),bytes=sum((folder/n).stat().st_size for n in files),pages=len(PAGES),bom_rows=len(ROWS),steps=46,stl_kinds=15,printed_instances=20,gerber_zips=1,local_links=links,offline_links=offline_links,native_sha256=native)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('folder',nargs='?',default=str(P/'dist'));p.add_argument('--atlas',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.folder,a.atlas),ensure_ascii=False,indent=2))
