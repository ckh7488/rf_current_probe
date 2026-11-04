# 조립 → VNA → 오실로스코프 연결·환산 절차

**9/28 후속 국부 보강(DEC-063): 다음 제작 검토본은 Head A04 SMA R2 + Fixture A03 SMA R2 + A17/C10이다.** C09 가이드 뒤 받침과R2.5/R0.75 뿌리만 보강해 프레임 P06 한 종류 두 개를 변경했다. 같은27.5 MPa 기준에서 최대24.084 MPa, 저장 CAD·가동/공구·재생성 검사를 통과했다(CALCULATED/SIMULATED). 재질·총15종20개·체결품은 유지한다. [수정·검증 기록](../reviews/c10_guide_fix_20260928/REPORT.md), [현재 파일 선택](3D_PRINT_RELEASE_A17_C10.md). 아래 A16/C09 동결·HOLD·제작 선택은 이전 버전 이력이며 원본 판정은 소급 변경하지 않는다. 실물/RF T01–T12는 미검증, 업체 제출·생산승인 전이다. 현재 후보 확인: `python reviews/c10_guide_fix_20260928/verify_candidate.py --mutations`.

**9/28 연결 오류 수정:** 로드 반사 단계5a의 수–수 접속 오류를 바로잡았다. [검수](../reviews/full_reinspection_20260928/REPORT.md) · [인수·측정 계획](../reviews/full_reinspection_20260928/ACCEPTANCE_PLAN.md). 보유 교정키트의 실제 성별·모델은 첫 벤치에서 확인한다. 공개/로컬 로드 기준면 UI는 DEC-058에서 동기화했다. 제작 파일은 [R2+A16 인계](../reviews/fresh_system_audit_20260928/BUILD_CONFIGURATION.md)를 따른다.

2026-09-28 갱신. Head A04 SMA R2 / A16·C09. **실물 연결·측정 미실행.** 교정지그는 Fixture A03이며 출력 포트 기준으로 교정한다([DEC-053](DECISIONS.md)). F-A는 연결도의 일반 지그 별칭이다. 6절의 합성 실행 기록은2026-09-16 이력이며 현재 기구 검증과 구분한다. 구형 A0.1 비교표는 [원문 보존본](../reviews/document_full_audit_20260922/before/docs/END_TO_END_REHEARSAL.md)에 있다.

> **초안 — 실물 도착 후 시험별 문서로 다시 작성한다([DEC-055](DECISIONS.md)).** 스코프 쪽은 BNC 어댑터(R07) 없이 LibreVNA CW 출력으로 응답을 확인한다(3.2절). 기본 출력 연결은 맨 프로브이며 첫 측정은 R05 10 dB로 최대값을 확인한다(강력 권고).

## 2. 사람 대신 순서대로 해 본 연결 리허설

기호: **M=male(수), F=female(암), 모두 표준 극성 50 Ω 부품 요구**. RP-SMA·75 Ω BNC는 대체품으로 사용하지 않는다. 나사/바요넷 외형만 보고 중심 접점의 성별을 판단하지 않는다.

`CAB-P1/P2`는 보유 SMA 수–수 케이블 1개와 신규 CAB-02 1개의 개체 ID다. `PRIMARY-LOAD`와 `HEAD-LOAD`는 종단 위치의 역할 이름이다. RF OFF 후 외장 SMA 수 50 Ω 로드 1개를 헤드에서 F-A.OUT로 옮겨 재사용할 수 있으며 같은 개체 ID를 기록한다. `ATT`(R05)는 첫 측정·착탈·전원 투입용이며 실제 ID를 기록한다. 대상 하네스에는 별도 보호부가 없다(DEC-055).

