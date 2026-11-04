> **이력 문서 · 현재 제작/사용 지시 아님 — 2026-09-22 분류.** 9/16 합성 소프트웨어/구형 기구 검증이다. 현재 제조 검증은 G3 인계에서 찾는다. 현재 기준은 [현재 준비 상태](CURRENT_READINESS.md)를 따른다. 아래의 “현재/최신/미확정”은 원래 작성 시점의 표현이다.

# G2 소프트웨어·기구 배치 검증 기록

2026-09-16 · **SYNTHETIC / CALCULATED / 문서 검토만 수행**

이 문서의 기존 본문은 G2 당시 실행 기록이다. 후속으로 만든 KiCad PCB·집게 CAD/STL와 ERC/DRC 결과는 [G3 검증 기록](G3_PROTOTYPE_PACKAGE.md)에 있다. 전체 프로세스 검토 후 추가한 시험은 마지막 절에 따로 기록했다.

## 결과

**pytest 66개 통과**, 합성 Touchstone 301점으로 두 분석 모드를 실제 실행했다. 제조사 STEP 기반 배치 파일도 생성하고 형상/교차 검사를 실행했다. 실물 측정·RF 센서 시뮬레이션·ERC/DRC 통과를 뜻하지 않는다.

| 검증 | 실제 결과 | 근거 |
|---|---|---|
| Touchstone 단위/형식/순서 | 4단위×3형식×3버전/순서 조합 36건 통과 | [자동시험](../tests/test_rfcp.py), [JUnit XML](../tests/results/unit_tests.xml) |
| 형식·비50 Ω·중복 주파수·NaN 등 거부 | 해당 회귀시험 통과 | 같은 XML의 testcase 목록 |
| 백서 −20 dB, dBm/RMS/peak/dBµ 단위 | 5 Ω, 13.979400 dBΩ; 정현파 외 peak 환산 거부 | `test_matched_whitepaper_and_units` |
| 기준면·우회 전류·위상 조건 | input-current 조건 거부 / HI로 알려진 값 복원 / 위상 미검증은 빈 열 | `test_mismatch_at_valid_current_plane`, `test_bypass_counterexample_and_hi_correction`, `test_matched_line_phase_requires_reference_evidence` |
| 대역·null·clipping·결손·체인 | 정량 환산/외삽/이중 보정 거부 | 무효 입력 시험 |
| 원본·결과 보존 | 입력 해시 동일; 기존 출력 경로·raw/release 보호; 합성의 MEASURED 재분류 거부 | `test_export_preserves_input_and_labels` |
| 합성 HI 모드 CLI | 301행, 조건부 환산 가능 301행, ZT=5 Ω 복원 | [CSV](../tests/results/hi_model_reviewed/zt.csv), [manifest](../tests/results/hi_model_reviewed/manifest.json) |
| 같은 합성 입력의 relative CLI | 301행, 환산 가능 0행, ZT 빈 값 | [CSV](../tests/results/relative_reviewed/zt.csv), [manifest](../tests/results/relative_reviewed/manifest.json) |
| 그래프 시각 검토 | SYNTHETIC/헤드/교정 ID/축·단위/불확도 미평가/범위 표기 확인. relative의 ZT 없음 설명 표시 | [HI 그래프](../tests/results/hi_model_reviewed/response.png), [relative 그래프](../tests/results/relative_reviewed/response.png) |
| 제조사 STEP | valid solid 1개; 원본 해시 보존 | [형상 검사](../mechanical/manufacturer_step_inspection.json) |
| 공칭 코어 2개+30 mm 게이지 | 겹침 체적 0 mm³, 최소 간격 3.6055 mm | [배치 계산](../mechanical/layout_check_calculated.json) |
| 가정한 권선 공간+30 mm 게이지 | 겹침 체적 0 mm³, 간격 1.3 mm | 같은 계산. 실제 권선 배치 검증 아님 |
| 분석 의존성 | `pip check`: No broken requirements found | [환경 버전 기록](../tests/results/environment.json) |
| 저장된 CAD 재열기 | 7개 객체·형상 유효성·DRAFT 표시·게이지 비간섭 재확인 | [저장 파일 검사](../mechanical/saved_layout_verification.json) |
| 작업 폴더 정합성 | 요구사항 56행/12열, 당시 내부 링크 107개 이상 없음, 원문 2개 및 참조 원본 7개 해시 보존, 실측/release 폴더 비어 있음 | [작업 폴더 검사 기록](../tests/results/workspace_review.json) |

초기 `hi_model_demo`/`relative_demo`는 그래프 검토 전 출력 이력이다. 최종 문서 링크는 설명을 보완한 `*_reviewed`를 사용한다. 모든 예제는 `tests/`에 있으며 실측 폴더에 넣지 않았다.

