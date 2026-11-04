from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];P=R/'viewer_A05';O=Path(__file__).resolve().parent
def read(p):return p.read_text(encoding='utf-8')
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
readme='''# A13 / C07 — 분실방지 부품 제거

2026-09-18 · DRAFT — NOT FOR FABRICATION

## 변경

- 프로브 너트 덮개 2개, 교정 PCB 너트 덮개 4개, 앞뒤 클램프 너트 덮개 4개와 받이를 제거했다.
- 바닥의 노란 너트 유지판 1개, 판 고정 M4 나사·너트 2쌍을 제거했다.
- 출력물은 12종 26개에서 **10종 15개**로 줄었다. 코어 고정바, 탄성 뚜껑, 권선 접근, 닫힌 경사 홈과 기존 얇은 벽 보강은 유지했다.
- 원래의 짧고 열린 사각너트 자리를 사용한다. 교정 PCB는 나일론 날개너트와 열린 받침을 유지하되 긴 받이와 덮개를 없앴다.
- M6 축의 잠금너트와 와셔는 축 위치 조절에 필요한 작동 부품이므로 유지했다. 너트 분실방지용 추가 부품이 아니다.

## 조립

1. 바닥을 뒤집어 여섯 사각너트를 놓고 잡아주면서 모듈의 M4×20 나사를 체결한다. 별도 밑판을 조립하지 않는다.
2. 프로브와 케이블 가로대의 사각너트는 앞쪽 열린 홈으로 넣고 반대편 나사를 시작한다. 너트 홈이 회전을 제한하고, 조이면 본체 받침면에 밀착한다.
3. 교정 PCB 날개너트는 받침의 바깥쪽 입구로 넣은 뒤 위쪽에서 M3 나사를 조인다. 초도 배치는 헤드를 바닥에 올리기 전에 한다.
4. 코어 고정바와 헤드 PCB는 기존 나일론 관통 체결을 유지한다. M6 축은 와셔와 잠금너트를 먼저 놓고, 10 mm 스패너로 너트를 잡고 큰 노브를 돌려 조립한다.

**나사를 완전히 빼면 너트가 빠질 수 있다. 분해할 때 직접 챙긴다.** 이 상태를 결함으로 보고 덮개를 다시 추가하지 않는다. 억지 압입이나 출력 나사산을 사용하지 않는다.

## 출력·검증 범위

parts/의 STL 10종: 헤드 4종 각1개, 공통 바닥1개, C07 클램프5종 각2개. 뚜껑은 반드시 UpperLid_FREE_DRAFT를 사용한다. 조립체 STEP의 휘어진 뚜껑은 출력용이 아니다.

검증 기록은 reviews/simplification_20260918 및 각 revision의 JSON을 따른다. 공칭 CAD 간섭·일부 삽입 경로와 출력 메쉬를 확인한 범위이며, 손조립·공구 전체 호환·출력 공차·내구성·RF 시험은 미실행이다. 최종 노브축과 팔로워 구매 규격도 미확정이다. 업체 제출이나 주문·결제는 갱신하지 않았다.

재제작: FreeCAD 1.0.2에서 build_cable_clamp_C07.py → build_assembly_A13.py. A07/A05 원본 입력은 유지한다. common_nut_cap.py는 더 이상 사용하지 않는다.
'''
write(O/'README.md',readme)
write(R/'mechanical/assembly_A13_DRAFT/README.md',readme)
clamp='''# C07 케이블 중심 클램프

2026-09-18 · DRAFT — NOT FOR FABRICATION

C06의 가로대 너트 덮개 2개와 받이를 제거했다. 출력물은 한 클램프당 **5종 5개**(Frame, DriveYoke, TopBridgeJaw, Jaw1, Jaw2)다. 가로대를 열 때 나사를 완전히 빼므로 사각너트를 직접 챙긴다. 원래의 짧고 열린 홈이 너트 회전을 제한한다.

홈 위 3.7 mm 보강과 구동너트 홈의 공칭 1 mm 방향전환 여유는 유지했다. 마지막은 조이는 방향으로 가볍게 맞춘다. 축 잠금너트를 과조여 구동너트 여유를 없애는 구조가 아니다.

처음에는 아래 턱을 열린 가이드에 넣고 요크를 앞에서 삽입한 뒤 팔로워를 연결한다. 와셔와 M6 잠금너트를 먼저 놓고 위에서 노브축을 넣는다. 10 mm 스패너로 너트를 잡고 큰 노브를 돌린다. 프레임을 꽉 죄지 않고 회전 여유를 남긴다. M6 잠금너트는 기존 Bossard BN33024/5813950(M6×1, AF10, H6) 후보를 유지한다. 노브축과 팔로워의 최종 구매품, 실제 공차와 반복 사용은 확인 전이다.

가로대 사각너트는 앞에서 넣고 손나사 두 개로 가로대를 고정한다. 덮개·스냅 팔·별도 분실방지판은 없다. 완전 분해 시 너트를 직접 받친다.

공칭 기구 범위 Ø6–26 mm. 강체 간섭·삽입 경로 검증은 verification.json과 assembly_verification.json을 따른다. 실제 마찰·외피 눌림·공구/손 접근·내구성·RF 무영향을 보증하지 않는다. 조임 힘 제한 장치는 없다.

재제작 원본: ../build_cable_clamp_C07.py, Cable_Clamp_C07_DRAFT.FCStd, parts/*.stl. FreeCAD 1.0.2. 너트 캡 공용 helper는 필요 없다.
'''
write(R/'mechanical/cable_clamp_C07_DRAFT/README.md',clamp)
write(O/'BOM_DELTA.md','''# A12/C06 → A13/C07 변경분

삭제: CommonNutCap 출력10개, BaseNutRetainer 출력1개, BasePanelScrew M4×12 2개, BasePanelNut M4 2개.

유지: 모듈 고정 M4×20 6개와 사각너트6개, 프로브/가로대 체결품, M3 나일론 날개너트4개, M6 작동축 잠금너트2개 및 와셔, 코어/PCB 나일론 체결품.

최신 출력 수량은 A13 10종15개. 기존 구매서·공급사 제출본에는 이전 리비전이 있을 수 있다. 이번에는 구매 가격이나 발주 장바구니를 변경하지 않았다. A12/C06 덮개와 밑판은 새로 주문하지 않는다.
''')
# Current routes only; earlier revision artifacts remain available as history.
for name in ['assembly_template.html','assembly_viewer.js','clamp_template.html','clamp_viewer.js','build_assembly_site.py','build_clamp_site.py','verify_current_cad_viewer.js']:
 p=P/name;s=read(p).replace('A12','A13').replace('C06','C07');write(p,s)
