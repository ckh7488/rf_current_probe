"""Build explanatory vectors and curated public evidence. Does not edit hardware."""
from pathlib import Path
from html import escape
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path('C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe')
ASSETS = REPORT / 'assets'
RECORDS = REPORT / 'records'
for directory in (ASSETS, RECORDS):
    directory.mkdir(parents=True, exist_ok=True)
INK, MUTED, LINE = '#172e33', '#5f737b', '#d9e1e4'
TEAL, SOFT, PAGE, WHITE = '#197d71', '#eaf4f1', '#f4f6f7', '#ffffff'
SIGNAL, RETURN = '#edaa65', '#577c96'

def txt(x, y, value, size=24, color=INK, anchor='middle', weight=500):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(value)}</text>'

def rect(x, y, w, h, fill=WHITE, stroke=LINE, r=7, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2" {extra}/>'

def path(d, color=TEAL, width=5, arrow=False, dashed=False):
    marker = ' marker-end="url(#arrow)"' if arrow else ''
    dash = ' stroke-dasharray="7 6"' if dashed else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{marker}{dash}/>'

def svg(name, width, height, title, body):
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 Z" fill="context-stroke"/></marker></defs>
<style>text{{font-family:'Malgun Gothic','Segoe UI',sans-serif}}</style>
<rect width="100%" height="100%" fill="{WHITE}"/>{body}</svg>'''
    (ASSETS / name).write_text(content, encoding='utf-8')

for mode in ('all', 'signal', 'return'):
    so = 1 if mode in ('all', 'signal') else .15
    ro = 1 if mode in ('all', 'return') else .15
    b = txt(320, 38, 'PCB 지그의 전류 경로', 29, weight=700)
    b += rect(82, 142, 476, 320, SOFT, LINE)
    b += rect(126, 194, 164, 206, WHITE, LINE) + rect(350, 194, 164, 206, WHITE, LINE)
    b += f'<g opacity="{ro}">'
    b += rect(74, 115, 492, 44, RETURN, RETURN, 4) + rect(74, 445, 492, 44, RETURN, RETURN, 4)
    b += rect(92, 159, 25, 286, RETURN, RETURN, 0) + rect(523, 159, 25, 286, RETURN, RETURN, 0)
    b += path('M 104 390 L 104 215', WHITE, 4, True) + path('M 535 390 L 535 215', WHITE, 4, True)
    b += '</g>'
    b += f'<g opacity="{so}">'
    b += '<circle cx="320" cy="137" r="20" fill="white"/><circle cx="320" cy="467" r="20" fill="white"/>'
    b += path('M 320 88 L 320 180', SIGNAL, 8) + path('M 320 419 L 320 521', SIGNAL, 8)
    b += rect(307, 180, 26, 239, SIGNAL, SIGNAL, 0)
    b += path('M 320 205 L 320 245', INK, 4, True) + path('M 320 353 L 320 396', INK, 4, True)
    b += '</g>'
    b += rect(267, 258, 106, 82, 'none', TEAL, 8, 'stroke-dasharray="8 6"')
    b += txt(207, 289, '귀환', 27, RETURN) + txt(435, 289, '귀환', 27, RETURN)
    b += txt(207, 322, '코어 밖', 23) + txt(435, 322, '코어 밖', 23)
    b += txt(320, 304, 'SIG', 24, weight=700)
    b += txt(320, 75, 'SMA IN · 중심', 25) + txt(320, 551, 'SMA OUT · 중심', 25)
    b += txt(173, 145, 'EndPanel', 22, WHITE) + txt(173, 475, 'EndPanel', 22, WHITE)
    b += txt(320, 588, '점선: 코어 구멍의 위치 / 형상은 개념도', 22, MUTED)
    svg('pcb-path' + ('' if mode == 'all' else '-' + mode) + '.svg', 640, 620, '중앙 SIG는 코어 안, 좌우 귀환 레일은 밖', b)

b = txt(156, 38, '새 중앙 다리', 26, weight=700) + txt(480, 38, '피해야 하는 구성', 26, weight=700)
b += rect(22, 70, 268, 125, SOFT, LINE) + rect(350, 70, 268, 125, PAGE, LINE)
for x in (55, 382):
    b += rect(x, 117, 202, 30, PAGE, LINE, 0)
    b += path(f'M {x} 110 L {x+202} 110', SIGNAL, 10)
b += path('M 55 154 L 257 154', SIGNAL, 10) + path('M 383 154 L 585 154', RETURN, 10)
b += path('M 151 109 L 151 154', SIGNAL, 7)
b += txt(156, 98, '윗면 SIG', 23) + txt(156, 185, '아랫면 SIG', 23)
b += txt(482, 98, '윗면 SIG', 23) + txt(482, 185, '아랫면 GND', 23)
b += txt(156, 234, '같은 신호 · 비아로 연결', 23, TEAL)
b += txt(482, 234, '왕복 전류가 함께 통과', 23, MUTED)
svg('cross-section.svg', 640, 270, '중앙 PCB 단면: 신호 양면 연결과 잘못된 GND 동시 통과의 비교', b)

def instrument(x, name, sub):
    return rect(x, 18, 145, 74, PAGE, LINE) + txt(x+72.5, 48, name, 24, weight=700) + txt(x+72.5, 76, sub, 21, MUTED)

for step in range(4):
    b = instrument(24, 'VNA P1', '신호 송신') + instrument(388, 'VNA P2', '50 Ω 수신')
    if step == 0:
        b += path('M 97 92 L 97 163', TEAL, 5) + path('M 461 92 L 461 163', TEAL, 5)
        b += '<circle cx="97" cy="163" r="6" fill="#197d71"/><circle cx="461" cy="163" r="6" fill="#197d71"/>'
        b += txt(97, 193, '케이블 끝', 22) + txt(461, 193, '케이블 끝', 22)
        b += rect(52, 229, 456, 103, SOFT, LINE)
        b += txt(280, 266, '각 끝에 Open / Short / Load', 24, weight=700)
        b += txt(280, 306, '모델·성별이 맞는 표준을 순서대로', 22)
        b += path('M 97 374 L 215 374', TEAL, 5) + path('M 345 374 L 461 374', TEAL, 5)
        b += rect(215, 350, 130, 49, PAGE, LINE) + txt(280, 383, 'Thru', 24)
        b += txt(280, 434, '두 케이블 끝 사이 Thru도 측정', 23, MUTED)
    else:
        b += path('M 97 92 L 97 215 L 119 215', TEAL, 5, True)
        b += rect(120, 172, 282, 86, SOFT, LINE)
        b += txt(261, 200, 'PCB 지그', 26, weight=700)
        b += path('M 145 221 L 378 221', SIGNAL, 5, True)
        b += txt(141, 154, 'IN', 23) + txt(382, 154, 'OUT', 23)
        b += txt(261, 249, '귀환은 코어 밖', 21, MUTED)
        if step in (1, 2):
            b += path('M 402 215 L 461 215 L 461 102', TEAL, 5, True)
            b += txt(487, 159, 'P2로', 21, TEAL)
        if step == 1:
            b += rect(154, 329, 252, 60, PAGE, LINE) + txt(280, 368, '헤드는 분리한 상태', 23, MUTED)
            b += txt(280, 429, '외장 부하 없음 · P2가 종단', 23)
        else:
            b += path('M 262 262 L 262 314', TEAL, 3, False, True)
            b += txt(136, 299, '자기 결합', 22, TEAL)
            b += rect(183, 326, 162, 69, SOFT, TEAL) + txt(264, 355, '프로브', 25, weight=700) + txt(264, 383, 'SMA 출력', 21)
            if step == 2:
                b += path('M 345 361 L 391 361', TEAL, 5)
                b += rect(392, 327, 140, 68, PAGE, LINE) + txt(462, 352, '외장 부하', 22) + txt(462, 382, '50 Ω', 25, weight=700)
                b += txt(280, 433, 'P2 위치 유지 · 프로브에 부하 추가', 22)
            else:
                b += path('M 402 215 L 423 215', TEAL, 5)
                b += rect(424, 181, 109, 69, PAGE, LINE) + txt(478, 207, '부하', 22) + txt(478, 236, '50 Ω', 25, weight=700)
                b += path('M 345 361 L 549 361 L 549 118 L 461 118 L 461 102', TEAL, 5, True)
                b += txt(432, 335, 'P2 케이블', 22, TEAL)
                b += txt(280, 433, '부하 → 지그 OUT / P2 → 프로브', 22)
    svg(f'step-{step}.svg', 560, 450, f'교정 단계 {step}의 실제 연결 역할', b)

shutil.copy2(ROOT/'mechanical/clamp_A03_DRAFT/assembly_preview.png', ASSETS/'clamp-a03.png')
shutil.copy2(ROOT/'hardware/calibration_fixture_PCB_A01/assembly/assembly_preview.png', ASSETS/'pcb-fixture-assembly.png')
shutil.copy2(ROOT/'hardware/calibration_fixture_PCB_A01/assembly/pcb_overview.png', ASSETS/'pcb-fixture-boards.png')

source_paths = [
 'docs/RF_CURRENT_PROBE_WHITEPAPER.md', 'docs/ASSEMBLY_CONSTRAINTS_20260917.md',
 'docs/G2_BENCH_PROCEDURE.md', 'docs/END_TO_END_REHEARSAL.md',
 'hardware/calibration_fixture_PCB_A01/build_pcbs.py',
 'hardware/calibration_fixture_PCB_A01/Frame/geometry.json',
 'hardware/calibration_fixture_PCB_A01/EndPanel/geometry.json',
 'hardware/calibration_fixture_PCB_A01/README.md',
 'hardware/calibration_fixture_PCB_A01/ASSEMBLY_AND_VALIDATION.md',
 'hardware/calibration_fixture_PCB_A01/verification.json',
 'hardware/calibration_fixture_PCB_A01/assembly/assembly_preview.png',
 'hardware/calibration_fixture_PCB_A01/assembly/pcb_overview.png',
 'hardware/calibration_fixture_PCB_A01/assembly/assembly_checks.json',
 'hardware/probe_head_A02/review/erc.json','hardware/probe_head_A02/review/drc.json',
 'mechanical/clamp_A03_DRAFT/README.md', 'tests/results/process_review_tests.xml',
 'tests/results/process_rehearsal_final_20260916/report.json'
]
test_summary=ET.parse(ROOT/'tests/results/process_review_tests.xml').getroot().find('testsuite').attrib
evidence={
 'document_date':'2026-09-17','document_revision':'0.2',
 'status':'PCB fixture design and planned calibration. No measured RF results.',
 'illustrations':'Original explanatory vectors based on the source geometry; not scale fabrication drawings.',
 'software_test_log':{k:test_summary[k] for k in ['tests','failures','errors','skipped','timestamp']},
 'sources':[{'project_relative_path':s,'sha256':hashlib.sha256((ROOT/s).read_bytes()).hexdigest()} for s in source_paths],
 'external_sources_checked':'2026-09-17',
 'external_sources':['https://www.tekbox.com/product/TBCPx_Calibrators_Manual.pdf','https://www.tekbox.com/product/FAQ_Current_Probes.pdf'],
 'limitations':['No physical assembly or RF calibration performed for this report.','Old copper fixture validation and cost do not establish PCB fixture validity.','No entire-band 50-ohm or current-model claim.']
}
(RECORDS/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

(RECORDS/'source-notes.md').write_text('''# RF 전류 프로브 · 문서 근거

2026-09-17 / v0.2 / 설계와 앞으로 수행할 시험 절차

## 현재 구조

- 프로브: Fair-Rite 2644181281의 물리적 반쪽 2개, 고정 반쪽 5턴 시작안. 유효 구경 30 mm 목표.
- 헤드 PCB A0.2: 20×16 mm, 공칭 두께 1.6 mm, 수신기 단일 50 Ω 종단. RF 응답은 미실측.
- 집게 A0.3: 얇은 벽 국소 보강과 CAD 검사. 출력·강도·맞춤은 미검증.
- PCB 교정지그 A0.1: Frame 118×65×1.0 mm 1장, EndPanel 128×24×1.0 mm 2장. 중앙 폭 8 mm 다리의 양면 SIG, 동박 폭 6.8 mm. ±55 mm의 바깥 귀환 레일. 설계값이며 RF 성능 사양이 아님.
- 금속 절단·드릴·줄질을 사용자 조립에 요구하는 동판안을 대체한다. 납땜·나사·권선·피복 제거·간단한 패드 재단은 필요하다.

## 문서의 근거

중심 백서 RFCP-WP-001 Rev.A/0.2의 물리량 정의·조건부 환산·시험 T01~T12를 따른다. 후속 조립 제약, 새 PCB 생성 원본·geometry.json, 벤치 절차, 전체 연결 리허설을 대조했다. 원본 식별과 SHA-256은 evidence.json에 기록한다. 기록된 소프트웨어 시험은 2026-09-16의 110개이며 이번 웹 문서 작업에서 센서 시험을 재실행했다는 뜻이 아니다.

직전 동판 교정지그는 과거 설계다. 해당 기구 검사·재료비·300 MHz 응답을 PCB 지그의 검증으로 가져오지 않는다. PCB 제작성 검사 통과도 RF 정합·코어 전류·실측 교정을 보장하지 않는다. 이 페이지는 구매·제작·현장 사용 승인서가 아니다.

새 PCB 지그의 조립·시험 절차에 맞춰 첫 설정안은 1~100 MHz / 401점 / −20 dBm / IF BW 1 kHz로, 파일명은 fixture_empty, fixture_probe_loaded, probe_transfer_01 계열로 통일했다. 평균은 실제 설정값을 기록한다. 기존 상세 벤치 절차의 1601점·−30 dBm은 더 낮은 레벨·세밀한 후속 비교 설정안으로 남는다. 장비 정격과 지원 범위가 우선이며 실측 실행값을 뜻하지 않는다.

## 그림의 의미

pcb-path.svg는 Frame의 중앙 신호·양옆 귀환과 양끝 EndPanel 연결을 단순화한 투영 개념도다. 점선은 코어 구멍의 위치를 뜻하며 코어 또는 집게 전체 외형이 아니다. cross-section.svg는 중앙 다리의 층별 전류를 설명한다. step-0~3.svg는 케이블·종단의 역할을 설명하며 실제 케이블 길이와 기구 배치는 표현하지 않는다. 프로브와 일차 회로 사이 점선은 자기 결합이며 도전 접속이 아니다.

## 일차자료

- Tekbox TBCPx Calibration Fixtures V1.0, https://www.tekbox.com/product/TBCPx_Calibrators_Manual.pdf : 중심/외부 귀환 및 약 50 Ω 지그의 전달 임피던스 관계. 2쪽의 전력 차 표현 부호는 S21 정의와 불일치하므로 프로젝트 백서의 검산을 따른다.
- Tekbox FAQ RF Current Monitoring Probes, https://www.tekbox.com/product/FAQ_Current_Probes.pdf : 50 Ω 수신 부하·정현파 전류 환산·과부하.
- LibreVNA 공식 문서, https://github.com/jankae/LibreVNA : 실제 보유 HW/FW/GUI와 지원 교정 모드·설정은 장비에서 확인해야 한다.

상용 지그의 대역과 사양을 자체 제작 PCB 지그에 전용하지 않는다. 조건이 입증되기 전에는 상대 응답으로 분류한다.
''',encoding='utf-8')

(RECORDS/'bench-checklist.md').write_text('''# PCB RF 전류 프로브 · 첫 벤치 기록

설계·시험 절차 v0.2 / 2026-09-17 / 빈 양식은 측정 결과가 아닙니다.

## 0. 구성 식별

- 측정 ID / 날짜 / 온도:
- 헤드 ID·리비전 / 코어 / 턴 수·방향 / 차폐 / 리드 길이:
- PCB 지그 리비전 / 실제 두께·SMA·슬롯 조립:
- LibreVNA HW/FW/GUI / 케이블 ID / 부하 ID / 교정키트·Thru 모델:
- 도체 위치 / 잠금 상태 / 사진:

## 1. 무전원 확인

- [ ] 중심 경로 IN–OUT 연속성, 외피·양옆 귀환 연속성 확인.
- [ ] 케이블·50 Ω 부하를 분리한 지그 중심–외피 분리 확인.
- [ ] 코어 안은 중앙 SIG만 통과. 양옆 귀환과 출력 동축은 밖.
- [ ] 일차 도체와 권선의 의도치 않은 도통 없음. 권선 자체의 낮은 DC 저항은 정상일 수 있음.
- [ ] SMA 체결·슬롯 납땜·코어 접합·권선 끼임·간섭 점검.
- [ ] 장비 입력 정격, 제한된 저에너지 소스, 정의된 출력 종단 확인.

## 2. 측정 순서 — 연결 변경은 항상 RF OFF

시작 설정안: 1~100 MHz / 1601점 linear / −30 dBm / IF BW 1 kHz / 평균 4. 실제 지원값·정격을 우선하고 설정을 저장.

1. 두 테스트 케이블 끝에서 실제 모델·성별이 맞는 O/S/L/T로 지원되는 2포트 교정. 교정 ID·기준면·재접속 확인을 저장.
2. 헤드 없이 P1 → 지그 IN, 지그 OUT → P2. 외장 부하 없음. fixture_through_empty.s2p 저장.
3. RF OFF. 헤드 장착, 헤드 출력 → 외장 50 Ω. P2는 지그 OUT에 유지. fixture_through_head_loaded.s2p 저장.
4. RF OFF. P2 케이블은 지그 OUT → 헤드 출력으로 이동. 외장 50 Ω는 헤드 → 지그 OUT으로 이동. 두 종단 확인 후 RF ON.
5. probe_transfer_5t_Lm30.s2p 및 같은 이름의 JSON에 설정·체인·위치·시간·교정 ID 저장. 모델 미검증이면 relative.
6. 소스 레벨·재장착 최소 5회·도체 위치·상쇄·직접 픽업·잡음을 비교하고 실패 구간도 보존.

## 3. 환산 전 확인

- [ ] 코어 전류 모델·기준면·출력 부하와 케이블 포함 범위를 확인.
- [ ] 누설·잡음·선형성·반복성·위치 의존성을 주파수별로 평가.
- [ ] 깊은 null·클리핑·미평가·대역 밖은 invalid. 불확도 미평가를 0으로 쓰지 않음.
- [ ] 전류 기준을 입증하지 못하면 ZT와 A를 만들지 않고 상대 S21만 보고.

## 4. 스코프

RF OFF 후 재배선. CW/P1만 출력. 실제 모델의 입력·정격·50 Ω 설정 확인. 원시 전압 파형을 먼저 저장. BNC 기준면, 체인, 수신기 응답·부하가 맞을 때만 단일 주파수 기본파 RMS를 환산. VNA용 어댑터 제거와 감쇠 중복 보정 주의. 광대역 펄스 피크를 단일 ZT로 나누지 않음.

## 5. 판정

- 관측한 사실:
- 유효/무효 구간과 근거:
- 실패·변경·중단 사항:
- 다음 한 가지 실험:

현장 적용은 입력 보호·장착·삽입 영향·순 DC 감도 확인 후의 별도 단계입니다. 보호접지·DUT 쉴드를 끊거나 고전압/VFD/서지 시험에 직접 적용하지 않습니다.
''',encoding='utf-8')
print(json.dumps({'svg_count':len(list(ASSETS.glob('*.svg'))),'source_count':len(source_paths),'report':str(REPORT)},ensure_ascii=False))
