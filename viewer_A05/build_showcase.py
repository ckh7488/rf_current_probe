"""Build a clean RFCP public profile; never copy procurement or audit trees."""
from pathlib import Path
import re, json, hashlib, zipfile, html, shutil, os, sys, tempfile, subprocess
from showcase_content import ROWS, manual
from showcase_analysis import build as build_analysis

P=Path(__file__).resolve().parent; R=P.parent; D=P/'dist'; S=P/'set_sources'
NAV=[('index.html','표지'),('manual.html','설명서'),('assembly-guide.html','조립절차서'),('bom.html','BOM'),('assembly.html','캘리브레이션 및 사용법')]
BUNDLE='RFCP_A14_DOCUMENT_SET.zip'
CSS=(P/'set.css').read_text(encoding='utf-8')+'''
details>summary{cursor:pointer;font-weight:650}details[open]>summary{margin-bottom:12px}
td{overflow-wrap:anywhere}.resource-list{display:flex;flex-wrap:wrap;gap:12px 24px}
.scope-note{font-size:14px;color:#526d78;max-width:75ch;margin:18px 0 0}
.tablewrap{overflow:auto}.technical-links{margin:30px 0}.technical-links a{margin-right:22px}
@media(max-width:600px){.intro h1{font-size:30px}.actions{flex-wrap:wrap}.tablewrap table{min-width:660px}}
'''
def nav(active):
    return ''.join(f'<a href="{url}"'+(' class="active" aria-current="page"' if url==active else '')+f'>{label}</a>' for url,label in NAV)

def frame(name,title,body):
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="RFCP 수동 RF 전류 프로브: 구조, 3D 조립절차, 부품 규격과 교정 원리"><title>RFCP · '+title+'</title><style>'+CSS+'</style></head><body><header><a class="brand" href="index.html">RFCP</a><nav aria-label="문서 세트">'+nav(name)+'</nav></header><main>'+body+'</main><footer><span>RFCP · A14 / C07 · Head PCB A04 · 교정지그 Fixture A03</span><div class="readmore"><a href="index.html">표지</a><a href="'+BUNDLE+'" download>문서 세트 저장</a></div></footer></body></html>'

def intro(num,title,text):
    return f'<section class="intro"><span class="eyebrow">RF CURRENT PROBE / {num}</span><h1>{title}</h1><p class="lead">{text}</p></section>'

def integrate(text,name,label):
    header='<header class="set-header"><a class="set-brand" href="index.html">RFCP<span>'+label+'</span></a><nav class="set-nav" aria-label="문서 세트">'+nav(name)+f'<a id="downloadHtml" href="{name}" download>HTML 저장</a></nav></header>'
    return re.sub(r'<header\b[^>]*>.*?</header>',lambda _:header,text,count=1,flags=re.S)

def file_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def sync_generated_tree(source,target,*,export_repository=None):
    """Resolve every path before pruning this explicitly named generated tree."""
    target=target.resolve()
    allowed=[(P/'dist').resolve(),Path('C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe').resolve()]
    if export_repository is not None:
        repository=Path(export_repository).resolve()
        assert (repository/'reports.json').is_file() and (repository/'assets/theme.v1.css').is_file()
        allowed.append((repository/'reports/rf-current-probe').resolve())
    assert target in allowed, f'Not an approved generated output directory: {target}'
    assert source.resolve()!=target and source.is_dir()
    target.mkdir(parents=True,exist_ok=True)
    wanted={f.relative_to(source).as_posix() for f in source.rglob('*') if f.is_file()}
    assert 'index.html' in wanted and 'assembly-guide.html' in wanted
    existing=list(target.rglob('*'))
    assert all(not f.is_symlink() and f.resolve().is_relative_to(target) for f in existing)
    if export_repository is None:
        for f in existing:
            if f.is_file() and f.relative_to(target).as_posix() not in wanted:f.unlink()
        for folder in sorted((f for f in existing if f.is_dir()),key=lambda f:len(f.parts),reverse=True):
            if not any(folder.iterdir()):folder.rmdir()
    for rel in sorted(wanted):
        dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/rel,dest)

