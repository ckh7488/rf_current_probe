# RFCP 오프라인 분석

2026-09-28 현행 안내 · Python 3.12.6 / scikit-rf 2.1.0 · 장비 제어 없음

첫 실물의 범위는 [현재 벤치 절차](../docs/G2_BENCH_PROCEDURE.md)다. 빈 양식의 개체 ID/리비전은 실제 조립체와 기록을 보고 채운다. Head A04라는 PCB 리비전만으로 권선 수·헤드 개체·교정 ID를 대체하지 않는다. 실물 데이터와 광대역 전류 파형 복원 기능은 아직 없다. 지금 준비된 도구는 S2P 분석과 CW 기본파 분석이다.

## 실행

현재 `.venv`는 시스템에 설치된 NumPy/Matplotlib/pytest를 공유하고 RF 의존성은 로컬에 설치했다. 별도 PC에서는 독립 환경으로 아래처럼 재현할 수 있다. 사용하는 패키지 버전은 [requirements.txt](requirements.txt)에 고정했다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r analysis/requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q --junitxml=tests/results/unit_tests.xml
.\.venv\Scripts\python.exe -m tests.generate_synthetic
.\.venv\Scripts\python.exe -m analysis.rfcp tests/synthetic/bypass_fixture.s2p --metadata tests/synthetic/bypass_fixture.json --out tests/results/my_new_demo
```

마지막 명령의 출력 디렉터리는 새 이름이어야 한다. 원시 입력과 기존 결과를 덮어쓰지 않는다. 재실행할 때 새 출력 경로를 지정한다. 합성 생성 스크립트만 `tests/synthetic/`의 결정론적 파생 예제를 갱신한다.

결과: `zt.csv`, 데이터 종류·헤드/교정 ID·주파수·불확도 표시 `response.png`, 입력 SHA-256·메타데이터·코드 해시·버전의 `manifest.json`.

## 지원과 거부

- 설치된 scikit-rf `Touchstone(file)` / `get_sparameter_arrays()` / `z0` API와 소스를 확인했다. S21은 `s[:,1,0]`이다.
- 지원 범위: 명시적인 옵션 줄, Touchstone 1.0/2.0, 1/2포트 single-ended, full S matrix, Hz/kHz/MHz/GHz, RI/MA/DB, v2의 `21_12`/`12_21`, 두 포트 모두 실수 50 Ω.
- 비50 Ω, 혼합 모드, 부분 행렬, 지원하지 않는 키워드, 다른 파라미터 Z/Y 등, 비단조/중복 주파수, NaN/Inf, Touchstone 2.1을 거부한다. 특히 2.1의 포트별 option-line 저항을 구버전 의미로 조용히 읽지 않는다. 파일 확장자만 바꾸어 우회하지 않는다.
- 메타데이터의 실제 코어/장비/교정/체인 ID, 설정, 위치, timestamp를 기록한다. [양식](metadata_template.json)은 미작성 상태여서 즉시 실행하면 거부되는 것이 정상이다.
- 기본 `relative`: S21만 표시, ZT/전류 환산 불가. `matched`, `input_current`, `hi_model`은 [지그 검토서](../docs/G1_FIXTURE_REVIEW.md)의 조건과 증거가 필요하다.
- 백서 11.6의 **출력 포트 기준** `output_reference`를 구현하고 파일 입력·CW 연동·합성 시험을 마쳤다. 장착 through/전달의 정·역방향 S2P, 별도 암 기준면 로드 S1P, 복소 K와 주파수별 검토·불확도를 함께 읽는다. [실행·양식·판정 규칙](OUTPUT_REFERENCE.md)을 따른다. 실측·K 적용성 검토가 없는 상태에서는 `relative`로 보존한다.
- `phase_validated=false`이면 복소수와 위상 열을 비운다. 불확도 미평가는 빈 값+`UNASSESSED`다. 모르는 불확도를 0으로 출력하지 않는다.
- `valid`는 명시한 대역·quality review·수치 조건을 만족한다는 **조건부 환산 가능 표시**다. 실제 대역, 측정 등급, ±3 dB 정확도 인증이 아니다. 메타데이터의 true나 증거 문자열 자체가 실물 검증을 대신하지 않는다.
- null 근처, clipping, 대역 밖, 평가하지 않은 품질, 명시적인 결손 구간을 정량화하지 않는다. `tone_current_rms`는 인접 유효 샘플 사이 log-frequency/log-magnitude 보간만 수행하고 결손 대역을 건너뛰지 않는다.
- `tone_current_rms`는 같은 순서의 체인 ID와 **단일 정현파 성분의 RMS 전압**을 받는 저수준 수식 API다. 이 함수만으로 실제 스코프 설정/기준면/수신기 응답을 검증하지 않는다. 스코프 데이터에는 아래 `scope_tone` 경로를 쓴다. 과도 최대값·전체 RMS·FFT 스펙트럼 밀도를 그대로 넣지 않는다. 시간 역복원·Tek 고유 CSV 자동 해석·FFT는 미구현이다.
- 교정에 포함된 케이블·감쇠기 재보정을 거부한다. 아직 별도 체인 보정 연산은 제공하지 않으므로 새 체인을 통째로 특성화한다. VNA 기준면에 스코프 내부 응답은 포함되지 않는다.

## 수식 검증 데이터

[fixture_model.py](fixture_model.py)는 L=30 nH/C=3 pF/R=52 Ω의 **합성 반례**다. 실제 지그 피팅 또는 센서 고주파 예측이 아니다. 입력전류와 코어전류가 다른 경우를 시험하며 `1−S11`을 무조건 적용하면 틀릴 수 있음을 수치로 보인다.

[../tests/synthetic/input_current.json](../tests/synthetic/input_current.json)은 의도적인 잘못된 조건 예제다. CLI가 `no_bypass_current_verified` 오류로 거부해야 한다. 동일 입력에 [relative.json](../tests/synthetic/relative.json)을 쓰면 S21 진단은 가능하나 ZT는 비워 둔다.

9/28 출력 기준 구현·새 전체 시험은 [검증 기록](../reviews/output_reference_20260928/REPORT.md)을 따른다. 이전 실행 근거: [9/22 시험110개](../reviews/document_full_audit_20260922/software_tests.xml), [자동시험 원본](../tests/test_rfcp.py). [초기 시험 보고서](../docs/G2_VERIFICATION.md)는 당시 기록이다. 공식 포맷 출처는 [IBIS Touchstone 사양](https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf), 라이브러리 근거는 [scikit-rf 공식 저장소](https://github.com/scikit-rf/scikit-rf)와 실제 설치 소스다. 2.1 사양을 참고한 사실과 이 도구의 지원 범위를 구분한다.

## 스코프 CW 분석과 전체 리허설 — 후속 추가

[scope_tone.py](scope_tone.py)는 명시적인 `time_s,voltage_v` 파일과 [설정 양식](scope_metadata_template.json)을 읽는다. 원시 장비 파일은 보존하고 별도 정규화 근거를 남긴다. DC/기본파/고조파를 동시에 fit하여 기본파 RMS를 분리한다. 최소 128점·20주기, 균일 샘플, Nyquist 여유와 잔차를 확인한다. 고조파/잡음/aliasing의 독립 검토도 필요하다.

```powershell
# 전압만: --calibration-* 두 인자를 생략
.\.venv\Scripts\python.exe -m analysis.scope_tone normalized_cw.csv --metadata cw.json --out new_voltage_result
# 전체 오프라인 합성 리허설; 실제 장비 명령을 보내지 않는다
.\.venv\Scripts\python.exe -m tests.rehearse_workflow --out tests/results/new_rehearsal
```

전류가 필요하면 `--calibration-s2p`와 `--calibration-metadata`를 함께 준다. 같은 head/revision·교정 ID·체인 순서, 검증된 동일 50 Ω 출력 기준면, 해당 주파수/개체/CH/설정의 receiver gain 및 부하 검증을 요구한다. 종합 불확도는 UNASSESSED로 유지한다. 파형 clipping/과부하·1 MΩ·이중 종단·10×·sweep·체인 중복 보정·어댑터 제거·미검증 교정은 거부한다.

출력은 새 디렉터리의 `tone_result.json`, 원시 입력/메타데이터/분석 코드 해시를 담은 `manifest.json`이다. 실제 측정·합성 데이터를 혼용하지 않는다. 증거 문자열은 검토자 진술이며 코드가 실물 증거의 진위를 확인하지 않는다.

수신기 gain 정의와 설정별 필드, BNC 교정 경로, 명령 예시 및 실행 결과는 [전체 절차 검토](../docs/END_TO_END_REHEARSAL.md) 3~6절을 따른다. [추가 자동시험](../tests/test_scope_tone.py)은 전류 복원·고조파/단위 오류·설정 불일치와 출력 보존을 검증한다.
