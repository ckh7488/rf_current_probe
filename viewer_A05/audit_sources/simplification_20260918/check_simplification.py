"""Saved geometry: deleted loss-prevention parts, retained repairs, open nut loading."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
paths={r:R/f'mechanical/assembly_{r}_DRAFT/RFCP_{r}_Integrated_DRAFT.FCStd' for r in ['A11','A13']}
paths.update({r:R/f'mechanical/cable_clamp_{r}_DRAFT/Cable_Clamp_{r}_DRAFT.FCStd' for r in ['C05','C07']})
ds={r:A.openDocument(str(p)) for r,p in paths.items()}
shape=lambda r,n:ds[r].getObject(n).Shape
def same(a,b):return a.cut(b).Volume+b.cut(a).Volume
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def overlap(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
repairs={n:same(shape('A11',n),shape('A13',n)) for n in ['LowerBody','UpperLid','LowerKeeper','UpperKeeper']}
repairs.update({'C07_'+n:same(shape('C05',n),shape('C07',n)) for n in ['Frame','DriveYoke','TopBridgeJaw','Jaw1','Jaw2']})
a=ds['A13'];names=[o.Name for o in a.Objects];assert not any(any(s in n for s in ['NutCover','NutCap','Retainer','BasePanel']) for n in names)
base=shape('A13','CommonBase');nuts=shape('A13','CalibrationNuts').Solids
nut_paths=[]
for n in nuts:
 sign=1 if n.CenterOfMass.x>0 else -1
 for step in range(21):nut_paths.append(overlap(mv(n,x=sign*step),base))
for n in [n for n in names if n.startswith('MountNut')]:
 for step in range(11):nut_paths.append(overlap(mv(shape('A13',n),y=-step),base))
for n in shape('A13','HeadSquareNuts').Solids:
 for step in range(21):nut_paths.append(overlap(mv(n,z=step),shape('A13','LowerBody')))
for n in ['BridgeNut1','BridgeNut2']:
 for step in range(21):nut_paths.append(overlap(mv(shape('C07',n),z=step),shape('C07','DriveYoke')))
report=dict(classification='CALCULATED_SAVED_CAD_NOT_PHYSICAL_TEST',sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},preserved_shape_difference_mm3=repairs,nut_loading_positions=len(nut_paths),max_nut_loading_overlap_mm3=max(nut_paths),deleted_loss_prevention_parts=True,limits=['Nuts may fall out when screws are fully removed.','Nominal insertion paths only; actual hand/tool access and printed fit need trial assembly.','No new RF, force, creep or durability qualification.'])
report['pass']=max(repairs.values())<1e-4 and max(nut_paths)<1e-4
(O/'simplification_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
