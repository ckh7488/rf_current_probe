from pathlib import Path
import json
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
out={}
for n in ['LowerBody_FREE_DRAFT','UpperLid_FREE_DRAFT','CommonBase_FREE_DRAFT','C03_Jaw1_DRAFT']:
 sh=Part.read(str(R/'mechanical/assembly_A09_DRAFT/parts'/(n+'.step')));b=sh.BoundBox
 rows=json.loads((O/'wall_scan_A09'/(n+'.json')).read_text())
 rr=[]
 for row in sorted(rows,key=lambda q:q['inward_chord_mm'])[:25]:
  p=row['point_stl_mm'];row['point_world_mm']=[p[0]+b.XMin,p[1]+b.YMin,p[2]+b.ZMin];rr.append(row)
 out[n]=rr
(O/'thin_coordinates.json').write_text(json.dumps(out,indent=2)+'\n')
for n,rr in out.items():print(n,[(r['inward_chord_mm'],r['point_world_mm'],r['normal']) for r in rr[:8]],flush=True)
