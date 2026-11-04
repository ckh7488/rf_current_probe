# 출력 포트 기준 분석 — 2026-09-28

백서 11.6의 현행 A03 교정식을 `rfcp`와 `scope_tone`의 공식 파일 입력 경로에 구현했다. 실측 데이터는 아직 없다. 아래 예제·시험·불확도·판정 한계는 모두 **SYNTHETIC**이며 실제 장비의 교정값이나 허용 기준이 아니다.

## 실행 가능한 예제

저장소 루트에서 새 디렉터리 이름으로 실행한다.

```powershell
.\.venv\Scripts\python.exe -m analysis.synthetic_output_reference --out tests/results/my_output_inputs
.\.venv\Scripts\python.exe -m analysis.rfcp tests/results/my_output_inputs/forward_transfer.s2p --metadata tests/results/my_output_inputs/metadata.json --out tests/results/my_output_result
```

첫 명령은 1–500 MHz 합성 원시 파일 묶음을 만들며, 두 번째는 실제 분석 명령이다. 생성기의 파동 경계조건 선형 연립방정식으로 정한 코어 전류와 알려진 ZT를 이용해 입력을 만든다. `expected.json`은 정답 비교용이며 분석기는 읽지 않는다. 입력·기존 결과를 덮어쓰지 않는다.

`zt.csv`에는 주파수별 복소 ZT(Ω), 크기, 위상, 유효 여부, 검토된 불확도(dB)와 제외 사유가 남는다. `response.png`는 상대 S21과 유효 ZT를 표시한다. `manifest.json`에는 메타데이터, 실제 읽은 모든 파일의 SHA-256, 분석 코드 해시·버전이 남는다. CW 분석도 같은 파일 묶음을 읽으며 스코프 응답·부하·기준면을 별도로 검증해야 한다. CW 종합 불확도는 아직 자동 합성하지 않으며 UNASSESSED로 남는다.

## 실측 파일 구성

1. [벤치 절차](../docs/G2_BENCH_PROCEDURE.md)에 따라 원시 자료와 교정 원본·배치 사진을 보존한다. 정방향과 역방향 각각 **헤드 장착 through S2P + 프로브 전달 S2P**, 같은 외장 로드의 S1P가 필요하다. 빈 지그 S2P는 진단용이며 장착 through를 대체하지 않는다.
2. [공통 양식](metadata_template.json)에 실제 개체·리비전·장비·주파수·턴수·체인·측정 조건을 기록한다. `current_model`을 `{"mode":"output_reference","bundle_file":"bundle.json","evidence":"검토 문서 경로"}`로 정하고 `fixture_revision`, `configuration_id`, `primary_load_id`를 추가한다. `output_reference_plane`에는 `id`, `verified`, `impedance_ohm:50`, `evidence`가 필요하다.
3. [묶음 양식](output_reference_bundle_template.json)의 UNKNOWN/빈 값/false를 실제 검토 근거로 채운다. 상대 파일 경로는 **bundle.json이 있는 폴더 기준**이다. `sha256`는 해당 원본 바이트의 해시다. PowerShell `Get-FileHash -Algorithm SHA256 파일`로 확인한다. 실측 획득 파일·review는 MEASURED, K는 그 원본에 따라 CALCULATED/SIMULATED/MEASURED로 구분한다. SYNTHETIC 파일을 실측으로 재표기하지 않는다.
4. 정/역방향별 복소 K CSV와 주파수별 검토 CSV를 준비한다. 예제의 숫자·true·불확도를 복사해 실측 근거로 쓰지 않는다. 증거 문자열은 검토자 진술이며 프로그램이 사진이나 장비를 검사하지 않는다.

필수 원본 열:

```csv
frequency_hz,k_real,k_imag,valid
```

K는 무차원 **Icore/Iout**이며 식에서 나눈다. A03 빈 지그 시뮬레이션을 실제 장착 상태에 쓰려면 부하·리비전 적용성 근거가 필요하다. SMA R2처럼 PCB가 달라졌다면 새 리비전과 모델 원본 리비전을 따로 적고 `revision_change_assessed:true` 및 근거를 기록한다. 이 선언 자체가 R2의 RF 검증을 뜻하지 않는다.

```csv
frequency_hz,forward_through_snr_db,forward_transfer_snr_db,reverse_through_snr_db,reverse_transfer_snr_db,direct_pickup_db,repeatability_db,uncertainty_db,valid,current_path_verified,head_load_swap_verified,phase_verified
```

