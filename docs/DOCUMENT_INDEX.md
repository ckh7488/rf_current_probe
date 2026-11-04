# 문서 색인과 적용 순서

제작·구매 선택은 [현재 제작 구성](CURRENT_BUILD.md), 업체/결제 상태는 [STATUS](STATUS.md)를 먼저 읽는다. 백서의 설계식·시험 기준은 유지하며 문서 앞부분에 남은 날짜별 접수 안내는 당시 이력이다.

| 문서 | 역할 |
|---|---|
| [현행 원본 독립 재검토](../reviews/independent_current_audit_20260929/REPORT.md) | 새 PCB/CAM/기구/수식/구매 대조, 수정한 문서 오류와 남은 실물 검증 |
| [현재 제작 구성](CURRENT_BUILD.md) · [파일/해시 명세](current_build.json) | PCB6종·출력15종·구매팀 파일의 정확한 경로 |
| [현재 상태](STATUS.md) | 접수번호·업체 상태·합계·미완료 절차 |
| [제작/사용 준비](CURRENT_READINESS.md) | 실물 없이 확인한 범위와 입고 후 시험 |
| [3D 제작 기준](3D_PRINT_RELEASE_A19.md) | 중앙 A19·나머지 A18/C10, 수량·재질·출력/조립 CAD 구분 |
| [구매팀 HTML](../outputs/purchasing-handoff-20260929/구매안내_20260929.html) · [메일](../outputs/purchasing-handoff-20260929/구매요청_메일초안.txt) | 공유 장바구니·판매처별 합배송 구매 인계 |
| [중심 백서](RF_CURRENT_PROBE_WHITEPAPER.md) | 물리적 정의·수식·교정·대역별 목표·검증 기준 |
| [설계 BOM](BOM_DRAFT.md) | 설치 구성과 부품 근거. 구매 포장수량은 구매팀 HTML 사용 |
| [요구사항](REQUIREMENTS.csv) · [결정 이력](DECISIONS.md) | 요구/시험 연결과 변경 이유 |
| [PCB 최종 제조 검수](../reviews/jlc_renewal_preflight_20260929/REPORT.md) | B-RJ2 원본·드릴·임피던스 양식·접수 검증 |
| [부품 도면 재검수](../reviews/datasheet_reaudit_20260929/REPORT.md) | 도면·부품·CAD 대응 및 한계 |
| [A19 중앙 검증](../reviews/base_a19_20260930/REPORT.md) | 둥근 개구부 수정·필수 지지면 보존·강도 계산·업체 교체 요청 |
| [A18 검증](../reviews/base_dfm_fix_20260928/REPORT.md) · [C10 검증](../reviews/c10_guide_fix_20260928/REPORT.md) | 공칭 기구/하중·재생성·출력 검증 |
| [인수 순서](../reviews/fresh_system_audit_20260928/FIRST_ARTICLE.md) · [인수 계획](../reviews/full_reinspection_20260928/ACCEPTANCE_PLAN.md) | 입고 검사와 실제 남은 시험 |
| [벤치 절차](G2_BENCH_PROCEDURE.md) · [장비 기준](INSTRUMENT_BASELINE.md) | 연결·기준면·저장 원자료·장비 설정 |
| [분석 실행](../analysis/README.md) · [출력 기준 보정](../analysis/OUTPUT_REFERENCE.md) | 실제 파일 입력과 품질/유효성 조건 |
| [VNA→스코프](END_TO_END_REHEARSAL.md) | 기준면·부하 이동·CW 환산 |
| [공개 설명 소스](../viewer_A05/README.md) | 기존 공개 뷰어 빌드. 제조 주문에는 현재 제작 구성 사용 |
| [프로젝트 정리 기록](../reviews/project_cleanup_20260929/REPORT.md) · [보관함](../archive/README.md) | 삭제/압축 이관 내역과 복구 |

## 이력으로 읽을 문서

`reviews/`의 날짜별 보고서·DECISIONS의 과거 결정은 당시 후보·관측 결과다. 최신 결정에 대체된 후보를 현재 제조 선택지로 다시 노출하지 않는다. 특히 RJ45 초기 반사변환 PASS는 철회됐고, B-RJ1 앞면 배선안과 Y30–Y33 주문은 대체/취소됐다.

과거 before/attempt/reproduction 사본과 구형 대형 해석 중간자료는 압축 보관함으로 이관했다. 해당 시점 보고서가 이 경로를 참조하면 [복구 안내](../archive/README.md)에 따라 필요 파일만 복원할 수 있다. 현행 원본, 검증 해시 대상, 최종 해석 원자료, 재제작 입력과 측정 폴더는 작업 위치를 유지한다.
