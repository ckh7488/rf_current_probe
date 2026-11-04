from pathlib import Path
import json

ATLAS = Path(r"C:\Users\artzy\Documents\ChatGPT\test_board\showcase")
REPORT = ATLAS / "reports/rf-current-probe"
page = REPORT / "index.html"
s = page.read_text(encoding="utf-8")
s = s.replace('href="report.css"', 'href="report.css?v=20260917-cad1"')
s = s.replace('<script src="report.js" defer></script>', '''<script src="vendor/three.min.js" defer></script>
  <script src="vendor/OrbitControls.js" defer></script>
  <script src="cad-viewer.js?v=20260917-cad1" defer></script>
  <script src="report.js?v=20260917-cad1" defer></script>''')

def viewer(kind):
    return f'''<div class="cad-stage" id="{kind}-cad" data-viewer="{kind}">
          <p class="cad-loading" role="status">원본 CAD 모델을 불러오는 중…</p>
          <span class="cad-badge">원본 CAD · PCB A0.1 / 집게 A0.3</span>
        </div>
        <div class="cad-toolbar" role="group" aria-label="3D 보기 조작">
          <span>드래그 회전 · 휠 확대</span>
          <button type="button" data-for="{kind}" data-camera="overview">처음 시점</button>
          <button type="button" data-for="{kind}" data-camera="top">위에서</button>
          <button type="button" data-for="{kind}" data-camera="front">출력 쪽에서</button>
          <button type="button" data-for="{kind}" data-zoom="1.25" aria-label="3D 확대">＋</button>
          <button type="button" data-for="{kind}" data-zoom="0.8" aria-label="3D 축소">−</button>
        </div>'''

old='''      <div class="topology-grid">
        <div class="diagram-wrap" id="topology-diagram" aria-label="PCB 지그 전류 경로"><img src="assets/pcb-path.svg" width="640" height="620" alt="가운데 신호 도체만 코어 구멍을 지나고 양옆 PCB 귀환은 코어 밖을 지나는 구조"></div>'''
new='''      <div class="assembly-controls" role="group" aria-label="원본 CAD 조립 상태">
        <button type="button" data-assembly="open" aria-pressed="true">집게 열기</button>
        <button type="button" data-assembly="closed" aria-pressed="false">집게 닫기</button>
        <button type="button" data-assembly="pcb" aria-pressed="false">PCB·SMA만 보기</button>
        <span>신호·귀환을 선택하면 해당 PCB 경로를 따로 봅니다.</span>
      </div>
      '''+viewer("structure")+'''
      <div class="topology-grid">
        <div class="cad-origin"><p class="eyebrow">저장된 설계 형상 그대로</p><h3>창·슬롯·SMA 위치를 직접 확인하세요.</h3><p>Frame·EndPanel은 KiCad에서 내보낸 형상, 집게·지지대는 조립 CAD입니다. 신호는 금색, 바깥 귀환은 초록색으로 구분합니다.</p><p class="note">CAD 초안이며 실물 사진이 아닙니다. 동박은 경로를 보여주기 위한 색으로 표시하며 솔더마스크·실크는 생략했습니다. 열림 보기에서는 일부 패드·체결 부품을 숨겼습니다.</p></div>'''
assert old in s
s=s.replace(old,new)
s=s.replace('치수는 CAD 설계값입니다. 이 그림은 전류 경로 설명용이며 치수 도면·조립 검사·RF 해석을 대신하지 않습니다.', '치수는 원본 CAD 설계값입니다. 3D 보기 자체가 조립 검사·RF 해석을 뜻하지는 않습니다.')
s=s.replace('새 PCB와 실제 조립 CAD 그림 보기','원본 CAD 렌더와 PCB 외곽을 큰 이미지로 보기')
start=s.index('        <figure class="step-figure">')
end=s.index('</figure>',start)+len('</figure>')
s=s[:start]+'''        <figure class="step-figure">
          <div id="solt-controls" class="solt-controls">
            <div role="group" aria-label="교정 표준 선택"><button type="button" data-standard="open" aria-pressed="false">Open</button><button type="button" data-standard="short" aria-pressed="false">Short</button><button type="button" data-standard="load" aria-pressed="false">Load</button><button type="button" data-standard="thru" aria-pressed="true">Thru</button></div>
            <div class="standard-ports" role="group" aria-label="표준을 연결할 케이블" hidden><button type="button" data-standard-port="1" aria-pressed="true">P1 끝</button><button type="button" data-standard-port="2" aria-pressed="false">P2 끝</button></div>
            <p id="standard-note">Thru를 두 케이블 끝 사이에 연결합니다. 실제 키트의 성별·지연값을 교정 설정에 반영합니다.</p>
          </div>
          '''+viewer("calibration")+'''
          <figcaption id="step-caption">교정 기준면은 케이블 끝입니다. 지그와 프로브를 연결하기 전에 VNA 측정 경로를 교정합니다.</figcaption>
          <p class="cad-disclosure">지그·집게는 원본 CAD입니다. 케이블·외장 부하·교정 표준은 연결 위치를 보여주는 예시 외형이며, 실제 제품의 길이·성별·규격은 보유품으로 확인합니다. 선은 동축 케이블 전체를 나타냅니다.</p>
        </figure>'''+s[end:]
s=s.replace('설계·절차 v0.2','설계·절차 v0.3')
s=s.replace('이 페이지의 도식·교정 절차는','이 페이지의 CAD·교정 절차는')
s=s.replace('전류 경로, LibreVNA 연결, 50 Ω 부하 이동과 교정 조건을 그림으로 살펴봅니다.', '원본 조립 CAD에서 PCB 형상, LibreVNA 연결과 50 Ω 부하 이동을 직접 살펴봅니다.')
page.write_text(s,encoding="utf-8")

js=REPORT / "report.js"
s=js.read_text(encoding="utf-8")
s=s.replace('점선은 자기 결합이며 전선 연결이 아닙니다.', '두 SMA 위치를 모델에서 비교해 보세요.')
s=s.replace('  const img=document.getElementById("step-image");img.src=`assets/step-${index}.svg`;img.alt=s.alt;', '''  document.getElementById("solt-controls").hidden=index!==0;
  window.rfcpViewers?.calibration?.setStep(index);
  document.querySelector("#calibration-cad .cad-badge").textContent=index===0?"교정 표준·케이블 · 외형 예시":"원본 CAD · PCB A0.1 / 집게 A0.3";''')
s=s.replace('document.querySelector("#topology-diagram img").src=`assets/pcb-path${mode==="all"?"":"-"+mode}.svg`;', 'window.rfcpViewers?.structure?.setPath(mode);')
s+='\nselectStep(0);\n'
js.write_text(s,encoding="utf-8")

catalog=ATLAS / "reports.json"
data=json.loads(catalog.read_text(encoding="utf-8"))
for r in data["reports"]:
    if r["id"]=="rf-current-probe":
        r["summary"]="PCB 교정지그와 집게의 원본 CAD를 돌려 보고, 실제 SMA 위치에서 LibreVNA 케이블·50 Ω 부하를 옮기는 교정 순서를 따라갑니다. 실물 RF 측정 전의 설계·시험 절차입니다."
        r["coverAlt"]="PCB 교정지그와 집게 원본 CAD에 P1·P2 동축 케이블과 50 Ω 부하를 연결한 교정 안내 화면"
        if "3D CAD" not in r["tags"]:r["tags"].insert(0,"3D CAD")
catalog.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Updated actual-CAD presentation")
