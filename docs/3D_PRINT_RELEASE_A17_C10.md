# 현재 3D 제작 검토본 — A17/C10

**9/28 JLC 재접수 완료:** A17/C10 교체4종5개를 기존 RF 주문 W2026091819397543에 제출했고 모두 **Reviewing**이다. 구형 대응4종만 파일 교체 사유로 취소했다. 새4종 $97.54, RF 주문은 배송 포함 $217.96. [접수·파일·검토 요청 기록](../procurement/jlc_refresh_A17_C10_20260928/README.md). **PCB SMA R2는 아직 미제출**, 결제·생산승인·실물/RF 검증은 미완료다. 아래 과거의 미제출·미견적 문장은 해당 검토 시점 이력으로 읽는다.

2026-09-28 · DEC-063 · DRAFT — NOT FOR FABRICATION

현재 조합은 **Head A04 SMA R2 + Fixture A03 SMA R2 + A17/C10**이다. C09 강도 선별 실패를 작은 가이드 보강으로 보완한 별도 후보이며, 실물·업체 공정 승인 전이다. [수정과 실제 검증](../reviews/c10_guide_fix_20260928/REPORT.md)을 먼저 확인한다.

| 기준 | 교체 범위 |
|---|---|
| A16/C09 준비본을 갖고 있을 때 | P06 `C09_Frame_DRAFT.stl` → `C10_Frame_DRAFT.stl`, 1종2개 |
| 기존9/22 A14/C07 업체 주문 | P05 BaseCenter_A16, P06 C10_Frame, P14 BaseFront_A16, P15 BaseRear_A15, 4종5개 |
| 처음부터 전체 묶음 | 15종20개;9600 Resin8종11개 +3201PA-F Nylon7종9개 |

P06은 **SLA/9600 Resin/White/2개**다. 다른14종 파일과 재질은 A16과 같다. 추가 체결품0개. mm/100%, 일반 납기, 표면마감·나사 가공 없음. 9/28 새 교체4종 견적은 $97.54이며 상세는 위 접수 기록을 따른다.

- [P06만 교체하는1종2개 ZIP](../reviews/c10_guide_fix_20260928/C10_FRAME_ONLY_1TYPE_2PCS_REVIEW.zip)
- [재질별 전체15종20개 ZIP](../reviews/c10_guide_fix_20260928/A17_C10_ALL_15TYPES_20PCS_REVIEW.zip)
- [개별 파일·수량·재질·해시](../reviews/c10_guide_fix_20260928/PRINT_MANIFEST.json)
- [재제작 원본](../mechanical/assembly_A17_DRAFT/RFCP_A17_Integrated_DRAFT.FCStd), [builder](../mechanical/build_assembly_A17.py)

후보 명세의 `submission_or_payment_performed=false`는 원본 작성 당시 이력이며 현재 접수는 위 기록을 따른다. 확인 명령: `python reviews/c10_guide_fix_20260928/verify_candidate.py --mutations`.

이전 A16/C09 ZIP과 문서는 보존 이력이다. 프레임1종 ZIP을 기존 A14 주문 전체에 대한 완전 교체본으로 오인하지 않는다. 후보 작성 시점에는 업체 업로드·주문·결제·생산승인·공개 사이트 변경을 하지 않았다. 이후 사용자 요청으로 위 접수 기록과 같이 3D4종만 재심사 제출했다. 실제 출력 뒤 인수·T01–T12 및 A03 출력 기준 RF 교정은 기존 절차를 유지한다.


## JLC 제작 조건 추가 대조 — 2026-09-28

[JLC DFM 추가 검토](../reviews/c10_jlc_dfm_20260928/REPORT.md): 현재15종의 파일·출력 크기·메시와 C10 변경부46개 단면/63개 가동 간격을 확인했다. 새 보강부의 두께3.5/5 mm·가동 간격0.8 mm는 일반 지침을 만족한다. 기존 축 받침 홈 옆1 mm 얕은 턱과 긴 레진 부품의 휨에 대한 업체 판단은 남아 있다. 이 검토는 전체 제조 승인이나 실제 휨 보증이 아니다. CAD·STL·ZIP·재질·수량은 유지하며, 이전4종 휨 경고를 일괄 수락하지 않는다. 업체 검토 위치는 같은 폴더의 JLC_REVIEW_NOTE_EN.md에 준비했다.
