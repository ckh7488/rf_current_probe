# 현행 문서 데이터

2026-09-23. Head A04 / A14·C07,57행 BOM,45단계 조립,출력15종20개. 현행 교정지그는 Fixture A03이며 출력 포트 기준으로1–500 MHz 보정을 수행한다(DEC-053). [빌드·공개 진입점](../README.md).

`showcase_bom.json`은 공개 BOM, `showcase_manifest.json`은 공개 파일 허용목록/해시다. 내부 `bom.json`·`readiness.json`은 현행 데이터이며 공개 배포하지 않는다. `purchase_manifest.json`은2026-09-21 구매 이력으로 현재 리비전·수량·주문 상태를 결정하는 입력이 아니다. 현재 설치·구매 기준은 `docs/BOM_DRAFT.md`를 따른다. 실시간 JLC 상태는 이 데이터에서 추정하지 말고 [날짜가 붙은 접수 기록](../../procurement/jlc_refresh_20260922/README.md)을 확인한다.

현행 CAD는125객체다. BOM의44개 CAD 연계 행은123객체를 다루며 나머지2개는 교정PCB 동박이다. 조립표현은131메시/완성128객체로 별도 수를 쓴다. 93ba CAD·A13 경로검사·이전 구매 수량은 역사 기록이다.

`manual_current.html`의 문구를 바꾸면 `showcase_content.py`의 원문 일치 검사를 함께 갱신하고 실제 출력 문서를 읽어야 한다. `catalogue_parts.json`은 초기 BOM 행을 덮어쓰므로 최종 ROWS를 검사한다. 결과 해시와 행/단계 수만으로 내용의 정확성을 보장하지 않는다.
