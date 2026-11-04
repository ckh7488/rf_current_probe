> **이력 문서 · 현재 제작/사용 지시 아님 — 2026-09-22 분류.** 초기 CAD 발표 구성 기록이다. 현재 기준은 [현재 준비 상태](../CURRENT_READINESS.md)를 따른다. 아래의 “현재/최신/미확정”은 원래 작성 시점의 표현이다.

# Atlas 원본 CAD 시각화 개정

2026-09-17 · v0.3

완료 → 단순 연결 그림을 원본 PCB 교정지그 A0.1·집게 A0.3의 3D 모델로 교체해 Atlas에 게시했다. 집게 열림/닫힘, PCB만 보기, 신호/귀환 강조, 회전·확대·시점 초기화와 네 교정 단계를 지원한다. O/S/L/T 표준과 P1/P2 선택도 케이블 끝의 연결 상태를 바꾼다.

변경 파일 → `docs/ATLAS_CURRENT_PROBE_DRAFT.md`, Atlas 보고서의 `index.html`, `report.css`, `report.js`, 신규 `cad-viewer.js`, 원본 CAD에서 내보낸 `assets/fixture-cad.bin` 및 `.json`, 근거 기록·표지·목록. 내보내기 원본은 `export_cad_viewer.py`, 브라우저 확인은 `review_cad.cjs`다. PCB/기구 제작 파일은 수정하지 않았다.

실제 검증 → 44개 원본 부품·654,058개 삼각형을 유지했다. float32 좌표 저장의 최대 반올림 0.00000381355 mm는 제작 정밀도와 무관하다. 로컬과 공개 Chrome에서 단계 4개, 표준 4개, 표준 연결 포트 2개, 조립 상태 3개, 경로 강조 3개, 키보드 조작, 시점 3개 및 390/320 px 폭을 확인했다. JavaScript 오류·실패 요청 0. 사이트 정적 검사 통과. GitHub Actions build/deploy 성공. 공개 확인 기록은 `review/cad-live/browser-checks.json`이다.

미검증/막힘 → 실물 조립·RF 측정은 수행하지 않았다. 지그·집게는 저장 CAD이며 액세서리는 설명용 외형이다. 원본의 SMA 외형 모델이나 표시상 케이블 경로가 실제 부품 맞춤을 입증하지 않는다. 실물 RF 검증을 문서 표시 검증과 구분한다.

다음 작업 → 사용자가 개정 화면의 이해도를 검토한다. 실제 시험 시 기존 벤치 절차에 따라 측정·설정·교정 ID를 남긴다.

- 게시: https://ckh7488.github.io/showcase/reports/rf-current-probe/?step=3#calibration
- 커밋: `9d9bfb5364aa617dd5db6ec3a81b4cb7510c7873`
- 배포: https://github.com/ckh7488/showcase/actions/runs/35203197455
