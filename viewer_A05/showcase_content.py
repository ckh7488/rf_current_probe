"""Reader-facing content. Procurement records remain in current_set_content.

Only these explicit rows are rendered publicly; hidden columns are not used to
conceal private purchase prose in the HTML or offline bundle.
"""
from copy import deepcopy
from pathlib import Path
from current_set_content import ROWS as INTERNAL_ROWS, MANUAL as INTERNAL_MANUAL

P = Path(__file__).resolve().parent
ROWS = deepcopy(INTERNAL_ROWS)
NOTES = {
    'E01': '물리적 반쪽 2개가 한 코어를 이룹니다. 아래 반쪽에 권선을 감고 위 반쪽을 열어 케이블을 넣습니다.',
    'E02': '권선 출력과 SMA를 연결합니다. 수신기 쪽 단일 50 Ω 종단을 사용합니다. SMA 완성 홀은 중심1.70 / 접지1.90 mm입니다.',
    'E03': 'Fixture A03 평판 교정지그입니다. 중앙 SIG만 코어 안을 지나고 리턴은 코어 밖의 두 창 바깥으로 흐릅니다. 교정은 빈 지그 S11이 아니라 프로브를 장착한 through의 출력 S21로 코어 전류를 정하는 출력 포트 기준으로 합니다. 같은 A03으로1–500 MHz 보정을 수행하고 주파수별 ZT·불확도·유효성을 기록합니다. −6 dB 전달 감소 자체를 대역 제외 사유로 쓰지 않습니다.',
    'E04': '헤드 PCB 1개와 Fixture A03 입출력 2개, 합계3개를 사용합니다. RP-SMA로 대체하지 않고 납땜 전에 다섯 핀의 삽입과 평면 안착을 확인합니다.',
    'E05': '권선용 도선입니다. 5턴을 기본으로 시작하고, 필요한 대역이 목표에 못 미칠 때만 3턴을 비교합니다. 턴수마다 교정 ID를 구분하고 유효 대역은 실제 교정으로 확인합니다.',
    'F01': '헤드 PCB에2개. 머리 아래 길이11.7–12.3 mm, 체결 그립7.85–8.85 mm, 너트 높이1.46 mm 이하가 설계 확인 범위입니다. 공급자 보증공차와 구별하며, 체결 후 완전 나사산과 끝 간섭을 확인합니다.',
    'F02': '제조사 도면 AF3.90±0.26 / H1.20±0.26 mm. PCB 뒤쪽에서 넣고 F01 M2×12 나사와 체결합니다.',
    'F05': '절단 가공 없이70 mm 스터드를 사용합니다. F22 관통노브 윗면과 끝을 평평하게 맞추고 F23 잼너트를 노브 아래에 고정합니다. 설치2개.',
    'F07': '개폐2 + 바닥 모듈6 + 가로대4 + 팔로워4. M4는 제조사 표의 DIN557 일반 치수 범위 밖이므로 BN147 / 8236739의7×7×3.2 mm 외형을 기준으로 합니다.',
    'F09': '설치2개. 높이6 mm 포켓과5 mm 너트 사이의 공칭 축방향 여유는1 mm입니다. 개별 치수 공차는 별도 확인합니다.',
    'F11': '프레임 아래에2개. F17 위쪽 와셔와 같은 품번으로 합계4개입니다. 아래 잠금너트를 조절해 축이 자유롭게 돌도록 하고 프레임을 압착하지 않습니다.',
    'F14': 'PA66 M3×0.5. 제조사 도면 폭15.96±0.3 / 높이8±0.3 mm. 외형이 다른 유사품으로 임의 대체하지 않습니다.',
    'F17': '프레임 위쪽에2개. F11 아래쪽 와셔와 같은 두께1.6 mm 제품을 사용합니다. 두 위치의 합계는4개입니다.',
    'F23': '설치2개. 프레임 밖에서7 mm 스패너로 노브 밑면에 조여 노브와 스터드를 고정합니다. 반복 개폐 때 잼너트가 따라 풀리지 않는지 확인합니다.',
    'R01': '양끝 SMA 수형 케이블입니다. VNA 두 포트에 각각1개를 사용하고 길이·배치·굽힘과 개체 ID를 유지합니다. 수형 외장 로드는 이 케이블 끝에 직접 연결하지 않습니다.',
    'R02': '이 세트에는 수형 로드1개를 사용합니다. RF OFF에서 헤드 출력과 지그 출력 사이로 옮깁니다. ΓL은 수형 SOL 표준으로 별도 교정한 SMA 암 기준면에서 측정합니다. M/M 케이블 끝에 직접 연결하거나 F/F 어댑터만 추가해 이전 교정을 적용하지 않습니다. 작업용 로드는 SOL 표준과 다르며 1포트·2포트 교정 ID를 분리합니다.',
    'R04': '케이블 끝 2포트 교정과 로드용 암 기준면 1포트 교정에 맞는 표준 성별·모델을 각각 확인합니다. 암 기준면에는 수형 SOL 표준이 필요합니다. THRU의 지연·모델 정의도 실제 구성에 맞춥니다.',
    'R05': '외장 10 dB 감쇠기입니다. 평상시에는 감쇠기 없이 프로브를 직접 연결합니다. 새 현장·새 케이블의 첫 측정은 반드시 감쇠기를 넣고 최대값을 확인한 뒤 빼기를 강력히 권고합니다. 케이블 착탈·전원 투입 때도 넣습니다. 연결 순서는 프로브 SMA 암 → 감쇠기 SMA 수/암 → R06 케이블이며, 감쇠기를 넣은 체인은 따로 특성화합니다. 현재 3D에는 감쇠기가 없습니다.',
    'R08': '대상 하네스(24 V·100BASE-TX)에서는 별도 보호 체인을 두지 않고 R05 첫 확인으로 운용합니다. 상용전원·VFD·고전압·서지 현장은 이 시제품의 범위 밖입니다.',
    'T01': '보유 LibreVNA 2포트를 사용합니다. 복소 S11/S21/S12/S22, 케이블 끝2포트 교정, 소스 레벨·IF BW 조절과 Touchstone 저장, 하한100 kHz 이하가 필요합니다.',
    'T03': 'PCB 뒤 M2 너트는 가는 평팁으로 잡습니다. 외경6.5 mm 원형 소켓은 홀더에 걸립니다. 평팁/뒤쪽 M3 공구의 치수 조건은 H04/H08/H11을 확인합니다. 10 mm 스패너는 머리폭18 / 두께4 mm 이내의 검토 외형이며 실제 공구를 대조합니다.',
    'T04': 'SMA·권선 납땜과 도통 검사에 사용합니다. 패드 크기에 맞는 팁·플럭스를 사용하고, 작업 중 PCB와 코어를 지지합니다.',
}
for row in ROWS:
    row.pop('status', None)
    if row['id'] in NOTES:
        row['note'] = NOTES[row['id']]
    if row['id'] in ['P01', 'P02', 'P05', 'P11', 'P12', 'P13', 'P14', 'P15']:
        row['note'] = '출력용 자유 형상 STL입니다. 조립 STEP에서 출력 형상을 추출하지 않습니다.'
    if row['id'] in ['P03', 'P04']:
        row['note'] = '코어를 받침에 고정합니다. 현재 세트에 포함된 자유 형상 STL을 사용합니다.'
    row['links'] = [(label, url) for label, url in row['links']
                    if not any(x in url for x in ['purchase', 'split-a14/', 'audit/', 'QUOTE_ONLY', 'short/'])]
    if row['id'] == 'E02':
        row['links'] = [('Gerber · Head A04', 'files/RFCP_Head_A04_DRAFT_REVIEW_ONLY.zip')]
    if row['id'] == 'E03':
        row['links'] = [('교정 원리 · Fixture A03', 'design-review.html')]
    if row['id'] == 'R03':
        row['spec'] = 'SMA 교정 표준 · 성별·모델값·유효 대역 확인'
    if row['id'] == 'R05':
        row['links'].append(('감쇠기 연결안', 'manual.html#output-connection'))
    if row['id'] == 'E05':
        row['qty'], row['unit'] = None, '필요 길이'

