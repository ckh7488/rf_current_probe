"""Saved A11 print-file identity, watertightness and sampled normal ray chords.

Same seed and 4000 area samples per actual STL as the A10 wall scan.
Sampling is NOT a global minimum-wall or manufacturer DFM certificate.
"""
from pathlib import Path
import json, hashlib, csv
import trimesh, numpy as np
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
P=R/'mechanical/assembly_A11_DRAFT';C=R/'mechanical/cable_clamp_C05_DRAFT'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parts=sorted((P/'parts').glob('*.stl'));assert len(parts)==10
wall_out=O/'wall_scan_A11';wall_out.mkdir(exist_ok=True)
native=P/'RFCP_A11_Integrated_DRAFT.FCStd';build=P/'build_report.json'
build_data=json.loads(build.read_text());assert build_data['pass']
assert build_data['native_sha256']==sha(native)
assert build_data['source_sha256']==sha(R/'mechanical/build_assembly_A11.py')
sources={str(p.relative_to(R)):sha(p) for p in [native,build,R/'mechanical/build_assembly_A11.py',C/'Cable_Clamp_C05_DRAFT.FCStd',R/'mechanical/build_cable_clamp_C05.py',Path(__file__)]}
rows=[];summary=[]
for p in parts:
 m=trimesh.load_mesh(p);pts,faces=trimesh.sample.sample_surface(m,4000,seed=20260918)
 directions=-m.face_normals[faces];orig=pts+directions*1e-4
 loc,ir,it=m.ray.intersects_location(orig,directions,multiple_hits=True)
 dist=np.linalg.norm(loc-orig[ir],axis=1);valid=dist>1e-5
 near=np.full(len(pts),np.inf);np.minimum.at(near,ir[valid],dist[valid]);near+=1e-4
 candidates=np.flatnonzero(near<2.0)
 flags=[dict(point_stl_mm=pts[i].tolist(),normal=m.face_normals[faces[i]].tolist(),inward_chord_mm=float(near[i])) for i in candidates]
 (wall_out/(p.stem+'.json')).write_text(json.dumps(flags,indent=2)+'\n')
 record=dict(part=p.name,stl_sha256=sha(p),watertight=bool(m.is_watertight),positive_volume=bool(m.volume>0),volume_mm3=float(m.volume),samples=4000,sampled_min_mm=float(near.min()),below_2mm_samples=len(flags),below_1p5mm_samples=int(sum(near<1.5)),rays_without_exit=int(sum(~np.isfinite(near))),percentiles_mm=np.percentile(near,[1,5,50]).tolist())
 summary.append(record);print(json.dumps(record),flush=True)
 stp=p.with_suffix('.step');assert stp.exists()
 clamp=p.name.startswith('C05_');qty=2 if clamp else 1
 key=p.stem.replace('_FREE_DRAFT','').replace('_DRAFT','')
 assert key in build_data['parts']
 source_clamp=C/'parts'/p.name.removeprefix('C05_') if clamp else None
 copied=sha(source_clamp)==sha(p) if clamp else None
 if clamp:assert copied
 dims=[round(float(x),3) for x in m.extents]
 rows.append(dict(file=str(p.relative_to(R)),quantity=qty,source_kind='C05_UNMODIFIED_PRINT_COPY' if clamp else 'FREE_PRINT_GEOMETRY',source_step=str(stp.relative_to(R)),source_step_sha256=sha(stp),source_c05_stl=str(source_clamp.relative_to(R)) if clamp else '',matches_c05_source=copied,x_mm=dims[0],y_mm=dims[1],z_mm=dims[2],watertight=record['watertight'],positive_volume=record['positive_volume'],fits_nominal_3301_machine_box=all(a<=b for a,b in zip(sorted(dims),[350,350,400])),sampled_min_chord_mm=record['sampled_min_mm'],below_1p5mm_samples=record['below_1p5mm_samples'],sha256=record['stl_sha256'],status='DRAFT - NOT FOR FABRICATION'))
 # Files must remain unchanged through the scan.
 assert sha(p)==record['stl_sha256']
for s,h in sources.items():assert sha(R/s)==h,'Input changed during sampling: '+s
assert sum(x['quantity'] for x in rows)==15
wall=dict(classification='CALCULATED_STL_AREA_SAMPLED_INWARD_RAY_CHORDS',trimesh_version=trimesh.__version__,seed=20260918,parts=summary,limitations=['Not a certified minimum-wall or manufacturer DFM check.','Normal chords near edges/chamfers/curved surfaces can flag intentional geometry; inspect coordinates.','Area sampling may miss small features; explicit CAD section checks supplement it.'])
(wall_out/'summary.json').write_text(json.dumps(wall,indent=2)+'\n')
with (O/'print_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
out=dict(classification='FILE_IDENTITY_AND_MESH_AUDIT_NOT_GLOBAL_DFM',sources=sources,unique=10,total_quantity=15,prints=rows,pass_saved_mesh_and_identity=all(x['watertight'] and x['positive_volume'] and x['fits_nominal_3301_machine_box'] for x in rows),new_sampling_below_1p5mm_total=sum(x['below_1p5mm_samples'] for x in rows),excluded=['Integrated assembly STEP/native includes nonprinted hardware and imposed lid deflection.','CarrierLoaded_INTERNAL.step and UpperLid_UNLOADED_DRAFT.step are not additional print jobs. Use exactly the 10 STL types in this manifest.','Old A02/A03 supplier orders and A10/C04 revisions are not this A11/C05 print set.'],limitations=['Units must be mm at 100% scale. STL has no embedded unit declaration.','A nominal machine-box fit does not establish print straightness, acceptable warpage, strength, orientation or vendor approval.','Material selection and actual assembly remain unverified.','All dimensions are calculated from saved files. No physical sample has been measured.'])
(O/'manifest.json').write_text(json.dumps(out,indent=2)+'\n');print('PRINT_AUDIT_PASS',out['pass_saved_mesh_and_identity'],'LOW_CHORD_FLAGS',out['new_sampling_below_1p5mm_total'],flush=True)
