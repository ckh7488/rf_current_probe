# 3D 제작 확정 — A16/C09

**9/28 후속 국부 보강(DEC-063): 다음 제작 검토본은 Head A04 SMA R2 + Fixture A03 SMA R2 + A17/C10이다.** C09 가이드 뒤 받침과R2.5/R0.75 뿌리만 보강해 프레임 P06 한 종류 두 개를 변경했다. 같은27.5 MPa 기준에서 최대24.084 MPa, 저장 CAD·가동/공구·재생성 검사를 통과했다(CALCULATED/SIMULATED). 재질·총15종20개·체결품은 유지한다. [수정·검증 기록](../reviews/c10_guide_fix_20260928/REPORT.md), [현재 파일 선택](3D_PRINT_RELEASE_A17_C10.md). 아래 A16/C09 동결·HOLD·제작 선택은 이전 버전 이력이며 원본 판정은 소급 변경하지 않는다. 실물/RF T01–T12는 미검증, 업체 제출·생산승인 전이다. 현재 후보 확인: `python reviews/c10_guide_fix_20260928/verify_candidate.py --mutations`.

2026-09-28 · **파일·수량·재질 선정 보존 / C09 강도 재검토 보류 / 현재 생산 GO 아님**

이 문서는 이전 A16/C09 파일 선택의 보존 기록이다. 후속 사용자 요청의 작은 국부 수정은 별도 A17/C10에 적용했고, 현재 파일 선택은 위 후속 기준을 따른다. 여기의 A16/C09 STL 바이트는 보존한다. PCB·RF 교정·실물 성능 판정은 이번 재질/문서 확정의 범위에 포함하지 않는다.

## 검수한 파일 식별 — 강도 재검토 후 인계

기존 주문 **W2026091819397543**에서는 [교체4종5개 ZIP](../procurement/3d_print_release_A16_C09_20260928/REPLACE_4TYPES_5PCS_9600.zip)을 풀어 아래4종만 바꾼다. 모두 **SLA / 9600 Resin / White**다. 나머지11종15개는 기존 선택을 유지한다.

| ID | 기존 파일 → 최종 파일 | 수량 |
|---|---|---:|
| P05 | `BaseCenter_A14_DRAFT.stl` → `BaseCenter_A16_DRAFT.stl` | 1 |
| P06 | `C07_Frame_DRAFT.stl` → `C09_Frame_DRAFT.stl` | 2 |
| P14 | `BaseFront_A14_DRAFT.stl` → `BaseFront_A16_DRAFT.stl` | 1 |
| P15 | `BaseRear_A14_DRAFT.stl` → `BaseRear_A15_DRAFT.stl` | 1 |

새 주문/전체 재견적이 필요할 때만 [전체15종20개 ZIP](../procurement/3d_print_release_A16_C09_20260928/ALL_15TYPES_20PCS.zip)을 사용한다. 내부를 재질별 폴더로 분리했다. **전체 묶음과 교체 묶음을 함께 주문하지 않는다.** STL 한 파일은 한 개 형상이며 수량은 주문 화면에 따로 입력한다.

뒤 바닥의 A15, 변경 없는 부품의 A14/C07 파일명은 정상이다. 숫자가 큰 파일을 임의로 골라 조합하지 않는다. 파일명의 DRAFT는 원본 식별을 위해 보존했으며, 현재 제작 선택은 이 확정표로 판단한다. 전체 조립 STEP에서 변형된 탄성 뚜껑을 다시 추출하지 않는다.

## 확정 재질·수량

**9600 Resin 8종11개 + 3201PA-F Nylon 7종9개 = 15종20개. 추가 체결품0개.** 모든 부품은 mm / 100%, 기본 후처리, No Surface Finish, No thread, 일반 납기로 지정한다. 도색·도금·외관 샌딩·급행 옵션을 추가하지 않는다. 정상적인 서포트 제거·세척·경화는 필요하며 기능면 치수를 깎아 바꾸지 않는다.

