from pathlib import Path
import json,re,html
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=R/'viewer_A05'
read=lambda p:p.read_text(encoding='utf-8')
write=lambda p,s:p.write_text(s,encoding='utf-8')
# The wall audit has no dependency on the deleted nut-cap system.
p=O/'check_prints.py';s=read(p).replace(",R/'mechanical/common_nut_cap.py'",'');write(p,s)
write(O/'check_lead_access.py',read(R/'reviews/c06_20260918/check_lead_access.py').replace('C06','C07'))
s=read(R/'reviews/nut_access_20260918/check_site_artifacts.py').replace('A12','A13').replace('C06','C07')
s=s.replace('(12,26)','(10,15)').replace("data['printCount']==7","data['printCount']==5").replace("len(data['cases'])==20","len(data['cases'])==24").replace('comparison_cases=20','comparison_cases=24').replace("'mechanical/common_nut_cap.py',",'')
write(O/'check_site_artifacts.py',s)
current='''> **2026-09-18 A13/C07 — 분실방지 추가 부품 제거.** 사용자 요청에 따라 덮개10개·받이·바닥 노란 유지판 및 판 고정 체결품2쌍을 제거했다. 기존 얇은 벽 보강과 작동 구조를 유지하고 출력은 **10종15개**로 복구했다. [현재 조립·변경 범위](../reviews/simplification_20260918/README.md), [현재 CAD](../mechanical/assembly_A13_DRAFT/README.md). 나사를 완전히 빼면 너트를 직접 챙긴다. A12/C06은 폐기한 추가 구조의 이력이며 현재 제작 대상이 아니다. 실제 출력·조립·RF·일부 최종 기성품 선정은 여전히 미완료다.

'''
p=R/'docs/STATUS.md';s=read(p);s=s.replace('\n\n','\n\n'+current,1);write(p,s)
p=R/'docs/DECISIONS.md';write(p,read(p)+'''\n\n## DEC-047 — A13/C07 분실방지 기능 철회, 단순 조립 우선 (2026-09-18)

사용자가 요구한 것은 쉬운 너트 삽입과 공구 접근이다. 별도 분실방지 요구를 추론하지 않는다. DEC-046의 공용 덮개10개, 긴 받이, 바닥 유지판1개 및 그 고정 체결품2쌍을 제거한다. 나사를 뺀 상태에서 너트가 빠지는 것을 허용한다. 나일론 날개너트와 작동축 M6 잠금너트는 유지한다. 기존 얇은 벽 보강과 권선 접근, 코어 고정은 유지했다.

10종15개 출력. 기존 A12/C06은 이력으로 보존하되 구매 대상에서 제외한다. 이번 검증은 저장 CAD/출력파일/공칭 경로에 한정하며 실물 조립이나 RF 합격을 의미하지 않는다. [변경·검증 기록](../reviews/simplification_20260918/README.md).
''')
page='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RFCP · 분실방지 부품 제거</title><style>body{margin:0;background:#edf3f7;color:#173244;font:16px/1.7 system-ui,sans-serif}main{max-width:920px;margin:auto;padding:32px 24px}a{color:#007c93}section{background:white;border:1px solid #ccdce6;border-radius:12px;padding:24px;margin:20px 0}h1,h2{line-height:1.35}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #dde6ed}.note{color:#805727}</style></head><body><main><a href="../index.html">전체 3D</a> · <a href="../compare.html">수정 전후 3D</a><h1>덮개와 바닥 노란 판을 없앴습니다</h1><p>현재 형상 A13 / C07 · DRAFT — NOT FOR FABRICATION</p><section><h2>26개에서 15개로</h2><table><tr><th>제거</th><th>수량</th></tr><tr><td>프로브·교정 PCB·케이블 클램프 너트 덮개</td><td>10개</td></tr><tr><td>바닥 노란 너트 유지판</td><td>1개</td></tr><tr><td>유지판만 고정하던 나사·너트</td><td>2쌍</td></tr></table><p>덮개를 끼우던 긴 받이도 없앴습니다. 출력물은 10종15개입니다. 나사를 완전히 빼면 너트는 직접 챙깁니다.</p></section><section><h2>남긴 구조</h2><p>코어 고정대, 탄성 뚜껑, 얇은 벽 보강, 권선·납땜 공간, 세 턱의 연동을 유지했습니다. 사각너트는 기존 열린 홈으로 넣습니다. 교정 PCB의 날개너트는 열린 받침에 놓고 위에서 조입니다. 바닥은 뒤집어 너트를 잡고 체결합니다.</p><p>M6 축의 잠금너트와 와셔는 축의 위치를 조절하는 작동 부품이므로 유지합니다.</p></section><section><h2>확인한 범위</h2><ul><li>공칭 조립·개폐·탈착 경로와 코어 고정 검사를 통과했습니다.</li><li>헤드4종·클램프5종은 보강된 이전 형상과 동일함을 CAD로 확인했습니다.</li><li>너트 삽입234위치에서 겹침0. 실제 손·공구 전체의 사용성을 보증하는 시험은 아닙니다.</li><li>STL10종 폐곡면과 출력 수량을 확인했습니다. 표면4만지점의 두께 표본검사에서1.5mm 미만 표본은 없었습니다. 전체 최소벽 인증은 아닙니다.</li></ul><p class="note">실제 출력·손조립·마찰·내구성·RF 시험과 일부 최종 기성품 선정은 남아 있습니다. 이번 수정으로 발주 승인이 완료된 것은 아닙니다.</p></section><p><a href="../assembly/A13_REVIEW_PACKAGE.zip">현재 원본·출력물·검토 기록</a></p></main></body></html>'''
write(P/'latest_review.html',page);write(P/'dist/audit/latest-review.html',page)
print('Current revision and review page updated.')
