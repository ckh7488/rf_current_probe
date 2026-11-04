"""Rebuild this SMA R2 revision from hash-checked preserved baseline, KiCad 10 Python."""
from pathlib import Path
import json, hashlib, re
import pcbnew as p

H = Path(__file__).resolve().parent
c = json.loads((H/'revision.json').read_text(encoding='utf-8'))
for name, digest in c['baseline_hashes'].items():
    assert hashlib.sha256((H/'baseline'/name).read_bytes()).hexdigest() == digest, name
b = p.LoadBoard(str(H/'baseline'/(c['old_name']+'.kicad_pcb')))
changes = []
for fp in b.GetFootprints():
    if fp.GetValue() != 'RFPC-SMA28-F':
        continue
    for pad in fp.Pads():
        signal = pad.GetNumber() == '1'
        old_hole, old_pad = (1.7,2.5) if signal else (1.9,2.8)
        hole, size = (1.9,2.8) if signal else (2.1,3.1)
        assert abs(p.ToMM(pad.GetDrillSize().x)-old_hole) < 1e-6
        assert abs(p.ToMM(pad.GetSize().x)-old_pad) < 1e-6
        pad.SetDrillSize(p.VECTOR2I(p.FromMM(hole),p.FromMM(hole)))
        pad.SetSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)))
        changes.append(dict(ref=fp.GetReference(),pad=pad.GetNumber(),old_hole_mm=old_hole,new_hole_mm=hole,old_pad_mm=old_pad,new_pad_mm=size))
    fp.SetLibDescription('GCT RFPC-SMA28-F; SMA R2: holes 1.90/2.10; pads 2.80/3.10; 5.08 pitch. DRAFT - NOT FOR FABRICATION. Dry fit required.')
    # Move the square ink outline outside the enlarged ground soldermask openings.
    for graphic in fp.GraphicalItems():
        if isinstance(graphic,p.PCB_SHAPE) and graphic.GetLayer() == p.F_SilkS:
            origin = fp.GetPosition()
            for getter,setter in [(graphic.GetStart,graphic.SetStart),(graphic.GetEnd,graphic.SetEnd)]:
                v=getter()-origin
                assert abs(abs(p.ToMM(v.x))-4.1)<1e-5 and abs(abs(p.ToMM(v.y))-4.1)<1e-5
                setter(origin+p.VECTOR2I(p.FromMM(4.35 if v.x>0 else -4.35),p.FromMM(4.35 if v.y>0 else -4.35)))
    libfp = p.FOOTPRINT(fp)
    libfp.SetPosition(p.VECTOR2I(0,0))
    libfp.SetOrientationDegrees(0)
    p.PCB_IO_KICAD_SEXPR().FootprintSave(str(H/c['library']),libfp)
assert len(changes) == c['sma_count']*5
# Keep all original text coordinates/sizes. A04R2/A03R2 identify the physical PCB.
for item in b.GetDrawings():
    if isinstance(item,p.PCB_TEXT):
        item.SetText(item.GetText().replace(c['old_board_label'],c['new_board_label']))
b.GetTitleBlock().SetRevision(c['revision']+' DRAFT')
b.GetTitleBlock().SetDate('2026-09-28')
p.SaveBoard(str(H/(c['new_name']+'.kicad_pcb')), b)
sch = (H/'baseline'/(c['old_name']+'.kicad_sch')).read_text(encoding='utf-8')
sch = sch.replace(c['old_name'], c['new_name'])
sch = sch.replace(c['old_title_label'], c['new_title_label'])
sch = re.sub(r'\(rev "[^"]+"\)', '(rev "'+c['revision']+' DRAFT")', sch, count=1)
sch = re.sub(r'\(date "[^"]+"\)', '(date "2026-09-28")', sch, count=1)
sch = sch.replace('center 1.70; four 1.90', 'center 1.90; four 2.10')
sch = sch.replace('position +/-0.05 mm', 'position +/-0.075 mm')
(H/(c['new_name']+'.kicad_sch')).write_text(sch,encoding='utf-8')
# Baseline project settings/constraints unchanged; names are the new project identity.
(H/(c['new_name']+'.kicad_pro')).write_bytes((H/'baseline'/(c['old_name']+'.kicad_pro')).read_bytes())
(H/'review/intentional_changes.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')
print(json.dumps(dict(revision=c['revision'],changed_sma_pads=len(changes))))
