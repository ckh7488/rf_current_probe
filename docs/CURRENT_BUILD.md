# 제작과 입고 기준

**2026-10-21 입고 대조 기준은 Head A04 SMA R2, Fixture A03 SMA R2, Ethernet VNA B-RJ2 4종, 중앙 A19·나머지 A18/C10입니다.** 파일명에 남은 `DRAFT`는 원본 이름입니다. 실물 조립과 RF 성능 상태는 [현재 진행 상태](CURRENT_READINESS.md)를 따릅니다.

## PCB 6종

제작 선정 수량은 **6종 각 5장**입니다. 아래 KiCad 프로젝트와 보드, 회로도, 필요한 프로젝트 라이브러리 표 및 커스텀 규칙을 함께 보관합니다.

| 제작 항목 | KiCad 프로젝트 | 설계 보드 |
| --- | --- | --- |
| Y23 · 프로브 헤드 A04 SMA R2 | [프로젝트](../hardware/probe_head_A04_SMA_R2_DRAFT/RFCP_Head_A04_SMA_R2_DRAFT.kicad_pro) | [PCB](../hardware/probe_head_A04_SMA_R2_DRAFT/RFCP_Head_A04_SMA_R2_DRAFT.kicad_pcb) |
| Y24 · 평판 교정 지그 A03 SMA R2 | [프로젝트](../hardware/calibration_fixture_PCB_A03_SMA_R2_DRAFT/RFCP_Fixture_Flat_A03_SMA_R2_DRAFT.kicad_pro) | [PCB](../hardware/calibration_fixture_PCB_A03_SMA_R2_DRAFT/RFCP_Fixture_Flat_A03_SMA_R2_DRAFT.kicad_pcb) |
| Y34 · Ethernet/RJ45 공통 B-RJ2 | [프로젝트](../reviews/jlc_renewal_preflight_20260929/candidate/common/balun_eth_rj45.kicad_pro) | [PCB](../reviews/jlc_renewal_preflight_20260929/candidate/common/balun_eth_rj45.kicad_pcb) |
| Y35 · LLC M12 B-RJ2 | [프로젝트](../reviews/jlc_renewal_preflight_20260929/candidate/llc/m12_llc.kicad_pro) | [PCB](../reviews/jlc_renewal_preflight_20260929/candidate/llc/m12_llc.kicad_pcb) |
| Y36 · TE M12 슬립링 B-RJ2 | [프로젝트](../reviews/jlc_renewal_preflight_20260929/candidate/te/m12_slipring.kicad_pro) | [PCB](../reviews/jlc_renewal_preflight_20260929/candidate/te/m12_slipring.kicad_pcb) |
| Y37 · Molex 슬립링 B-RJ2 | [프로젝트](../reviews/jlc_renewal_preflight_20260929/candidate/molex/molex_slipring.kicad_pro) | [PCB](../reviews/jlc_renewal_preflight_20260929/candidate/molex/molex_slipring.kicad_pcb) |

- **Head·Fixture.** SMA 신호홀과 접지홀의 완성 지름은 각각 **1.90 mm, 2.10 mm**입니다. 평판 지그의 중심 신호는 코어 안, 귀환은 코어 밖으로 흐릅니다. PCB의 설계 기준 SMA는 GCT RFPC-SMA28-F 수직형입니다. 10월 27일 교정지그 시험에는 Samtec SMA-J-P-H-RA-TH1 직각형 2개를 선정했습니다. 장착한 SMA는 측정 세션에 기록합니다.
- **Ethernet VNA.** 공통 보드는 **RJ45·SMA B면, 발룬 F면**입니다. LLC·TE는 A쌍 전체 L1·B쌍 전체 L4, Molex는 두 쌍 모두 L1입니다. 세 어댑터의 신호 비아는 0개입니다. 4층 보드의 지정 차동 구간은 **100 Ω**, 공통 보드의 SMA RF 구간은 **50 Ω**입니다. 11월 17일 사전 예측의 대상은 공통 Y34 한 장입니다.

## 기구와 설치량

출력은 **15종 20개**, 9600 Resin **8종 11개**와 3201PA-F Nylon **7종 9개**입니다. 9월 30일 중앙 P05를 A19로 교체 제출했고, 10월 21일 입고 대조에서 A19 표기를 확인했습니다. A19는 A18 중앙 베이스의 앞뒤 이음판에 관통 개구부 8개를 넣은 버전입니다. 나머지 출력품은 A18·C10과 공통 부품입니다.

- [A19 조립 FreeCAD](../mechanical/base_A19_DRAFT/RFCP_A19_CurrentHardware_Assembly_DRAFT.FCStd) · [중앙 STL](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.stl) · [중앙 STEP](../mechanical/base_A19_DRAFT/parts/BaseCenter_A19_DRAFT.step)
- [A18·C10 및 공통 STL](../mechanical/assembly_A18_DRAFT/parts/) · [출력품별 수량·재질](../reviews/base_a19_20260930/PRINT_MANIFEST.json) · [설치 BOM](../release/assembly-bom.md)
- [중앙 형상 변경과 검사](../reviews/base_a19_20260930/REPORT.md) · [A19 생성기](../mechanical/build_base_A19.py) · [생성 입력 A18 조립 CAD](../reviews/base_dfm_fix_20260928/RFCP_A18_CurrentHardware_Assembly_DRAFT.FCStd)

재생성에는 FreeCAD 1.0.2의 Python 환경을 사용합니다. 저장소 루트에서 `python mechanical/build_base_A19.py --out <새 출력 폴더>`로 실행합니다. 저장 시각이 들어가는 FCStd와 STEP은 형상으로, 재생성한 STL은 바이트 해시로 대조할 수 있습니다. [생성 기록](../mechanical/base_A19_DRAFT/build_report.json)

## 공개 파일 대조

[공개 설계 SHA-256 목록](../release/design.sha256)은 입고 명세 97개 중 **PCB 프로젝트·기구·생성 입력 등 공개 원본 84개**를 담습니다. Linux 또는 Git Bash에서 저장소 루트의 `sha256sum -c release/design.sha256`으로 대조합니다. 나머지 13개는 제출·업체 최종 CAM·출력 제출 ZIP이며 원 프로젝트에 보존합니다. 입고 원본 증빙과 업체 문서도 원 프로젝트에서 관리합니다.

9월 30일 업체 심사 상태와 제출 파일은 [당시 상태 기록](STATUS.md)과 [당시 명세](current_build.json)에 남아 있습니다.
