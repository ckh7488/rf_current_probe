"""Read-only A13 geometry supplements: free lid and a checked spanner envelope."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
P=Path(__file__).resolve().parent;R=P.parent;O=P/'guide_sources';O.mkdir(exist_ok=True);V=A.Vector
src=R/'mechanical/assembly_A13_DRAFT/UpperLid_UNLOADED_DRAFT.step'
lid=Part.read(str(src))
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
wrench=box(74,36,17,20,4,18).cut(box(72,35,20.75,15,6,10.5)).fuse(box(94,36,22,66,4,8))
data={}
for n,s in [('UpperLidFree',lid),('ToolM6',wrench)]:
 vs,tr=s.tessellate(.15);data[n]=dict(vertices=[list(v) for v in vs],triangles=tr,color='#5a9daf' if n=='UpperLidFree' else '#748597',group='SUPPLEMENT')
data['_sources']={str(src.relative_to(R)).replace('\\','/'):hashlib.sha256(src.read_bytes()).hexdigest()}
native=R/'mechanical/assembly_A13_DRAFT/RFCP_A13_Integrated_DRAFT.FCStd'
doc=A.openDocument(str(native))
for i,s in enumerate(doc.getObject('CalibrationNuts').Shape.Solids):
 vs,tr=s.tessellate(.15)
 data['CalibrationNut'+str(i+1)]=dict(vertices=[list(v) for v in vs],triangles=tr,color='#ded8c3',group='BASE',sign=1 if s.CenterOfMass.x>0 else -1)
data['_sources'][str(native.relative_to(R)).replace('\\','/')]=hashlib.sha256(native.read_bytes()).hexdigest()
(O/'geometry_supplements.json').write_text(json.dumps(data,separators=(',',':')))
# Exact part bounds help author anchors without changing any mechanical source.
mesh=json.loads((R/'mechanical/assembly_A13_DRAFT/mesh.json').read_text())
bounds={n:[[min(v[i] for v in p['vertices']),max(v[i] for v in p['vertices'])] for i in range(3)] for n,p in mesh.items()}
(O/'part_bounds.json').write_text(json.dumps(bounds,indent=2))
print('Exported free lid and spanner envelope. Product CAD unchanged.')
