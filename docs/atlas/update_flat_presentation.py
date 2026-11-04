"""Update the report to the current A02 flat fixture, preserving A01 for comparison."""
from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[2]
ATLAS=Path(r'C:\Users\artzy\Documents\ChatGPT\test_board\showcase')
REPORT=ATLAS/'reports/rf-current-probe'
H=ROOT/'hardware/calibration_fixture_PCB_A02'
for src,dst in [('assembly_preview.png','flat-a02-assembly.png'),('pcb_overview.png','flat-a02-board.png')]:
    shutil.copy2(H/'assembly'/src,REPORT/'assets'/dst)

p=REPORT/'index.html';s=p.read_text(encoding='utf-8')
s=s.replace('20260917-cad1','20260917-flat2').replace('설계·절차 v0.3','설계·절차 v0.4')
s=s.replace('PCB 교정지그로 전환 중','평판 PCB 1장 · 지그 A0.2')
s=s.replace('동판 가공 대신, PCB 3장으로','평판 PCB 한 장으로, 지그를 단순하게')
s=s.replace('Frame 1장 + 같은 EndPanel 2장. 납땜과 나사 조립을 중심으로 바꿉니다.','144 × 92.7 mm 보드 1장 · 직접 납땜하는 SMA 2개 · 네 모서리 고정.')
s=s.replace('기존에는 동판·동띠를 잘라 구멍을 가공했습니다. 새 초안은 판의 외곽·슬롯·전류 경로를 PCB 제작에 맡깁니다. 권선 감기, 짧은 연결선 납땜, 패드 직선 재단은 남습니다. <strong>출력물 공차와 실제 끼움은 아직 확인 전</strong>이므로 무가공 조립이 보장된 상태는 아닙니다.',
'''새 A0.2는 이전 3장 PCB를 한 장으로 합쳤습니다. 세로 보드 접합과 점퍼선이 사라지고, 두 SMA를 보드에 직접 납땜합니다. 기존 바닥판과 헤드 브래킷을 유지하고, 양끝 출력 지지대는 <strong>65 mm 나일론 기둥 4곳</strong>으로 바꿉니다. 판의 외곽·두 창·구멍은 PCB 업체에서 가공합니다.''')
s=s.replace('<div class="interactive topology-panel">','''<div class="interactive topology-panel">
      <div class="revision-controls" role="group" aria-label="현재와 이전 지그 비교">
        <button type="button" data-revision-choice="A02" aria-pressed="true">현재 A0.2 · 평판 1장</button>
        <button type="button" data-revision-choice="A01" aria-pressed="false">이전 A0.1 · 3장과 비교</button>
      </div>
      <p id="revision-note" class="revision-note" aria-live="polite">현재 A0.2: 평판 1장 · SMA 직접 납땜 · 나일론 기둥 4곳. 아래 제작·교정 설명의 기준입니다.</p>''')
