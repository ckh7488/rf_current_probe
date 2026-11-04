"""Actual A09 free-lid tetrahedral elasticity model, mm/N/MPa.
Gmsh 4.15.2 -> CalculiX 2.22. No measured/creep/fatigue/contact model.
Usage: python lid_fem.py [mesh_size_mm]
"""
from pathlib import Path
import sys,json,hashlib,subprocess,os
import numpy as np
import gmsh
R=Path(__file__).resolve().parents[2]
rev=sys.argv[2] if len(sys.argv)>2 else 'A09'
O=Path(__file__).resolve().parent/('fem' if rev=='A09' else 'fem_'+rev)
size=float(sys.argv[1]) if len(sys.argv)>1 else 2.4
out=O/('mesh_'+str(size).replace('.','p'));out.mkdir(parents=True,exist_ok=True)
src=R/('mechanical/assembly_'+rev+'_DRAFT/parts/UpperLid_FREE_DRAFT.step')
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.logger.start()
gmsh.model.add('free_lid');gmsh.model.occ.importShapes(str(src));gmsh.model.occ.synchronize()
pg=gmsh.model.addPhysicalGroup(3,[tag for dim,tag in gmsh.model.getEntities(3)])
gmsh.model.setPhysicalName(3,pg,'LID')
gmsh.option.setNumber('General.NumThreads',4)
gmsh.option.setNumber('Mesh.MeshSizeMax',size*2);gmsh.option.setNumber('Mesh.MeshSizeMin',size/2)
# Refine both beams and their root transitions. At least two quadratic layers
# through the 2.4 mm beam in the finer models; actual mesh saved for inspection.
flds=[]
for a,b in [(-106,-36),(36,106)]:
 f=gmsh.model.mesh.field.add('Box');flds.append(f)
 for k,v in {'VIn':size/2,'VOut':size*2,'XMin':a,'XMax':b,'YMin':28,'YMax':38,'ZMin':-5,'ZMax':17,'Thickness':3}.items():gmsh.model.mesh.field.setNumber(f,k,v)
f=gmsh.model.mesh.field.add('Min');gmsh.model.mesh.field.setNumbers(f,'FieldsList',flds);gmsh.model.mesh.field.setAsBackgroundMesh(f)
gmsh.option.setNumber('Mesh.SecondOrderLinear',1)
gmsh.option.setNumber('Mesh.Algorithm3D',1);gmsh.model.mesh.generate(3);gmsh.model.mesh.setOrder(2)
gmsh.write(str(out/'mesh.inp'));gmsh.write(str(out/'mesh.msh'))
ids,xyz,_=gmsh.model.mesh.getNodes();xyz=np.asarray(xyz).reshape(-1,3);ids=np.asarray(ids)
fixed=ids[(np.abs(xyz[:,1])<1e-5)&(np.abs(xyz[:,0])>102.99)]
seat=ids[(np.abs(xyz[:,1]-27.8418)<1e-5)&(np.abs(xyz[:,0])>=5.999)&(np.abs(xyz[:,0])<=12.001)&(xyz[:,2]>=1.999)&(xyz[:,2]<=10.001)]
assert len(fixed)>10 and len(seat)>5,(len(fixed),len(seat))
logs=gmsh.logger.get();(out/'gmsh.log').write_text('\n'.join(logs))
gmsh.logger.stop();gmsh.finalize()
mesh=(out/'mesh.inp').read_text();assert '*ELEMENT, type=C3D10' in mesh
def nset(name,vals):return '*NSET,NSET='+name+'\n'+'\n'.join(','.join(str(int(n)) for n in vals[i:i+12]) for i in range(0,len(vals),12))+'\n'
# Gmsh writes one volume ELSET. Explicitly use its saved declaration.
import re
sets=re.findall(r'\*ELEMENT, type=C3D10, ELSET=([^\n]+)',mesh)
assert len(sets)==1,sets
text=mesh+nset('FOOT',fixed)+nset('CORESEAT',seat)+nset('ALLN',ids)
text+='*MATERIAL,NAME=PA_ASSUMED\n*ELASTIC\n1500.,0.40\n*SOLID SECTION,ELSET='+sets[0]+',MATERIAL=PA_ASSUMED\n'
text+='*STEP\n*STATIC\n*BOUNDARY\nFOOT,1,3,0.\nCORESEAT,2,2,1.8\n*NODE FILE\nU,RF\n*EL FILE\nS,E\n*NODE PRINT,NSET=CORESEAT,TOTALS=YES\nRF\n*NODE PRINT,NSET=ALLN\nU\n*EL PRINT,ELSET='+sets[0]+'\nS\n*END STEP\n'
(out/'lid.inp').write_text(text)
settings=dict(classification='SIMULATED_LINEAR_STATIC_ISOTROPIC',step_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_step=str(src),mesh_parameter_mm=size,gmsh_version=gmsh.__version__,node_count=len(ids),foot_nodes=len(fixed),core_seat_nodes=len(seat),E_MPa=1500,poisson=.4,seat_displacement_mm=1.8,foot_constraint='All translations fixed on two outer pillar bottom faces Y=0',core_constraint='Prescribed Y displacement on two bare-ferrite support lands; X/Z free',limits=['No creep, fatigue, material nonlinearity, temperature/humidity or print anisotropy.','Ideal fixed feet and uniform contact displacement; real ferrite seating/contact not solved.','No prediction of production acceptance or allowable hand torque.'])
(out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
env=os.environ.copy();env['OMP_NUM_THREADS']='4';env['CCX_NPROC_RESULTS']='4'
rr=subprocess.run(['C:/Program Files/FreeCAD 1.0/bin/ccx.exe','-i','lid'],cwd=out,env=env,capture_output=True)
(out/'solver.log').write_bytes(rr.stdout+b'\n'+rr.stderr)
print(json.dumps({'mesh':size,'nodes':len(ids),'solver_exit':rr.returncode,'folder':str(out)}),flush=True)
if rr.returncode:raise RuntimeError('Read solver.log')
