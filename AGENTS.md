# RF Current Probe 에이전트 지침

## 처음 들어오면

1. [README](README.md)와 [현재 진행 상태](docs/CURRENT_READINESS.md)에서 작업 범위와 마지막 실물 관측을 확인한다. RF 프로브 교정과 Ethernet VNA 공통 보드 비교는 각각 이어갈 수 있다.
2. [제작과 입고 기준](docs/CURRENT_BUILD.md), [공개 해시 목록](release/design.sha256), [설치 BOM](release/assembly-bom.md)에서 PCB·CAD·출력품·수량을 식별한다. 기준은 Head A04 SMA R2, Fixture A03 SMA R2, B-RJ2 4종과 중앙 A19·나머지 A18/C10이다.
3. RF 프로브는 [출력 기준 분석](analysis/OUTPUT_REFERENCE.md)과 [벤치 절차](docs/G2_BENCH_PROCEDURE.md), B-RJ2는 [네 결선과 비교 절차](measurements/ethernet-vna/README.md)와 [예측 보존 묶음](selected-evidence/ethernet-vna-prediction-v1/README.md)을 따른다. [문서 색인](docs/DOCUMENT_INDEX.md)에서 관련 이력을 찾는다.

## 임무와 고정 원칙

산업용 Ethernet/24 V 하네스의 간헐 장애 진단을 위한 수동 범용 RF 전류 프로브다. 코어+권선 → 헤드 PCB → SMA → 정의된 50 Ω 측정 체인을 사용한다. ADC/MCU/GUI/PHY/RJ45 종합 인증 기능을 추가하지 않는다.

- 5턴 기본·3턴 선택(7턴 제외), 공칭 26 mm 구경. 선정값을 실물 유효 구경·대역 보장으로 쓰지 않는다. Fair-Rite 2644181281 반쪽 2개가 한 쌍이다.
- 현행 교정은 A03 출력 포트 기준([백서](docs/RF_CURRENT_PROBE_WHITEPAPER.md) 11.6), 1–500 MHz 특성화다. 첫 실측 확인은 1–150 MHz부터 진행한다. 300 MHz 일괄 제한이나 빈 지그 S11≤−20 dB 조건을 추가하지 않는다.
- 지그의 중심 전류는 코어 안, 귀환은 코어 밖을 지난다. `ZT≈50×S21`과 `1−S11`은 각각 정합·기준면·전류 경로 조건을 검토한 경우만 적용한다. 출력 기준은 ΓL·K·정/역방향·직접 픽업·깊은 null 조건을 확인한 구간만 절대 ZT로 표시한다.
- 수신기 쪽 단일 50 Ω 종단. 임의 헤드 이중종단 금지. 차폐·나사·GND가 만드는 단락턴, 삽입 영향과 반복성을 검토한다.
- 전체 도체군 합전류가 작아도 내부 CM 스트레스를 배제하지 않는다. 보호접지 제거·쉴드 임의 절단·고전압 직접 적용 금지.
- 새 현장·케이블의 첫 관측은 10 dB 감쇠기를 넣어 최대값을 확인한다(DEC-055). 대역·오차 목표는 백서 14.5를 사용한다.

## 근거와 변경

실제 CAD·기록·원시 출력·해시를 확인한다. CALCULATED, SIMULATED, SYNTHETIC, MEASURED와 실물 사용 관측을 구분한다. 시험 환경·리비전·개체·조건을 기록하고 원본 및 실패 구간을 보존한다. 과거 해시와 업체 상태는 당시 기록으로 보존한다.

코드나 분석을 바꾸면 [README의 공개본 검증 명령](README.md#git만으로-확인할-수-있는-것)에서 관련 시험을 실행한다. 설계 변경은 [DECISIONS](docs/DECISIONS.md)에 이유·영향·재시험을 남긴다. 하위 리비전 CAD가 생성기의 입력으로 쓰일 수 있으므로 이동·삭제 전에 참조를 조사한다.

RF 실물 작업은 [도통과 클램프 상태](docs/CURRENT_READINESS.md#실물-조립과-도통)를 확인해 이미 완료한 단계부터 이어간다. B-RJ2 실측은 별도 세션에 추가하고 사전 예측은 원래 값으로 보존한다. 구매나 현장 작업은 사용자 승인 범위에서 진행한다. 진행 상태를 갱신할 때는 완료 범위, 실제 검증 명령과 결과, 필요한 다음 증거를 함께 남긴다.
