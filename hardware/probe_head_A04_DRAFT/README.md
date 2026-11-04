# 헤드 PCB A04 — SMA 조립 여유 보완

> 2026-09-22 추가 제출 전 검토: 실제 ZIP의 동박/드릴/마스크와 최대 PCB 조립 간섭을 독립 확인했습니다. 이 PCB와 제조 ZIP은 변경하지 않았으며 [제출 대상·제조 옵션](../../reviews/submission_freeze_20260922/MANUFACTURING_HANDOFF.md)을 고정했습니다.

> 2026-09-22 재검토: 보존 원본에서 재생성한 PCB/회로도와 현행 파일의 바이트 일치, 라이브러리/드릴/ZIP 일치, ERC/DRC/회로 일치 오류0을 다시 확인했습니다. 헤드 회로도의 잔존 A0.3 제목을 A0.4로 바로잡았으며 PCB·제조 ZIP·출력 형상은 추가 변경하지 않았습니다. [새 검토 기록](../../reviews/recheck_20260922/README.md).

2026-09-21 · **DRAFT — NOT FOR FABRICATION**

A03의 중앙 SMA 홀을 Ø1.50→1.70 mm, 네 접지 홀을 Ø1.70→1.90 mm로 넓힌 검토본이다. 36×28×1.6 mm 외곽, SMA/권선/고정홀 위치, 패드 외경, 신호 배선과 비아는 같다. 기존 출력물과의 외형 인터페이스 변경은 없다.

근거: [공차 계산](../../reviews/design_closure_20260921/sma/fit_result.json). GCT Rev1.2의 대칭 배치와 중심핀 정렬을 가정한 보수 모델에서 JLC 홀 크기·XY 위치 오차를 함께 적용했다. 수정 후 중심핀 반경 여유 약0.054 mm, 접지핀 모서리 여유 약0.061 mm다. 이 값은 도면에 없는 핀 휨·진위치 공차까지 보증하지 않는다. 첫 부품은 납땜 전 5핀 무가압 동시삽입과 평면 안착을 확인한다.

## 원본·검사

- [KiCad PCB](RFCP_Head_A04_DRAFT.kicad_pcb), [회로](RFCP_Head_A04_DRAFT.kicad_sch), [프로젝트](RFCP_Head_A04_DRAFT.kicad_pro)
- [제조 검토용 ZIP](RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip): Gerber 7개, PTH/NPTH 드릴, 작업 정보. **2026-09-22 JLC Y21-9961994A로 접수한 동일 파일이다. 18:49 KST 재조회에서 Approved, RF 묶음은 Awaiting Payment다. 결제·생산 파일 수동 승인은 하지 않았다.** [새 관측](../../reviews/document_full_audit_20260922/jlc_observation_1849.json).
- [저장 파일·드릴 대조](review/revision_verification.json), [ERC](review/erc.json), [DRC](review/drc.json)
- [재생성](build_revision.py): KiCad 10 Python으로 실행. `baseline/`의 보존 A03 원본을 읽어 이 디렉터리만 재생성한다. 이후 프로젝트 루트의 `analysis/export_sma_revisions.py`와 `analysis/verify_sma_revisions.py`로 내보내고 대조한다.

이전 A03 Y20 항목은9/22 취소하고 A04를 새 접수했다. [실제 제출·옵션·금액 기록](../../procurement/jlc_refresh_20260922/README.md)을 따른다. 이전 승인이나 Gerber 생성으로 새 생산 승인을 대신하지 않는다. PCB·3D 출력 형상은 이번 문서 정리에서 바꾸지 않았다.

조립은 SMA만 선납땜 → 권선 끝선을 분리한 채 H05 경로로 PCB 장착 → PA66 M2×12 체결 → 권선 납땜 → 아래 고정바 순서다. 장착면에 누른 채 PCB를 기울이지 않는다. [현행 조립 인계](../../docs/G3_PROTOTYPE_PACKAGE.md).

홀 확대는 제조사 권장 레이아웃에서의 프로젝트 변경이며, 최대 완성홀에서 납땜 충전·접합부 지지 상태를 첫 실물로 확인해야 한다. RF 전달함수와 입력 보호는 미검증이다.
