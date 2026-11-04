# 현재 3D 제작 검토본 — 중앙 A19 / 나머지 A18·C10

2026-09-30 · 중앙 P05만 수정 · **업체 교체 확인/재심사 및 새 견적 대기**

총 **15종20개**, **9600 Resin 8종11개 + 3201PA-F Nylon 7종9개**. 부품과 나사는 추가하지 않는다. 최신 업체 상태는 [STATUS](STATUS.md)를 따른다.

| 항목 | 선택 파일 | 수량 | 업체에 요청한 처리 |
|---|---|---:|---|
| P05 중앙 베이스 | BaseCenter_A19_DRAFT.stl | 1 | 기존 D2026092832500233의 A18 파일만 교체·재심사 |
| P14 앞 / P15 뒤 | BaseFront_A18_DRAFT.stl / BaseRear_A18_DRAFT.stl | 각1 | 기존 Approved 항목 유지 |
| P06 프레임 | C10_Frame_DRAFT.stl | 2 | 기존 Approved 항목 유지 |
| 나머지11종 | 아래 전체 명세의 파일 | 15 | 기존 재질·수량·옵션 유지 |

- [교체용 중앙 STL](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.stl) · [중앙만 ZIP](../outputs/jlc-base-a19-20260930/A19_CENTER_1TYPE_1PC_REVIEW.zip)
- [전체15종20개 보관 ZIP](../outputs/jlc-base-a19-20260930/A19_A18_C10_ALL_15TYPES_20PCS_REVIEW.zip) · [전체 수량·재질·해시](../reviews/base_a19_20260930/PRINT_MANIFEST.json)
- [현재 조립 CAD](../mechanical/base_A19_DRAFT/RFCP_A19_CurrentHardware_Assembly_DRAFT.FCStd) · [중앙 STEP](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.step) · [재생성 코드](../mechanical/build_base_A19.py)
- [수정·검증·발송 기록](../reviews/base_a19_20260930/REPORT.md) · [업체 전달 메모](../outputs/jlc-base-a19-20260930/REVIEW_NOTES.txt)

**현재 주문에는 중앙1개만 교체한다. 전체 ZIP을 새 주문으로 추가하지 않는다.** A19 중앙은 SLA/9600 Resin/White/No Surface Finish/No thread/100%/mm/Standard이며 현재 사이트상 파일은 아직 A18이다. 담당자에게9/30 16:19 STL·PNG·TXT를 발송했고 수동 교체 또는 Replace File 기능 활성화를 요청했다. A19 새 가격은 미확정이며 기존 중앙 $26.76와 총액 $444.35는 이전 견적이다.

조립 순서와 나사/너트 종류는 기존 안내를 유지한다. 중앙 베이스의 넓은 앞뒤 이음판에 둥근 개구부8개가 추가됐지만 기둥·볼트 구멍·본체 받침·필수 좌면은 보존했다. 외곽 맞댐 높이도 동일하며 개구부를 막거나 추가 부품으로 메울 필요가 없다. 전체 조립 CAD는 참고용이고 개별 STL만 출력한다.

입고 시 앞·중앙·뒤 베이스를 힘을 가하지 않고 맞대어 홀 정렬과 들뜸을 확인한다. 본체를 얹고 받침 접촉을 확인한 다음 PCB를 네 기둥에 올려 홀 정렬·흔들림·기판 휨을 확인한다. 나사로 뒤틀린 부품을 끌어당겨 평탄하게 만드는 방식은 합격으로 처리하지 않는다. 결과·사진·치수는 `measurements/raw/mechanical/A19_<개체번호>/`에 저장하고 불일치는 업체와 협의한다. 이는 아직 실행하지 않은 인수 절차다.

CAD/STL 검사와 선형 탄성 계산은 완료했다. 레진 경화 수축·후경화 휨을 시뮬레이션한 결과가 아니며 업체 검토/실물 가조립을 대체하지 않는다. DRAFT 파일명과 이전 A18 원본은 보존한다.
