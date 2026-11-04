"""Keep the written guide and public provenance aligned with the CAD viewer."""
from pathlib import Path
import json, hashlib, shutil

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(r"C:\Users\artzy\Documents\ChatGPT\test_board\showcase\reports\rf-current-probe")
review=ROOT/'docs/atlas/review/cad'
manifest=json.loads((REPORT/'assets/fixture-cad.json').read_text(encoding='utf-8'))
evidence_path=REPORT/'records/evidence.json'
evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
evidence['document_revision']='0.3'
evidence['illustrations']='Original saved CAD tessellation for the fixture, PCB, clamp and supports. External cables, mating plugs, load and O/S/L/T standards are illustrative envelopes. No new RF measurement.'
evidence['cad_viewer']={k:manifest[k] for k in ['source','source_sha256','binary_sha256','precision','maximum_coordinate_rounding_mm','triangle_count','geometry_reduction']}
evidence['cad_viewer']['parts']=len(manifest['parts'])
evidence['cad_viewer']['display_omissions']='Open-clamp view hides backing/radial/front pads, keeper screws/nuts and latch screw. PCB-only and net modes intentionally hide the support and head. All 44 source parts remain in the asset.'
evidence['cad_viewer']['accessories']='Illustrative 50-ohm load, mating connectors and coax routes are anchored at the saved SMA envelope end coordinates, not manufacturer-certified fits or cable lengths.'
evidence['cad_viewer']['library']='Three.js r128 with matching OrbitControls and MIT license, vendored in this report.'
source={'project_relative_path':manifest['source'],'sha256':manifest['source_sha256']}
evidence['sources']=[x for x in evidence['sources'] if x['project_relative_path']!=source['project_relative_path']]+[source]
checks=json.loads((review/'browser-checks.json').read_text())
checks.pop('url')
checks['scope']='Browser/CAD display checks only, not RF or physical assembly verification.'
(REPORT/'records/viewer-verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

p=REPORT/'records/source-notes.md';s=p.read_text(encoding='utf-8').replace('/ v0.2 /','/ v0.3 /')
start=s.index('## 그림의 의미');end=s.index('## 일차자료',start)
s=s[:start]+'''## 그림과 3D의 의미

PCB 지그 A0.1의 저장된 assembly_mesh.json을 그대로 웹용 데이터로 옮겼다. 44개 부품, 삼각형 654,058개를 유지했으며 형상 단순화나 재모델링은 하지 않았다. 좌표를 float32로 저장하면서 생긴 최대 반올림은 약 0.00000382 mm다. 이 값은 표시 데이터 변환 오차이며 실물 제작 정밀도를 뜻하지 않는다. 원본·출력 해시는 evidence.json에 남겼다.

Frame·EndPanel 형상과 구리 영역은 KiCad에서 내보낸 CAD이며, 집게·지지대·SMA 외형은 저장된 조립 CAD다. 동박은 경로 구분을 위한 색이고 마스크·실크는 생략했다. 집게 열림은 원본 힌지 축 기준 90° 표시이며, 이 보기에서는 일부 패드·체결 부품을 숨긴다. PCB만 보기와 신호·귀환 강조에서는 다른 부품을 숨긴다. 표시 조작이 새로운 간섭 검사를 실행하지는 않는다.

교정 단계에도 같은 지그 형상을 사용한다. 1단계는 헤드를 숨기고, 2단계는 헤드를 장착해 프로브 출력에 부하를 붙인다. 3단계는 원본 SMA 끝 위치를 기준으로 P2 케이블을 프로브에, 부하를 지그 OUT에 표시한다. 케이블·상대 커넥터·외장 50 Ω 부하·O/S/L/T 표준은 연결 설명용 외형이다. 보유품의 실제 형상·길이·성별·정격이나 물리적 맞춤을 인증한 것이 아니다. Open/Short/Load는 한 표준씩 선택한 포트에 연결하는 모습이고 Thru는 두 케이블 끝을 연결한다.

cross-section.svg는 SIG/SIG와 SIG/GND의 차이를 설명하는 보조 개념도다. 원본 CAD 이미지도 접힌 상세 영역에서 볼 수 있다. 브라우저 조작·모바일 확인 기록은 viewer-verification.json이며 센서 시험 기록과 구분한다.

'''+s[end:];p.write_text(s,encoding='utf-8')

p=REPORT/'README.md';s=p.read_text(encoding='utf-8').replace('v0.2','v0.3')
s=s.replace('- 실제 저장 CAD 이미지와 단순화한 경로·연결 SVG.', '- 저장 CAD 원본 44개 부품을 직접 돌리는 3D 보기: 열기·닫기·PCB 분리·신호/귀환 강조.\n- 원본 SMA 위치에 연결한 단계별 케이블·부하 배치, O/S/L/T 표준과 포트 선택. 액세서리 외형은 예시.')
s=s.replace('`index.html`, `report.css`, `report.js`와 `assets/`, `records/`', '`index.html`, `report.css`, `report.js`, `cad-viewer.js`와 `assets/`, `records/`, `vendor/`')
s=s.replace('공통 theme와 favicon 외에 외부 런타임 의존성이 없다.', '공통 theme와 favicon 외에 다른 보고서나 CDN 의존성이 없다. Three.js r128·OrbitControls·MIT 라이선스를 자체 vendor 폴더에 둔다.')
s+='\n원본 프로젝트의 `docs/atlas/export_cad_viewer.py`로 저장 CAD를 웹 모델로 내보낸다. 모델의 단위·부품별 오프셋·원본 해시는 `assets/fixture-cad.json`에 기록한다. `?step=3#calibration` 링크로 프로브 출력 연결 상태를 바로 열 수 있다.\n'
p.write_text(s,encoding='utf-8')

p=ROOT/'docs/ATLAS_CURRENT_PROBE_DRAFT.md';s=p.read_text(encoding='utf-8').replace('PCB 교정지그 반영 v0.2','원본 CAD 교정 안내 v0.3')
s=s.replace('Atlas에서 그림과 단계별 연결 보기','Atlas에서 원본 CAD와 단계별 연결 보기')
s=s.replace('![PCB 신호와 귀환의 개념도](E:/Current_Probe/docs/atlas/review/pcb-current-path.png)', '![원본 PCB 형상에서 신호 경로 강조](E:/Current_Probe/docs/atlas/review/cad/path-signal.png)')
s=s.replace('그림은 전류 경로 설명용이며 제작 도면을 대신하지 않는다.', '그림은 저장 CAD의 원래 형상이다. Atlas에서는 집게 열기·닫기, PCB만 보기, 경로 강조와 회전·확대를 직접 할 수 있다. 동박 색은 경로 구분용이며 제작 승인이나 RF 검증을 뜻하지 않는다.')
for i in range(4):s=s.replace(f'docs/atlas/review/step-{i}.png',f'docs/atlas/review/cad/step-{i}.png')
s=s.replace('### 네 단계로 연결하기', '### 네 단계로 연결하기\n\n아래는 같은 원본 조립 CAD의 단계별 화면이다. 케이블·상대 커넥터·부하·교정 표준의 외형은 연결 위치 설명용이다. 실제 보유품의 모델·성별·길이는 별도로 확인한다. [3단계 원본 CAD 바로 보기](https://ckh7488.github.io/showcase/reports/rf-current-probe/?step=3#calibration).')
p.write_text(s,encoding='utf-8')
shutil.copy2(review/'step-3.png',REPORT/'cover.png')
print('Updated revision 0.3, source records, local guide and cover.')
