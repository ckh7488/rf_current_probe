"""Publish review prose and exact local evidence with the owned static Site."""
from pathlib import Path
import json,hashlib,html,shutil,zipfile
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=R/'viewer_A05'
A=R/'mechanical/assembly_A12_DRAFT';C=R/'mechanical/cable_clamp_C06_DRAFT'
a=json.loads((A/'build_report.json').read_text());c=json.loads((C/'verification.json').read_text())
assert a['pass'] and c['pass']
assert hashlib.sha256((A/'RFCP_A12_Integrated_DRAFT.FCStd').read_bytes()).hexdigest()==a['native_sha256']
css='body{max-width:1060px;margin:28px auto;padding:0 20px;font:16px/1.8 "Segoe UI","Malgun Gothic",sans-serif;color:#183b4d;background:#f3f7fa}h1{font-size:27px}h2{font-size:21px;margin-top:30px}a{color:#06758b}table{border-collapse:collapse;width:100%;background:#fff}th,td{text-align:left;border:1px solid #ccdce6;padding:12px;vertical-align:top}th{background:#e3eef4}small{font-size:14px}.box{padding:16px 20px;border-left:4px solid #0c8095;background:#e0eff4}.links{display:flex;gap:20px;flex-wrap:wrap}@media(max-width:650px){table,tbody,tr,td,th{display:block}thead{display:none}tr{margin-bottom:16px}td{border-bottom:0}td:last-child{border-bottom:1px solid #ccdce6}}'
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RFCP A12 / C06 · 너트 조립과 제작성</title><style>CSS</style>
<div class="links"><a href="../index.html">전체 3D</a><a href="../compare.html">수정 전후 3D</a></div>
<h1>너트를 쉽게 넣고, 열어도 잃어버리지 않게</h1><p>2026-09-18 · A12 / C06</p>
<p class="box"><b>너트의 체결 기능과 탈락 방지를 나눴습니다.</b><br>조이는 힘은 본체 받침면이 받고, 덮개는 풀린 너트가 떨어지는 것을 막습니다. 실제 출력물의 손조립·걸림 힘·수명·RF 시험은 아직 남아 있습니다.</p>
<h2>이번 변경</h2><table><thead><tr><th>부위</th><th>바꾼 내용</th><th>사용 방법</th></tr></thead><tbody>
<tr><td><a href="../compare.html?part=head_nut">프로브 개폐 너트</a></td><td>기존 사각 너트를 유지하고 바깥쪽 덮개 추가.</td><td>처음에 너트를 넣고 덮개를 장착. 뚜껑을 열고 닫을 때 너트를 다시 잡지 않음.</td></tr>
<tr><td><a href="../compare.html?part=bridge_nut">케이블 가로대 너트</a></td><td>가로대 손나사를 완전히 빼도 남아 있는 덮개.</td><td>연결된 선을 넣을 때는 기존의 손나사 두 개와 가로대만 제거.</td></tr>
<tr><td><a href="../compare.html?part=cal_nut">교정 PCB 받침</a></td><td>나일론 M3 날개 너트 4개와 회전 방지 받침. 작은 스패너를 창에 넣던 순서 제거.</td><td>너트를 먼저 설치하고 덮개를 닫은 뒤 PCB를 올려 위에서 나사를 조임.</td></tr>
<tr><td><a href="../compare.html?part=base_nut">바닥의 모듈 고정 너트</a></td><td>6개 너트를 한 장의 밑판으로 유지. 밑판 고정은 별도의 M4 두 곳.</td><td>처음에 뒤집어 조립. 이후 프로브·케이블 클램프를 분리해도 모듈용 너트는 남음.</td></tr>
<tr><td><a href="../compare.html?part=lead_nut">구경 노브 축</a></td><td>얇은 너트 두 개 대신 M6 풀림 방지 너트 한 개.</td><td>초도 조립 때 10 mm 스패너 하나로 잡고 노브를 돌림. 축이 회전할 틈은 유지.</td></tr>
</tbody></table>
<p>교정 받침 덮개는 헤드 장착 전에 설치·정비합니다. 앞 클램프 덮개 정비는 해당 모듈을 먼저 분리합니다. 평소 뚜껑·가로대 개폐에는 이 분해가 필요 없습니다.</p>
<h2>확인한 제작 조건</h2><p>원본 솔리드와 실제 STL, 조립·분리 경로, 너트 회전 및 탈락 경로, 새 덮개와 주변 부품, 책상면 돌출과 공구 접근을 확인했습니다. 검사 조건과 수치·입력 파일 식별 정보는 아래 검토 기록에 포함했습니다.</p>
<p>통합 개폐·탈착 233위치, 출력물 12종의 두께 표본48,000곳을 확인했습니다. 표본에서2 mm 미만은0곳이었습니다. 전체 조립체의 Ø12 mm 손끝 게이지 최소 간격은 약0.487 mm이며, 공칭 무간섭을 실제 손조작의 편안함으로 보장하지 않습니다.</p>
<p>검토 출력 재료는 <b>3301PA SLS 나일론</b>입니다. 새 유연팔은 조립 후 계속 휘어 있도록 만들지 않았습니다. 벽 두께와 걸림 여유를 계산했지만 실제 걸림 힘·수명은 시제품에서 확인해야 합니다. 다른 수지나 FDM으로 자동 대체하지 않습니다. <a href="https://jlc3dp.com/help/article/3301pa-nylon">제조사 재료 기준</a> · <a href="https://jlc3dp.com/help/article/3d-printing-design-guideline">출력 설계 지침</a></p>
<p>작은 덮개의 손조립부터 확인할 수 있도록 <a href="optional_fit_sample.zip">선택형 출력 샘플 2개</a>도 준비했습니다. 전체 조립품에 추가되는 필수 부품은 아닙니다.</p>
<h2>부품과 남은 조건</h2><p>출력물은 <b>PRINT_KINDS종 / PRINT_COUNT개</b>입니다. 같은 너트 덮개를 여러 곳에서 사용합니다. 전자 회로와 코어 권선 방식은 바꾸지 않았습니다.</p>
<p>M6 구동너트의 방향 전환 여유는 공칭1 mm를 유지합니다. 고정용 너트처럼 과조임으로 없애는 여유가 아닙니다. 코어 고정바·작은 헤드 PCB의 초도 체결에는 지정된 공구가 필요합니다.</p>
<p>실제 기성품 치수·출력물 수축과 뒤틀림·스냅 조작·코어 맞댐 반복성·케이블 압착·RF 성능은 아직 실물 검증 전입니다. 예전 구매서와 업체 제출 파일이 새 형상으로 자동 교체된 것은 아닙니다.</p>
<div class="links"><a href="../assembly/A12_REVIEW_PACKAGE.zip">원본 CAD·출력물·검사 기록</a><a href="latest_review_sources.zip">이번 검토 원문과 계산 기록</a></div><p><small>DRAFT — NOT FOR FABRICATION · CAD/계산 검토 · 실물·RF 측정 미실행</small></p></html>'''
page=page.replace('CSS',css).replace('PRINT_KINDS',str(a['printed_unique'])).replace('PRINT_COUNT',str(a['printed_total']))
(P/'latest_review.html').write_text(page,encoding='utf-8');out=P/'dist/audit';out.mkdir(exist_ok=True);(out/'latest-review.html').write_text(page,encoding='utf-8')
with zipfile.ZipFile(out/'latest_review_sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,R/'reviews/independent_a12_20260918',R/'reviews/a12_20260918',R/'reviews/c06_20260918']:
  if not folder.exists():continue
  for f in folder.rglob('*'):
   if f.is_file() and f.suffix in ['.md','.json','.py','.csv'] and f.name!='comparison_3d.json' and '__pycache__' not in f.parts:z.write(f,str(f.relative_to(R)))
 for folder in [A,C]:
  for f in folder.glob('*.json'):
   if f.name!='mesh.json':z.write(f,str(f.relative_to(R)))
with zipfile.ZipFile(out/'optional_fit_sample.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (O/'optional_fit_sample').glob('*'):
  if f.is_file():z.write(f,f.name)
src=P/'audit_sources/nut_access_20260918';src.mkdir(parents=True,exist_ok=True)
for f in O.glob('*'):
 if f.suffix in ['.md','.py']:shutil.copyfile(f,src/f.name)
print(json.dumps(dict(printed_unique=a['printed_unique'],printed_total=a['printed_total'],page_bytes=len(page.encode()))))
