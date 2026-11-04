from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['assembly_template.html','dist/assembly.html']:
 p=P/name;s=p.read_text(encoding='utf-8');needle='<a href="compare.html">수정 전·후 3D 비교</a>'
 if '<a href="assembly-guide.html">단계별 조립절차서</a>' not in s:
  assert needle in s;s=s.replace(needle,'<a href="assembly-guide.html">단계별 조립절차서</a>'+needle,1);p.write_text(s,encoding='utf-8')
print('Linked assembly procedure from the existing main document.')
