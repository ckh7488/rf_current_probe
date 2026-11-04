> **이력 문서 · 현재 제작/사용 지시 아님 — 2026-09-22 분류.** 초기 A02 웹 자료의 소스 안내다. 현재 기준은 [현재 준비 상태](../../CURRENT_READINESS.md)를 따른다. 아래의 “현재/최신/미확정”은 원래 작성 시점의 표현이다.

# RF 전류 프로브 · 조립과 테스트

문서 v{{document.revision}} / {{document.date}} / DRAFT, 실측 전.

한 보고서 패키지 안의 두 문서:

- `index.html`: 전체 조립 A01–A08, 실제 CAD, 이전 지그 비교.
- `testing.html`: 준비·무전원 점검, 4단계 VNA 연결, 비교 시험, 조건부 환산·기록.

기존 `?step=3#calibration` 등 시험 링크는 `testing.html`로 이동한다. 문서 상단/하단에서 두 절차서를 오간다.

현재 설계는 평판 지그 {{fixture.revision}}, 헤드 {{head.revision}}, 집게 {{clamp.revision}}, 고정 반쪽 {{head.turns}}턴이다. 기존 3장 PCB 모델은 비교용이다. `records/design.json`과 같은 내용의 `design-data.js`를 두 문서와 CAD 뷰어가 사용한다.

원본 편집 위치는 Current_Probe 프로젝트의 `docs/atlas/source/`이며 `docs/atlas/build_docs.py`로 이 폴더에 생성한다. 문단은 `sections/`, 공통 값은 `design.json`, 상호작용은 `runtime/`에서 수정한다. 출력 HTML/JS만 수동 편집하면 다음 생성 시 덮어쓰므로 원본부터 고친다.

실제 CAD는 `assets/fixture-flat-a02.json`과 `.bin`이다. 소스 해시·원시 설계 근거는 `records/evidence.json`, 독립 검사 범위는 `records/a02-design-review.md`와 `.json`에 있다. 케이블·플러그·부하·SOLT 표준 외형은 예시다.

Three.js r128과 OrbitControls는 `vendor/`에 고정하며 MIT 라이선스를 함께 유지한다. 런타임 외부 의존은 ATLAS 공통 테마와 favicon뿐이다. 로컬 HTTP 서버 또는 GitHub Pages로 연다.
