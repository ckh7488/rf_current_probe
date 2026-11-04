from pathlib import Path
import json,hashlib,ast
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
rows=[]
for rev in ['A10','A11']:
 p=R/f'mechanical/assembly_{rev}_DRAFT/RFCP_{rev}_Integrated_DRAFT.FCStd'
 d=A.openDocument(str(p));lid=d.getObject('UpperLid').Shape.copy()
 f=R/f'mechanical/assembly_{rev}_DRAFT/parts/UpperLid_FREE_DRAFT.step';free=Part.read(str(f))
 before=lid.isValid()
 try:errors=lid.check(True)
 except Exception as e:errors=str(e)
 try:free_errors=free.check(True)
 except Exception as e:free_errors=str(e)
 rows.append(dict(revision=rev,native_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),loaded_valid_on_open=before,
  loaded_check_errors=errors,free_step_valid=free.isValid(),free_step_check_errors=free_errors))
 source=R/f'mechanical/build_assembly_{rev}.py';tree=ast.parse(source.read_text())
 env=dict(A=A,Part=Part,V=A.Vector,DELTA=1.8,carrier=Part.read(str(p.parent/'CarrierLoaded_INTERNAL.step')))
 fs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['box','cy','mv','fuse','lid']]
 exec(compile(ast.Module(body=fs,type_ignores=[]),'saved_lid_generator','exec'),env)
 poses=[]
 for displacement in [0,.3,.6,.9,1.2,1.5,1.8,2.42,3.02]:
  try:
   q=env['lid'](displacement)
   poses.append(dict(imposed_deflection_mm=displacement,valid=q.isValid(),solids=len(q.Solids)))
  except Exception as e:poses.append(dict(imposed_deflection_mm=displacement,error=str(e),valid=False))
 rows[-1]['generator_deflection_cases']=poses
 rows[-1]['generator_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
print(json.dumps(rows,indent=2),flush=True)
(O/'loaded_lid_validity.json').write_text(json.dumps(rows,indent=2)+'\n')
