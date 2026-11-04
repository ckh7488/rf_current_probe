from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'mechanical/assembly_A10_DRAFT';C=R/'mechanical/cable_clamp_C04_DRAFT'
b=read(A/'build_report.json');c=read(C/'verification.json');v=read(A/'verification.json');ret=read(A/'retention_mount_verification.json');use=read(O/'use_paths.json')
assert b['pass'] and c['pass'] and v['pass'] and ret['pass'] and use['pass_nominal']
assert b['source_sha256']==sha(R/'mechanical/build_assembly_A10.py')
assert c['source_sha256']==sha(R/'mechanical/build_cable_clamp_C04.py')
assert all(x['native_sha256']==b['native_sha256'] for x in [v,ret,use])
assert read(C/'assembly_verification.json')['native_sha256']==c['native_sha256']
wall=read(O/'wall_scan_A10/summary.json')
for p in wall['parts']:assert p['stl_sha256']==sha(A/'parts'/p['part'])
assert all(p['watertight'] and p['sampled_min_mm']>1.9999 for p in wall['parts'])
pcbs={}
for n in ['head_drc','fixture_drc','head_strict_erc','fixture_erc']:
 d=read(O/(n+'.json'));errs=d.get('violations',[])+d.get('unconnected_items',[])+d.get('schematic_parity',[])+[v for s in d.get('sheets',[]) for v in s['violations']]
 assert not errs and not d['ignored_checks'];pcbs[n]=dict(violations=0,ignored_checks=0,sha256=sha(O/(n+'.json')))
tree=ET.parse(O/'software_tests.xml');suite=tree.getroot().find('testsuite');assert int(suite.get('failures'))==int(suite.get('errors'))==0
assert read(O/'fem_A10/source_equivalence.json')['pass_geometry']
r=dict(status='DRAFT — NOT FOR FABRICATION',classification='AUDIT_SUMMARY_NOT_MEASURED',current=dict(assembly='A10',clamp='C04',head_pcb='A03',fixture_pcb='A02'),native_sha256=b['native_sha256'],source_sha256=b['source_sha256'],printed_unique=10,printed_total=15,static_objects=73,existing_paths=len(v['paths']),existing_positions=sum(len(x) for x in v['paths'].values()),additional_paths=len(use['paths']),additional_positions=sum(x['positions'] for x in use['paths']),core_ADC_cases=len(v['core_ADC_corners'])+len(v['upper_core_ADC_corners']),stl_samples=sum(x['samples'] for x in wall['parts']),sampled_min_mm=min(x['sampled_min_mm'] for x in wall['parts']),fem=read(O/'fem_A10/summary.json'),pcb_checks=pcbs,software_tests=int(suite.get('tests')),physical_tests=0,remaining=['Exact commodity hardware selection and real tool assembly','Print tolerance/warpage, core contact, creep and repeated opening','Cable pressure and real centering','RF fixture local-current validation, calibrated bandwidth and insertion effect','BNC/receiver response, broadband waveform conversion and input protection'])
(O/'audit_summary.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k not in ['fem','pcb_checks']},ensure_ascii=True))