p=P/'assembly_viewer.js';s=read(p)
begin=s.index('<details open><summary>너트를 넣고 조이는 방법')
end=s.index('<details><summary>권선',begin)
s=s[:begin]+'''<details open><summary>너트를 넣고 조이는 방법</summary><p>프로브와 가로대의 사각너트를 짧고 열린 홈으로 넣고, 반대편 나사를 조입니다. 홈은 회전을 제한하며 조이면 너트가 본체 받침면에 밀착합니다. 바닥은 뒤집어서 너트를 잡고 모듈을 체결합니다.</p><p>분실방지 덮개와 바닥 노란 판을 제거했습니다. 나사를 완전히 빼면 너트가 빠질 수 있으므로 직접 챙깁니다. 교정 PCB 날개너트는 바깥쪽에서 넣고, M6 축은 스패너로 잡아 처음 조립합니다.</p><p><a href="compare.html?part=remove_head_covers">제거한 부품 전후 3D →</a></p></details>'''+s[end:]
s=s.replace('너트를 먼저 넣고 탈락 방지 덮개를 닫은 뒤, 위에서 나사를 조입니다.','바깥쪽 열린 자리로 너트를 먼저 넣고 위에서 나사를 조입니다. 나사를 완전히 뺄 때는 너트를 받쳐 줍니다.')
s='\n'.join(line for line in s.splitlines() if 'if(explode&&/NutCover|' not in line)+'\n'
begin=s.index("(/NutCover/.test(p.name)?");end=s.index("p.local==='LeadScrewKnob'",begin)
s=s[:begin]+'('+s[end:];write(p,s)
p=P/'clamp_viewer.js';s=read(p)
begin=s.index(",BridgeNutCover1:");end=s.index('};',begin);s=s[:begin]+s[end:]
s=s.replace('열고 닫아도 너트는 제자리에','다섯 출력 부품으로 조립')
s=s.replace('기존 다섯 출력 부품에 너트 탈락 방지 덮개를 더했습니다. 작은 손나사를 완전히 빼도 사각 너트를 다시 넣지 않도록 했습니다.','너트 덮개와 받이를 제거하고 다섯 출력 부품으로 정리했습니다. 작은 손나사를 완전히 뺄 때는 사각너트를 직접 챙깁니다.')
s=s.replace('가로대용 사각 너트를 넣고 탈락 방지 덮개를 닫습니다. 덮개 조립 상태를 확인한 뒤 가로대를 올리고 손나사 두 개로 고정합니다.','가로대용 사각너트를 앞쪽 열린 홈에 넣고, 가로대를 올려 손나사 두 개로 고정합니다. 별도 덮개는 없습니다.')
write(p,s)
for name in ['build_assembly_site.py','build_clamp_site.py']:
 p=P/name;s=read(p)
 s='\n'.join(line for line in s.splitlines() if "assert cv['helper_sha256']" not in line and "assert v['helper_sha256']" not in line and "z.write(R/'mechanical/common_nut_cap.py'" not in line)+'\n'
 s=s.replace(",R/'mechanical/common_nut_cap.py'",'')
 if name=='build_assembly_site.py':
  start=s.index("audit=json.loads(");end=s.index("mesh=json.loads",start)
  s=s[:start]+'''audit=json.loads((R/'reviews/simplification_20260918/simplification_verification.json').read_text());assert audit['pass']
for rel,h in audit['sources'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
scan=json.loads((R/'reviews/simplification_20260918/print_scan_A13/summary.json').read_text());assert scan['pass_identity_and_mesh'] and scan['below_1p5mm_samples']==0
'''+s[end:]
  s=s.replace('너트의 쉬운 삽입·회전 방지·탈락 방지와 새 부품의 제작성을 검토했습니다.','분실방지 덮개10개와 바닥 유지판1개를 제거해 출력물을26개에서15개로 줄였습니다. 기존 보강 형상과 열린 너트 삽입 경로를 확인했습니다.')
  s=s.replace('reviews/nut_access_20260918','reviews/simplification_20260918').replace('reviews/independent_a12_20260918','reviews/simplification_20260918')
  s=s.replace("['reviews/simplification_20260918','reviews/a12_20260918','reviews/c06_20260918','reviews/simplification_20260918']","['reviews/simplification_20260918']")
 else:s=s.replace('출력용 솔리드와 너트 덮개 조립을 별도로 검사했습니다.','분실방지 덮개를 제거했습니다. 출력용 솔리드와 열린 가이드 조립 경로를 검사했습니다.')
 write(p,s)