| ID | 부품 / 실제 STL | 수량 | 공정·재질 | 기존 행 견적 USD |
|---|---|---:|---|---:|
| P01 | 프로브 아래 중앙 몸체 · `LowerCenter_A14_DRAFT.stl` | 1 | SLS · 3201PA-F Nylon | 42.87 |
| P02 | 프로브 왼쪽 탄성 뚜껑 · `UpperLeft_A14_DRAFT.stl` | 1 | SLS · 3201PA-F Nylon | 10.44 |
| P03 | 아래 코어 고정바 · `LowerKeeper_FREE_DRAFT.stl` | 1 | SLS · 3201PA-F Nylon | 1.54 |
| P04 | 위 코어 고정바 · `UpperKeeper_FREE_DRAFT.stl` | 1 | SLS · 3201PA-F Nylon | 1.54 |
| P05 | 바닥 가운데 · `BaseCenter_A16_DRAFT.stl` | 1 | SLA · 9600 Resin | 31.02 * |
| P06 | 클램프 고정틀 · `C09_Frame_DRAFT.stl` | 2 | SLA · 9600 Resin | 27.74 * |
| P07 | 클램프 연결틀 · `C07_DriveYoke_DRAFT.stl` | 2 | SLA · 9600 Resin | 10.04 |
| P08 | 클램프 가로대·위 턱 · `C07_TopBridgeJaw_DRAFT.stl` | 2 | SLA · 9600 Resin | 2.94 |
| P09 | 아래 왼쪽 턱 · `C07_Jaw1_DRAFT.stl` | 2 | SLS · 3201PA-F Nylon | 2.10 |
| P10 | 아래 오른쪽 턱 · `C07_Jaw2_DRAFT.stl` | 2 | SLS · 3201PA-F Nylon | 2.10 |
| P11 | 프로브 아래 왼팔 · `LowerArmLeft_A14_DRAFT.stl` | 1 | SLA · 9600 Resin | 3.80 |
| P12 | 프로브 아래 오른팔 · `LowerArmRight_A14_DRAFT.stl` | 1 | SLA · 9600 Resin | 3.46 |
| P13 | 프로브 오른쪽 탄성 뚜껑 · `UpperRight_A14_DRAFT.stl` | 1 | SLS · 3201PA-F Nylon | 9.87 |
| P14 | 바닥 앞쪽 · `BaseFront_A16_DRAFT.stl` | 1 | SLA · 9600 Resin | 18.51 * |
| P15 | 바닥 뒤쪽 · `BaseRear_A15_DRAFT.stl` | 1 | SLA · 9600 Resin | 17.91 * |

금액은 **2026-09-28 저장 주문에서 확인한 행 전체 수량 가격**이다. `*`4행은 **보강 전 A14/C07의 가격**이며 새 형상 가격이 아니다. 수량2인 행의 가격을 다시2배 하지 않는다.

## 비용 판단

- 종전 전체 나일론 출력비 **$383.77** → 재질 분리 후 실제 출력 견적 **$185.88**. 절감 **$197.89 / 51.56%**. 비교용 가정환율1,400원/$에서 약53.7만원 →26.0만원이다. 현재 환율·A16 최종 결제액으로 표시하지 않는다.
- 기존 혼합 견적은 레진8종11개 **$115.42**, 나일론7종9개 **$70.46**다.
- 그대로 두는11종의 기존 소계는 **$90.70**다. **새 출력 총액 = 유지11종 가격 + 새 P05 + 새 P06(2개 합계) + 새 P14 + 새 P15**. 유지행 가격이 같다면 $90.70에 새4행 견적을 더한다. 교체되는 옛4행의 $95.18을 중복 합산하지 않는다.
- PCB·배송·세금·통관/카드 수수료는 출력비와 따로 적는다. 새4행은 아직 재견적하지 않았으므로 확정 총액은 비워 둔다.
- 큰 바닥/프레임까지 일괄 나일론으로 되돌리지 않는다. 자동 고급재질·MJF PA12·특수 레진·금속·급행 추가는 이번 확정안에 없다. 업체가 특정 부위를 거부하면 **해당 품목만**, 기능을 유지하는 가장 저렴한 대안과 차액을 먼저 제시받는다. 형상이나 재료가 바뀌면 그 부품의 관련 검증과 명세를 갱신한다.

9/23 동일 BaseCenter의 실제 비교 견적은 나일론$84.20, ABS FDM$111.91, PLA-P$54.30, 8228 레진$44.32, **9600 레진$31.02**였다. 외주에서는 FDM이 자동으로 더 싸지 않았다. 이는 당시 A14 한 형상의 비교이며 A16의 신규 견적이나 전체 시장 최저가 증명이 아니다. [실견적 기록](../procurement/print_costdown_20260923/README.md).