s=s.replace('원본 CAD · PCB A0.1 / 집게 A0.3','현재 · 평판 PCB A0.2 / 집게 A0.3')
s=s.replace('창·슬롯·SMA 위치를 직접 확인하세요.','한 장의 보드와 위로 향한 SMA를 보세요.')
s=s.replace('Frame·EndPanel은 KiCad에서 내보낸 형상, 집게·지지대는 조립 CAD입니다. 신호는 금색, 바깥 귀환은 초록색으로 구분합니다.','평판 PCB는 KiCad에서 내보낸 형상, 집게·브래킷·바닥판은 저장 CAD입니다. 기둥은 제조사 도면 치수의 공칭 모델입니다. 신호는 금색, 바깥 귀환은 초록색입니다.')
s=s.replace('가운데 신호 길과 양옆 귀환 길은 서로 다른 동박입니다. 두 귀환은 양끝 EndPanel에서 SMA 외피와 연결됩니다.','같은 한 장의 PCB 안에서 중앙 SIG와 바깥 GND를 분리합니다. 두 창 사이 중앙 다리만 코어 안으로 들어갑니다.')
s=re.sub(r'<dl class="parts">.*?</dl>', '''<dl class="parts"><dt>평판 PCB × 1</dt><dd>144 × 92.7 × 1.6 mm, 2층 초안. 47 × 33.75 mm 창 2개 사이에 폭 8 mm의 중앙 다리가 있습니다.</dd><dt>J1 / J2 · 수직 SMA</dt><dd>RFPC-SMA28-F 2개. 중심 핀은 SIG, 네 외피 핀은 GND에 직접 납땜합니다. 지그에는 점퍼선이 없습니다.</dd><dt>모서리 기둥 × 4곳</dt><dd>30 mm F/F + 35 mm M/F 나일론 기둥을 한 쌍씩 사용합니다. 총 8개 부품으로 높이 65 mm를 만듭니다. 구멍 간격은 130 × 76.7 mm입니다.</dd><dt>집게 무게는 별도로 지지</dt><dd>기존 Base와 HeadBracket이 받칩니다. 좁은 PCB 중앙 다리에 집게를 매달지 않습니다.</dd></dl>''',s,flags=re.S)
s=s.replace('Frame의 양옆 레일을 두 EndPanel에 끼우고 납땜합니다. 금색 중앙 다리가 코어 안을 지나며, 녹색 바깥 레일은 밖으로 돌아갑니다.','평판 PCB를 네 모서리 기둥에 고정합니다. 금색 중앙 다리가 코어 안을 지나며, 녹색 바깥 레일은 밖으로 돌아갑니다.')
s=s.replace('assets/pcb-fixture-assembly.png','assets/flat-a02-assembly.png').replace('assets/pcb-fixture-boards.png','assets/flat-a02-board.png')
s=s.replace('PCB Frame과 양끝 EndPanel이 기존 지지대와 집게 A0.3에 조립된 CAD의 닫힘과 열림 모습','평판 PCB 한 장과 네 모서리 기둥, 기존 집게와 바닥판을 조립한 A0.2 CAD의 닫힘과 열림 모습')
s=s.replace('PCB 교정지그 A0.1 초안.','평판 PCB 교정지그 A0.2 초안.')
s=s.replace('두 창이 있는 Frame PCB 한 장과 SMA용 홀 및 레일 슬롯이 있는 EndPanel PCB 두 장의 설계 외형','두 창과 모서리 고정 구멍 네 곳, 직접 납땜하는 SMA 두 개를 가진 평판 PCB 한 장의 설계 외형')
s=s.replace('Frame 1장과 같은 EndPanel 2장을 사용합니다. 중앙 다리는 양면 신호이고, EndPanel은 SMA 외피·귀환을 연결합니다.','별도 EndPanel이 없습니다. 중앙 다리는 양면 SIG이며, 같은 보드의 바깥 GND가 두 SMA 외피를 연결합니다.')
s=s.replace('새 Frame은','평판 A0.2의 중앙 다리는')
s=s.replace('새 교정지그는 PCB A0.1 초안이며 기존 동판 F-A A0.1을 대체하는 작업입니다. 기존 동판 지그의 간섭·조립 검사나 견적이 새 PCB 지그에 자동으로 적용되지는 않습니다. 이 보고서는 새 PCB 구조와 앞으로 수행할 교정 절차를 설명합니다.',
'''현재 교정지그는 평판 PCB A0.2 초안입니다. 이전 동판 지그와 PCB 3장 A0.1은 이력·비교용입니다. 이전 교정값·간섭 결과·견적을 새 지그에 전용하지 않습니다. 아래 제작·교정 연결은 A0.2 기준입니다.''')
marker='\n  <section id="calibration">'
review='''
  <section id="design-review">
    <div class="section-heading"><span class="section-number">검토</span><div><h2>지금 구조가 더 나은가요?</h2><p><strong>조립과 재제작에는 더 적합합니다.</strong> RF 성능의 우열은 아직 측정으로 확인해야 합니다.</p></div></div>
    <p class="readable">금속 가공 없이 만들려는 현재 조건에서는 A0.2를 다음 시제품으로 유지하는 편이 낫습니다. 보드 사이 납땜과 점퍼의 길이·접촉 변수가 줄었습니다. 이것은 설계 비교에 따른 판단이며, 감도·정확도·대역폭이 향상됐다는 실측 결론은 아닙니다.</p>
    <div class="table-wrap"><table><thead><tr><th>비교 항목</th><th>이전 A0.1 · PCB 3장</th><th>현재 A0.2 · PCB 1장</th></tr></thead><tbody>
      <tr><td>조립</td><td>Frame와 EndPanel 2장의 직각 접합, 점퍼 2개</td><td><strong>평판 한 장, SMA 2개 직접 납땜.</strong> 보드 사이 접합·점퍼 없음</td></tr>
      <tr><td>SMA 접지</td><td>외피와 EndPanel의 기계적 접촉 확인 필요</td><td>커넥터마다 GND 핀 4개 납땜. 접속 구조가 명확해짐</td></tr>
      <tr><td>지지 구조</td><td>Base·HeadBracket·InputStand·OutputStand</td><td>Base·HeadBracket 유지, 양끝 지지대 2개 제외. 나일론 기둥 30+35 mm 네 쌍 추가</td></tr>
      <tr><td>코어 안 전류 경로</td><td>중앙 SIG만 통과</td><td>같은 원칙 유지. 새 저장 CAD 전체 구경 길이에서 GND 통과량 0 확인</td></tr>
      <tr><td>새로 주의할 점</td><td>접합·점퍼·SMA 외피 체결의 편차</td><td>보드에 선 SMA의 케이블 하중, 65 mm 기둥 휨·풀림, 나사 끝 닿음</td></tr>
      <tr><td>RF / 비용</td><td>실측 교정·확정 PCB 견적 없음</td><td><strong>RF 개선·전체 비용 절감 모두 미확정.</strong> 새 PCB·기둥·SMA·배송 재견적 필요</td></tr>
    </tbody></table></div>
    <div class="two-col review-grid"><div><h3>이번에 다시 확인한 것</h3><ul><li>저장 PCB의 ERC·DRC·미연결·회로 일치 위반 각 0건.</li><li>코어의 길이 12.7 mm 전체에서 중앙 SIG만 통과하고 GND는 밖에 있음.</li><li>PCB와 닫힌 헤드의 공칭 간격 2.00 mm.</li><li>Ø12 × 30 mm 플러그 외형 2개를 가정해도 0~90° 개폐 19점에서 겹침 0, 최소 간격 4.91 mm.</li></ul><p class="note">FreeCAD 1.0.2 / KiCad 10.0.0으로 저장 파일을 재검사했습니다. 공차·연속 개폐·실제 케이블과 힘에 대한 검증은 포함하지 않습니다.</p></div>
    <div><h3>먼저 보완할 두 가지</h3><p><strong>① 케이블 하중:</strong> SMA 몸체를 지지하며 연결하고 케이블을 별도로 받칩니다. 보드를 손잡이처럼 비틀거나 긴 케이블을 매달지 않습니다.</p><p><strong>② 바닥 나사 길이:</strong> 현재 M3×12의 암나사 끝 여유는 공칭 0.6 mm입니다. M3×10이면 계산상 2.6 mm가 남습니다. 보유 M3 나사의 길이·머리·체결 상태를 확인해 선택하고, 절연 나일론 기둥은 유지합니다.</p><p class="note">M3×10은 검토 후보입니다. 현재 CAD를 바꿔 체결을 검증한 것은 아닙니다. PCB·기둥이 흔들리거나 판이 휘면 RF 시험 전에 원인을 수정합니다.</p></div></div>
    <p class="source-note">설계 판단과 검사 범위: <a href="records/a02-design-review.md">A0.2 비교 검토</a> · <a href="records/a02-design-verification.json">독립 재검사 기록</a>. 기둥 치수: <a href="https://www.we-online.com/components/products/datasheet/970300365.pdf">Würth 30 mm</a> / <a href="https://www.we-online.com/components/products/datasheet/971350365.pdf">35 mm 제조사 도면</a>.</p>
  </section>
'''
assert marker in s;s=s.replace(marker,review+marker)
s=s.replace('<a href="#calibration">연결 순서</a>','<a href="#design-review">설계 비교</a><a href="#calibration">연결 순서</a>')
s=s.replace('1~100 MHz, 401점, linear','1~100 MHz, 1601점, linear')
s=s.replace('−20 dBm / 1 kHz / 실제 평균값 기록','−30 dBm / 1 kHz / 평균 4회 시작안, 실제 지원값 기록')
s=s.replace('fixture_empty.s2p','fixture_A02_empty.s2p').replace('fixture_probe_loaded.s2p','fixture_A02_probe_loaded.s2p')
s=s.replace('probe_transfer_01.s2p','fixture_A02_probe_transfer.s2p').replace('probe_transfer_01.json','fixture_A02_probe_transfer.json').replace('probe_transfer_02.s2p … 05.s2p','fixture_A02_repeat_01.s2p … 05.s2p')
s=s.replace('PCB 교정지그 A0.1: 새 구조 초안. 이 페이지의 CAD·교정 절차는 RF 성능 확인 전입니다.', '평판 PCB 교정지그 A0.2: 새 저장 파일의 ERC/DRC와 공칭 전류 경로·간격을 재검사했습니다. RF 성능은 미측정입니다.')
s=s.replace('원본 조립 CAD에서 PCB 형상, LibreVNA 연결과 50 Ω 부하 이동을 직접 살펴봅니다.', '평판 PCB 1장 A0.2의 실제 CAD, 이전 3장 구조 비교, LibreVNA 연결과 50 Ω 부하 이동을 살펴봅니다.')
p.write_text(s,encoding='utf-8')

