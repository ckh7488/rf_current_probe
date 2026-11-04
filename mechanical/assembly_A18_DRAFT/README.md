# A18/C10 재제작 원본

현재 제작 선택은 [A18/C10 안내](../../docs/3D_PRINT_RELEASE_A18_C10.md), 업체 상태는 [STATUS](../../docs/STATUS.md)를 따른다. A18 베이스3종은 제출 완료이며 최종 상태와 생산승인은 별도다.

`parts/`의15종 STL은 현재15종20개 출력 명세다. 베이스3종은 A18, C10 프레임 및 다른 공통12종은 이전 버전과 동일하다. 이 디렉터리의 통합 FCStd는 비교/재생성 기준이며 상속된 옛 노브 표현을 포함한다. 실제 조립 참고는 [현재 일반 볼트·너트 CAD](../../reviews/base_dfm_fix_20260928/RFCP_A18_CurrentHardware_Assembly_DRAFT.FCStd)를 사용한다.

프로젝트 루트에서, 기존 결과를 덮어쓰지 않는 새 출력 경로로 실행한다:

```powershell
& 'C:/Program Files/FreeCAD 1.0/bin/python.exe' -X utf8 mechanical/build_assembly_A18.py --out reviews/base_dfm_fix_20260928/rebuild_user
python -X utf8 reviews/project_cleanup_20260929/verify_current_project.py
```

builder는 동결 A17 FCStd·mesh·build_report 및 `base_A18_tip_cuts.json`을 입력으로 사용한다. 따라서 A17은 재생성 의존파일로 보존한다. 원본 베이스 형상 확인 후 `verify_standard_bolts.py`, `verify_current_nuts.py`가 현재 일반 체결품 참고본을 별도로 작성한다. 최종 해석 원자료와 완료된 FEA 폴더는 덮어쓰지 않는다.
