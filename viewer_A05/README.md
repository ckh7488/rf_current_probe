# RFCP 공개 문서 빌드

2026-09-28. 폴더 이름 A05는 경로 유지용이며, 이 뷰어의 기구 표시 기준은 **A14/C07**이다. 최종3D 제작은 [A16/C09 확정 기준](../docs/3D_PRINT_RELEASE_A16_C09.md)을 따른다. 뷰어의 구형 다운로드는 최종 제출 파일 선택을 대신하지 않는다. 현행 교정지그는 Fixture A03(출력 포트 기준1–500 MHz 보정, DEC-053)이며, 3D 화면은 A03과 외곽·고정홀이 같은 공통 장착 형상이며 내부 동박 설계의 표시·제조 기준은 A03 원본과 구분한다. [ATLAS](https://ckh7488.github.io/showcase/reports/rf-current-probe/)를 현행 공개 진입점으로 사용한다. 별도 Sites의 과거 파일을 최신본으로 취급하지 않는다.

## 원본

- `current_set_content.py`와 `set_sources/catalogue_parts.json`: 내부57행 BOM. 공개용은 `showcase_content.py`에서 설치·사용 정보로 정리한다.
- `current_guide_steps.py`:46단계. `guide_sources/reviewed_steps_20260928.json`에 공개본의 H01/H02/H06/Q00/Q01–Q04 수정 내용을 보존했다. `guide_sources/geometry_supplements_a14.json`의 해시를 CAD와 대조한다.
- `set_sources/manual_current.html`: 연결·특성화 절차. `showcase_content.py`의 원문 일치 단언을 함께 유지한다.
- `showcase_analysis.py`: A03의 저장 S11/S21/K와500 MHz 보정 절차. 폐기 후보 비교표·그래프는 현행 화면에서 제거했다.
- `viewer_annotations.js/.css`: 형상 밖 주석과 전역 글씨 표시 설정. 세3D 페이지에서 설정을 공유한다.
- `assembly_viewer.js`와 `assembly_template.html`: 실험실 교정은 0단계 VNA SOLT와 빈 지그, 헤드 장착 through, 프로브 전달, 외장 로드 반사의 네 측정으로 나눈다. SOLT에는 양 포트 O/S/L·THROUGH·적용 확인 연결을 표시하고, SOLT 장면은 케이블 끝 기준면, 로드 반사는 별도 1포트 SOL로 교정한 VNA 암 포트에 수형 로드를 직접 연결하는 개념도다. 두 교정 ID를 구분한다. 오른쪽은 현재 연결·동작·저장 파일만 기본 표시하고 상세 절차는 접어 둔다. 구조·개폐는 소개와 세 동작만 표시한다. 단계별 원본 파일명은 G2 벤치 절차와 같으며 실제 저장은 LibreVNA에서 한다. 교정값 수집·ZT 계산 기능은 아니다.
- `verify_showcase.py`: 공개 파일 허용목록. 내부 구매·다른 제품 제조파일·과거 자료를 dist에 복사하지 않는다.

## 재생성

프로젝트 루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe viewer_A05/build_document_set.py
.\.venv\Scripts\python.exe viewer_A05/verify_showcase.py
```

`build_purchase_handoff.py`는 폐기된 구매/지그 판정을 재생성하지 않도록 실행을 막았다. 원문은 정리 기록에 보존하며, 현재 설치·구매 기준은 `docs/BOM_DRAFT.md`와 날짜가 있는 조달 기록을 사용한다.

현재 CAD의 build_report와 원본 해시가 일치해야 한다. `build.py`, `build_clamp_site.py` 등 구형 생성기는 현행 공개 빌드 명령이 아니다. [A14 소스 재생성 검증](../reviews/document_full_audit_20260922/cad_reproduction.json)은125객체 형상·15종 STL 일치를 확인했다.

ATLAS 복사는 `publish_atlas_showcase.py --repo 검토한_격리_체크아웃`을 사용한다. 기존 공개 파일 중 생성 대상 밖의 파일은 삭제하지 않는다. 별도 지그 페이지의 수정 소스는 `fixture_reference/`에 보존한다. 복사와 게시 완료는 다르다. ATLAS 저장소의 검증·브라우저 확인·배포 후 확인을 거친다. 공개 파일 manifest와 BOM/조립 검사는 `set_sources/`에 기록한다. 제조 파일은 이 문서 작업으로 바꾸지 않는다.

이전 안내는 [보존본](../reviews/document_full_audit_20260922/before/viewer_A05/README.md)에 있다. 실물 조립·RF 유효 대역·정확도·보호 정격은 검증 전이다.
