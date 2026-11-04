"""Review a copy with all original ignored ERC keys enabled; preserve source."""
from pathlib import Path
import json,shutil,subprocess,hashlib
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
src=R/'hardware/probe_head_A03';dst=O/'head_strict_erc';dst.mkdir(exist_ok=True)
for p in src.iterdir():
 if p.is_file() and (p.suffix in ['.kicad_sch','.kicad_pro','.kicad_sym'] or p.name in ['fp-lib-table','sym-lib-table']):
  shutil.copyfile(p,dst/p.name)
shutil.copytree(src/'RFCP.pretty',dst/'RFCP.pretty',dirs_exist_ok=True)
p=dst/'RFCP_Head_A03_DRAFT.kicad_pro';d=json.loads(p.read_text())
ignored=json.loads((O/'head_erc.json').read_text())['ignored_checks']
d['erc']={'erc_exclusions':[],'meta':{'version':0},'pin_map':[], 'rule_severities':{r['key']:'warning' for r in ignored}}
p.write_text(json.dumps(d,indent=2)+'\n')
cmd=['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','sch','erc','--severity-all','--exit-code-violations','--format','json','--output',str(O/'head_strict_erc.json'),str(dst/'RFCP_Head_A03_DRAFT.kicad_sch')]
r=subprocess.run(cmd,capture_output=True);(O/'head_strict_erc.log').write_bytes(r.stdout+r.stderr);print('Strict ERC exit',r.returncode)
