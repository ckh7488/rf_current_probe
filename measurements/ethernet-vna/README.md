# B-RJ2 예측과 실측 비교

최종 보드 한 장의 네 연결을, 2026-11-17에 저장한 사전 예측과 비교합니다.
[예측 모델·설정·원시 파형](../../selected-evidence/ethernet-vna-prediction-v1/README.md) · [ATLAS의 모델과 결과](https://ckh7488.github.io/showcase/reports/ethernet-vna-fixture/)

## 측정 PC 준비

비교 도구는 Windows · Python 3.12.6 환경에서 확인했습니다.

```sh
git clone https://github.com/ckh7488/rf_current_probe.git
cd rf_current_probe
python -m pip install -r measurements/ethernet-vna/requirements.txt
python selected-evidence/ethernet-vna-prediction-v1/verify.py
```

실측 비교에는 Python 분석 패키지만 사용합니다. openEMS는 PCB를 다시 해석할 때 설치합니다.

## 네 연결

SMA 케이블 끝을 보정 기준면으로 정합니다. **1–200 MHz, 선형 1601점, 기준 50 Ω**로 크기와 위상이 있는 Touchstone을 저장합니다. RCT1–4·RSH1·CSH1은 모두 미실장입니다.

| 저장 파일 | VNA와 나머지 SMA | RJ45 |
| --- | --- | --- |
| `01_open_B_J3.s1p` | P1→J3/B, J2·J4·J5에 50 Ω | 외부 개방 |
| `02_open_D_to_C.s2p` | P1→J5/D, P2→J4/C, J2·J3에 50 Ω | 외부 개방 |
| `03_load_A_J2.s1p` | P1→J2/A, J3·J4·J5에 50 Ω | 흰주황(1)–100 Ω–주황(2) |
| `04_loop_D_to_C.s2p` | P1→J5/D, P2→J4/C, J2·J3에 50 Ω | 흰갈색(7)↔파랑(4), 갈색(8)↔흰파랑(5) |

반사 시험을 S2P로 저장했다면 같은 이름에서 확장자를 `.s2p`로 사용합니다. 루프백은 수신 VNA의 50 Ω이 발룬을 통해 종단을 만듭니다. 두 전달 페어에 별도 100 Ω 저항을 추가하지 않습니다. 다른 RJ45 도체는 외부 개방입니다.

제작 플러그의 핀 도통과 정합 플러그 양단 저항을 재서 기록합니다. 예측의 99.9 Ω은 [납땜 전 저항 단품 사진](../../selected-evidence/ethernet-vna-prediction-v1/provenance/resistor-dmm.jpg)의 표시입니다.

## 원본 저장과 비교

1. `measurements/raw/ethernet-vna/20261120-unit01/`처럼 새 세션 폴더를 만듭니다.
2. 위 Touchstone 파일을 넣습니다. 한 시험부터 비교해도 됩니다.
3. [receipt-template.json](receipt-template.json)을 같은 폴더의 `receipt.json`으로 복사하고 개체 ID·측정 시각·장비, 보정·출력·IFBW·평균과 실제 결선을 기록합니다.
4. 저장소 루트에서 실행합니다.

```sh
python measurements/ethernet-vna/compare.py 20261120-unit01
```

`measurements/processed/ethernet-vna/20261120-unit01/`에 크기 겹침 그림, 주파수별 크기·위상 차이 CSV, 원본 해시와 조건을 포함한 JSON이 생깁니다. 주파수는 저장된 예측의 1601점과 대조하며 보간하지 않습니다. 100 MHz 근처의 비교에는 실제 격자점인 100.0025 MHz를 명시합니다.

개방 결합의 1 MHz는 예측의 시간창 변동 표시를 함께 남기고, 시간창이 안정된 점들의 최대 차이를 별도로 계산합니다. 차이의 크기를 보여주며 합격 기준은 추가하지 않습니다.

원본과 조건, 비교 결과를 확인한 다음 해당 세션만 커밋합니다.

```sh
git add measurements/raw/ethernet-vna/20261120-unit01 measurements/processed/ethernet-vna/20261120-unit01
git commit -m "Add B-RJ2 unit01 VNA comparison"
git push
```

사전 예측 폴더는 그대로 두고 세션을 추가합니다. 공개 ATLAS의 실측 그래프는 검토한 비교 결과를 반영해 갱신합니다.
