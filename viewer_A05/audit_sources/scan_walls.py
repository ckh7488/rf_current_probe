"""Area-sampled inward ray chords on actual STL; flags, NOT global DFM proof."""
from pathlib import Path
import sys,json,hashlib
import trimesh,numpy as np
R=Path(__file__).resolve().parents[2];rev=sys.argv[1] if len(sys.argv)>1 else 'A09'
P=R/('mechanical/assembly_'+rev+'_DRAFT/parts');out=Path(__file__).resolve().parent/('wall_scan_'+rev);out.mkdir(exist_ok=True)
summary=[]
for p in sorted(P.glob('*.stl')):
 mesh=trimesh.load_mesh(p);pts,faces=trimesh.sample.sample_surface(mesh,4000,seed=20260918)
 directions=-mesh.face_normals[faces];orig=pts+directions*1e-4
 loc,ir,it=mesh.ray.intersects_location(orig,directions,multiple_hits=True)
 dist=np.linalg.norm(loc-orig[ir],axis=1);valid=dist>1e-5
 near=np.full(len(pts),np.inf);np.minimum.at(near,ir[valid],dist[valid]);near+=1e-4
 candidates=np.flatnonzero(near<2.0)
 rows=[dict(point_stl_mm=pts[i].tolist(),normal=mesh.face_normals[faces[i]].tolist(),inward_chord_mm=float(near[i])) for i in candidates]
 (out/(p.stem+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 rec=dict(part=p.name,stl_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),watertight=mesh.is_watertight,samples=4000,sampled_min_mm=float(near.min()),below_2mm_samples=len(rows),below_1p5mm_samples=int(sum(near<1.5)),percentiles_mm=np.percentile(near,[1,5,50]).tolist())
 summary.append(rec);print(json.dumps(rec),flush=True)
(out/'summary.json').write_text(json.dumps(dict(classification='CALCULATED_STL_SAMPLING',trimesh_version=trimesh.__version__,parts=summary,limitations=['Not a certified minimum-wall or manufacturer DFM check.','Normal chords near edges/chamfers/curved surfaces can flag intentional geometry; inspect coordinates.','Area sampling may miss small features; explicit CAD section checks supplement it.']),indent=2)+'\n')
