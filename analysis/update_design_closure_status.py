"""Update local status after final report; preserve published and order history."""
from pathlib import Path
import json,csv,io
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
assert (B/'README.md').exists() and (B/'comparison.json').exists()
summary='제작 전 두 항목 검토를 마쳤습니다. 1–100 MHz 우선 검증용 첫 시제품의 기구 외형을 유지하고, SMA 홀을 보완한 헤드 A04·교정 PCB A03 검토본을 작성했습니다. 새 PCB는 JLC 미제출이며 출력물15종·20개는 동일합니다. 실측 정밀도와 제조·조달·현장 보호 조건은 아직 확정되지 않았습니다.'
finding='무코어 전체 PCB 모델에서 연결·수동성 선별·양방향 전달·유한 시간창과 추가 격자/영역/재료/런치 비교를 수행했습니다. 1–100 MHz 중앙 전류의 격자·영역·유전율·런치 변경 비교는 각각 복소 차1% 이내였습니다. 양방향 중앙 전류 차이는 비대칭 구조와 함께 별도로 검토했습니다. 100 MHz의 S11≤−20 dB 목표는 미달이며100–300 MHz 이상에서 민감도가 커집니다. 전역 에너지−50 dB 수렴과 실제 SMA 기준면·코어 부하·실측 정밀도는 미검증입니다.'
next_step='첫 시제품의 기존 외곽·창·장착홀·높이와 BaseCenter는 유지합니다. 두 SMA의 홀만 확대한 A03 검토본을 사용하며 새 PCB 제조조건 확인과 업체 심사가 필요합니다. 입고 후 실제 교정 기준면에서 빈 지그/헤드 장착 S2P, 선형성·5회 재장착·직접 픽업을 확인합니다. 시뮬레이션 HI를 실물 교정값으로 자동 적용하지 않습니다.'
p=R/'docs/CURRENT_READINESS.md';s=p.read_text(encoding='utf-8')
start=s.index('\n\n',s.index('전체 세트의 일괄 제작 준비'))+2;end=s.index('## G-PRINT')
s=s[:start]+summary+'\n\n## G-CAL · 교정 PCB A03\n\n**첫 시제품 외형 유지 판정 · RF 교정 승인 전** — 제작 전 모델 검토 완료, 실물 성능 확인 필요\n\n'+finding+'\n\n다음: '+next_step+' [검토 결과와 실제 실행](../reviews/design_closure_20260921/README.md), [첫 실물 인수 절차](../reviews/design_closure_20260921/BENCH_ACCEPTANCE.md).\n\n'+s[end:]
p.write_text(s,encoding='utf-8')
p=R/'viewer_A05/set_sources/readiness.json';j=json.loads(p.read_text(encoding='utf-8'));j['summary']=summary;j['local_update_not_published']='2026-09-21 design_closure; Sites/ATLAS and JLC order remain previous publication/submission history.'
g=next(x for x in j['gates'] if x['id']=='G-CAL');g.update(name='교정 PCB A03',phase='첫 시제품 외형 유지 · RF 교정 승인 전',status='제작 전 모델 검토 완료 / 실물 성능 미검증',finding=finding,next=next_step,local_evidence='reviews/design_closure_20260921/README.md')
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=R/'docs/STATUS.md';s=p.read_text(encoding='utf-8');i=s.index('\n')+1
entry='\n> **2026-09-21 제작 전 두 항목 검토 완료:** 기존 기구 외형을1–100 MHz 우선 검증용 첫 시제품에 유지한다. SMA 공차 여유 보완으로 헤드 A04·교정 PCB A03의 중심홀1.70/접지홀1.90 mm 검토본 작성; 두 PCB ERC/DRC/미연결/회로일치 위반 각0, Gerber/드릴/ZIP 대조 통과. 외곽·창·장착홀·배선·STL15종은 보존했다. 새 FDTD6개 및 이전2개 재분석으로 시간창·양방향·격자/영역·재료·런치 민감도를 기록했다. 전역−50 dB 수렴, 실제 SMA/코어 포함 정밀도,300 MHz 성능은 미검증이다. 헤드 PCB 파일 교체·재심사는 필요하나 이번3D 재제출 근거는 없다. 새 JLC 제출·결제 및 공개 사이트 갱신 없음. [결과·원본·한계](../reviews/design_closure_20260921/README.md), [현행 상태](CURRENT_READINESS.md).\n'
if entry.strip() not in s:p.write_text(s[:i]+entry+s[i:],encoding='utf-8')
p=R/'docs/DECISIONS.md';s=p.read_text(encoding='utf-8')
entry='''

## 2026-09-21 · 제작 전 지그 외형 유지와 SMA 홀 보완

첫 시제품의1–100 MHz 우선 검증은 기존 A14/C07 외형·교정 PCB 외곽/창/고정홀/높이를 유지한다. GCT Rev1.2와 JLC 일반 PTH 공차를 함께 계산해 중심 SMA 홀1.50→1.70 mm, 접지홀1.70→1.90 mm로 보완하고 헤드 A04·교정 PCB A03 검토본을 별도로 작성했다. 핀 휨·진위치·납땜 접합·실제5핀 맞춤은 첫 실물의 인수 조건이다. 기존 제조파일과 STL15종은 보존했다. 헤드 A03 업체 승인은 A04에 승계하지 않으며, 새 PCB 파일 교체/심사와3D 출력물 재제출을 구분한다.

6개 새 무코어 FDTD와 이전2개 비교에서1–100 MHz 중앙 전류의 수치/재료/런치 민감도를 확인했다. dual mesh 관측면이 요청 중앙과 어긋난 점을 소스로 확인하고 실제 y=0 공간 보간과 오차 비교를 추가했다. 원래 결과를 덮어쓰지 않는다. 양방향 중앙 전류의 차이는 비대칭 창/귀환부와 함께 검토하고, 상호성은 S21/S12로 판단한다. 관측량 안정성을 확인해 정상 정리 중지했지만 전역 에너지−50 dB 수렴으로 기록하지 않는다.

100 MHz에서 정합−20 dB 목표 미달,300 MHz 이상에서 수치/재료 민감도가 남으므로 실물에50×S21/1−S11 또는 모델 HI를 자동 적용하지 않는다. 이번 완료는 제작 전 두 항목의 설계 검토이며 센서 성능·현장 사용·전체 제작 승인 완료가 아니다. 공개 사이트/업체 주문은 이전 상태를 보존한다. 근거와 원시 출력은 `reviews/design_closure_20260921/README.md`, 후속 연결·설정·저장 파일은 `BENCH_ACCEPTANCE.md`를 따른다.
'''
if '## 2026-09-21 · 제작 전 지그 외형 유지와 SMA 홀 보완' not in s:p.write_text(s+entry,encoding='utf-8')
p=R/'docs/REQUIREMENTS.csv';s=p.read_text(encoding='utf-8-sig');rows=list(csv.DictReader(io.StringIO(s)));cols=list(rows[0])
for row in rows:
    if row['id'] in ['CAL-01','CAL-02','CAL-03','CAL-04','HW-02','DATA-01','DATA-02']:
        evidence='reviews/design_closure_20260921/README.md; CALCULATED/SIMULATED only; physical validation pending'
        if evidence not in row['evidence']:row['evidence']=(row['evidence']+'; '+evidence).strip('; ')
        row['verification_status']='PARTIAL'
