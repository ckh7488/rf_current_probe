from pathlib import Path
import json,base64,html,shutil
P=Path(__file__).resolve().parent;R=P.parent;O=R/'reviews/functionality_20260918';D=P/'dist'
cards=json.loads((O/'comparison_content.json').read_text(encoding='utf-8'))
for c in cards:c['src']='data:image/png;base64,'+base64.b64encode((O/'images'/c['image']).read_bytes()).decode()
payload=json.dumps(cards,ensure_ascii=False).replace('</','<\\/')
buttons=''.join(f'<button data-card="{i}" aria-pressed="{str(i==0).lower()}">{i+1:02d} {html.escape(c["title"])}</button>' for i,c in enumerate(cards))
page='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RFCP · 수정 전후 비교</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f7;color:#173547;font:16px/1.65 system-ui,"Malgun Gothic",sans-serif}header{padding:16px 4vw;background:#142d3e;color:white;display:flex;gap:24px;justify-content:space-between;align-items:center}header a{color:#b8e7ee}header strong{font-size:21px}main{max-width:1400px;margin:auto;padding:22px}h1{font-size:27px;margin:0}p{margin:8px 0 16px}.intro{color:#536e7f}nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}button{font:inherit;font-size:14px;cursor:pointer;border:1px solid #bdd0dd;background:white;color:#21485b;border-radius:7px;padding:9px 13px}button[aria-pressed="true"]{background:#176d83;color:white;border-color:#176d83}button:focus-visible,a:focus-visible{outline:3px solid #d59938;outline-offset:3px}figure{margin:0;border:1px solid #cbdde7;background:#f2f6f8;border-radius:12px;overflow:hidden}figure img{display:block;width:100%;height:auto}.bar{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-top:1px solid #d4e1e7}.bar a{font-size:14px;color:#176d83}.note{font-size:14px;color:#557385}.findings{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px}.panel{background:white;border:1px solid #ccdce5;padding:20px;border-radius:10px}h2{font-size:20px;margin:0 0 12px}.big{font-size:28px;color:#086d82;font-weight:700}.panel p:last-child{margin-bottom:0}ul{padding-left:22px}.evidence{margin-top:22px;padding:18px;background:#e2edf3;border-radius:9px}.evidence a{color:#145b77;margin-right:18px}footer{padding:20px;color:#607987;font-size:13px}a{color:#166985}@media(max-width:700px){main{padding:14px}header{padding:14px;align-items:flex-start;flex-wrap:wrap}.findings{grid-template-columns:1fr}figure{overflow:auto}figure img{min-width:920px}.note{font-size:14px}nav button{flex:1 1 44%;text-align:left}h1{font-size:24px}}@media print{nav,.bar,header a{display:none}.findings{break-inside:avoid}main{max-width:none}}</style></head><body>
<header><strong>RFCP · 수정 전후</strong><a href="index.html">전체 3D · 개폐 · 교정 · 사용으로 돌아가기</a></header>
<main><p><a href="compare.html">현재 수정 전후 3D로 돌아가기 →</a></p><h1>어디가 약했고, 어떻게 고쳤나</h1><p class="intro">A09 / C03 → A10 / C04. 실제 CAD를 같은 위치에서 자른 단면입니다. 빈 곳은 홈이나 통로이고, 색칠한 곳은 플라스틱입니다.</p>
<nav aria-label="비교할 부위">BUTTONS</nav>
<figure><img id="comparison" alt="아래 턱 너트 홈 수정 전후"><div class="bar"><button id="previous">← 이전</button><span id="count" aria-live="polite">1 / 8</span><a id="download" download>그림 저장</a><button id="next">다음 →</button></div></figure>
<p class="note">휴대폰에서는 그림을 옆으로 밀어 볼 수 있습니다. 치수를 보여주는 단면이며, 실제 조립품 전체가 절단돼 있다는 뜻은 아닙니다.</p>
<div class="findings"><section class="panel"><h2>뚜껑의 긴 탄성부는 유지</h2><div class="big">2.4 mm · 계산 반력 5.29 N</div><p>얇아 보이던 연결부는 코어 높이 차이를 받아주는 부분입니다. A09에서 늘린 두께2.4 mm·길이63 mm를 유지하고, 이번에는 실제 형상으로 구조해석했습니다.</p><p class="note">두 메시의 반력 차이 약1.08%. 최대 응력은4.54–5.24 MPa로 메시 차이가 남아 있습니다. 가정한 나일론 재료와1.8 mm 변위의 선형 계산이며 실제 힘·수명 합격은 아닙니다.</p></section>
<section class="panel"><h2>검증한 것과 남은 것</h2><p><b>확인:</b> 공칭 개폐·분리233위치, 추가 나사·케이블 삽입423위치, 출력물10종의40,000점 두께 선별검사, 두 PCB 규칙 검사, 분석 코드110개 시험.</p><p><b>남음:</b> 실제 부품 조립, 출력 뒤틀림, 코어 맞댐·장기 유지력, 케이블 압착, RF 교정·보호 체인.</p><p class="note">설계상 문제를 수정한 검토본입니다. 실제 제작·내구성·측정 성능이100% 보장된 상태는 아닙니다.</p></section></div>
<section class="evidence"><b>검토 자료</b><p>큰 구조와 부품 수는 유지했습니다. 추가 재단 패드·별도 스프링·플라스틱 작동 나사산은 없습니다.</p><a href="index.html">수정된 전체 3D</a><a href="audit/README.md">전체 감사 기록</a><a href="audit/NEXT_CHECKS.md">실물 확인 순서</a><a href="assembly/A10_REVIEW_PACKAGE.zip">CAD와 출력 원본</a></section>
<footer>DRAFT — NOT FOR FABRICATION · 이 비교는 설계 변경의 설명이며 제조사 출력 승인이나 실측 성적서가 아닙니다.</footer></main>
<script>const cards=PAYLOAD;let current=0;const $=id=>document.getElementById(id);function show(i){current=(i+cards.length)%cards.length;const c=cards[current];$('comparison').src=c.src;$('comparison').alt=c.title+' 수정 전후: '+c.why.replaceAll('\\n',' ');$('count').textContent=(current+1)+' / '+cards.length;$('download').href=c.src;$('download').download=c.image;document.querySelectorAll('[data-card]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.card===current)));}document.querySelectorAll('[data-card]').forEach(b=>b.onclick=()=>show(+b.dataset.card));$('previous').onclick=()=>show(current-1);$('next').onclick=()=>show(current+1);show(0);</script></body></html>'''.replace('BUTTONS',buttons).replace('PAYLOAD',payload)
(D/'compare-history.html').write_text(page,encoding='utf-8')
out=D/'audit';out.mkdir(exist_ok=True)
for name in ['README.md','NEXT_CHECKS.md','audit_summary.json','use_paths.json','head_drc.json','fixture_drc.json','head_strict_erc.json','fixture_erc.json']:
 shutil.copyfile(O/name,out/name)
shutil.copyfile(O/'fem_A10/summary.json',out/'lid_fem_summary.json')
shutil.copyfile(O/'wall_scan_A10/summary.json',out/'wall_sampling_summary.json')
sources=P/'audit_sources';sources.mkdir(exist_ok=True)
for p in O.glob('*.py'):shutil.copyfile(p,sources/p.name)
for name in ['comparison_content.json','comparison_geometry.json','audit_summary.json','README.md','NEXT_CHECKS.md']:shutil.copyfile(O/name,sources/name)
shutil.copytree(O/'images',sources/'images',dirs_exist_ok=True)
# Provide the original linked project documents together; the short web page
# remains self-contained. Review Markdown is an explicitly downloadable source.
import zipfile,re
with zipfile.ZipFile(out/'review_documents.zip','w',zipfile.ZIP_DEFLATED) as z:
 for root in [O,R/'mechanical/assembly_A10_DRAFT',R/'mechanical/cable_clamp_C04_DRAFT']:
  for f in root.glob('*.md'):z.write(f,str(f.relative_to(R)))
 for f in (R/'docs').glob('*.md'):z.write(f,str(f.relative_to(R)))
 for f in (R/'docs').glob('*.csv'):z.write(f,str(f.relative_to(R)))
 for f in (O/'images').glob('*.png'):z.write(f,str(f.relative_to(R)))
# Publish readable HTML for the short next-check list, without an added runtime.
checks=(O/'NEXT_CHECKS.md').read_text(encoding='utf-8')
paras=''.join(('<h1>'+html.escape(line[2:])+'</h1>') if line.startswith('# ') else '<p>'+html.escape(line.replace('**',''))+'</p>' for line in checks.splitlines() if line.strip())
(out/'next-checks.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RFCP 실물 확인 순서</title><style>body{max-width:900px;margin:30px auto;padding:20px;font:17px/1.8 system-ui;color:#173547;background:#f4f7fa}p{margin:20px 0}a{color:#176d83}</style><a href="../compare.html">← 전후 비교</a>'+paras+'</html>',encoding='utf-8')
# Only expose working web links in downloaded Markdown; originals remain in ZIP.
md=(out/'README.md').read_text(encoding='utf-8')
md=re.sub(r'\]\((?!https?://)([^)]+)\)','](review_documents.zip)',md)
(out/'README.md').write_text(md,encoding='utf-8')
page=page.replace('href="audit/NEXT_CHECKS.md"','href="audit/next-checks.html"')
(D/'compare-history.html').write_text(page,encoding='utf-8')
print('Comparison page: 8 actual CAD pairs; embedded images; no external dependencies.')