## 실제 실행 명령

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q --junitxml=tests/results/unit_tests.xml
.\.venv\Scripts\python.exe -m tests.generate_synthetic
.\.venv\Scripts\python.exe -m analysis.rfcp tests/synthetic/bypass_fixture.s2p --metadata tests/synthetic/bypass_fixture.json --out tests/results/hi_model_reviewed
.\.venv\Scripts\python.exe -m analysis.rfcp tests/synthetic/bypass_fixture.s2p --metadata tests/synthetic/relative.json --out tests/results/relative_reviewed
& 'C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe' mechanical/inspect_manufacturer_step.py
& 'C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe' mechanical/build_layout.py
.\.venv\Scripts\python.exe mechanical/render_layout.py
.\.venv\Scripts\python.exe -m pip check
```

동일 결과 디렉터리가 있으면 분석 CLI 재실행은 새 이름을 요구한다. Python 3.12.6, scikit-rf 2.1.0, FreeCAD 1.0.2, KiCad CLI 10.0.0, Poppler 26.07.0의 버전/지원 API·도움말을 실제 확인했다. KiCad는 실행 가능성 확인만 했고 회로/PCB 파일은 아직 없다.

## 요구사항 반영

CAL-05, SW-01~05, DATA-03은 **현재 구현된 오프라인 기능 범위**의 증거를 연결했다. 센서·장비가 함께 검증되어야 하는 CAL-01~04, DATA-01/02, SW-03/04/05의 하드웨어/실측 관련 부분은 부분 검증으로 둔다. 요구사항 표에서 `PARTIAL`은 증거가 있는 일부 범위만 완료됨을 뜻한다.

## 미검증

- 실제 코어/절연/권선/잠금의 공차·개폐·장착·내구·전기적 안전.
- 지그의 RF 정합·전류 경로/기준면·직접 누설, 실제 ZT·대역·감도·위상·불확도.
- 입력 보호, 개체별 출력 체인, 스코프 응답, T01~T12의 실측.
- 실제 측정기에서 내보낸 Touchstone 파일과 회귀 비교. 현재 66개는 합성 시험이다.
- 시간 파형 역복원, 자동 불확도 산출, Touchstone 2.1, 별도 체인 de-embedding.
- 제조용 KiCad/하우징, ERC/DRC, 최종 견적·발주·현장 적용.

**다음 실물 검증은 F-A through + Head A 5턴 상대 S21**이다. 연결·설정·파일명은 [G2_BENCH_PROCEDURE.md](G2_BENCH_PROCEDURE.md)에 지정했다.

## 후속 전체 절차 검토 — 2026-09-16

추가 [scope_tone 자동시험](../tests/test_scope_tone.py) 44개와 기존 66개를 함께 실행해 **110개 통과**했다. [process_review_tests.xml](../tests/results/process_review_tests.xml)에 실제 결과가 있다. 기존 `unit_tests.xml`의 G2 실행 이력은 보존했다.

추가 범위: 고조파/DC/비정수 주기의 기본파 추출, 감쇠 및 수신기 gain을 한 번씩 적용한 A RMS 복원, 기준면·헤드·체인·수신 설정 불일치, 1 MΩ/이중 종단/10×/sweep/clipping/불명 품질의 거부, 잘못된 시간 단위/NaN/불규칙 샘플/짧은 기록/드리프트 거부, CLI 입출력과 기존 결과 보존. 합성 데이터는 실측 폴더에 쓸 수 없다.

[전체 리허설 보고서](END_TO_END_REHEARSAL.md)는 연결 8종+기존 어댑터 오류 거부, 1/10/30/100 MHz 기본파 1 mA 복원, 오류 시나리오 10개 거부의 실제 실행 기록을 연결한다. `end_to_end_20260916` 및 `end_to_end_reviewed_20260916` 디렉터리는 개발 중 실행 이력이고 최종 링크는 코드/manifest를 갱신한 `process_rehearsal_final_20260916`을 사용한다.

기구 접속 검토에서는 저장 A0.1 CAD를 변경하지 않고 다시 읽었다. 가정한 F-A 귀환을 포함하면 110°부터 간섭하고 가정한 큰 플러그 몸통은 낮은 체결 위치에서 덮개와 충돌한다. 이를 90° 지그 개방 제한과 실제 체결 확인 조건에 반영했다. 양끝 런치/지지대/개방 스토퍼는 여전히 미완료다.

실제 계측기 CSV 형식, CW 파형, BNC 기준면, 수신기 응답/부하, 종합 불확도 및 실측 전류의 정확도는 이번 시험으로 검증되지 않는다. PCB/기구 형상이 같으므로 기존 ERC/DRC를 재실행했다고 보고하지 않는다.