o=io.StringIO(newline='');w=csv.DictWriter(o,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows);p.write_text(o.getvalue(),encoding='utf-8')
p=R/'README.md';s=p.read_text(encoding='utf-8');i=s.index('\n')+1
entry='\n> **2026-09-21 최신 제작 전 검토:** 기구 A14/C07의 외형을 유지하며 SMA 홀을 보완한 헤드 A04·교정 PCB A03 검토본을 작성했다. [두 항목의 결과·제조파일](reviews/design_closure_20260921/README.md)와 [현재 준비 상태](docs/CURRENT_READINESS.md)를 먼저 본다. 실측 정밀도/제작 승인은 미완료이며 새 PCB는 JLC 미제출이다. 아래 구매/제출 내용은 각 날짜의 이력이다.\n'
if entry.strip() not in s:p.write_text(s[:i]+entry+s[i:],encoding='utf-8')
p=R/'hardware/calibration_fixture_PCB_A03_DRAFT/README.md';s=p.read_text(encoding='utf-8');s=s.replace('최종 해석 판정 전 발주 보류이며, `50×S21`을 자동 승인하지 않는다.','[추가 해석 판정](../../reviews/design_closure_20260921/README.md)은1–100 MHz 우선 검증용 첫 시제품의 외형 유지다. 실물 교정·업체 제조조건·제작 승인은 남아 있으며, `50×S21`을 자동 승인하지 않는다.');p.write_text(s,encoding='utf-8')
print('Local status/history/evidence updated. No website deployment or order update.')
