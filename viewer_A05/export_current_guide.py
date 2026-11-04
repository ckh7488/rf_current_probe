"""Read-only free-print and tool meshes from frozen A14 source."""
from pathlib import Path
import json,hashlib
import FreeCAD as A, Part
P=Path(__file__).resolve().parent; R=P.parent; C=R/'mechanical/assembly_A14_DRAFT'; V=A.Vector
doc=A.openDocument(str(C/'RFCP_A14_Integrated_DRAFT.FCStd'))
old=json.loads((P/'guide_sources/geometry_supplements.json').read_text()); out={'ToolM6':old['ToolM6']}; sources={}
for n in ['UpperLeft','UpperRight']:
 f=C/'parts'/f'{n}_A14_DRAFT.step';s=Part.read(str(f));vs,tr=s.tessellate(.15)
 out[n+'Free']=dict(vertices=[list(v) for v in vs],triangles=tr,color='#5a9daf',group='SUPPLEMENT')
 sources[f.relative_to(R).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
for i,s in enumerate(doc.getObject('CalibrationNuts').Shape.Solids):
 vs,tr=s.tessellate(.15);out['CalibrationNut'+str(i+1)]=dict(vertices=[list(v) for v in vs],triangles=tr,color='#ded8c3',group='BASE',sign=1 if s.CenterOfMass.x>0 else -1)
f=C/'RFCP_A14_Integrated_DRAFT.FCStd';sources[f.relative_to(R).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
out['_sources']=sources
(P/'guide_sources/geometry_supplements_a14.json').write_text(json.dumps(out,separators=(',',':')))
A.closeDocument(doc.Name)
print('A14 free print meshes and individual calibration nuts exported')