| 단계 | 손으로 할 일 / 연결 | 진행 조건과 남길 파일 |
|---|---|---|
| 0. 제작 전 | 실물 코어·선경·PCB stack-up·출력 공차 확인 → 시험편 → 하우징 → 권선·납땜 | [G3 조립 순서](G3_PROTOTYPE_PACKAGE.md). 접합면/권선 사진, 홀 시험편 결과. 기구는 출력 전 상태 |
| 1. 조립/T01 | [A16/C09 현행 조립 절차 및 PCB 납땜 순서](G3_PROTOTYPE_PACKAGE.md) | SMA 선납땜 → PCB 장착·M2×12 → 권선 납땜 → 아래 고정바. 실제 도통·공차 확인 |
| 2. VNA 기준면 | `P1(F)—CAB-P1(M/M)` 및 `P2(F)—CAB-P2(M/M)` 끝에 female SOL. 두 끝 사이 female–female THRU | 표준별 ID/모델/방향·GUI/HW/FW·교정 파일·기준면 사진. 검증용 부하/THRU 재접속 확인. 값 없는 THRU를 이상적인 길이 0으로 입력하지 않음 |
| 3. 지그 through | `P1—CAB-P1—F-A.IN(F) → 중심 도체 → F-A.OUT(F)—CAB-P2—P2` | **F-A.OUT에 별도 부하 없음**: P2가 일차 종단. `fixture_through_empty.s2p` |
| 4. 삽입 영향 | 3과 동일 + 헤드 장착, `HEAD.OUT(F)—HEAD-LOAD(M)` | 출력 연결 상태 고정. `fixture_through_head_loaded.s2p`. A16의 공통 상부 구조를 분리해 지그를 넣은 뒤 닫음 |
| 5. 헤드 전달 | RF OFF → CAB-P2를 F-A.OUT에서 분리 → HEAD-LOAD를 헤드에서 빼 F-A.OUT에 PRIMARY-LOAD로 옮김 → `HEAD.OUT—CAB-P2—P2` | 소스가 켜지기 전에 두 종단 확인. `probe_transfer_5t_Lm30.s2p`. 일차/헤드 각각 단일 50 Ω. 4와 5 사이에 지그·헤드·CAB-P1을 건드리지 않음 |
| 5a. 로드 반사 | RF OFF → 같은 SMA 수 PRIMARY-LOAD를 **별도로 교정된 SMA 암 기준면**에 연결. 예: VNA 암 포트를 male SOL/실제 표준 모델로1포트 교정 후 직접 연결 | `primary_load_s11.s1p`. ΓL 기준면·별도 교정 ID 저장. CAB-P2 끝도 수이므로 직접 접속 불가. F/F 어댑터만 추가하고 기존 교정 유지 금지 |
| 5b. 역방향 | 지그 J1/J2를 바꿔 3–5 반복 | `*_reverse`. 정/역방향 ZT의 일관성 확인; 공통 K 오차의 독립 검증과 구분 |
| 6. 품질 확인 | 동일 배치에서 레벨·개폐·위치·상쇄·직접 픽업 대조 | T04~T08, [벤치 표](G2_BENCH_PROCEDURE.md). 모델/품질 미입증이면 상대 S21만 |
| 7. 스코프 체인 응답 | RF OFF → `P1(F)—CAB-01(SMA-M/BNC-M)—SCOPE.CH1(BNC-F, 내부 50 Ω)`, P1만 CW 출력. 기준 레벨은 같은 설정에서 `P1—CAB-P1—P2`로 확인 | 1/10/30/100/300/500 MHz의 표시 기본파 V ÷ 기준 V = `gain_receiver(f)`: `scope_chain_cw.csv`. ATT를 쓸 때는 ATT만 VNA로 S21을 따로 잰다. 감쇠기 직접 체결 공간 미확인 |
| 8. 스코프 전압 관측 | RF OFF → VNA P2 쪽 분리 → `HEAD—ATT—CAB-01—SCOPE.CH1(BNC-F, 내부 50 Ω)` | 기본은 `HEAD—CAB-01—CH1`, 첫 측정은 `HEAD—ATT—CAB-01—CH1`. 소스는 아래 4절 CW. 기본 결과는 전압·기본파·시간 관측 |
| 9. 전류 환산 | 동일 헤드/리비전·체인·유효 ZT·7단계 스코프 체인 응답 대조 | 조건이 모두 충족된 **단일 주파수 성분**만 A RMS. 조건 불일치 시 분석기가 거부 |
| 10. 현장 전 | T11 보호·삽입/링크 영향·필요 DC 바이어스 검증 및 승인 | 현장 외부 에너지가 있는 DUT를 위 수동 벤치 절차에 곧바로 연결하지 않음 |
| 11. 현장 후 | 동일 기준 지그/체인으로 T12 재확인 | 변화 시 이전/이후 데이터를 분리하고 해당 교정 유효성 재검토 |

