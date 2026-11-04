"""Optional small common-cap fit sample. Not part of assembly quantities."""
from pathlib import Path
import sys,json,hashlib
import FreeCAD as A,Part,MeshPart
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent/'optional_fit_sample';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'mechanical'))
from common_nut_cap import make_nut_cap_system
receiver,cap,dims=make_nut_cap_system()
out={}
for n,s in [('Receiver_SAMPLE',receiver),('NutCover_SAMPLE',cap)]:
 assert s.isValid() and len(s.Solids)==1
 s.exportStep(str(O/(n+'.step')));b=s.BoundBox;q=s.copy();q.translate(A.Vector(-b.XMin,-b.YMin,-b.ZMin))
 MeshPart.meshFromShape(Shape=q,LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(O/(n+'.stl')))
 out[n]={'dimensions_mm':[b.XLength,b.YLength,b.ZLength],'quantity':1,'volume_mm3':s.Volume}
report={'status':'DRAFT_SAMPLE_NOT_PRODUCTION_APPROVAL','helper_sha256':hashlib.sha256((R/'mechanical/common_nut_cap.py').read_bytes()).hexdigest(),'parts':out,'dimensions':dims,'notes':['Optional 2-part fitting sample. Excluded from the actual assembly BOM.','Does not test host-adapter geometry, nut retention, core preload or RF.','Print in the same 3301PA material and process as the intended assembly.']}
(O/'sample_manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