p=REPORT/'report.js';s=p.read_text(encoding='utf-8')
s=s.replace('원본 CAD · PCB A0.1 / 집게 A0.3','현재 · 평판 PCB A0.2 / 집게 A0.3')
s=s.replace('fixture_empty.s2p','fixture_A02_empty.s2p').replace('fixture_probe_loaded.s2p','fixture_A02_probe_loaded.s2p').replace('probe_transfer_01.s2p','fixture_A02_probe_transfer.s2p')
s=s.replace('지그 IN','지그 J1 · IN').replace('지그 OUT','지그 J2 · OUT')
start=s.index('const pathNotes=');end=s.index('function updateExample()',start)
s=s[:start]+'''const pathNotes={
 A02:{all:"같은 한 장의 PCB 안에서 중앙 SIG와 바깥 GND를 분리합니다. 두 창 사이 중앙 다리만 코어 안으로 들어갑니다.",signal:"① 신호: J1 중심 핀 → 같은 보드의 SIG 동박 → 중앙 다리 → J2 중심 핀. 양면 모두 SIG이며 점퍼선이 없습니다.",return:"② 귀환: J2 외피의 GND 핀 → 같은 보드의 양옆 바깥 레일 → J1 외피의 GND 핀. 코어 구멍 밖으로 돌아갑니다."},
 A01:{all:"이전 비교용 구조입니다. Frame과 양끝 EndPanel 2장을 접합합니다. 아래 조립·교정 설명은 현재 A0.2 기준입니다.",signal:"이전 A0.1: SMA 중심 → 점퍼 → Frame 중앙 SIG → 점퍼 → 반대 SMA 중심입니다.",return:"이전 A0.1: SMA 외피 → EndPanel → Frame 양옆 귀환 → 반대 EndPanel → 반대 SMA 외피입니다."}
};
window.updateRFCPPath=()=>{const v=window.rfcpViewers?.structure;const mode=document.querySelector('button[data-path][aria-pressed="true"]').dataset.path;document.getElementById("path-explanation").textContent=pathNotes[v?.revision||"A02"][mode];};
document.querySelectorAll("button[data-path]").forEach(btn=>btn.addEventListener("click",()=>{const mode=btn.dataset.path;document.querySelectorAll("button[data-path]").forEach(b=>b.setAttribute("aria-pressed",String(b===btn)));window.rfcpViewers?.structure?.setPath(mode);window.updateRFCPPath();}));
'''+s[end:]
p.write_text(s,encoding='utf-8')