**부하 위치를 혼동하지 않는다.** Through에서는 VNA P2가 일차 부하이고 헤드에는 별도 부하가 있다. Transfer에서는 외장 PRIMARY-LOAD가 일차 부하이고 VNA P2가 헤드 부하다. 스코프에서는 CH1 내부 50 Ω가 헤드 부하이며 외부 feed-through를 병렬로 추가하지 않는다.

F-A는 실제 사용할 지그, 즉 Fixture A03를 가리킨다. 중심 SIG만 코어 안을 지나고 귀환은 밖으로 흐른다. 빈 지그 S11은 300 MHz 이상에서 커지지만 교정은 4단계 through의 출력 S21을 코어 전류 기준으로 쓰는 백서 11.6 식으로 한다. A03 출력 포트 기준으로 1–500 MHz 보정을 수행한다. 300 MHz에서 일괄 제한하지 않고 주파수별 보정값·불확도·유효성을 기록한다. Fixture A04/A05는 이력이다.

## 3. VNA 교정에서 스코프로 넘기는 과정

### 3.1 처음 가능한 것

동일한 SMA 케이블 끝에서 교정한 뒤 헤드/지그를 교체해 측정할 수 있다. 케이블 끝이라는 전기적 기준면이 유지되고 교정이 유효하면 **접속 대상이 바뀌었다는 이유만으로 반드시 새 SOLT를 할 필요는 없다**. 대신 setup/measurement ID와 접속 위치를 구분하고 재접속 검증을 한다. 케이블·어댑터·레벨·주파수 범위가 바뀌면 교정 유효성을 다시 확인한다.

`F-A.IN`의 S11이 좋거나 나쁘다는 사실만으로 `Icore`가 정해지지는 않는다. 현행 기준은 4단계 through의 출력 S21로 코어 전류를 정하고 로드 ΓL과 모델 보정 K를 적용하는 출력 포트 기준이다(백서 11.6). 기존 matched/input_current/HI 조건도 그대로 둔다. 출력 기준 모드는 2026-09-28 공식 파일 입력과 CW 경로에 구현하고 합성 시험을 마쳤다([절차](../analysis/OUTPUT_REFERENCE.md), DEC-058). 역방향 일치·직접 픽업·깊은 null·실제 K 적용성·불확도 조건이 확인되기 전에는 상대 응답으로 저장하고 A를 표시하지 않는다.

### 3.2 스코프 체인 응답 — LibreVNA CW로 확인 (DEC-055)

VNA 교정으로 얻은 ZT는 헤드 SMA까지다. 그 뒤의 R06 케이블(CAB-01)과 스코프 입력은 한 덩어리로 CW 신호를 넣어 잰다. BNC 교정키트나 BNC–SMA 어댑터(R07)는 쓰지 않는다.

1. LibreVNA를 Signal Generator 모드, P1만 출력으로 둔다. 같은 주파수·레벨에서 `P1—CAB-P1—P2`로 기준 레벨을 먼저 확인해 기록한다.
2. RF OFF → `P1—CAB-01—SCOPE.CH1(내부 50 Ω)`로 바꾼다. 1/10/30/100/300/500 MHz에서 표시 기본파 V를 기준 V로 나눈 `gain_receiver(f)`를 `scope_chain_cw.csv`에 남긴다. 수직 범위·대역·샘플링 설정을 함께 기록한다.
3. R05 감쇠기를 넣는 체인은 감쇠기만 VNA로 S21을 따로 재서 곱한다.

