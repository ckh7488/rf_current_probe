"""Locate sampled 1 mm chord in exact A10/A11 STEP sections; read-only."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
samples=json.loads((O/'before_roof_cleanup/wall_scan_A11/LowerBody_FREE_DRAFT.json').read_text())
low=[q for q in samples if q['inward_chord_mm']<1.5]
result={'classification':'CALCULATED_EXACT_CAD_SECTION_AT_SAMPLED_FLAG','parts':[]}
for rev in ['A10','A11']:
 p=R/f'mechanical/assembly_{rev}_DRAFT/parts/LowerBody_FREE_DRAFT.step';s=Part.read(str(p))
 row={'revision':rev,'step_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bbox_min_mm':[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin],'flag_sections':[]}
 for q in low:
  # STL samples use A11 print-local coordinates. Both revisions are queried in
  # the same native CAD coordinates, not at their differing STL origins.
  cp=V(q['point_stl_mm'][0]-127,q['point_stl_mm'][1]-72,q['point_stl_mm'][2]-14)
  edge=s.common(Part.makeLine(V(cp.x,-40,cp.z),V(cp.x,-30,cp.z)))
  row['flag_sections'].append({'cad_point_mm':list(cp),'solid_intervals_y_mm':[[e.BoundBox.YMin,e.BoundBox.YMax] for e in edge.Edges]})
 result['parts'].append(row)
result['original_flag_ray_empty_in_current_A11']=all(not q['solid_intervals_y_mm'] for p in result['parts'] if p['revision']=='A11' for q in p['flag_sections'])
(O/'low_chord_inspection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
