# 보존 시점의 제작 검토 구성

2026년 9월 30일 중앙 베이스 A19 변경과 재심사 요청을 기록한 구성입니다. 보존 당시 조합은 **Head A04 SMA R2 · Fixture A03 SMA R2 · VNA B-RJ2 · 중앙 A19 / 나머지 A18·C10**입니다. 아래 링크는 공개 저장소에 있는 설계 원본입니다. 제작 승인과 실제 조립·RF 검증 상태는 [검토 기록](CURRENT_READINESS.md)에 있습니다.

## PCB

| 검토한 보드 | 공개 KiCad 원본 |
| --- | --- |
| 프로브 헤드 A04 SMA R2 | [기판](../hardware/probe_head_A04_SMA_R2_DRAFT/RFCP_Head_A04_SMA_R2_DRAFT.kicad_pcb) |
| 평판 교정 지그 A03 SMA R2 | [기판](../hardware/calibration_fixture_PCB_A03_SMA_R2_DRAFT/RFCP_Fixture_Flat_A03_SMA_R2_DRAFT.kicad_pcb) |
| 공통 Ethernet/RJ45 | [기판](../reviews/jlc_renewal_preflight_20260929/candidate/common/balun_eth_rj45.kicad_pcb) |
| LLC M12 어댑터 | [기판](../reviews/jlc_renewal_preflight_20260929/candidate/llc/m12_llc.kicad_pcb) |
| TE M12 슬립링 어댑터 | [기판](../reviews/jlc_renewal_preflight_20260929/candidate/te/m12_slipring.kicad_pcb) |
| Molex 슬립링 어댑터 | [기판](../reviews/jlc_renewal_preflight_20260929/candidate/molex/molex_slipring.kicad_pcb) |

당시 검토 수량은 PCB **6종, 각 5장**입니다. 공통 Ethernet 보드는 RJ45·SMA를 B면, 발룬을 F면에 배치했습니다. LLC·TE는 A쌍을 L1, B쌍을 L4에 두었고, Molex는 두 쌍을 L1에 두었습니다.

## 기구

- [A19 조립 FreeCAD](../mechanical/base_A19_DRAFT/RFCP_A19_CurrentHardware_Assembly_DRAFT.FCStd) · [A19 중앙 베이스 STL](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.stl) · [STEP](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.step)
- [A18 부품 원본](../mechanical/assembly_A18_DRAFT/parts/) · [전체 수량·재질·해시](../reviews/base_a19_20260930/PRINT_MANIFEST.json) · [A19 수정 기록](../reviews/base_a19_20260930/REPORT.md)

검토 구성은 **15종 20개**입니다. 9600 Resin 8종 11개, 3201PA-F Nylon 7종 9개이며, 9월 30일 변경 대상은 중앙 베이스 한 종류였습니다.

## 보관 범위

[당시 기계 판독 명세](current_build.json)에는 제출 ZIP과 구매 자료의 이름과 해시도 들어 있습니다. 해당 제출본 ZIP과 구매 전달 파일은 공개 소스 보관 범위에서 제외됐습니다. 저장된 PCB·CAD·STL은 각 파일이 표시하는 판본의 설계 검토 자료입니다.