이 확인의 절대 정확도는 LibreVNA 레벨 정확도 안으로 한정하고 불확도에 넣는다. 프로브 ZT를 이 경로로 다시 검증하지 않는다(순환 계산 금지 유지).

VNA에서의 이상적 50 Ω 출력과 실제 스코프의 입력은 정확히 같지 않다. 이후에도 스코프의 주파수별 전압 응답과 부하 차이가 남는다. `output_reference_plane`만 채웠다고 스코프 교정이 완료되지는 않는다.

## 4. CW 발생 및 MSO4054 설정

1. 원 MSO4054 명판/일련번호/FW 확인, 예열·SPC 조건 확인. 모델이 다르면 해당 매뉴얼로 갱신한다.
2. VNA sweep 데이터를 먼저 저장한다. **RF OFF → 8단계 재배선 → CW/Signal Generator mode → P1만 선택 → 낮은 레벨 시작**. P2가 번갈아 송신하는 sweep을 시간 관측 소스로 사용하지 않는다. 모드 전환 후 주파수·출력 포트·레벨을 다시 읽어 기록한다.
3. 우선 1 MHz, 10 MHz에서 안정적인 파형과 기본파를 확인하고 30/100 MHz로 진행한다. 200/300 MHz는 지그/교정·샘플링·감도 조건이 통과한 뒤 확장한다. 명목 −30 dBm은 시작 설정안이며 실제 코어 전류의 표준값이 아니다.
4. CH1의 **DC coupling, 내부 50 Ω, FULL, Voltage probe, Attenuation 1×**를 실제 화면에서 확인한다. 외부 감쇠기는 전체 체인 ZT에 포함하므로 스코프에서 다시 10× 등을 적용하지 않는다. 10 dB와 10×는 같은 값이 아니다. AC coupling을 선택하면 이 장비의 입력은 1 MΩ가 된다.
5. 처음에는 5 mV/div 이상에서 시작하고 clipping 없이 감도를 조절한다. 수직 범위를 바꾸면 실제 대역과 수신기 응답의 적용 조건도 바뀐다. 1~1.99 mV/div의 200 MHz 대역으로 300 MHz를 검증하지 않는다. 화면을 키우는 것과 SNR이 좋아지는 것은 별개다.
6. Sample 모드로 시작하고 임의 averaging/HiRes/Peak Detect를 끈다. tone 주파수, 실제 sample rate/record length를 기록한다. 분석기 기본 3고조파 fit에는 `3 f0 < 0.45 fs`, 최소 128점·20주기가 필요하다. 이것만으로 아날로그 대역 밖 성분의 aliasing이 없다고 증명되지는 않는다.
7. 안정적인 edge trigger를 잡고 원 파형/설정/스크린샷을 저장한다. 소스 OFF 잡음, 레벨 변화, clipping/overload와 샘플링 변경 시 기본파 재현성을 확인한다. 불안정 주파수·진폭이면 CW 환산을 진행하지 않는다.

LibreVNA 공식 매뉴얼은 발생기 모드의 출력 레벨 정확도와 고조파 한계를 밝힌다. 유지보수자는 2025년 설명에서 25 MHz 부근의 소스 전환과 필터 차이도 설명했다. **보유 HW/FW의 파형은 실제로 확인**하며, 이번 절차는 펌웨어 변경을 요구하지 않는다. 전체 RMS에 고조파/DC/잡음이 들어 있으므로 기본파 전류에는 기본파 RMS만 쓴다.

