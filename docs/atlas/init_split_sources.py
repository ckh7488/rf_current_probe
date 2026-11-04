"""One-time extraction of the reviewed guide into maintainable section sources."""
from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(r'C:\Users\artzy\Documents\ChatGPT\test_board\showcase\reports\rf-current-probe')
S=ROOT/'docs/atlas/source'
for d in ['sections','runtime']:(S/d).mkdir(parents=True,exist_ok=True)
html=(REPORT/'index.html').read_text(encoding='utf-8')
(ROOT/'docs/history/ATLAS_CURRENT_PROBE_DRAFT_v0.3.md').write_text((ROOT/'docs/ATLAS_CURRENT_PROBE_DRAFT.md').read_text(encoding='utf-8'),encoding='utf-8')
data={
 'document':{'revision':'0.5','date':'2026-09-17','cache':'20260917-split5','design_id':'RFCP-FLAT-A02_HEAD-A02_CLAMP-A03_5T','status':'DRAFT — NOT FOR FABRICATION'},
 'fixture':{'revision':'A0.2','model_id':'A02','asset':'fixture-flat-a02','size':'144 × 92.7 × 1.6 mm','pcb_count':1,'mount_spacing':'130 × 76.7 mm','bridge_width_mm':8,'signal_width_mm':6.8,'window_size':'47 × 33.75 mm','posts_height_mm':65,'post_lower':'970300365','post_upper':'971350365','cad_source':'hardware/calibration_fixture_PCB_A02/assembly/assembly_mesh.json'},
 'head':{'revision':'A0.2','size':'20 × 16 × 1.6 mm','core':'2644181281','core_halves':2,'turns':5,'wire_mm':0.3,'aperture_mm':30,'sma':'RFPC-SMA28-F'},
 'clamp':{'revision':'A0.3','max_open_degrees':90},
 'ports':{'input':{'anchor':[0,9.2,-28],'direction':[0,1,0]},'output':{'anchor':[0,9.2,40.7],'direction':[0,1,0]},'probe':{'anchor':[0,-41,15.95],'direction':[0,0,1]}},
 'cad':{'signal_parts':['SignalCopper'],'return_parts':['ReturnCopper'],'pcb_parts':['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput'],'expected_parts':35,'expected_triangles':456702},
 'test':{'start_mhz':1,'stop_mhz':100,'points':1601,'level_dbm':-30,'ifbw_hz':1000,'averages':4,'repeat_count':5,'file_prefix':'fixture_A02','empty_file':'fixture_A02_empty.s2p','loaded_file':'fixture_A02_probe_loaded.s2p','transfer_file':'fixture_A02_probe_transfer.s2p','direct_file':'fixture_A02_direct_pickup.s2p'},
 'assets':{'assembly':'assets/flat-a02-assembly.png','board':'assets/flat-a02-board.png','head':'assets/clamp-a03.png'},
 'documents':{'assembly':'index.html','testing':'testing.html'},
 'sources':['docs/RF_CURRENT_PROBE_WHITEPAPER.md','docs/ASSEMBLY_CONSTRAINTS_20260917.md','docs/G2_BENCH_PROCEDURE.md','docs/END_TO_END_REHEARSAL.md','hardware/calibration_fixture_PCB_A02/README.md','hardware/calibration_fixture_PCB_A02/ASSEMBLY.md','hardware/calibration_fixture_PCB_A02/BOM_DELTA.md','hardware/calibration_fixture_PCB_A02/geometry.json','hardware/calibration_fixture_PCB_A02/verification.json','hardware/calibration_fixture_PCB_A02/assembly/assembly_checks.json','hardware/calibration_fixture_PCB_A02/assembly/assembly_mesh.json','hardware/probe_head_A02/README.md','mechanical/clamp_A03_DRAFT/README.md'],
}
(S/'design.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
replace={'20260917-flat2':'{{document.cache}}','현재 · 평판 PCB A0.2 / 집게 A0.3':'현재 · 평판 PCB {{fixture.revision}} / 집게 {{clamp.revision}}','assets/flat-a02-assembly.png':'{{assets.assembly}}','assets/flat-a02-board.png':'{{assets.board}}','144 × 92.7 × 1.6 mm':'{{fixture.size}}','130 × 76.7 mm':'{{fixture.mount_spacing}}','47 × 33.75 mm':'{{fixture.window_size}}','RFPC-SMA28-F':'{{head.sma}}','2644181281':'{{head.core}}','fixture_A02_empty.s2p':'{{test.empty_file}}','fixture_A02_probe_loaded.s2p':'{{test.loaded_file}}','fixture_A02_probe_transfer.s2p':'{{test.transfer_file}}','fixture_A02_probe_transfer.json':'{{test.file_prefix}}_probe_transfer.json','fixture_A02_repeat_':'{{test.file_prefix}}_repeat_','5턴':'{{head.turns}}턴','1601점':'{{test.points}}점','−30 dBm / 1 kHz / 평균 4회':'{{test.level_dbm}} dBm / {{test.ifbw_hz}} Hz / 평균 {{test.averages}}회'}
def template(text):
 for a,b in replace.items():text=text.replace(a,b)
 return text
for section in ['purpose','structure','design-review','calibration','conversion','quality','scope','records']:
 match=re.search(r'  <section id="'+section+r'">.*?</section>',html,re.S)
 assert match,section
 (S/'sections'/f'{section}.html').write_text(template(match.group())+'\n',encoding='utf-8')
for f in ['cad-viewer.js','report.js','report.css']:
 (S/'runtime'/f).write_text(template((REPORT/f).read_text(encoding='utf-8')),encoding='utf-8')
shutil.copy2(REPORT/'records/bench-checklist.md',S/'bench-checklist.md')
print('Extracted modular sources; do not rerun this bootstrap after editing source/.')