p=P/'verify_current_cad_viewer.js';s=read(p).replace('Object.keys(am).length>73','Object.keys(am).length===71').replace('Object.values(cm).filter(x=>x.printed).length>5','Object.values(cm).filter(x=>x.printed).length===5')
begin=s.index('for(const [name,p] of Object.entries(am).filter');end=s.index('for(const offset',begin)
s=s[:begin]+"assert(!Object.keys(am).some(n=>/NutCover|NutCap|Retainer|BasePanel/.test(n)));\n"+s[end:]
s=s.replace('reviews/nut_access_20260918','reviews/simplification_20260918');write(p,s)
# Comparison history is retained but the default shows removal, not the rejected caps.
p=P/'compare_3d_viewer.js';s=read(p).replace("c.after==='A12'||c.after==='C06'","c.after==='A13'||c.after==='C07'");write(p,s)
p=P/'compare_3d_template.html';s=read(p).replace('이번 수정 · A11 / C05 → A12 / C06','이번 수정 · 분실방지 부품 제거').replace('이전 수정 14곳도 3D로 보기','이전 수정 기록 20곳').replace('A09 / C03부터 A11 / C05까지의 이전 수정 기록입니다. 현재 전체 조립체에는 이 보강과 이번 수정이 함께 반영돼 있습니다.','과거 리비전 기록입니다. A12/C06의 덮개·밑판은 이번 A13/C07에서 제거했습니다. 이전 보강은 유지합니다.');write(p,s)
p=P/'build_compare_3d.py';write(p,read(p).replace('nut_access_20260918','simplification_20260918'))
print('Updated current CAD documents and viewer sources; preserved historical artifacts.')
