"""Write the review only after all frozen final results exist and pass stated screens."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
d=json.loads((B/'comparison.json').read_text());assert not d['partial'] and len(d['runs'])==8
run={v['name']:v for v in d['runs']};comparisons={v['name']:v for v in d['comparisons']}
for n in ['combined_numerics','epsilon','launch','source_and_window','new_holes_and_local_mesh']:
    assert comparisons[n]['bands'][0]['HI_complex_delta_percent']<1,(n,'manual review required')
for name,v in run.items():
    if not v['new_execution']:continue
    sd=json.loads((B/'em'/name/'stop_decision.json').read_text())
    assert sd['last_common_ns']>=12
    assert all(x['hi_complex_relative_max']<=.0005 and x['s_ref_abs_max']<=.0005 and x['s_thru_abs_max']<=.0005 for x in sd['changes'])
    assert v['max_power_fraction']<=1.03 and v['max_nested_percent_1_100']<1
    assert v['samples'][0]['f_Hz']==1e6 and abs(v['samples'][0]['I_over_matched_mag']-1)<.02
    pec=json.loads((B/'em'/name/'pec_connectivity.json').read_text())['connections']
    assert pec=={'signal_thru':True,'return_thru':True,'input_short':False,'output_short':False,'centre_signal':True}
lines=['# 제작 전 두 항목 검토 결과','',
'2026-09-21 · **DRAFT — NOT FOR FABRICATION** · 계산/시뮬레이션 완료, 실측·업체 재심사·제작 승인 없음.','',
'**판정: 1–100 MHz 우선 검증용 첫 시제품은 기존 기구 외형을 유지한다. SMA 홀은 보완한 헤드 A04·교정 PCB A03 검토본을 사용한다. 이번 결과로 A14/C07 출력물을 다시 수정하거나 제출할 근거는 없다.**','',
'이 판정은 첫 시제품의 제작 전 설계 검토다. 이더넷 케이블의 RF 합전류/공통모드 잡음을 얼마나 정밀하게 측정하는지는 실제 코어·권선·케이블·교정·반복성 시험 후 결정한다. 100–300 MHz 정량 성능과500 MHz 확장 목표는 미확보다. 실물 문제에 따른 향후 변경 가능성이 없다고 보증하지 않는다.','',
'## 1. 형상과 JLC에 미치는 영향','',
'| 대상 | 이번 결과 | 업체 파일 작업 |','|---|---|---|',
'| A14/C07 출력물 | 15종·20개 모두 유지; 보존 STL15종의 SHA256 동일 | 이번 검토로 인한 재제출 없음 |',
'| 헤드 PCB | A03→A04; SMA 중심홀1.50→1.70, 접지4홀1.70→1.90 mm | 채택 시 기존 헤드 PCB 파일 교체·재심사 필요 |',
'| 교정 PCB | A02→A03; 두 SMA에 같은 홀 확대 | 기존 A02는 미접수였으므로 새 A03 검토 접수 대상 |','',
'두 PCB의 외곽·두께·창·고정홀·SMA 위치·패드 외경·배선·비아를 보존했다. 기존 조립 CAD는 이전 홀을 표시하므로 정확한 새 제조 원본은 아래 KiCad 파일이다. 기구 외형/장착 검사의 재사용과 새 PCB 제조 원본을 구별한다. 기존 JLC의 파일 승인은 새 PCB로 승계되지 않는다. 새 업로드·주문 변경·결제·위험 수락은 실행하지 않았다.','',
'- [헤드 A04 원본·제조 검토 ZIP](../../hardware/probe_head_A04_DRAFT/README.md)','- [교정 PCB A03 원본·제조 검토 ZIP](../../hardware/calibration_fixture_PCB_A03_DRAFT/README.md)','- [업체 인계 범위·CAM 문구](MANUFACTURING_HANDOFF.md)','',
'## 2. SMA 공차','',
'GCT Rev1.2의 핀 치수와 JLC 일반 PTH 크기/위치 공차를 함께 적용했다. 기존 홀은 보수적인 동시삽입 치수 범위에서 여유가 음수였다. 새 홀의 계산 여유는 중심핀 반경 약0.054 mm, 접지핀 모서리 약0.061 mm다. 도면의 대칭·중심핀 정렬을 가정한 계산이며 공급자의 핀 휨/진위치 보증이 아니다. 제조사 권장 레이아웃보다 넓혔으므로 첫 부품의5핀 무가압 삽입·평면 안착과 최대 완성홀에서의 납땜 충전/지지 상태가 인수 조건이다.','',
'두 PCB의 ERC·DRC·미연결·회로 일치 위반은 각각0이며, 검사 비활성 항목도0이다. 제조 ZIP을 다시 열어 Gerber/드릴 파일과 바이트 일치를 확인했다. [계산 원본](sma/fit_result.json), [그림](sma/fit_envelopes.png), [저장 PCB/제조파일 검증](pcb_verification.json), [제조사·JLC 근거 및 가정](SOURCES_AND_ASSUMPTIONS.md).','',
'## 3. 빈 교정지그 시뮬레이션','',
'새 FDTD 실행6개와 보존한 이전 실행2개를 비교했다. 모든 새 실행에서 이산화된 신호/귀환 경로가 각각 연결되고 서로 단락되지 않음을 확인했다. 포트는 실제 SMA 체결면이 아닌 가정한 커넥터 내부이며 코어·권선·케이블·실제 손실은 포함하지 않는다. 따라서 아래 값은 센서 정밀도나 실물 교정값이 아니다.','',
'### 시간창과 종료','',
'전역 에너지−50 dB 기준은 달성하지 못했다. 새 실행은12 ns 이상 계산 후, 연속 두 번의1 ns 확장에서1–500 MHz 중앙 전류 복소 변화≤0.05% 및 복소 S 변화≤0.0005를 확인하고 openEMS의 정상 정리 중지 기능을 사용했다. 기준과 중지 이유는 각 `stop_decision.json`에 보존했다. 이는 관측량의 유한 시간창 안정성이며 완전한 필드·공간 수렴이 아니다.','',
'| 실행 | 원시 공통 시간(ns) | 최종 DFT 창(ns) | 마지막 기록 에너지(dB) | 마지막1 ns 전류 변화,1–100 MHz(%) |','|---|---:|---:|---:|---:|']
for name,v in run.items():
    lines.append(f"| {name} | {v['last_common_ns']:.3f} | {v['DFT_end_ns']:.1f} | {v['energy_db']:.2f} | {v['time_window_changes'][-1]['bands']['1_100_MHz']['hi_complex_relative_percent']:.5f} |")
lines+=['','앞의 `reference_1g_*` 두 행은 이전 실행을 복사해 같은 좌표/부호 후처리로 재분석한 것이며 새 실행 수에 포함하지 않는다.','',
'### 설정 변화에 대한 중앙 전류의 복소 상대차','',
'| 비교 | 1–100 MHz(%) | 100–300 MHz(%) | 300–500 MHz(%) |','|---|---:|---:|---:|']
labels={'old_local_mesh':'이전 국소 격자0.20/0.25 mm','source_and_window':'소스1 GHz/600 MHz 및 시간창','holes_and_source':'동일 격자, 새 홀 + 소스/시간창','new_holes_and_local_mesh':'동일600 MHz, 새 홀 + 국소 격자','combined_numerics':'새 PCB의 XY/Z 격자·영역 복합 변경','epsilon':'유전율4.3→4.5','launch':'동일ε4.5에서 런치 높이·내경 변경','direction':'앞/뒤 급전; 물리 전류 부호 정렬'}
for name,c in comparisons.items():
    lines.append('| '+labels[name]+' | '+' | '.join(f"{v['HI_complex_delta_percent']:.4f}" for v in c['bands'])+' |')
lines+=['','이 값들은 시험한 사례 간 차이이며 독립적인 오차 상한이 아니다. XY/Z/영역을 함께 바꾼 경우에는 각각의 효과를 분리하지 않았다. 실제 재료·SMA 내부의 전체 공차 범위를 포괄하지도 않는다. 특히300 MHz 이상의 수치/재료 민감도가 커서 그 구간의 정밀 교정은 승인하지 않는다.','',
f"양방향 복소 S21/S12 차이는1–100 MHz 최대 {comparisons['direction']['bands'][0]['S_through_complex_abs_delta']:.6g}, 1–500 MHz 최대 {max(v['S_through_complex_abs_delta'] for v in comparisons['direction']['bands']):.6g}다. 중앙 전류의 방향별 차이는 별도로 남겼다. 창의 범위−16.10..+17.65 mm와 귀환부가 완전한 앞뒤 대칭이 아니므로 중앙 전류가 동일해야 한다는 조건을 적용하지 않는다. 비대칭만으로 전체 차이의 원인을 엄밀히 분리했다는 뜻은 아니며, 교정할 때 IN/OUT 방향을 고정한다.",'',
'### 대표값 — 새 홀 기준 모델','',
'| MHz | S11(dB) | S21(dB) | 중앙 전류 크기 / (입사전압 크기/50 Ω) | 중앙 전류 위상(°) |','|---|---:|---:|---:|---:|']
for v in run['revised_holes_600']['samples']:
    lines.append(f"| {v['f_Hz']/1e6:g} | {v['S_ref_dB']:.3f} | {v['S_thru_dB']:.3f} | {v['I_over_matched_mag']:.6f} | {v['I_over_matched_phase_deg']:.3f} |")
vals=[next(v for v in run[n]['samples'] if v['f_Hz']==1e8)['S_ref_dB'] for n in ['revised_holes_600','revised_numeric_corner','revised_epsilon45','revised_material_launch_corner']]
lines+=['',f"100 MHz의 S11은 비교한 새 PCB 모델에서 {min(vals):.2f}..{max(vals):.2f} dB로, 목표−20 dB를 충족하지 않는다. 1–100 MHz 중앙 전류 크기가 입사전압/50 Ω에 가깝다는 결과만으로 `50×S21`이나 입력단의 `1−S11` 보정을 실물에 승인하지 않는다. 실제 기준면·헤드 부하·복소 전달함수와 불확도 확인이 필요하다.",'',
'![빈 지그 비교](fixture_comparison.png)','![설정 민감도](fixture_sensitivity.png)','',
'### 전류 위치 정정과 추가 검산','',
'기존 요청 y=0은 기본 격자에서 실제 y=−0.9675 mm에 배치됐다. openEMS 소스와 ASCII 인덱스를 대조해 실제 dual 좌표를 읽고5개 전류면을 물리적 중앙 y=0에 공간 보간했다. 기존 원출력을 덮어쓰지 않았다. 이번 판단에는 `final_analysis` 파일을 사용한다. 선형/3차/4차 보간의 차이와 두 Ampere 경로, 코어 축 두께12.7 mm 양끝 및 평균도 비교했다. 자기 코어의 실제 자속 가중 응답을 계산한 것은 아니다.','',
f"새 모델들의1–100 MHz 두 적분경로 차이 최대 {max(v['max_nested_percent_1_100'] for v in run.values() if v['new_execution']):.4f}%, 선형/4차 공간 보간 차이 최대 {max(v['max_linear_vs_quartic_percent_1_100'] for v in run.values() if v['new_execution']):.4f}%다. Fourier 변환·V/I 부호·50 Ω 정규화는 시간축이 반 스텝 다른 지연 Gaussian의 닫힌 식으로 독립 검산했다. [합성 검산](postprocess_verification.json)은 제품 실측이 아니다.",'',
'## 4. 이번에 닫은 항목과 실물로 남는 항목','',
'- 완료: SMA 홀 공차 보완, 새 KiCad/제조 검토파일, 규칙/원본/ZIP 대조,6개 추가 FDTD의 기록과 비교, 기존 외형을 유지하는 첫 시제품 판단.','- 미검증: 코어·권선 포함 감도/잡음/유효 대역, 실제 SMA 기준면·FR4·납땜, 삽입 영향·직접 픽업·재장착 반복성·정량 불확도, 실물 조립/강도, 현장 입력 보호.','- 다음: 제조조건 검토 후 첫 시제품에서 빈 지그/헤드 장착 S2P와 선형성·5회 재장착을 확인한다. 연결·시작 설정·저장 파일은 [인수 절차](BENCH_ACCEPTANCE.md)에 지정했다. 실측 전에는 상대 S21와 원시 전압을 보존한다.','',
'100 kHz–300 MHz는 개발 목표이며, 우선1–100 MHz의 검증을 완료한다. 사용자가 요구한 정밀도를 달성했다고 표시하지 않는다. 이 검토는 구매·현장 작업 승인도 아니다. 공개 Sites/ATLAS와 업체 주문은 갱신하지 않았으므로 그곳의 이전 PCB 리비전과 이번 로컬 검토본을 혼용하지 않는다.','',
'## 파일과 재현','',
'[기계 판독 비교표](comparison.json), [수행 범위/판정 기준](PLAN.md), [출처·가정](SOURCES_AND_ASSUMPTIONS.md), [재현 방법](REPRODUCE.md), [현행 제작 상태](../../docs/CURRENT_READINESS.md). 전체 검토 묶음은 `RFCP_DESIGN_CLOSURE_REVIEW_ONLY.zip`이며 최종 해시는 `package_manifest.json`에 기록한다. 원래 PCB·이전 시뮬레이션·출력 STL은 보존했다.','']
(B/'README.md').write_text('\n'.join(lines),encoding='utf-8')
print('Evidence-based report written; no production or measured-performance approval.')
