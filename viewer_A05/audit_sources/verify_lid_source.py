from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
O=Path(__file__).resolve().parent;R=O.parents[1]
old=O/'fem_A10/source_lid.step';new=R/'mechanical/assembly_A10_DRAFT/parts/UpperLid_FREE_DRAFT.step'
a=Part.read(str(old));b=Part.read(str(new));sa=hashlib.sha256(old.read_bytes()).hexdigest();sb=hashlib.sha256(new.read_bytes()).hexdigest()
settings=json.loads((O/'fem_A10/mesh_1p6/settings.json').read_text());assert sa==settings['step_sha256']
diff=a.cut(b).Volume+b.cut(a).Volume
res=dict(classification='CALCULATED_BREP_EQUIVALENCE',fem_source_sha256=sa,current_source_sha256=sb,symmetric_difference_mm3=diff,pass_geometry=diff<1e-6)
(O/'fem_A10/source_equivalence.json').write_text(json.dumps(res,indent=2)+'\n');print(res)
