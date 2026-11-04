# 교정 PCB A03 — 외형 유지, SMA 홀 여유 보완

> **2026-09-23 현행 교정지그 ([DEC-053](../../docs/DECISIONS.md)).** 이 A03를 유일한 현행 교정지그로 사용하며1–500 MHz 보정을 수행한다. −6 dB 전달 감소 자체를 상단 대역 제외 사유로 사용하지 않는다. 주파수별 ZT·불확도·유효성을 기록한다. 판정 기준은 빈 지그 S11이 아니라 출력 포트 기준 코어 전류다(백서 11.6). 아래 해석의 100 MHz S11 −20 dB 미달은 기록으로 유지하되 교정 판정 조건이 아니다. 저장 모델의 코어/출구 보정량 K는 100/300/500 MHz 약0.05–0.10/0.41–0.78/0.87–1.65 dB다. [채택 근거](../../reviews/fixture_a03_output_reference_20260923/ENGINEERING.md). PCB·제조 ZIP은 변경하지 않았다. 조립 부품: SMA 2개(E04), PA66 M3×12 나사·날개너트 각4(F13/F14).

> 2026-09-22 추가 제출 전 검토: 실제 ZIP의 동박/드릴/마스크와 최대 PCB 조립 간섭, 네 고정홀의 복합 치수 공차를 확인했습니다. 이 PCB와 제조 ZIP은 변경하지 않았으며 [제출 대상·제조 옵션](../../reviews/submission_freeze_20260922/MANUFACTURING_HANDOFF.md)을 고정했습니다.

> 2026-09-22 재검토: 보존 원본에서 재생성한 PCB/회로도와 현행 파일의 바이트 일치, 라이브러리/드릴/ZIP 일치, ERC/DRC/회로 일치 오류0을 다시 확인했습니다. PCB·제조 ZIP·출력 형상은 추가 변경하지 않았습니다. [새 검토 기록](../../reviews/recheck_20260922/README.md).

2026-09-21 · **DRAFT — NOT FOR FABRICATION**

A02와 동일한 144×92.7×1.6 mm 외곽·창·고정홀·중앙 신호·외부 귀환 구조를 사용한다. 두 SMA의 중심홀을 Ø1.50→1.70 mm, 접지홀을 Ø1.70→1.90 mm로 넓혔다. 패드 외경·SMA 위치·신호 배선·비아는 같다. BaseCenter 및 출력물 장착 인터페이스는 같다.

헤드와 같은 GCT RFPC-SMA28-F를 사용하므로 [같은 공차 보완](../../reviews/design_closure_20260921/sma/fit_result.json)을 적용한다. 기존 A02는 보존한다.

- [KiCad PCB](RFCP_Fixture_Flat_A03_DRAFT.kicad_pcb), [회로](RFCP_Fixture_Flat_A03_DRAFT.kicad_sch), [프로젝트](RFCP_Fixture_Flat_A03_DRAFT.kicad_pro)
- [제조 검토용 ZIP](RFCP_Fixture_Flat_A03_DRAFT_REVIEW_ONLY.zip), [저장 파일·드릴 대조](review/revision_verification.json)
- [ERC](review/erc.json), [DRC](review/drc.json), [재생성 코드](build_revision.py)

`build_revision.py`는 보존한 A02 원본에서 홀과 리비전 표기만 바꾸며 KiCad 10 Python으로 실행한다. 프로젝트 루트의 `analysis/export_sma_revisions.py`, `analysis/verify_sma_revisions.py`가 내보내기와 독립 대조를 수행한다.

현행 전자기 해석은 기존 중실비아7조건과 추가 Z격자2조건의 [새 환산과 판정](../../reviews/document_full_audit_20260922/RF_REFINEMENT.md)을 따른다. Z0.3→0.2 mm의1–100/100–300 MHz 최대 복소 전류 차이는 0.2168% / 1.7206%, Z0.2→0.15 mm는 0.2564% / 2.1231%다. 차이는 단조 감소하지 않으므로 수렴 차수나 연속해 오차 상한을 확정하지 않는다. 새 모델의100 MHz S11도 각각−16.23/−16.73 dB로−20 dB 목표 미달이다. 기존0.5/0.3 mm의100–300 MHz 차4.5949% 미달은 보존한다. 마지막 두 격자 비교가 전체3D 수렴이나 실물 정밀도를 보증하지 않는다. 빈 지그 모델을 코어·권선·실제 케이블이 포함된 교정으로 사용하지 않으며,50S21을 자동 적용하지 않는다.

첫 실물에서는 5핀 삽입·평면 안착·납땜 충전, 무코어/헤드 장착 상태 S2P 및 전류 모델을 검증한다.


## 실제 제출 상태

2026-09-22 JLC `Y22-9961994A`로5장 접수했다. [17:25 접수 기록](../../procurement/jlc_refresh_20260922/README.md)에서는 Reviewing이었으며 [18:49 KST 재조회](../../reviews/document_full_audit_20260922/jlc_observation_1849.json)에서 Approved, RF 묶음은 Awaiting Payment로 바뀌었다. 수동 생산 파일 확인 조건은 유지되며 결제·생산 파일 승인은 실행하지 않았다. 추가 Z격자 계산과 문서 대조는 [전수 조사 보고서](../../reviews/document_full_audit_20260922/README.md)를 따른다. 과거 해석 결과를 덮어쓰지 않는다.