p=REPORT/'report.css';s=p.read_text(encoding='utf-8');s+='''
.revision-controls{display:flex;flex-wrap:wrap;gap:9px;padding:20px 24px 8px}.revision-note{margin:0;padding:5px 24px 17px;color:var(--sc-muted);font-size:13px;border-bottom:1px solid var(--sc-line)}.review-grid{margin-top:32px}.review-grid ul{padding-left:23px}.review-grid li{margin-bottom:10px}@media(max-width:540px){.revision-controls{padding:14px 12px 6px}.revision-controls button{font-size:12px;flex:1 1 auto}.revision-note{padding:5px 14px 14px;font-size:12px}}
''';p.write_text(s,encoding='utf-8')

p=REPORT/'records/bench-checklist.md';s=p.read_text(encoding='utf-8').replace('v0.2','v0.4 · 평판 A0.2')
s=s.replace('실제 두께·SMA·슬롯 조립','실제 두께·SMA 납땜·나일론 기둥 조립')
s=s.replace('SMA 체결·슬롯 납땜·코어 접합·권선 끼임·간섭 점검.','SMA 핀 납땜·네 모서리 고정·코어 접합·권선 끼임·간섭 점검.\n- [ ] 기둥/나사 끝 닿음·흔들림·PCB 휨 없음. 케이블 무게 별도 지지.')
s=s.replace('401점 linear / −20 dBm / IF BW 1 kHz / 실제 평균값 기록','1601점 linear / −30 dBm / IF BW 1 kHz / 평균 4회 시작안, 실제 값 기록')
s=s.replace('fixture_empty.s2p','fixture_A02_empty.s2p').replace('fixture_probe_loaded.s2p','fixture_A02_probe_loaded.s2p').replace('probe_transfer_01.s2p','fixture_A02_probe_transfer.s2p')
s=s.replace('지그 IN','지그 J1 · IN').replace('지그 OUT','지그 J2 · OUT')
p.write_text(s,encoding='utf-8')

p=ATLAS/'reports.json';d=json.loads(p.read_text(encoding='utf-8'))
for r in d['reports']:
    if r['id']=='rf-current-probe':
        r['summary']='평판 PCB 1장 A0.2의 실제 CAD를 돌려 보고 이전 3장 구조와 비교합니다. 조립 개선과 남은 검증, LibreVNA 케이블·50 Ω 부하 이동을 안내합니다.'
        r['coverAlt']='평판 PCB 한 장과 네 모서리 기둥, 위로 향한 SMA에 연결한 케이블·50 Ω 부하를 보여주는 실제 CAD 교정 화면'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated A02 flat-fixture presentation')