CSV의 boolean은 `true`/`false`로 쓴다. K와 검토 CSV는 양의 오름차순 Hz와 두 점 이상이 필요하다. 모든 수치는 유한해야 한다. 직접 픽업은 유효 프로브 신호 대비 대조 측정의 진폭비 dB, repeatability는 동일 조건 반복의 진폭 변동 폭 dB이다. 보정 후 진폭 불확도는 양의 dB 상한이며 평가 전에는 빈 칸으로 둔다. VNA·로드 반사·K 공통 모델 오차·헤드 부하 교환·반복성·위치·직접 픽업을 포함한 합성 방법과 근거를 별도 문서로 기록한다. 정/역방향 일치만으로 K 공통 오차가 사라지지 않는다.

## 기준면·배치

- 각 방향의 `identity`는 주 메타데이터의 헤드·지그 ID/리비전, configuration, 턴수, 차폐, 체인 순서, 로드 ID와 일치해야 한다. through/transfer의 setup·2포트 교정 ID·포트 기준면도 일치시킨다.
- **로드는 SMA 수형이다.** 별도 SOL 교정한 SMA 암 포트에 직접 연결한다. 보유 수형 OPEN/SHORT/LOAD 표준의 모델을 먼저 확인한다. 케이블 수 끝과 수 로드는 결합되지 않으며 F/F 어댑터만 추가해 이전 교정을 그대로 쓰지 않는다. 작업용 로드와 교정 LOAD 표준을 구분한다.
- 로드 S1P는 2포트 획득과 별도의 1포트 교정 ID를 요구한다. 물리 P2를 썼다면 S22를 1포트로 내보낸다(S1P 내부 표기는 S11). 암 포트 기준면이 지그 출력의 동일한 SMA 결합면에 적용되는 근거를 `reference_plane_transfer_evidence`에 기록한다. 연장선·어댑터 영향은 자동 제거하지 않는다.
- `polarity`는 정방향 +1, 역방향은 실제 코어 전류 방향·권선 극성에 따라 ±1이다. 위상을 검증할 때 방향 반전 부호를 반영한다.
- `reflection_phase_validated`와 로드의 `phase_validated`는 S22·ΓL 복소 반사 보정의 근거다. 하나라도 미확인일 때 크기 ZT도 차단한다. 반사 위상은 확인했지만 체인 전체의 절대 위상을 검증하지 못했다면 주 `phase_validated:false`로 크기만 출력한다. 위상·복소 ZT 열은 비운다.

## 주파수별 판정

`alignment.method=exact`가 기본이다. 파일 주파수 그리드가 다르면 일치하는 점만 평가한다. 필요하면 `linear_complex`와 `maximum_gap_hz`, 보간 검토 근거를 명시한다. 복소수는 실수부·허수부 선형 보간이며 외삽하지 않는다. 명시한 유효 대역 경계·무효 대역·최대 간격·무효 원본 샘플을 건너뛰지 않는다. 검토 항목은 양끝 모두 통과해야 하고 SNR은 작은 값, 픽업·반복성·불확도는 큰 값을 사용한다. 촘촘하지 않은 데이터 사이의 숨은 공진을 코드가 발견할 수는 없다.

한계값은 null 회피용 through·K·1−ΓL·1−S22ΓL의 최소 크기, 최소 SNR, 최대 직접 픽업·반복성, 정/역방향 크기·위상 차이다. 예제 한계값은 실물 합격 기준이 아니다. 실제 장비·측정과 불확도 목표에 맞는 근거를 기록해야 한다.

기준면/ID/해시/단위 불일치는 실행을 거부한다. null, 수동 로드 조건 위반, clipping, 미평가 불확도, 품질·전류 경로·헤드 부하 교환·정/역방향 불일치 구간은 `valid=false`, 절대 ZT 모든 열은 빈 값으로 남긴다. 진단 S21과 제외 사유는 보존한다. 300 MHz 일괄 제한이나 빈 지그 S11 ≤ −20 dB 조건은 넣지 않았다.

검토 자료: [구현·시험 기록](../reviews/output_reference_20260928/REPORT.md), [자동시험](../tests/test_output_reference.py). 실물의 교정 완료·유효 대역·정확도·펄스 파형 복원은 이 소프트웨어 검증 범위 밖이다.
