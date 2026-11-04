# 현재 제작 구성

2026-09-30 · 중앙 베이스 A19 수정·재심사 요청본 · **업체 최종 심사 및 생산승인과는 별도**

아래 원본·ZIP만 현재 주문에 사용한다. [기계 판독 명세와 SHA-256](current_build.json), [업체 상태](STATUS.md)를 함께 확인한다. 9/30에는 중앙 베이스 P05만 A19로 수정했다. 나머지 출력14종·PCB6종·구매품·수량은 유지한다. 사이트에는 아직 A18이 표시되며 A19 STL을 담당자에게 발송해 교체·재심사를 요청했다.

## PCB — 6종, 각 5장

| 용도 / JLC 번호 | 재제작 원본 | 제출 ZIP |
|---|---|---|
| 프로브 헤드 R2 / Y23 | [KiCad](../hardware/probe_head_A04_SMA_R2_DRAFT/RFCP_Head_A04_SMA_R2_DRAFT.kicad_pcb) | [제조 ZIP](../hardware/probe_head_A04_SMA_R2_DRAFT/RFCP_Head_A04_SMA_R2_DRAFT_REVIEW_ONLY.zip) |
| 교정지그 R2 / Y24 | [KiCad](../hardware/calibration_fixture_PCB_A03_SMA_R2_DRAFT/RFCP_Fixture_Flat_A03_SMA_R2_DRAFT.kicad_pcb) | [제조 ZIP](../hardware/calibration_fixture_PCB_A03_SMA_R2_DRAFT/RFCP_Fixture_Flat_A03_SMA_R2_DRAFT_REVIEW_ONLY.zip) |
| 공통 ETH/RJ45 / Y34 | [KiCad](../reviews/jlc_renewal_preflight_20260929/candidate/common/balun_eth_rj45.kicad_pcb) | [제조 ZIP](../outputs/jlc-renewal-20260929/balun_eth_rj45/balun_eth_rj45_BRJ2_CAM_20260929.zip) |
| LLC M12 / Y35 | [KiCad](../reviews/jlc_renewal_preflight_20260929/candidate/llc/m12_llc.kicad_pcb) | [제조 ZIP](../outputs/jlc-renewal-20260929/m12_llc/m12_llc_BRJ2_CAM_20260929.zip) |
| TE M12 slipring / Y36 | [KiCad](../reviews/jlc_renewal_preflight_20260929/candidate/te/m12_slipring.kicad_pcb) | [제조 ZIP](../outputs/jlc-renewal-20260929/m12_slipring/m12_slipring_BRJ2_CAM_20260929.zip) |
| Molex slipring / Y37 | [KiCad](../reviews/jlc_renewal_preflight_20260929/candidate/molex/molex_slipring.kicad_pcb) | [제조 ZIP](../outputs/jlc-renewal-20260929/molex_slipring/molex_slipring_BRJ2_CAM_20260929.zip) |

회로도·프로젝트·규칙·로컬 라이브러리는 각 PCB와 같은 폴더에 있다. VNA B-RJ1/Y30–Y33은 취소된 중간본이다.

- 공통 ETH: **RJ45 J1 + SMA J2–J5는 B면**, 발룬 T1–T4는 F면.
- LLC·TE: 모든 커넥터 F면, **A쌍 전체 L1 / B쌍 전체 L4**, 신호 비아 0개.
- Molex: 모든 커넥터 F면, 두 쌍 L1, 신호 비아 0개.
- VNA: 4층/1.6 mm/JLC04161H-7628, 외층1 oz·내층0.5 oz, 녹색·무연 HASL. 지정 차동구간 100Ω ±10%, 공통 보드 RF 구간 50Ω. 별도 임피던스 성적서 `No`, 제조파일 수동 확인 `Yes`.

## 3D 출력 — 중앙 A19 / 나머지 A18·C10, 15종 20개

- [중앙만 교체 ZIP 1종1개](../outputs/jlc-base-a19-20260930/A19_CENTER_1TYPE_1PC_REVIEW.zip) · [전체 세트 ZIP](../outputs/jlc-base-a19-20260930/A19_A18_C10_ALL_15TYPES_20PCS_REVIEW.zip)
- [15종 수량·재질·해시](../reviews/base_a19_20260930/PRINT_MANIFEST.json) · [제작 안내](3D_PRINT_RELEASE_A19.md)
- [현재 일반 볼트·너트 조립 CAD](../mechanical/base_A19_DRAFT/RFCP_A19_CurrentHardware_Assembly_DRAFT.FCStd)
- [A19 중앙 STEP/STL](../mechanical/base_A19_DRAFT/parts/) · [중앙 재생성 스크립트](../mechanical/build_base_A19.py) · [나머지 출력 원본](../mechanical/assembly_A18_DRAFT/parts/)
- 재질: **9600 Resin 8종11개 + 3201PA-F Nylon 7종9개**. 부품/나사 추가0개.

A19 STL·전후 비교 PNG·검토 메모를9/30 16:19 Elinor에게 발송했다. 기존 P05 `D2026092832500233-9961994A` 한 항목의 교체 요청이며, 사이트 교체 완료나 업체 승인을 뜻하지 않는다. [검사·발송 기록](../reviews/base_a19_20260930/REPORT.md)

현재 주문에 전체 ZIP을 다시 추가하면 중복 주문이 된다. 전체 조립 CAD/STEP은 참고용이며 개별 출력 STL 대신 업로드하지 않는다. A18 현재 하드웨어 조립 CAD와 A17 등 이전 원본은 A19/A18 builder 입력으로 보존한다.

## 구매팀 전달

[구매안내 HTML](../outputs/purchasing-handoff-20260929/구매안내_20260929.html)과 [메일 본문](../outputs/purchasing-handoff-20260929/구매요청_메일초안.txt)을 사용한다. HTML에 DigiKey 공유 장바구니 및 국내 판매처별 합배송 목록이 들어 있다. JLC는 승인 후 인보이스·결제 링크를 별도 전달한다.

코어 2644181281 주문2개=반쪽2개=한쌍. 발룬10개/SMA10개/RJ45 8개 예비 포함 구매수량 유지. LLC용 수 M12 1개는 사용자 보유품이며 신규구매0개. M12용 별도 지지 패널은 구매 필수품으로 추가하지 않는다.
