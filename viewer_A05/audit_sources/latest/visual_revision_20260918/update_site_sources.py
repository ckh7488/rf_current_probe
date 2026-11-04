"""One-time migration of only the maintained A10/C04 viewer sources."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'viewer_A05'
for name in ['build_assembly_site.py','build_clamp_site.py','assembly_template.html','assembly_viewer.js','clamp_template.html','clamp_viewer.js']:
 p=P/name;s=p.read_text(encoding='utf-8');s=s.replace('A10','A11').replace('C04','C05');p.write_text(s,encoding='utf-8')
p=P/'build_comparison.py';s=p.read_text(encoding='utf-8').replace("D/'compare.html'","D/'compare-history.html'")
s=s.replace('<main><h1>','<main><p><a href="compare.html">현재 수정 전후 3D로 돌아가기 →</a></p><h1>');p.write_text(s,encoding='utf-8')
p=P/'assembly_template.html';s=p.read_text(encoding='utf-8').replace('수정 전·후 비교 8장','수정 전·후 3D 비교').replace('<section class="display"><h2>확인한 범위</h2>','<section class="display"><h2>확인한 범위</h2><p><a href="audit/latest-review.html">이번 재검토 결과 보기</a></p>');p.write_text(s,encoding='utf-8')
p=P/'assembly_viewer.js';s=p.read_text(encoding='utf-8')
s=s.replace('선 넣기: 위 나사를 풀고 상부를 들어냅니다.<br>중심 맞추기: 앞뒤 클램프의 큰 노브를 각각 조입니다.','선 넣기: 위 나사를 풀고 상부를 들어냅니다.<br>닫기: 왼쪽 바깥 기둥을 아래 몸체의 ㄱ자 기준에 가볍게 대고 양쪽 나사를 조입니다.<br>중심 맞추기: 앞뒤 큰 노브를 각각 조입니다.')
s=s.replace('이번 실제 형상의 선형 해석에서는 공칭 닫힘 반력 약5.29 N이 나왔습니다.','변경하지 않은 뚜껑 자유 형상의 기존 선형 해석 반력은 약5.29 N입니다.')
s=s.replace('헤드 PCB는 M2 나일론 나사·너트로 고정합니다.</p>','헤드 PCB는 M2 나일론 나사·너트로 고정합니다. 바닥 체결은 M4×20 여섯 개입니다.</p><details><summary>권선·PCB·고정바 조립 순서</summary><ol><li>맨 PCB에서 SMA를 먼저 납땜합니다.</li><li>권선 끝선을 앞으로 자유롭게 둔 채 코어를 받침에 넣습니다.</li><li>PCB를 장착하고 S+ / S−를 배선·납땜한 뒤 검사합니다.</li><li>코어 고정바를 끼우고 나일론 나사로 고정합니다.</li></ol><p class="fine">뚜껑의 ㄱ자 기준은 손으로 맞대는 위치 기준입니다. 자동 정밀 정렬이나 실제 코어 맞댐 반복성이 보장된 구조는 아닙니다.</p></details>')
s=s.replace('PCB를 끼우거나 빼기 전에는 프로브 상부를 엽니다.','교정 PCB 아래의 너트는 기둥 바깥쪽 창에서 얇은 5.5 mm 스패너로 잡고 나사를 조입니다. PCB를 끼우거나 빼기 전에는 프로브 상부를 엽니다.')
s=s.replace('실제로는 앞 노브·뒤 노브를 각각 돌립니다. 외피가 눌리기 전, 가볍게 닿으면 멈춥니다.','실제로는 앞 노브·뒤 노브를 각각 돌립니다. 방향 전환 때 공칭1 mm의 너트 여유가 있어, 마지막은 조이는 방향으로 맞춥니다. 외피가 눌리기 전, 가볍게 닿으면 멈춥니다.')
s=s.replace("LowerKeeper:'아래 코어 고정바 — 위쪽과 같은 이탈 대비 턱을 추가했습니다. 권선을 피해 앞에서 나일론 M3 나사로 가볍게 고정합니다.'","LowerKeeper:'아래 코어 고정바 — 가로대를 위로 옮겨 SMA 플러그와 S+ / S− 앞을 열었습니다. 코어에 닿는 면과 안쪽 이탈 방지턱은 유지했습니다.'")
s=s.replace("LowerBody:'프로브 아래 몸체 — 코어는 넓은 일체형 받침에 놓습니다. 권선과 SMA 앞은 열려 있습니다.'","LowerBody:'프로브 아래 몸체 — 왼쪽 바깥 기둥의 ㄱ자 기준에 뚜껑을 가볍게 맞대고 조입니다. 코어는 넓은 일체형 받침에 놓습니다.'")
p.write_text(s,encoding='utf-8')
p=P/'clamp_viewer.js';s=p.read_text(encoding='utf-8')
s=s.replace('정확한 부품은 선정 전입니다.','5 mm 높이의 M6 사각너트 검토 형상입니다. 홈 높이6 mm라 방향 전환 때 공칭1 mm의 여유가 남습니다. 최종 구매 공차는 확인 전입니다.')
s=s.replace('구경은 검토 범위입니다. 허용 케이블 규격이나 압착력 보장값이 아닙니다.','구동너트 홈의 공칭 여유는 1.8 → 1.0 mm로 줄였습니다. 무유격 구조는 아니므로 마지막은 조이는 방향으로 맞춥니다. 구경·압착력은 보장값이 아닙니다.')
s=s.replace('<li>구동 너트·조절 나사·축 고정부를 장착합니다.</li>','<li>와셔와 M6 잠금너트 두 개를 앞쪽에서 미리 놓고, 위에서 조절 나사를 통과시킵니다. 축을 넣은 뒤 와셔를 옆에서 끼우는 순서는 불가능합니다.</li>')
p.write_text(s,encoding='utf-8')
print('Updated maintained viewer sources only; unrelated WIP preserved.')
