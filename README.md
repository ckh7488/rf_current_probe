# RF 전류 프로브 소스 보관

2026-11-04 시점에 보존한 설계·분석 소스와 선택된 결과입니다.

- [원 프로젝트의 현재 구성 문서](docs/CURRENT_BUILD.md), [설계 명세](docs/current_build.json)
- hardware/: 프로브 헤드·교정지그의 KiCad 및 CAD 원본. VNA 보드 4종은 reviews/jlc_renewal_preflight_20260929/candidate/에 있습니다.
- analysis/: RF 분석 및 시뮬레이션 코드와 requirements.txt.
- mechanical/: A17·A18·A19 CAD, 부품 STEP/STL, 생성 스크립트. A19 builder가 읽는 기준 CAD는 reviews/base_dfm_fix_20260928/에 포함했습니다.
- viewer_A05/: 안내·조립 화면의 소스와 정적 의존성. dist는 재생성 대상입니다.
- selected-evidence/: 경력 문서에 연결한 저장 결과. 시뮬레이션과 실측을 구분해 읽습니다.

전체 FEM 출력·반복 mesh.json·설치 런타임·제조 ZIP·구매 전달 파일은 제외했습니다. 원 프로젝트 문서의 이들 경로는 이 소스 보관본에 없을 수 있습니다. A17/A18 이전 버전부터 모든 CAD를 연속 재생성하는 묶음이 아니며, 포함된 CAD를 기준으로 검토합니다. 전체 과거 자료는 SYNC_CHECKPOINT_20261104.json의 원본 경로에 남아 있습니다.

최신 실측 sweep의 경력 문서 연결은 아직 남아 있습니다. 이 저장소 업로드를 새 계측·제조 승인으로 해석하지 않습니다. 원본 위치·해시는 SYNC_CHECKPOINT_20261104.json 및 SYNC_SUPPLEMENT_20261104.json에 기록했습니다.
