"""Reproduce only this revision from preserved native baseline; KiCad 10 Python."""
from pathlib import Path
import json,hashlib,shutil
import pcbnew as p
H=Path(__file__).resolve().parent
c=json.loads((H/'revision.json').read_text())
b=p.LoadBoard(str(H/'baseline'/(c['old_name']+'.kicad_pcb')))
before=[]
for fp in b.GetFootprints():
 if 'SMA' not in fp.GetValue():continue
 for pad in fp.Pads():
  old=p.ToMM(pad.GetDrillSize().x)
  target=1.7 if pad.GetNumber()=='1' else 1.9
  assert abs(old-(1.5 if pad.GetNumber()=='1' else 1.7))<1e-6
  pad.SetDrillSize(p.VECTOR2I(p.FromMM(target),p.FromMM(target)))
  before.append(dict(ref=fp.GetReference(),pad=pad.GetNumber(),old_mm=old,new_mm=target))
 fp.SetLibDescription('GCT RFPC-SMA28-F; RFCP clearance revision: centre 1.70, ground 1.90, 5.08 pitch. First-article dry fit required.')
 libfp=p.FOOTPRINT(fp);libfp.SetPosition(p.VECTOR2I(0,0))
 p.PCB_IO_KICAD_SEXPR().FootprintSave(str(H/c['library']),libfp)
for item in b.GetDrawings():
 if isinstance(item,p.PCB_TEXT):item.SetText(item.GetText().replace(c['old_label'],c['new_label']))
b.GetTitleBlock().SetRevision(c['revision']+' DRAFT')
b.GetTitleBlock().SetDate('2026-09-21')
p.SaveBoard(str(H/(c['new_name']+'.kicad_pcb')),b)
sch=(H/'baseline'/(c['old_name']+'.kicad_sch')).read_text(encoding='utf-8')
sch=sch.replace(c['old_name'],c['new_name']).replace(c['old_label'],c['new_label'])
if c['revision']=='A0.4':sch=sch.replace('HEAD A0.3  /', 'HEAD A0.4  /')
sch=sch.replace('SMA recommended holes: center 1.50; four 1.70 on a 5.08 square.', 'RFCP clearance holes: center 1.70; four 1.90 on a 5.08 square.')
sch=sch.replace('Finished-hole tolerance TBD.', 'Finished holes +0.13/-0.08 mm; position +/-0.05 mm; dry fit required.')
sch=sch.replace('(rev "A0.3 DRAFT")','(rev "A0.4 DRAFT")') if c['revision']=='A0.4' else sch.replace('(rev "A0.2 DRAFT")','(rev "A0.3 DRAFT")')
(H/(c['new_name']+'.kicad_sch')).write_text(sch,encoding='utf-8')
shutil.copy2(H/'baseline'/(c['old_name']+'.kicad_pro'),H/(c['new_name']+'.kicad_pro'))
(H/'review/intentional_changes.json').write_text(json.dumps(dict(data_kind='CALCULATED',holes=before),indent=2))
print(json.dumps({'revision':c['revision'],'sma_holes_changed':len(before)}))