## 이 재질 구분을 유지하는 이유

바닥3종과 C09 프레임의 초기 하중 해석은 통과했지만, 추가2 mm 메시의 C09 가이드 벌림 하중은29.901 MPa로 기존27.5 MPa 기준을 초과했다. 해당 부위를 재검토하며 전체 재질을 임의 상향하지 않는다. 연결틀·가로대·아래 팔도 기존 9600 선택을 유지한다. 모든15종에 동일 하중 해석을 했다고 확대하지 않는다.

탄성 뚜껑 P02/P13은 의도된 휨이 필요하다. 제조사 전형 파단연신율은 [9600 5.5%](https://jlc3dp.com/help/article/photosensitive-9600-resin), [3201PA-F 35%](https://jlc3dp.com/help/article/3201pa-f-nylon)로, 동일 형상에 재료를 단순 교체하지 않는다. P01 중앙 몸체는 코어·PCB 정렬과 이전 레진 박벽 경고 때문에 나일론을 유지한다. 작은 고정바/턱 P03/P04/P09/P10은 **전체 합계$7.28**이므로 재질 변경으로 얻을 수 있는 절감은 그보다 작다. 반복 접촉·체결 역할을 유지하는 편이 합리적이다.

적용 범위는 기존 설계의 **실내 상온 시제품**이다. 제조사 물성은 실제 부품의 수명·허용 체결 토크 보증이 아니며,100 N 해석을 노브 토크 정격으로 표시하지 않는다.

## 검수와 제조 인계

[최초 A16 보완 검수](../reviews/a16_strength_fix_20260928/REPORT.md)와 [최신 통합 재검수](../reviews/fresh_system_audit_20260928/REPORT.md)를 근거로 한다. 최신 재실행에서125개 CAD 물체/조립·공구 경로/15종 STL 재생성을 확인했다. 완료된 구조 솔버6작업12경우 중 초기11경우는 기준을 통과했고 추가2 mm 가이드 벌림은29.901 MPa로 미달이다. 축100 N의3 mm 결과20.51 MPa는 유지되지만 전체 최소 전형강도 대비 여유는1.84배로2배 기준을 충족하지 않는다(CALCULATED/SIMULATED). 이번 확정 작업은 형상·재료를 바꾸거나 해석을 새로 수행한 작업이 아니다.

JLC에는 **새4종 형상으로 재심사**를 요청한다. 기존 휨 경고를 일괄 수락하지 않는다. 바닥 맞댐/장착면은 나사 힘으로 휨을 펴지 않아도 맞아야 하고, 프레임의 가이드·축 받침 기능을 유지해야 한다. 공칭0.8 mm 가이드 여유를 허용 휨으로 적지 않는다. 영문 전달 문구는 [ORDER_GUIDE_EN.md](../procurement/3d_print_release_A16_C09_20260928/ORDER_GUIDE_EN.md)에 준비했다. 외부 업로드·발송·결제는 이 문서 정리에서 수행하지 않았다.

## 원본과 확인

- [15행 파일·수량·재료·SHA256](../procurement/3d_print_release_A16_C09_20260928/PRINT_MANIFEST.json) / [CSV](../procurement/3d_print_release_A16_C09_20260928/PRINT_MANIFEST.csv)
- [제출 ZIP 해시](../procurement/3d_print_release_A16_C09_20260928/PACKAGES.json)
- [확정 상태 검사](../procurement/3d_print_release_A16_C09_20260928/verify_release.py)
- [문서 정리·실제 검증 기록](../reviews/3d_release_consistency_20260928/REPORT.md)

```powershell
python procurement/3d_print_release_A16_C09_20260928/verify_release.py --mutations
```

이 검사는 최종 출력파일·재질·수량·ZIP의 동일성과 연결 문서를 확인한다. JLC 제조심사와 납품품 검사를 대체하지 않는다.

기존 ZIP은 바이트 보존하며 그 안의 이전 engineering GO 문구는 후속 강도 결과를 반영하지 않는다. 현재 생산 인계에는 이 보류가 우선한다. 별도 [강도 보류 기록](../procurement/3d_print_release_A16_C09_20260928/ENGINEERING_HOLD.json)을 함께 확인한다.