def manual():
    """Reuse technical instructions; replace conversational/project-office prose."""
    text = INTERNAL_MANUAL
    replacements = [
        ('클램프의 공칭 설계 구경은 Ø6–26 mm다. 2026-09-22 사용자가 실제 큰 대상도 약20 mm 수준이고 현행26 mm 기준이면 충분하다고 확인했다. 헤드 고정바를 포함한 공칭 통과 지름은 약26.40 mm이며 초기30 mm 목표는 대체한다. 커넥터를 구경에 통과시키지 않고 케이블을 위에서 넣는다. 실제 중심 오차·외피 눌림·주변 커넥터 간섭은 조립 시 확인한다.',
         '클램프의 공칭 설계 구경은 Ø6–26 mm이며, 주 대상은 최대 약20 mm 수준의 케이블·다발이다. 헤드 고정바를 포함한 공칭 통과 지름은 약26.40 mm다. 케이블을 위에서 넣는 분할 구조이므로 커넥터를 구경에 통과시키지 않는다. 실제 중심 오차·외피 눌림·주변 커넥터와의 간섭은 조립 시 확인한다.'),
        ('10 mm에서 길이만 늘렸으며 출력물은 그대로 사용합니다. ', ''),
        ('<p><b>이 절은 검증을 끝낸 교정기의 즉시 사용법이 아니라 앞으로 수행할 시험 절차입니다.</b> <a href="bom.html#readiness">전체 제작·교정 준비 상태</a>에서 선행 조건을 먼저 확인합니다.</p>',
         '<p>다음은 저에너지 벤치 특성화 절차입니다. 외부 전원이나 현장 케이블을 연결하지 않고 VNA 자체의 낮은 레벨 신호부터 사용합니다. <a href="#check">검증 범위와 첫 시험</a>을 함께 확인합니다.</p>'),
        ('리비전이 바뀐 부품을 이전 구매서와 섞지 않는다.', '같은 조립체에서 사용하는 PCB·기구 리비전과 교정 ID를 함께 관리한다.'),
        ('이 설명서는 현재 설계의 사용·검증 절차를 정리한 문서다. 실물 제작 완료나 현장 사용 승인을 뜻하지 않는다.', '이 문서는 CAD 기준 시제품의 조립·특성화 절차다. 실측 유효 대역·정확도와 현장 보호 정격은 아직 확정되지 않았다.'),
    ]
    for old, new in replacements:
        assert old in text, f'Public manual source changed: {old[:60]}'
        text = text.replace(old, new)
    return text

def guide_steps(steps):
    """Keep assembly actions visible and place calculation detail in the disclosure."""
    for step in steps:
        step['tool']=step['tool'].replace('구매한','사용하는')
        if step['id']=='H05':
            step['proof']+=' 확인 조건: '+step['note']
            step['check']='기판을 장착면에 누른 채 기울이지 않습니다. 탈착은 권선 납땜과 나사를 제거한 뒤, 장착면에서 앞쪽으로 살짝 띄우고 기울입니다. 걸리면 억지로 누르지 않습니다.'
            step['note']='F01은 PA66 M2×12 두 개입니다. 체결 후 완전 나사산과 끝 간섭을 확인합니다. 연결된 짧은 권선 끝선을 당겨 PCB를 기울이지 않습니다. 치수·공차 조건은 아래 검증 범위에 있습니다.'
    return steps
