"""Update the review draft for the PCB fixture and link the interactive report."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]
doc=ROOT/'docs/ATLAS_CURRENT_PROBE_DRAFT.md'
history=ROOT/'docs/history/ATLAS_CURRENT_PROBE_DRAFT_v0.1.md'
if not history.exists(): shutil.copy2(doc,history)
text=history.read_text(encoding='utf-8')
text=text.replace('Atlas 등록 전 검토 초안 v0.1','PCB 교정지그 반영 v0.2 · Atlas 게시용')
intro='''
**PCB 지그 반영:** 동판·동띠의 금속 가공을 줄이기 위해 Frame PCB 1장과 EndPanel PCB 2장으로 교정지그를 바꾸는 초안을 반영했다. 무가공 조립·RF 성능·새 견적은 검증 전이다. 이전 동판 지그 그림과 구매 상태는 과거 기록으로 읽는다.

**[Atlas에서 그림과 단계별 연결 보기](https://ckh7488.github.io/showcase/reports/rf-current-probe/)** · [로컬 HTML](C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe/index.html)
'''
text=text.replace('## 1. 왜 만드는가',intro+'\n## 1. 왜 만드는가')
start=text.index('## 5. 교정지그를 함께 만드는 이유')
end=text.index('## 6. 지금까지 완료한 작업과 증거')
section='''## 5. PCB 교정지그와 캘리브레이션

프로브 출력 전압을 전류로 바꾸려면 **코어 안의 전류와 출력의 관계**를 알아야 한다. 교정지그는 전류 경로를 통제하고 그 관계를 조사하는 실험 장치다. VNA의 케이블 교정과 프로브의 전류 감도 교정은 별도 단계다.

### 동판에서 PCB로 바꾸는 부분

기존 F-A는 동판·동띠 절단과 홀 가공이 필요했다. 새 PCB A0.1 초안은 **Frame 1장 + 같은 EndPanel 2장**으로 이 부분을 대체한다. 납땜·나사 조립을 중심으로 하되, 권선 감기·피복 제거·간단한 패드 재단은 남는다. 사용자에게 금속 절단·드릴·줄질을 요구하지 않는 방향이다. 실제 출력 공차와 끼움은 아직 확인 전이다.

![새 PCB 교정지그 조립 CAD](E:/Current_Probe/hardware/calibration_fixture_PCB_A01/assembly/assembly_preview.png)

*새 PCB 지그와 집게 A0.3의 저장 CAD 이미지다. 금색 중앙 신호 경로만 코어 안을 지나고, 양옆 귀환은 밖으로 돌아간다. 실물 사진이나 RF 검증 결과가 아니다.*

| 부품 | 현재 설계값 | 연결 역할 |
|---|---|---|
| Frame × 1 | 118×65×1.0 mm, 중앙 다리 폭 8 mm | 양면 SIG 동박을 중앙에, 귀환 레일을 양옆에 배치 |
| EndPanel × 2 | 128×24×1.0 mm, SMA 홀과 레일 슬롯 | 양옆 귀환을 서로 연결하고 SMA 외피로 복귀 |
| 짧은 연결선 | 실제 접점에 맞춰 조립·기록 | SMA 중심을 Frame SIG에 직접 연결. EndPanel GND와 분리 |

![PCB 신호와 귀환의 개념도](E:/Current_Probe/docs/atlas/review/pcb-current-path.png)

**중앙 다리의 앞·뒤 동박은 모두 SIG다.** 신호 바로 아래에 GND를 깔아 함께 코어를 통과시키면 왕복 전류가 상쇄될 수 있다. 귀환은 코어 밖의 양옆 레일을 사용한다. 그림은 전류 경로 설명용이며 제작 도면을 대신하지 않는다.

### 네 단계로 연결하기

P1은 신호를 보내는 포트, P2는 신호를 받는 50 Ω 포트다. 아래 연결을 바꾸기 전에는 항상 **RF OFF**, 재배선 후에는 일차와 프로브 출력의 종단을 확인한다.

| 단계 | P1 | P2 | 외장 50 Ω 부하 | 확인하는 것 |
|---|---|---|---|---|
| 0. VNA 교정 | 테스트 케이블 끝에서 O/S/L/T | 테스트 케이블 끝에서 O/S/L/T | 실제 교정 표준 Load를 순서대로 사용 | VNA·케이블의 측정 오차와 기준면 |
| 1. 지그만 | 지그 IN | 지그 OUT | 사용 안 함. P2가 일차 종단 | 지그 반사·손실·위상 |
| 2. 헤드 장착 | 지그 IN 그대로 | 지그 OUT 그대로 | 프로브 SMA 출력 | 헤드 장착이 일차 경로에 주는 영향 |
| 3. 프로브 전달 | 지그 IN 그대로 | **프로브 SMA 출력으로 이동** | **지그 OUT으로 이동** | 입력에 대한 프로브 출력의 상대 S21 |

0단계에서는 모델·성별이 맞는 Open/Short/Load를 각 케이블 끝에 순서대로 연결하고, 두 케이블 끝 사이의 Thru도 측정한다. 지원되는 전체 2포트 교정을 적용하고 검증용 부하·Thru를 재접속한다. 알 수 없는 어댑터를 길이 0의 Thru로 가정하지 않는다.

![VNA 기준면 교정](E:/Current_Probe/docs/atlas/review/step-0.png)

1단계는 헤드를 분리하고 지그만 측정한다. `fixture_through_empty.s2p`를 저장한다. 2단계는 헤드를 장착하고 출력을 외장 50 Ω로 종단해 `fixture_through_head_loaded.s2p`를 저장한다. 이때 P2는 계속 지그 OUT에 있다. 이 두 파일의 S21은 지그 전달 특성이다.

![지그 단독 측정](E:/Current_Probe/docs/atlas/review/step-1.png)

![헤드 장착 영향 측정](E:/Current_Probe/docs/atlas/review/step-2.png)

가장 중요한 전환은 **2 → 3**이다. RF를 끈 뒤 P2 케이블을 프로브로 옮기고, 프로브에 있던 외장 부하를 지그 OUT으로 옮긴다. 같은 부하 한 개를 재사용할 수 있다. 일차 회로와 권선 출력은 별도 경로이므로 각각 한 번씩 50 Ω로 종단한다. 한 출력에 50 Ω 두 개를 병렬로 붙이는 이중 종단이 아니다.

![프로브 전달 측정](E:/Current_Probe/docs/atlas/review/step-3.png)

3단계에서 `probe_transfer_5t_Lm30.s2p`와 같은 이름의 JSON을 저장한다. 헤드·지그·케이블·부하 ID, 교정 ID와 기준면, 턴 수·극성, 도체 위치, 레벨·주파수·IF BW·평균·온도·시각을 기록한다. 전류 모델 확인 전에는 `relative` 모드로 두고 ZT/A 값을 만들지 않는다.

시작 설정안은 **1~100 MHz / 1601점 linear / −30 dBm / IF BW 1 kHz / 평균 4회**다. 장비 지원값·정격·실제 선형 범위를 우선한다. 후속으로 레벨 변경, 최소 5회 재장착, 도체 위치, 왕복 상쇄, 직접 픽업·잡음을 비교한다. 실패 구간도 원시 파일로 보존한다.

### 언제 출력 전압을 전류로 바꾸는가

동일한 실수 50 Ω 기준 임피던스, 충분한 정합, 코어 전류를 입력 진행파로 근사할 수 있는 조건, 정리된 케이블·기준면과 50 Ω 출력 부하에서만 `|ZT| ≈ 50×|S21|`을 적용한다. `S21`은 dB가 아닌 선형 진폭비다. 예를 들어 −20 dB는 0.1이므로 ZT는 5 Ω이고, 이 조건의 5 mV RMS 정현파는 1 mA RMS에 해당한다. 이는 **설명용 계산**이지 이 PCB 지그의 실측 감도가 아니다.

좋은 S11만으로 코어 위치 전류를 입증할 수는 없다. `1−S11` 보정도 입력 기준면과 코어 위치 사이 전류 분기·지연이 정리된 모델에서만 사용한다. 조건을 입증하지 못하면 같은 지그·연결에서의 상대 응답으로 남긴다. 누설·잡음·선형성·반복성·위치 의존성이 검토되지 않은 주파수는 정량화하지 않는다.

### 스코프로 옮길 때

RF OFF 후 재배선하고 벤치 소스는 CW/P1만 활성화한다. 기본 연결은 `헤드 → 검증된 감쇠·보호 → SMA–BNC → 스코프 내부 50 Ω`다. 실제 MSO4054 모델·입력 상태 확인 후 DC coupling / Voltage 1× / FULL / Sample 설정안을 적용한다. 내부 50 Ω와 외장 50 Ω를 병렬로 쓰지 않는다.

먼저 **V 단위 원시 파형**을 저장한다. BNC 입력 위치까지의 교정, 같은 체인, 스코프 응답·부하가 확인된 단일 주파수 기본파 RMS만 전류로 환산한다. VNA용 어댑터를 빼면 교정 조건이 달라지고, VNA 교정은 스코프 내부 응답을 자동 보정하지 않는다. 펄스 피크를 임의의 한 ZT로 나누지 않는다.

자세한 실행 기록 양식은 [벤치 체크리스트](C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe/records/bench-checklist.md), 원칙과 한계는 [기존 벤치 절차](E:/Current_Probe/docs/G2_BENCH_PROCEDURE.md)와 [전체 연결 절차](E:/Current_Probe/docs/END_TO_END_REHEARSAL.md)를 따른다. 이전 동판 지그의 기구 검사·견적을 새 PCB 지그에 전용하지 않는다.

'''
text=text[:start]+section+text[end:]
text=text.replace('| 지그 F-A A0.1 | 전체 CAD·금속 도체 형상·인쇄 부품 4개, 공칭 간섭·저장 파일 검사 | RF 정합·코어 위치 전류·직접 누설 |','| 기존 동판 지그 F-A A0.1 | 과거 CAD·공칭 검사 기록. 금속 가공을 줄이기 위해 PCB 지그로 대체 중 | 새 PCB 지그의 RF 정합·조립·코어 위치 전류 |\n| 새 PCB 지그 A0.1 | Frame·EndPanel의 KiCad와 조립 CAD 초안. 5절의 구조·연결을 적용 | 실물 맞춤·RF 정합·직접 누설·교정 |')
text=text.replace('최신 전달 자료의 총액은 **966,349원**','PCB 지그 전환 전 전달 자료의 총액은 **966,349원**')
text=text.replace('현재 구매 전달본은 [구매안내 HTML]','이전 동판안의 구매 전달본은 [구매안내 HTML]')
text=text.replace('이 초안의 이미지와 근거 링크는 현재 작업 폴더를 가리킨다. Atlas에 실제 등록할 때 이미지 첨부와 내부 링크를 해당 환경에 맞게 옮길 수 있다.','이 Markdown은 작업용 원본이다. Atlas에는 PC 절대 경로·개인 구매 링크를 제외하고, 관련 그림·교정 체크리스트·원본 식별 기록을 포함한 별도 HTML 문서로 등록한다.')
text=text.replace('**문서 상태 해석:** 백서와 초기 선정 문서의 “아직 CAD 없음”, “캠 잠금 검토” 같은 표현은 당시의 상태다. 이 초안은 상세 설계에 PCB A0.2·집게 A0.3·지그 F-A A0.1을, 구매 준비에는 9월 17일 최종 검증 기록을 적용했다. 기존 원본과 과거 기록은 변경하지 않았다.','**문서 상태 해석:** 현재 헤드 PCB A0.2·집게 A0.3은 유지하고, 교정지그는 동판 F-A A0.1에서 PCB A0.1 초안으로 전환한다. 금속 가공 제외 지시와 PCB 원본을 반영했다. 기존 구매·기구 검증은 당시 이력이며 새 PCB 지그의 완료 근거가 아니다. 이전 설명서 v0.1은 history에 보존했다.')
doc.write_text(text,encoding='utf-8')
print('Updated documentation v0.2; v0.1 preserved.')
