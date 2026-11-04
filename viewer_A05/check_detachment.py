"""Finite nominal CAD screen for detachment; no physical/force claims."""
from pathlib import Path
import json, hashlib
import FreeCAD as A
import Part
P=Path(__file__).resolve().parents[1]/'mechanical/clamp_A05_DRAFT'
source=P/'RFCP_A05_Fixture_REVIEW.FCStd'
d=A.openDocument(str(source)); S={o.Name:o.Shape for o in d.Objects if hasattr(o,'Shape')}
B=json.loads((P/'build_report.json').read_text())['parts']
def cp(names): return Part.makeCompound([S[n] for n in names])
fixed=[n for n in S if n.startswith('Head_') and B[n[5:]]['group']=='FIXED']
# Assumes upper assembly, hand knobs, calibration PCB and its corner screws,
# and bench M2 top nuts have already been removed. Keep PCB with lower head.
obstacles=[n for n in S if not n.startswith('Head_') and n not in
 ['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput','CornerPCBScrews','BenchM2Nuts']]
head=cp(fixed); obs=cp(obstacles); rows=[]
for dz in range(0,61,2):
 q=head.copy(); q.translate(A.Vector(0,0,dz)); v=q.common(obs).Volume
 rows.append({'offset_z_mm':dz,'overlap_mm3':v})
res={'classification':'CALCULATED_CAD','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'assumptions':['Upper assembly, hand knobs, calibration board, corner screws and bench M2 nuts removed.',
 'Small head PCB is held together with the lower assembly by the operator during lift.',
 'No cable, tool, hand, friction or manufacturing-tolerance model.'],
 'moving_parts':fixed,'obstacles':obstacles,'samples':rows,
 'pass':all(r['overlap_mm3']<1e-5 for r in rows),
 'max_overlap_mm3':max(r['overlap_mm3'] for r in rows)}
(Path(__file__).parent/'detachment_check.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({'detachment_path_pass':res['pass'],'samples':len(rows),'max_overlap_mm3':res['max_overlap_mm3']}),flush=True)
