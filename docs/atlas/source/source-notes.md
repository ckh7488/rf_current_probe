> **이력 문서 — 2026-09-22 분류.** 초기 A02/A11/A12 당시 기록이며 현재 제작·사용 지시가 아니다. 최종3D 제조 선택은 [A16/C09 확정 기준](../../3D_PRINT_RELEASE_A16_C09.md)을 따른다. 아래 A14/C07 및 이전 자료는 당시 기록이다.

# RF 전류 프로브 · 두 절차서의 근거

{{document.date}} · 문서 v{{document.revision}} · {{document.status}}

현재 조합: **지그 {{fixture.revision}} / 헤드 {{head.revision}} / 집게 {{clamp.revision}} / {{head.turns}}턴**.
설계 ID: `{{document.design_id}}`.

## 문서 구성

- [조립 절차서](../index.html): 코어·권선·헤드 PCB·집게·지그의 A01–A08 작업, 단계별 완료 조건과 설계 변경 시 재확인.
- [점검·교정·측정 절차서](../testing.html): 무전원 확인, SOLT, 지그 through, 헤드 장착 through, 프로브 상대 S21, 반복성·누설, 조건부 전류 환산, 기록.
- 공통 치수·부품·리비전·시험 설정·CAD 포트 좌표는 [design.json](design.json)에서 관리하며 두 페이지와 3D 연결 배치에 반영한다. 설명은 공정별 HTML 원본으로 관리한다.

## 확인한 설계와 판단

평판 PCB {{fixture.revision}}는 {{fixture.size}} 1장, 두 창과 중앙 SIG, 외곽 GND 귀환 구조다. SMA {{head.sma}} 두 개를 직접 납땜한다. 이전 PCB 3장 A0.1은 구조 비교용으로만 보존했다.

이번 재검사는 저장 PCB의 ERC/DRC/미연결/회로 일치 위반 0건, 전체 구경 길이에서 SIG 통과/GND 통과량 0, 닫힘 간격 및 가정 플러그를 포함한 개폐 19점 간섭을 확인했다. 검증 도구, 해시, 수치와 범위는 [비교 검토](a02-design-review.md), [검사 기록](a02-design-verification.json)에 있다.

판단은 **조립·재제작의 변수 감소**에 대한 것이다. RF 감도·대역·정확도·반복성이 개선됐다는 실측 결론이 아니며 비용 절감도 새 견적 전에는 확정하지 않는다. 바닥 M3×12의 공칭 끝 여유 0.6 mm와 65 mm 나일론 기둥의 케이블 하중을 실물에서 먼저 확인해야 한다.

## 원본과 그림

기준 문서는 프로젝트 백서, 사용자 조립 제약, G2 벤치 절차와 현재 하드웨어 README/ASSEMBLY/BOM이다. 프로젝트 상대 경로와 SHA-256은 [evidence.json](evidence.json)에 기록한다. 실물 접근 없이 설계 원본을 읽어 문서화했다.

3D 지그·PCB·집게 형상은 저장된 CAD의 35개 부품, 456,702개 삼각형을 축약하지 않고 변환했다. 동박은 식별 색이며 실제 솔더마스크·실크와 다르다. 개방 보기에서는 일부 패드·체결물을 숨긴다. 사진처럼 보이는 정적 그림도 CAD/PCB 렌더다. 케이블·외장 부하·교정 표준·체결 플러그는 위치 설명을 위한 예시 외형이다.

## 제조사 일차자료

- [GCT RFPC-SMA28-F](https://gct.co/connector/rfpc-sma28-f): 수직 SMA의 핀 배치와 권장 홀. 보유 제조사 Rev 1.2 도면과 대조했다.
- [Würth 970300365](https://www.we-online.com/components/products/datasheet/970300365.pdf), [971350365](https://www.we-online.com/components/products/datasheet/971350365.pdf): 나일론 기둥 길이·M3 암나사 깊이·수나사 길이.
- [Tekbox TBCPx 교정지그](https://www.tekbox.com/product/TBCPx_Calibrators_Manual.pdf): 정의된 50 Ω 조건의 전달 임피던스 관계. 전력 차 식의 부호는 정의상 Pout−Pin으로 검산해 적용한다.

## 아직 없는 결과

실물 맞춤·출력 공차·강도·조임 토크·실측 RF 교정표·유효 대역·허용 전류·내전압·현장 보호 정격은 미검증이다. EM 시뮬레이션을 실행하지 않았다. 제조 승인·발주·공급사 카트 변경을 하지 않았다. 기록 양식의 빈 칸은 앞으로 실제값을 적기 위한 것이며, 절차의 생략이나 측정 결과를 뜻하지 않는다.

이전 교정값과 검사 결과를 새 리비전에 자동 승계하지 않는다. 원본 해시가 달라지면 재검사 후 문서를 갱신한다.

