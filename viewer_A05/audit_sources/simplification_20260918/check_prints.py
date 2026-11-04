"""Saved print-file audit adapted from the A11 scan; no product edits.
4000 area samples/part by default. Sampling is not global minimum-wall DFM.
"""
from pathlib import Path
import json,hashlib,csv,argparse
import trimesh,numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--assembly',default='A12')
parser.add_argument('--clamp',default='C06')
parser.add_argument('--samples',type=int,default=4000)
parser.add_argument('--seed',type=int,default=20260918)
args=parser.parse_args()
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
P=R/f'mechanical/assembly_{args.assembly}_DRAFT';C=R/f'mechanical/cable_clamp_{args.clamp}_DRAFT'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=P/f'RFCP_{args.assembly}_Integrated_DRAFT.FCStd'
build=P/'build_report.json';bd=json.loads(build.read_text());assert bd['pass']
assert bd['native_sha256']==sha(native)
generator=R/f'mechanical/build_assembly_{args.assembly}.py'
assert bd['source_sha256']==sha(generator)
parts=sorted((P/'parts').glob('*.stl'));assert parts
expected=set(bd['parts'])
actual={p.stem.replace('_FREE_DRAFT','').replace('_DRAFT','') for p in parts}
assert expected==actual,dict(missing=sorted(expected-actual),stale_or_extra=sorted(actual-expected))
sources={str(p.relative_to(R)):sha(p) for p in [native,build,generator,P/'mesh.json',C/'mesh.json',C/'verification.json',C/f'Cable_Clamp_{args.clamp}_DRAFT.FCStd',R/f'mechanical/build_cable_clamp_{args.clamp}.py',Path(__file__)]}
mesh_meta=json.loads((P/'mesh.json').read_text());clamp_meta=json.loads((C/'mesh.json').read_text())
out=O/f'print_scan_{args.assembly}';out.mkdir(exist_ok=True)
rows=[]
for p in parts:
 m=trimesh.load_mesh(p);assert isinstance(m,trimesh.Trimesh)
 points,faces=trimesh.sample.sample_surface(m,args.samples,seed=args.seed)
 direction=-m.face_normals[faces];origins=points+direction*1e-4
 hit,ray,tri=m.ray.intersects_location(origins,direction,multiple_hits=True)
 dist=np.linalg.norm(hit-origins[ray],axis=1);valid=dist>1e-5
 near=np.full(len(points),np.inf);np.minimum.at(near,ray[valid],dist[valid]);near+=1e-4
 # 1e-6 numerical tolerance avoids classifying 1.9999999998 as a sub-2mm wall.
 indices=np.flatnonzero(near<2.0-1e-6)
 flags=[dict(point_stl_mm=points[i].tolist(),normal=m.face_normals[faces[i]].tolist(),inward_chord_mm=float(near[i])) for i in indices]
 (out/(p.stem+'_flags.json')).write_text(json.dumps(flags,indent=2)+'\n')
 stp=p.with_suffix('.step');assert stp.exists()
 is_clamp=p.name.startswith(args.clamp+'_')
 key=p.stem.replace('_FREE_DRAFT','').replace('_DRAFT','')
 if key in bd.get('print_quantities',{}):quantity=int(bd['print_quantities'][key])
 elif 'quantity' in bd['parts'][key]:quantity=int(bd['parts'][key]['quantity'])
 elif is_clamp:
  local=key.removeprefix(args.clamp+'_')
  quantity=2*int(clamp_meta[local].get('print_quantity',1))
 else:quantity=int(mesh_meta.get(key,{}).get('print_quantity',1))
 source_clamp=C/'parts'/p.name.removeprefix(args.clamp+'_') if is_clamp else None
 copied=(sha(source_clamp)==sha(p)) if is_clamp else None
 if is_clamp:assert copied
 dims=[round(float(v),3) for v in m.extents]
 row=dict(file=str(p.relative_to(R)),quantity=quantity,stl_sha256=sha(p),step_sha256=sha(stp),
  watertight=bool(m.is_watertight),consistent_winding=bool(m.is_winding_consistent),positive_volume=bool(m.volume>0),
  volume_mm3=float(m.volume),extent_mm=dims,fits_nominal_3301_machine_box=all(a<=b for a,b in zip(sorted(dims),[350,350,400])),
  clamp_copy_matches=copied,samples=args.samples,sampled_min_mm=float(near.min()),
  below_2mm_samples=len(indices),below_1p5mm_samples=int(sum(near<1.5-1e-6)),rays_without_exit=int(sum(~np.isfinite(near))),
  percentiles_mm=np.percentile(near,[1,5,50]).tolist())
 rows.append(row);assert sha(p)==row['stl_sha256']
 print(json.dumps(row),flush=True)
for p,h in sources.items():assert sha(R/p)==h,'Source changed during scan: '+p
assert len(rows)==bd['printed_unique']
assert sum(r['quantity'] for r in rows)==bd['printed_total'],'Review actual print quantities; do not assume a new retainer quantity.'
result=dict(classification='FILE_IDENTITY_MESH_AND_AREA_SAMPLED_NORMAL_CHORDS_NOT_GLOBAL_DFM',
 sources=sources,trimesh_version=trimesh.__version__,seed=args.seed,unique=len(rows),total_quantity=sum(r['quantity'] for r in rows),parts=rows,
 pass_identity_and_mesh=all(r['watertight'] and r['consistent_winding'] and r['positive_volume'] and r['fits_nominal_3301_machine_box'] for r in rows),
 total_samples=sum(r['samples'] for r in rows),below_1p5mm_samples=sum(r['below_1p5mm_samples'] for r in rows),
 limits=['Not a global minimum-wall certificate: small features can escape area sampling.',
 'Flags near edges, chamfers or snap hooks require exact CAD section checks; no automatic mechanical failure label.',
 'Positive closed mesh and machine-box fit do not validate printed fit, stiffness, anisotropy, creep, snap fatigue or vendor approval.',
 'Use FREE lid print geometry, not the imposed-deflection integrated assembly. Units mm, scale100%.'])
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('MESH_PASS',result['pass_identity_and_mesh'],'THIN_FLAGS',result['below_1p5mm_samples'],flush=True)
