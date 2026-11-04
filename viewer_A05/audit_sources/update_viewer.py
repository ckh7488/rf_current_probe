from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'viewer_A05'
if 'assembly_A10_DRAFT' in (P/'build_assembly_site.py').read_text(encoding='utf-8'):
 raise SystemExit('Migration already applied. Use the current three build_*_site / build_comparison entrypoints.')
for n in ['assembly_template.html','assembly_viewer.js','build_assembly_site.py','clamp_template.html','clamp_viewer.js','build_clamp_site.py']:
 p=P/n;s=p.read_text(encoding='utf-8').replace('A09','A10').replace('C03','C04')
 if n=='assembly_template.html':
  s=s.replace('<span class="draft">통합 설계 검토 · 실물 제작 승인 전</span>','<a href="compare.html">수정 전·후 비교 8장</a><span class="draft">통합 설계 검토 · 실물 제작 승인 전</span>')
 if n=='assembly_viewer.js':
  s=s.replace('23+z','26+z')
  s=s.replace('탄성부를 1.6 → 2.4 mm로 두껍게 하고 길이도 늘렸습니다. 힘과 수명은 아직 시험 전입니다.','탄성부2.4 mm·길이63 mm는 유지했습니다. 이번 실제 형상의 선형 해석에서는 공칭 닫힘 반력 약5.29 N이 나왔습니다. 실제 힘과 장기 수명은 시험 전입니다.')
  s=s.replace('프로브 SMA → 정해진 50 Ω 측정 체인 → 오실로스코프. 주파수별 교정값으로 출력 전압을 전류로 바꿉니다.','프로브 SMA → 정해진 50 Ω 측정 체인 → 오실로스코프. 확인된 주파수의 정현파 성분은 교정값으로 전류로 바꿀 수 있습니다. 광대역 잡음·과도파형 전체의 전류 복원과 현장 보호 체인은 아직 미완료입니다.')
 if n=='clamp_viewer.js':s=s.replace('80,62.5,23','80,62.5,26').replace('80,66,23+','80,66,26+')
 if n=='clamp_template.html':s=s.replace('← 프로브 문서</a>','← 프로브 문서</a><a href="compare.html">수정 전·후 비교</a>')
 if n=='build_assembly_site.py':
  s=s.replace('힘·마찰·RF 실측은 미실행입니다.','추가 너트·케이블 삽입18경로423위치와 출력물40,000점 두께 선별검사도 확인했습니다. 뚜껑 선형 해석 반력은 약5.29 N입니다. 실물·RF 시험은 미실행입니다.')
 p.write_text(s,encoding='utf-8')
print('Viewer source now A10/C04; existing four sections retained.')