출처: [LibreVNA 매뉴얼](https://github.com/jankae/LibreVNA/blob/master/Documentation/UserManual/manual.tex), [유지보수자 설명 #309](https://github.com/jankae/LibreVNA/discussions/309), [MSO/DPO4000 사용자 매뉴얼 071-2121-04](https://download.tek.com/manual/071212104web.pdf) 본문 86~89쪽, [원 MSO4054 사양 077-0247-01](https://download.tek.com/manual/077024701Rev_A_web.pdf). 조회 2026-09-16. 실제 장비 버전 적용 여부는 미확인이다.

## 5. 파형 파일 → 기본파 → 조건부 전류

### 입력 파일과 전압 분석

원시 Tek 파일을 보존한 뒤 별도 파일에 **`time_s,voltage_v` 두 열**로 정규화한다. 시간은 초, 전압은 Voltage/1× 설정의 표시 V다. 원시 헤더·시간 간격·전압 단위·Probe factor와 결과를 대조하고 변환 스크립트/스케일 근거를 `normalization_evidence`에 남긴다. Tek 고유 CSV에는 헤더/다른 열이 있을 수 있어 이번 코드가 자동 추측하지 않는다. 실제 장비 내보내기 파일은 아직 없다.

[scope_metadata_template.json](../analysis/scope_metadata_template.json)에 설정과 실제 관찰을 기록한다. 미기입 양식은 거부되는 것이 정상이다. [scope_tone.py](../analysis/scope_tone.py)는 DC 및 기본파/고조파를 동시에 최소제곱으로 맞추고 `hypot(sin 계수, cos 계수)/√2`로 각 성분 RMS를 구한다. 비정수 주기 기록을 지원한다. FFT 피크·dBm·V/√Hz·전체 RMS를 입력하는 도구가 아니다.

```powershell
# 경로는 실제 파일로 대체한다. 출력은 새 디렉터리여야 한다.
.\.venv\Scripts\python.exe -m analysis.scope_tone normalized_cw.csv --metadata cw.json --out measurements/processed/run01_voltage
```

교정 파일을 지정하지 않으면 **VOLTAGE_ONLY**, `current_rms_a=null`을 출력한다. 잡음/aliasing/안정성 검토 없이 코드 실행만으로 신뢰할 전압 측정이라고 표시하지 않는다. 잔차/기본파 비율 0.1은 소프트웨어의 초기 불일치 검사이며 정확도 등급이나 SNR 인증이 아니다.

### A로 환산할 때 추가로 필요한 것

1. 기존 S2P·메타데이터의 전류 모델/품질/유효 대역 통과.
2. 실제 head ID/리비전, 교정 ID, 순서 있는 체인 ID 및 출력 기준면 일치. 체인에 들어간 ATT·CAB-01을 빼놓고 ID만 숨기지 않는다.
3. `receiver_response`: 해당 개체/CH/수직 범위/offset/입력/대역/샘플링/체인/주파수/온도에서 **표시 V ÷ 교정된 50 Ω 기준 V**인 gain과 검증 증거. `loading_verified`에는 프로브 체인이 실제 스코프를 구동할 때 부하 차이의 영향도 포함한다.

수신기 응답은 3.2절 CW 방식으로 CAB-01 BNC 끝에서 확인하고, 기준 레벨의 불확도(LibreVNA 레벨 정확도)를 함께 기록한다. 별도 저임피던스 발생기로 얻은 gain만으로 프로브의 출력 임피던스와 스코프 입력 반사 영향을 검증했다고 하지 않는다. 필요하면 출력 S22/스코프 입력 반사 및 오차 예산을 검토한다. **프로브 교정값과 명목 LibreVNA dBm으로 서로를 검증하는 순환 계산은 금지**한다. 검증 장비/기준이 없으면 전압·상대 관측을 유지한다.

```powershell
.\.venv\Scripts\python.exe -m analysis.scope_tone normalized_cw.csv --metadata cw.json --calibration-s2p transfer_bnc.s2p --calibration-metadata transfer_bnc.json --out measurements/processed/run01_current
```

결과는 `I1,rms = V1,rms,display / gain_receiver / |ZT_chain(f0)|`. 전체 체인에 들어간 감쇠기를 또 보정하지 않는다. 수신기 gain은 한 주파수에서만 적용하며 자동 주파수 외삽을 하지 않는다. 종합 불확도는 자동 계산하지 않아 **UNASSESSED**로 남는다. 펄스 피크/광대역 전류 파형 복원은 이 기능의 범위 밖이다.

설정 필드 일치와 증거 문자열은 입력 오류를 막는 장치다. 실제 메타데이터를 사실대로 작성했는지 장비를 통해 검증해 주는 기능은 아니다.

## 6. 2026-09-16 합성 리허설 이력 — 기구 결과는 당시 A0.1 기준

재현 명령:

```powershell
.\.venv\Scripts\python.exe -m tests.rehearse_workflow --out tests/results/my_new_rehearsal
.\.venv\Scripts\python.exe -m pytest tests -q --junitxml=tests/results/my_new_tests.xml
# 현행 기구는 G3_PROTOTYPE_PACKAGE.md의 원본/검증 경로를 따른다.
```

저장 결과: [전체 실행 보고서](../tests/results/process_rehearsal_final_20260916/report.json), [선언한 연결표](../tests/results/process_rehearsal_final_20260916/connection_plan.json), [입력 S2P/파형/메타데이터](../tests/results/process_rehearsal_final_20260916/inputs), [조건부 기본파 환산](../tests/results/process_rehearsal_final_20260916/scope_current/tone_result.json), [CAD 접속 공간 검사](../mechanical/clamp_A01_DRAFT/connection_access_review.json).

- 기존 66개와 추가 44개를 포함한 [자동시험 110개](../tests/results/process_review_tests.xml) 통과.
- 연결 8종을 대조하고 기존 어댑터의 수–수 충돌을 거부: **9개 예상 결과 일치**.
- 합성 1/10/30/100 MHz에서 알려진 **1.000 mA RMS 기본파** 복원. 이상적 5 Ω 센서 + 10 dB 감쇠 + 수신기 gain 0.9, 3차 고조파 40% 및 DC offset 조건. 10 MHz 예에서 전체 파형 RMS를 잘못 쓰면 약 **1.1846 mA**, +18.46% 오류.
- 어댑터 제거, 기준면 불일치, 이중 50 Ω, 1 MΩ, 10×, sweep 소스, 감쇠 중복 보정, 미검증 수신기, 상대 교정, clipping의 **10가지 오류 시나리오를 거부**.
- CAD 공칭 형상과 가정한 플러그/지그 동 스트립 검사. F-A 귀환은 0~90° 샘플에서 간섭 없지만 110/115/120°에서 간섭. R6 mm 몸통이 낮게 내려오면 덮개와 교차 체적 10.804 mm³; 큰 몸통이 Z≥17 mm에 있으면 가정 검사상 간격 0.60 mm.

이는 **SYNTHETIC 수식/소프트웨어 시험 및 CALCULATED 공칭 형상 검사**다. 실제 코어의 대역·감도·정합, 기구 공차/강도, 장비 조작 성공이나 보호 성능의 시뮬레이션 결과가 아니다. PCB/기구 형상은 이번에 바꾸지 않았으므로 이전 ERC/DRC 결과를 새 실행으로 표시하지 않는다.

## 7. 아직 진행을 막는 실물 조건과 다음 순서

1. 현행 부품 입고, 실제 케이블 주변 체결 공간, 장비·교정키트·부하/동축 개체 확인. [누적 확인 목록](OPEN_DECISIONS.md)을 유지한다.
2. Fixture A03의 커넥터·A14 장착 조건·부하를 기록 → T01 → through·전달·로드 S11·역방향. S11은 기록하되 합격 조건으로 쓰지 않고, S21 null·반복성·정/역방향 일치를 판정한다.
3. 5턴 전달 S21·반복성·누설 → 출력 기준 ZT와 K 실물 확인 → 스코프 체인 CW 응답 확인. 절대 교정 기준을 마련하지 못하면 상대 노이즈 비교로 범위를 명시한다.
4. 현장 전에 보호/삽입 영향과 **DC 합전류에 따른 감도 변화**를 확인한다. 저전압·전류 제한 벤치에서 적용할 DC 범위/실험 배선을 먼저 정하고, DC=0 기준과 RF 응답/복귀를 비교한다. RF-only는 DC 영향을 받지 않는다는 뜻이 아니다. 실제 범위는 아직 미정이다.
5. 시험별 문서는 실물 도착 후 작성한다. 목록은 [벤치 절차 8절](G2_BENCH_PROCEDURE.md)에 있다.
