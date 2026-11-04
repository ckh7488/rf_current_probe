# A0.4-SMA-R2 — SMA 삽입 여유 보완

2026-09-28 · **DRAFT — NOT FOR FABRICATION / 업체 미제출 / CALCULATED**

기존 probe_head_A04_DRAFT 원본을 보존한 별도 수정본이다. 중심/접지 완성홀1.90/2.10 mm, 패드2.80/3.10 mm. 중심 핀 계산 여유0.1189 mm, 추가 편심0.03 mm 후0.0889 mm. 실제5핀 무응력 삽입·평평한 안착·납땜 검사와 RF 검증은 미실행이다.

- [PCB 원본](RFCP_Head_A04_SMA_R2_DRAFT.kicad_pcb), [회로도](RFCP_Head_A04_SMA_R2_DRAFT.kicad_sch), [프로젝트](RFCP_Head_A04_SMA_R2_DRAFT.kicad_pro)
- [Gerber/드릴 검토 ZIP](RFCP_Head_A04_SMA_R2_DRAFT_REVIEW_ONLY.zip) · SHA-256 `f38d4e177e991fbe681871b09888b5cdb60bd6ed33f7cd93776eb3872421ed73`
- [전체 수정 근거와 실제 검증](../../reviews/sma_clearance_r2_20260928/REPORT.md)
- [재생성 코드](build_revision.py), [baseline 식별](revision.json), [의도된 변경](review/intentional_changes.json)
- [ERC](review/erc.json), [기본 무시 항목 포함 ERC](review/strict_erc.json), [DRC](review/drc.json), [board STEP](review/board_only.step), [상면 SVG](review/top.svg)

재생성은 이 디렉터리의 `baseline/`과 `build_revision.py`를 사용한다. KiCad10 Python으로 builder를 실행한 뒤 KiCad CLI로 zone refill/DRC와 제조파일 내보내기를 한다. 프로젝트 루트의 `reviews/sma_clearance_r2_20260928/export_and_check.py`에 정확한 명령이 있다. `analysis/export_sma_revisions.py`는 이전 제출본용이므로 이 R2 재생성에 사용하지 않는다.

기존 외곽·창·고정홀·커넥터 위치·트랙·비아 및 A14/C07 출력물은 동일하다. 실제 launch 동박은 바뀌었으므로 기존 빈 지그 K를 R2의 검증 완료 RF 결과로 취급하지 않는다. 기존 업체 주문에는 R2가 아직 반영되지 않았다.
