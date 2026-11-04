"""Independent source-revision geometry delta: no product files are changed."""
from pathlib import Path
import json, hashlib
import FreeCAD as A, Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'classification':'CALCULATED_BREP_DIFFERENCE_NOT_VALIDATION_OF_DESIGN',
 'script_sha256':sha(Path(__file__)), 'comparisons':[]}
def read(p):
 d=A.openDocument(str(p));return d,{o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
for folder,old,new,filename in [('assembly','A10','A11','RFCP_{}_Integrated_DRAFT.FCStd'),('cable_clamp','C04','C05','Cable_Clamp_{}_DRAFT.FCStd')]:
 p=R/f'mechanical/{folder}_{old}_DRAFT'/filename.format(old)
 q=R/f'mechanical/{folder}_{new}_DRAFT'/filename.format(new)
 if not q.exists():continue
 da,SA=read(p);db,SB=read(q)
 row={'old':old,'new':new,'source_sha256':{str(p.relative_to(R)):sha(p),str(q.relative_to(R)):sha(q)},'parts':[]}
 for n in sorted(SA.keys()|SB.keys()):
  if n not in SA or n not in SB:
   row['parts'].append(dict(name=n,status='added' if n in SB else 'removed'));continue
  a,b=SA[n],SB[n];av=a.Volume;bv=b.Volume;va=a.isValid();vb=b.isValid()
  # Do not infer shape equivalence using Boolean volume on an invalid input.
  delta=max(0,av+bv-2*a.common(b).Volume) if va and vb else None
  row['parts'].append(dict(name=n,old_volume_mm3=av,new_volume_mm3=bv,symmetric_difference_mm3=delta,
   changed=(delta>1e-4 if delta is not None else va!=vb),old_valid=va,new_valid=vb,new_solids=len(b.Solids),
   change_basis='valid_volume_difference' if delta is not None else 'validity_repair_or_unassessable_invalid_input'))
 row['changed_parts']=[p['name'] for p in row['parts'] if p.get('changed') or 'status' in p]
 print(old,new,'changed',row['changed_parts'],flush=True)
 result['comparisons'].append(row);A.closeDocument(da.Name);A.closeDocument(db.Name)
p=R/'mechanical/assembly_A10_DRAFT/parts/UpperLid_FREE_DRAFT.step'
q=R/'mechanical/assembly_A11_DRAFT/parts/UpperLid_FREE_DRAFT.step'
if q.exists():
 a,b=Part.read(str(p)),Part.read(str(q));delta=a.Volume+b.Volume-2*a.common(b).Volume
 result['free_lid_equivalence']={'A10_sha256':sha(p),'A11_sha256':sha(q),'symmetric_difference_mm3':max(0,delta),
  'same_geometry_at_volume_tolerance_1e_4':delta<1e-4,
  'limit':'Geometric identity does not validate new support boundary conditions or real printed properties.'}
(O/'revision_delta.json').write_text(json.dumps(result,indent=2)+'\n')
print('REPORT',str(O/'revision_delta.json'),flush=True)
