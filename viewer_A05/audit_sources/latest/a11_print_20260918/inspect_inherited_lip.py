"""Bound the A10 source surface behind the A11 sampled thin-edge flag."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
p=R/'mechanical/assembly_A10_DRAFT/parts/LowerBody_FREE_DRAFT.step';s=Part.read(str(p))
point=A.Vector(-2.438593334484011,-34,4.791118589031576)
faces=[]
for i,f in enumerate(s.Faces):
 if f.distToShape(Part.Vertex(point))[0]<1e-7:
  b=f.BoundBox;faces.append({'face_index':i,'area_mm2':f.Area,'bounds_mm':{'min':[b.XMin,b.YMin,b.ZMin],'max':[b.XMax,b.YMax,b.ZMax]}})
sections=[]
for z in [-2,-1,0,3,4.7,4.74,4.76,4.8,4.89,4.91,6,7.7]:
 section=s.common(Part.makeLine(A.Vector(point.x,-45,z),A.Vector(point.x,-30,z)))
 sections.append({'z_mm':z,'solid_intervals_y_mm':[[e.BoundBox.YMin,e.BoundBox.YMax] for e in section.Edges]})
result={'classification':'CALCULATED_SOURCE_SURFACE_EXTENT_NOT_LOAD_ANALYSIS','source_step':str(p.relative_to(R)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sample_cad_point_mm':list(point),'faces_containing_point':faces,'sections_through_candidate_z_bounds':sections}
(O/'inherited_lip_extent.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
