"""Audit new DRAFT artifacts and preserved originals after the CAD/EDA checks."""
from pathlib import Path
import csv
from datetime import datetime,timezone
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
errors=[]
def check(condition,message):
    if not condition:errors.append(message)
def hashcheck(path,expected):
    check((ROOT/path).is_file() and sha(ROOT/path)==expected,f'Hash mismatch: {path}')
for path,expected in {'AGENTS.md':'24ce532f7accc6f56caebbbc499ca28b9a3ffbcfb0fac77c717b90d6e9c259dc','docs/history/RF_CURRENT_PROBE_WHITEPAPER_0.1.md':'a89eb1a47eed1dbf0a0005657f6bf931b5d49d811165e8c01ad13e133317919d'}.items():hashcheck(path,expected)
ref_count=0
for folder in ['docs/references','docs/references/fixture_20260917']:
    for row in read(folder+'/manifest.json')['files']:
        hashcheck(folder+'/'+row['file'],row['sha256']);ref_count+=1
for folder in ['hardware/probe_head','hardware/probe_head_A02']:
    r=read(folder+'/review/saved_board_verification.json')
    check(r['saved_board_checks_pass'],f'PCB failed: {folder}')
    for path,expected in r['sha256'].items():hashcheck(folder+'/'+path,expected)
for revision in ['A01','A02']:
    folder=f'mechanical/clamp_{revision}_DRAFT'
    r=read(folder+'/saved_assembly_verification.json');checks=read(folder+'/mechanical_checks.json')
    check(r['saved_native_and_stl_checks_pass'] and checks['nominal_checks_pass'],f'Clamp failed: {revision}')
    hashcheck(folder+f'/RFCP_Clamp_{revision}_DRAFT.FCStd',r['native_file_sha256'])
    hashcheck(folder+'/mechanical_checks.json',r['mechanical_checks_sha256'])
    hashcheck('mechanical/build_clamp'+('_A02' if revision=='A02' else '')+'.py',checks['generator_sha256'])
    for name,row in r['stl_parts'].items():hashcheck(folder+'/parts/'+name+'_DRAFT.stl',row['sha256'])
folder='hardware/calibration_fixture/F_A_A01_DRAFT'
r=read(folder+'/saved_fixture_verification.json');checks=read(folder+'/fixture_checks.json')
check(r['saved_native_and_stl_checks_pass'] and checks['nominal_checks_pass'],'Fixture checks failed')
hashcheck(folder+'/RFCP_F_A_A01_DRAFT.FCStd',r['native_sha256'])
hashcheck(folder+'/fixture_checks.json',r['fixture_checks_sha256'])
hashcheck('hardware/calibration_fixture/build_fixture.py',r['generator_sha256'])
hashcheck('mechanical/clamp_A02_DRAFT/RFCP_Clamp_A02_DRAFT.FCStd',checks['source_head_sha256'])
for name,row in r['stl_parts'].items():hashcheck(folder+'/parts/'+name+'_DRAFT.stl',row['sha256'])
f=read('hardware/probe_head_A02/review/fabrication_verification.json')
check(f['a01_a02_pad_track_via_outline_thickness_equal'] and f['drill_coordinates_match_saved_pcb'],'Fabrication comparison failed')
for name,h in f['files_sha256'].items():hashcheck('hardware/probe_head_A02/fabrication_DRAFT/'+name,h)
hashcheck('hardware/probe_head_A02/RFCP_Head_A02_DRAFT.kicad_pcb',f['source_pcb_sha256'])

link_count=0;mds=[ROOT/'README.md',ROOT/'AGENTS.md']
for directory in ['docs','hardware','mechanical','analysis','tests']:
    mds.extend((ROOT/directory).rglob('*.md'))
for p in mds:
    text=p.read_text(encoding='utf-8-sig')
    for target in re.findall(r'\]\(([^)]+)\)',text):
        target=target.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
        link_count+=1
        check((p.parent/target).exists(),f'Broken local link: {p.relative_to(ROOT)} -> {target}')
for folder in ['measurements/raw','measurements/processed','release']:
    check(not any(p.is_file() for p in (ROOT/folder).rglob('*')),f'Unexpected file in {folder}')
with (ROOT/'docs/REQUIREMENTS.csv').open(encoding='utf-8-sig',newline='') as stream:
    rows=list(csv.reader(stream))
check(len(rows)==57 and all(len(row)==12 for row in rows),'Requirement table changed unexpectedly')
junit=ET.parse(ROOT/'tests/results/process_review_tests.xml').getroot()
totals={key:sum(int(s.get(key,0)) for s in junit.findall('testsuite')) for key in ['tests','failures','errors','skipped']}
check(totals=={'tests':110,'failures':0,'errors':0,'skipped':0},'Prior software test record differs')
result={'data_kind':'CALCULATED','status':'DRAFT - NOT FOR FABRICATION','timestamp_utc':datetime.now(timezone.utc).isoformat(),
 'original_and_reference_hashes_preserved':not any('Hash mismatch' in s for s in errors),
 'references_checked':ref_count,'markdown_files':len(mds),'local_links_checked':link_count,
 'old_and_new_native_reports_hashes_current':not any('Hash mismatch' in s for s in errors),
 'new_printable_stl_count':9,'gerber_count':f['gerber_count'],'pth_count':f['pth_count'],'npth_count':f['npth_count'],
 'prior_software_junit_not_rerun':totals,'requirements_rows':len(rows)-1,
 'measurements_and_release_empty':not any(s.startswith('Unexpected file') for s in errors),'errors':errors}
(ROOT/'tests/results/build_readiness_20260917.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
