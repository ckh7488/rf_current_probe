# 9/29 제작 이력 — A18/C10

9/30 중앙 P05는 A19 교체·재심사 요청으로 대체됐다. 현재 제출 파일은 [A19 제작 안내](3D_PRINT_RELEASE_A19.md)를 따른다. 아래 A18 중앙 파일/견적/상태는 당시 이력이며 나머지14종은 유지된다.

2026-09-29 · 형상·수량·재질 선택 확정 · 업체 최종 심사/생산승인은 [현재 상태](STATUS.md) 참조.

총 **15종 20개**, **9600 Resin 8종 11개 + 3201PA-F Nylon 7종 9개**다. 기존 주문에서 A18 베이스3종을 교체 접수했고, C10 프레임 및 나머지 공통 부품을 유지한다. 현재 RF 주문은 출력$188.41 + PCB$19.20 + 배송$10.52 = **$218.13, 쿠폰 전**이다.

| 부품 | 현행 JLC 번호 | 수량 | 재질 | 9/29 18:50 상태 |
|---|---|---:|---|---|
| P05 중앙베이스 | D2026092832500233 | 1 | 9600 Resin | Reviewing |
| P14 앞베이스 | D2026092832500228 | 1 | 9600 Resin | Approved |
| P15 뒤베이스 | D2026092832500232 | 1 | 9600 Resin | Approved |
| P06 C10 프레임 | D2026092828500181 | 2 | 9600 Resin | Approved |

- [전체 출력 ZIP 15종20개](../reviews/base_dfm_fix_20260928/A18_C10_ALL_15TYPES_20PCS_REVIEW.zip)
- [베이스만 교체 ZIP 3종3개](../reviews/base_dfm_fix_20260928/A18_BASES_3TYPES_3PCS_REVIEW.zip)
- [전체 수량·재질·SHA256 명세](../reviews/base_dfm_fix_20260928/PRINT_MANIFEST.json)
- [현재 일반 렌치볼트·M3 나일론 육각너트 조립 CAD](../reviews/base_dfm_fix_20260928/RFCP_A18_CurrentHardware_Assembly_DRAFT.FCStd)
- [재제작 builder](../mechanical/build_assembly_A18.py) · [국부 수정 좌표](../mechanical/base_A18_tip_cuts.json) · [재제작 안내](../mechanical/assembly_A18_DRAFT/README.md)

전체 ZIP은 신규 전체 세트용이고 현재 주문에 다시 추가하지 않는다. 전체 조립 CAD는 참고용이며 출력은 명세에 지정된 개별 STL로 한다. 파일명에 A14/C07이 남은 공통12종도 현재 세트의 정상 구성품이다.

[A18 검증 기록](../reviews/base_dfm_fix_20260928/REPORT.md)과 [C10 검증 기록](../reviews/c10_guide_fix_20260928/REPORT.md)은 CALCULATED/SIMULATED 결과다. 업체 Approved는 앞베이스 자동 Thin walls 경고의 상세 위치나 기능면 휨·실물 맞춤의 검증을 뜻하지 않는다. 입고 시 자유 조립·맞댐·홀·너트·PCB 지지를 확인한다. 제조파일/현행 원본의 DRAFT 파일명은 승인 이력 보존을 위해 바꾸지 않았다.
