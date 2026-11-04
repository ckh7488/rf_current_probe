from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'clamp_viewer.js';s=p.read_text(encoding='utf-8')
a=s.index('function pose(');b=s.index('function update()',a)
s=s[:a]+'const pose=window.C01_POSE;\n'+s[b:]
s=s.replace("clamp((open-.55)/.45)*80","clamp((open-.55)/.45)*35")
s=s.replace("host.prepend(renderer.domElement);const camera=", "host.prepend(renderer.domElement);renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','C01 클램프 실제 CAD. 드래그로 회전하고 부품을 클릭하세요.');const camera=")
p.write_text(s,encoding='utf-8')
p=P/'build_clamp_site.py';s=p.read_text(encoding='utf-8');s=s.replace("+(P/'clamp_viewer.js').read_text(encoding='utf-8')", "+(P/'clamp_kinematics.js').read_text(encoding='utf-8')+'\\n'+(P/'clamp_viewer.js').read_text(encoding='utf-8')");p.write_text(s,encoding='utf-8')