def build():
    source_hashes={}
    with tempfile.TemporaryDirectory(prefix='.rfcp-showcase-',dir=P) as temporary:
        out=Path(temporary)
        assert out.resolve().parent==P.resolve()
        env=dict(os.environ,RFCP_BUILD_DIR=str(out),RFCP_SHOWCASE='1')
        for script in ['build_guide.py','build_current_assembly.py','build_showcase_compare.py']:
            subprocess.run([sys.executable,'-X','utf8',str(P/script)],cwd=P,env=env,check=True)
        for name,label in [('assembly.html','캘리브레이션 및 사용법'),('assembly-guide.html','조립절차서'),('compare.html','분할 구조 비교')]:
            f=out/name;f.write_text(integrate(f.read_text(encoding='utf-8'),name,label),encoding='utf-8')
        front=intro('DESIGN ATLAS','케이블을 감싸서 RF 전류를 보다','분할 코어와 수동 권선으로 케이블의 RF 합전류를 관측하는 프로브입니다. 앞뒤 클램프가 케이블을 지지합니다. 교정은 Fixture A03 평판 지그에서 출구로 나온 전류를 기준으로 합니다.')
        front+='<a href="assembly.html"><img src="cover-a14.png" alt="A14 분할 바닥 위 프로브와 앞뒤 케이블 클램프의 CAD 형상" style="display:block;width:100%;border-radius:12px;margin:20px 0"></a>'
        cards=[('01','manual.html','원리와 사용','어떤 전류를 측정하고, 어떻게 연결·교정하는지 읽습니다.'),('02','assembly-guide.html','46단계 조립절차','부품을 꺼내 보며 잡을 위치와 공구 방향을 확인합니다.'),('03','bom.html','부품 규격과 설계 파일','한 세트의 사용 수량·규격과 현행 STL·STEP·Gerber를 확인합니다.'),('04','assembly.html','전체 구조와 움직임','개폐·교정·분리·케이블 측정의 네 장면을 조작합니다.')]
        front+='<div class="grid">'+''.join(f'<a class="card" href="{url}"><div class="number">{n}</div><div><h2>{title}</h2><p>{copy}</p><span class="open">열기 →</span></div></a>' for n,url,title,copy in cards)+'</div>'
        front+='<div class="factbar"><span><b>기구</b> A14 / C07</span><span><b>출력물</b> 15종 · 20개</span><span><b>클램프 구경</b> 공칭6–26 mm</span><span><b>A03 보정</b> 1–500 MHz</span></div>'
        front+='<p class="scope-note">CAD 기반 시제품 설계입니다. 실물의 조립·유효 대역·정확도와 현장 보호 정격은 검증 전입니다.</p><div class="technical-links"><a href="https://ckh7488.github.io/showcase/reports/vna-calibration-fixture/">CM 프로브 교정지그 · A03 독립 문서 →</a><a href="compare.html">분할 구조의 변화 →</a><a href="design-review.html">A03 보정 원리와 수치 →</a></div>'
        (out/'index.html').write_text(frame('index.html','구조와 사용',front),encoding='utf-8')

        groups=list(dict.fromkeys(r['group'] for r in ROWS)); sections=[]
        for number,group in enumerate(groups):
            lines=[]
            for row in (r for r in ROWS if r['group']==group):
                links=[f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>' for label,url in row['links']]
                if row['file']:links.insert(0,f'<a href="files/{row["file"]}" download>STL</a>')
                quantity=(str(row['qty'])+' '+row['unit']) if row['qty'] is not None else row['unit']
                lines.append(f'<tr id="{row["id"]}"><td><b>{row["id"]}</b><br>{html.escape(row["name"])}</td><td>{html.escape(quantity)}</td><td>{html.escape(row["spec"])}</td><td>{html.escape(row["note"])}<div class="readmore">'+''.join(links)+'</div></td></tr>')
            sections.append(f'<section class="sheet" id="group-{number}"><h2>{group}</h2><div class="tablewrap"><table><thead><tr><th>부품</th><th>사용 수량</th><th>규격</th><th>역할·조립 참고</th></tr></thead><tbody>'+''.join(lines)+'</tbody></table></div></section>')
        bom=intro('03 / BILL OF MATERIALS','부품 규격과 설계 파일','프로브1개, 케이블 클램프2개, 공통 바닥과 Fixture A03 교정지그의 구성입니다.')
        bom+='<div class="split"><aside class="toc">'+''.join(f'<a href="#group-{i}">{g}</a>' for i,g in enumerate(groups))+'<a href="#downloads">설계 파일</a></aside><article>'+''.join(sections)
        bom+='''<section class="sheet" id="downloads"><h2>현재 설계 파일</h2><p>출력용 자유 형상 STL15종은 위 부품표의 링크를 사용합니다. 같은 클램프 부품을 앞뒤에 사용하므로 한 세트의 총 출력 수량은20개입니다. 현행 교정지그 Fixture A03의 제조자료는 이 공개 세트에 포함하지 않습니다.</p><div class="resource-list"><a href="assembly/RFCP_A14_Integrated_DRAFT.step" download>조립 STEP · A14/C07</a><a href="files/RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip" download>Gerber · Head A04</a><a href="files/READ_FIRST_NOT_FOR_FABRICATION.txt">파일 구성과 적용 범위</a></div><p class="subtle"><b>DRAFT — NOT FOR FABRICATION.</b> 시제품 설계 참고 자료입니다. STEP은 조립 배치용이며 출력 형상은 개별 STL을 사용합니다. 실제 부품·공정 조건과 실측 성능을 확인하기 전에는 검증된 제품 사양으로 취급하지 않습니다.</p></section></article></div>'''
        (out/'bom.html').write_text(frame('bom.html','부품 규격과 설계 파일',bom),encoding='utf-8')
        links=[('purpose','목적과 범위'),('parts','세트 구성'),('assembly','조립과 노브'),('calibration','실험실 교정'),('measurement','케이블 측정'),('check','검증 범위와 첫 시험'),('records','기록과 유지')]
        body=intro('01 / MANUAL','RFCP 설명서','측정 원리, 조립, 교정과 케이블 관측의 순서를 설명합니다.')+'<div class="split"><aside class="toc">'+''.join(f'<a href="#{i}">{label}</a>' for i,label in links)+'</aside><article>'+manual()+'</article></div>'
        (out/'manual.html').write_text(frame('manual.html','설명서',body),encoding='utf-8')
        build_analysis(out,frame)
        def copy(source,relative):
            target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            source_hashes[source.relative_to(R).as_posix()]=file_hash(source)
        for row in ROWS:
            if row['file']:copy(R/'mechanical/assembly_A14_DRAFT'/row['file'],'files/'+row['file'])
        for rel in ['hardware/probe_head_A04_DRAFT/RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip','reviews/a12_20260918/sources/SMO-3.pdf']:
            copy(R/rel,'files/'+Path(rel).name)
        source_hashes['mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.step']=file_hash(R/'mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.step')
        copy(S/'cover-a14.png','cover-a14.png')
        copy(P/'vendor/LICENSE-three.txt','vendor/LICENSE-three.txt')
        (out/'files/READ_FIRST_NOT_FOR_FABRICATION.txt').write_text('RFCP A14 / C07 — DESIGN REFERENCE\nDRAFT — NOT FOR FABRICATION\n\n출력 STL: 15종 / 한 세트20개. 파일별 수량은 bom.html 참조.\nSTEP: 조립 배치 참고용. 출력 형상은 개별 자유 형상 STL 사용.\nPCB: 공개 세트에는 Head A04 FR4 2층 제조자료만 포함.\n교정지그는 Fixture A03(2층)이며 제조자료는 이 공개 세트에 포함하지 않음.\nSMA 완성 홀: 중심1.70 / 접지1.90 mm. 수신기 쪽 단일50 Ω 종단.\n\nCAD와 SIMULATED 모델에 기반한 시제품 자료이며 실측 유효 대역·정확도·안전 정격을 보증하지 않음.\n실제 부품 치수와 제조 공정 조건을 확인하고 조립·특성화 절차를 적용할 것.\n설명: manual.html / 조립: assembly-guide.html / 해석: design-review.html\n',encoding='utf-8')
        for name,target,label in [('testing.html','manual.html#calibration','실험실 교정'),('split-review.html','compare.html','분할 구조 비교')]:
            page=frame(name,label,f'<section class="intro"><h1>{label}</h1><p><a href="{target}">현재 문서 열기 →</a></p></section>')
            (out/name).write_text(page.replace('</head>',f'<meta http-equiv="refresh" content="0;url={target}"></head>',1),encoding='utf-8')
        with zipfile.ZipFile(out/BUNDLE,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob('*')):
                if not f.is_file() or f.name==BUNDLE:continue
                name=f.relative_to(out).as_posix()
                if f.suffix=='.html':
                    page=re.sub(r'<a\b[^>]*href="'+BUNDLE+r'"[^>]*>.*?</a>','<span>오프라인 문서 세트</span>',f.read_text(encoding='utf-8'),flags=re.S)
                    z.writestr(name,page)
                else:z.write(f,name)
        from verify_showcase import verify
        validation=verify(out)
        manifest=dict(profile='PUBLIC_SHOWCASE_ALLOWLIST',files={f.relative_to(out).as_posix():file_hash(f) for f in sorted(out.rglob('*')) if f.is_file()},source_sha256=source_hashes,validation=validation)
        sync_generated_tree(out,D)
        (S/'showcase_bom.json').write_text(json.dumps(ROWS,ensure_ascii=False,indent=2),encoding='utf-8')
        (S/'showcase_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(validation,ensure_ascii=False))

if __name__=='__main__':build()
