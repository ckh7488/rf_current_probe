# RF 전류 프로브 측정 이관, 2026-10-27

압축을 **짧은 로컬 경로**에 전부 풀고 `START_HERE.html`을 연다. Windows에서는 `OPEN_GUIDE.cmd`도 된다. 그림·연결 목적·설정·저장 파일·문제 분리 순서가 들어 있다. HTML/그림은 인터넷 없이 열린다.

## 새 컴퓨터의 에이전트에게 붙여넣기

> 이 폴더의 AGENTS.md, CURRENT_STATE.json, AGENT_RUNBOOK.md와 START_HERE.html을 읽고 RF 전류 프로브 측정을 이어서 맡아줘. 먼저 권선의 마지막 보고가 3MΩ인 점을 해결하고 실제 숫자를 확인해줘. 클램프는 C04B 큰 축과 F12 주변 유격으로 사용 보류야. 직각 SMA는 보유 Samtec SMA-J-P-H-RA-TH1 2개를 사용하며, 1–150MHz 근사 모델 계산은 수정 후 수치 검증을 마쳤지만 실물 교정은 아직이야. 파일 확인·환경 준비·데이터 분석·에러 수정은 직접 계속하고, 내가 해야 하는 결선·납땜·장비 조작은 해당 연결 그림을 보여주며 목적, 연결할 두 단자, 설정, 저장할 파일, 확인할 숫자를 한 단계씩 안내해줘. 이미 끝낸 실물 작업은 확인 후 이어가고, 불확실한 값이나 true를 채워서 합격시키지 마. ΓL/K가 미확인이어도 가능한 상대 S21·반복성 측정은 계속해줘. 원래 공개 조립절차서와 제조 원본은 그대로 보존해줘.

## 시작 순서

1. `python verify_transfer.py`로 이관 무결성을 확인한다. Python 없이도 가이드는 열린다.
2. `python tools/session.py new`로 새 측정 세션과 미작성 양식을 만든다. 생성된 세션을 기록한다.
3. R00 DMM부터 실제 관측을 확인한다. 지난 대화의 “확인했어”보다 뒤에 보고된 **3MΩ**가 최신 상태다.
4. `software/LibreVNA-GUI_Windows-v1.6.5.zip`의 공식 배포본을 풀고 실제 HW/FW 호환을 확인한다. 이것을 최신 버전이라고 가정하거나 펌웨어를 자동 갱신하지 않는다.
5. Python 분석이 필요할 때 `tools/Setup-Analysis.ps1`을 실행한다. Windows x64 Python3.12 설치가 필요하며 동봉 wheelhouse로 오프라인 설치한다. `tools/Run-SelfTest.ps1`은 합성·소프트웨어 시험이며 장비를 제어하지 않는다.

## 내용과 범위

- `project/`: 현행 작업 트리·실제 CAD·제조파일·분석·시험·검토·새 SMA 원시 해석. 당시 상태 문구는 그 날짜의 이력이다. 이번 작업의 최신 실물 상태는 CURRENT_STATE가 우선한다.
- `images/`: 결선도 10장, 실제 A03 R2 동박 도면과 헤드 PCB 탐침 위치도 2장. 개념도는 실물 사진으로 표기하지 않았다.
- `templates/`, `tools/`: 빈 실측 양식·세션 생성/목록 점검·환경 준비.
- `software/`, `reference/`: 공식 LibreVNA GUI/매뉴얼, Tektronix·Samtec 도면, Python3.12 Windows x64 오프라인 분석 의존성.
- `project/reviews/sma_port_repair_20261027/`: 수정 후 정상 계산과 검증. `sma_right_angle_20261026/REJECTED_FULL_WAVE.json`은 이전 실패 증거로 그대로 보존한다.

과거 탐색 복구 ZIP `project/archive/superseded-artifacts-20260929.zip`, 재설치할 venv/node_modules, 이번/이전 이관 ZIP 자체는 중첩하지 않는다. 현행 보존검사 입력은 포함한다. 자세한 범위는 PACKAGE_SCOPE.json. 이관 확인은 RF 성능 검사와 별개다.

실측 데이터는 아직 없다. 완료한 것은 이관 준비와 계산/소프트웨어 검증이며, 첫 물리 작업은 **R00 권선 접속의 낮은 Ω·움직임 안정성 확인**이다.
