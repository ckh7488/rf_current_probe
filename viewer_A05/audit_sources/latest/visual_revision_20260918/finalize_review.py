"""Bind the review page, documents and downloadable evidence to final CAD."""
from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=R/'viewer_A05';C=R/'mechanical/assembly_A11_DRAFT'
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=sha(C/'RFCP_A11_Integrated_DRAFT.FCStd')
for name in ['build_report.json','verification.json','retention_mount_verification.json']:
 j=read(C/name);assert j['pass'] and j['native_sha256']==h,name
t=read(R/'reviews/a11_20260918/targeted.json');assert t['pass'] and t['native_sha256']==h
tools=read(R/'reviews/independent_a11_20260918/operation_tools.json')['revisions']['A11'];assert tools['native_sha256']==h and tools['failed_cases']==0
spanner=read(R/'reviews/independent_a11_20260918/calibration_spanner.json');assert spanner['pass'] and spanner['native_sha256']==h
prints=read(R/'reviews/a11_print_20260918/manifest.json');assert prints['pass_saved_mesh_and_identity'] and prints['new_sampling_below_1p5mm_total']==0
for rel,hashval in read(O/'comparison_3d.json')['sources'].items():assert sha(R/rel)==hashval,rel
report={'classification':'CALCULATED_CAD_AND_SITE_REVIEW_NOT_FABRICATION_APPROVAL','native_sha256':h,'revision':'A11/C05','comparisons':14,'printed_unique':10,'printed_total':15,'scoped_checks_pass':True,'physical_or_RF_measurements':False}
(O/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
md='''# A11 / C05 再검토와 3D 문서 갱신

2026-09-18 · **DRAFT — NOT FOR FABRICATION**

## 완료

기존 조립 문제를 CAD와 출력물에 반영하고, 기존 문서의 4개 장면(구조·개폐 / 실험실 교정 / 지그·분리 / 케이블 측정)을 최신 조립체로 갱신했다. 전후 비교는 이전8곳 + 이번6곳을 실제 CAD로 회전·확대·변경 부분 강조할 수 있게 했다.

| 이번 변경 | 결과 |
|---|---|
| 바닥 M4 나사6개 | 25→20 mm, 너트 안착. 공칭 바닥 안쪽1/2 mm |
| 코어 고정바 | SMA·S+/S− 접근을 위해 가로대 이동. 코어 접촉부 유지 |
| 뚜껑 정렬 | 왼쪽 L형 기준에 손으로 가볍게 맞대고 조임. 자동 정밀 정렬은 아님 |
| 교정 PCB 너트 | 바깥 X 방향 공구 창. 얇은5.5 mm 스패너로 잡고 체결 |
| C05 구동너트 | 포켓6.8→6.0 mm, 공칭 여유1.8→1.0 mm. 무유격 아님 |
| 권선 출구 | 이전 절삭에서 남은0.15 mm 깊이의 작은 조각 제거. 뒤 벽2.5 mm 유지 |

닫힘 상태를 표현하는 뚜껑 CAD의 면 연결 오류도 수정했다. **출력용 자유 뚜껑은 기존과 같은 형상**이다. 기존 약5.29 N 선형 FEA는 당시 재료·지지조건에서의 결과이며 새 기준면 접촉·출력물 수명 검증이 아니다. 비교에서 뚜껑이 포함된 두 부위는 양쪽 모두 유효한 FREE 출력 형상으로 대조했다.

## 실제 검증

- 새 원본의73객체 형상 유효성·정적 간섭,233자세 개폐/탈착,24개 코어 ADC 민감도,코어 접촉/이탈·체결 공간.
- 독립 검사: SMA·테이퍼 인두·드라이버15조건, 바깥 방향 스패너368자세.
- 뚜껑 수동 배치41자세·나사/너트 위치 여유9자세, 자유 뚜껑 형상 동일성.
- 출력10종/15개: 폐곡면·양의 부피·원본 해시;40,000개 두께 표본에서1.5 mm 미만0. 표본 검사는 전면 최소 두께나 업체 DFM 승인과 다르다.
- Site의 새 CAD 포함·동작 그룹·내부 링크·문법 및 브라우저 표시/조작은 별도 검증 기록으로 남긴다.

## 미검증/다음

정확한 구매 체결품·공구·출력 재료/공차 대조,시제품의 무가공 조립·마찰·닫힘 반복성·내구성,RF 교정·삽입 영향·보호 체인이 남는다. PCB 전기 설계는 바꾸지 않았고 이전 규칙검사/거버 대조를 유지했다. 업체 제출·구매·이전 장바구니는 갱신하지 않았다. 기존 구매서를 현재 제작 승인본으로 사용하지 않는다.

근거: [A11](../a11_20260918/README.md), [독립 검사](../independent_a11_20260918/README.md), [출력 검사](../a11_print_20260918/README.md), [C05](../c05_20260918/README.md), [원본](../../mechanical/assembly_A11_DRAFT/README.md).
'''
(O/'README.md').write_text(md,encoding='utf-8')
def prepend_after_title(path,marker,text):
 s=path.read_text(encoding='utf-8')
 if marker in s:return
 i=s.index('\n');path.write_text(s[:i+1]+'\n'+text+'\n\n'+s[i+1:],encoding='utf-8')
prepend_after_title(R/'docs/STATUS.md','A11/C05 3D 통합 갱신','> **2026-09-18 A11/C05 3D 통합 갱신 — 현재 설계 검토본.** 바닥 나사·SMA/납땜 접근·뚜껑 수동 위치 기준·교정 PCB 너트 공구 창·구동너트 여유·권선 출구 잔여 조각을 수정했다. [이번 검토와14곳3D 비교](../reviews/visual_revision_20260918/README.md), [최신 원본](../mechanical/assembly_A11_DRAFT/README.md). 원본/출력물/문서를 동기화했다. 이전 표기는 이력이다. 실물·RF·최종 구매품/출력 공차 미검증으로 DRAFT 유지. 업체 주문은 변경하지 않았다.')
prepend_after_title(R/'docs/BOM_DRAFT.md','A11/C05 현재 변경','> **2026-09-18 A11/C05 현재 변경:** 바닥 M4×20 나사6개, 출력10종/15개. 고정바·아래 몸체·공통 바닥·C05 연결틀은 최신 STL을 사용한다. M3 나일론 너트를 잡을 얇은5.5 mm 스패너(검토 외형≤두께3 mm/머리Ø14 mm/중심부터길이55 mm)가 필요하다. 보유 공구 대조 전 구매 확정품으로 세지 않는다. [최신 제작 검토](../reviews/visual_revision_20260918/README.md). 아래 옛 카트/가격은 현재 전체 구매 BOM이 아니며, 정확한 품번·재료/공차 확정은 남아 있다.')
dec=R/'docs/DECISIONS.md';s=dec.read_text(encoding='utf-8')
if 'DEC-045' not in s:dec.write_text(s+'\n\n## DEC-045 — A11/C05 실제 형상과 문서 동기화 (2026-09-18)\n\n바닥 나사20mm·고정바 접근·L형 수동 기준·교정 너트 바깥쪽 공구 창·구동너트1mm공칭여유·권선 출구 작은 잔여 조각 제거를 반영했다. 닫힘 표시CAD의 곡선/면 연결도 수정했다. 자유 뚜껑은 동일하며 이전FEA 범위를 확장하지 않는다. 14곳 실제CAD 3D비교와 원본4장면 문서를 최신파일로 갱신한다. [검토 근거](../reviews/visual_revision_20260918/README.md). 실물/RF/최종부품선정 미완료,DRAFT,구매나업체제출 변경없음.\n',encoding='utf-8')
audit=P/'dist/audit';audit.mkdir(exist_ok=True)
shutil.copyfile(P/'latest_review.html',audit/'latest-review.html')
with zipfile.ZipFile(audit/'latest_review_sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for d in [O,R/'reviews/a11_20260918',R/'reviews/independent_a11_20260918',R/'reviews/a11_print_20260918',R/'reviews/c05_20260918']:
  for p in d.rglob('*'):
   if p.is_file() and p.suffix in ['.md','.json','.py','.csv'] and p.name!='comparison_3d.json' and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for p in [R/'docs/STATUS.md',R/'docs/BOM_DRAFT.md',R/'docs/DECISIONS.md']:z.write(p,str(p.relative_to(R)))
dest=P/'audit_sources/latest';dest.mkdir(exist_ok=True)
for d in [O,R/'reviews/a11_20260918',R/'reviews/independent_a11_20260918',R/'reviews/a11_print_20260918',R/'reviews/c05_20260918']:
 for p in d.glob('*'):
  if p.is_file() and p.suffix in ['.md','.json','.py','.csv'] and p.name!='comparison_3d.json':
   q=dest/d.name/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
print(json.dumps(report))
