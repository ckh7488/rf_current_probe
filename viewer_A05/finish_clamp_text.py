from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'clamp_viewer.js';s=p.read_text(encoding='utf-8')
s=s.replace('연결틀을 수직 가이드에 넣습니다.','연결틀을 앞에서 수직 가이드 사이에 끼웁니다.')
s=s.replace("V(.42,.24,.83).normalize().multiplyScalar(d)","(mode==='pair'?V(1,.45,.65):V(.42,.24,.83)).normalize().multiplyScalar(d)")
p.write_text(s,encoding='utf-8')
p=P/'build_clamp_site.py';s=p.read_text(encoding='utf-8')
s=s.replace("v=json.loads((C/'verification.json').read_text());assert v['pass']", "v=json.loads((C/'verification.json').read_text());assert v['pass']\na=json.loads((C/'assembly_verification.json').read_text());assert a['pass'];assert a['native_sha256']==v['native_sha256']")
s=s.replace("'verification.json','README.md'", "'verification.json','assembly_verification.json','README.md'")
p.write_text(s,encoding='utf-8')
