"""Checks actual A14 saved CAD, insertion paths, wrench envelopes and inherited datums."""
from pathlib import Path
import FreeCAD as A
import Part, Mesh
import ast,json,hashlib,itertools
R=Path(__file__).resolve().parents[1];O=R/'mechanical/assembly_A14_DRAFT';OLD=R/'mechanical/assembly_A13_DRAFT';V=A.Vector
d=A.openDocument(str(O/'RFCP_A14_Integrated_DRAFT.FCStd'));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
od=A.openDocument(str(OLD/'RFCP_A13_Integrated_DRAFT.FCStd'));OS={o.Name:o.Shape.copy() for o in od.Objects if hasattr(o,'Shape')}
M=json.loads((O/'mesh.json').read_text());build=json.loads((O/'build_report.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(O/'RFCP_A14_Integrated_DRAFT.FCStd')==build['native_sha256']
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
paths={}
def path(name,moving,obstacles,axis,travels):
 rows=[]
 for t in travels:
  bad=[]
  for n,s in moving.items():
   q=mv(s,*[a*t for a in axis])
   for k,v in obstacles.items():
    z=vol(q,v)
    if z>1e-4:bad.append(dict(a=n,b=k,volume_mm3=z))
  rows.append(dict(travel_mm=t,collisions=bad))
 paths[name]=rows
 print(name,'failed',sum(bool(x['collisions']) for x in rows),flush=True)
for n in ['LowerArmLeft','LowerArmRight']:path(n+'_from_rear_before_core_and_base',{n:S[n]},{'LowerCenter':S['LowerCenter']},[0,0,-1],range(0,61,3))
path('upper_right_from_rear_before_keeper_and_core',{'UpperRight':S['UpperRight']},{'UpperLeft':S['UpperLeft']},[0,0,-1],range(0,51,2))
path('middle_base_lower_onto_end_laps',{'BaseCenter':S['BaseCenter']},{n:S[n] for n in ['BaseFront','BaseRear']},[0,1,0],range(0,61,3))
for n in ['FixedCore','MovingCore']:
 ob={k:s for k,s in S.items() if k in (['LowerCenter','LowerArmLeft','LowerArmRight'] if n=='FixedCore' else ['UpperLeft','UpperRight'])}
 path(n+'_front_insertion', {n:S[n]},ob,[0,0,1],range(0,61,3))
# Recreate the same imposed leaf curve; this tests geometry, not forces.
env=dict(A=A,Part=Part,V=V,DELTA=1.8,carrier=Part.read(str(OLD/'CarrierLoaded_INTERNAL.step')))
src=ast.parse((R/'mechanical/build_assembly_A13.py').read_text())
exec(compile(ast.Module(body=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ['box','cy','mv','fuse','lid']],type_ignores=[]),'a13_lid','exec'),env)
src=ast.parse((R/'mechanical/build_assembly_A14.py').read_text())
exec(compile(ast.Module(body=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ['box','cyl','clip','split_lid']],type_ignores=[]),'a14_lid','exec'),env)
fixed={n:s for n,s in S.items() if M[n]['group'] not in ['HEAD_CAP','HEAD_SCREW']};rows=[]
for h in [0,.3,.6,.9,1.2,1.5,1.8,3,5,10,20,40,80,120]:
 delta=max(0,1.8-h);halves=env['split_lid'](env['lid'](delta),delta-1.8)
 cap={n:mv(s,y=max(0,h-1.8)) for n,s in S.items() if M[n]['group']=='HEAD_CAP'}
 cap.update(UpperLeft=mv(halves[0],y=h),UpperRight=mv(halves[1],y=h))
 bad=[]
 for n,s in cap.items():
  for k,v in fixed.items():
   z=vol(s,v)
   if z>1e-4:bad.append(dict(a=n,b=k,volume_mm3=z))
 rows.append(dict(lift_mm=h,collisions=bad))
paths['lid_release_and_lift']=rows
print('lid_release_and_lift','failed',sum(bool(x['collisions']) for x in rows),flush=True)
# Bare parts are joined before core / PCB / full base installation. Actual assembly order matters.
tools=[]
for n,p in M.items():
 if not p.get('new_hardware') or not n.endswith('Nut'):continue
 s=S[n];b=s.BoundBox;c=b.Center
 if n.startswith('BaseJoint'):
  gauge=Part.makeCylinder(6,30,V(c.x,b.YMin,c.z),V(0,1,0));ob=[k for k in S if k.startswith('Base') and k!=n]
 else:
  gauge=Part.makeCylinder(6,30,V(c.x,c.y,b.ZMin),V(0,0,1));ob=[k for k in S if k.startswith(('UpperLeft','UpperRight','UpperJoint'))] if n.startswith('Upper') else [k for k in S if k.startswith(('LowerCenter','LowerArm','LowerJoint'))]
 # The matching screw end enters the socket's hollow bore; exclude only that deliberate fit.
 bad=[dict(part=k,volume_mm3=vol(gauge,S[k])) for k in ob if k not in [n,n[:-3]+'Screw'] and vol(gauge,S[k])>1e-4]
 tools.append(dict(nut=n,tool='OD12 mm socket, 30 mm axial insertion',collisions=bad))
identity={n:sha(O/'parts'/n)==sha(OLD/'parts'/n) for n in [p.name for p in (O/'parts').glob('*.stl') if '_A14_' not in p.name]}
core={n:OS[n].cut(S[n]).Volume+S[n].cut(OS[n]).Volume for n in ['FixedCore','MovingCore','Winding','PCB','SMAEnvelope']}
free14=[Part.read(str(O/'parts'/(n+'_A14_DRAFT.step'))) for n in ['UpperLeft','UpperRight']]
oldlid=Part.read(str(OLD/'parts/UpperLid_FREE_DRAFT.step'))
leaf=[]
for sign in [-1,1]:
 region=env['box'](40 if sign>0 else -105,25,-3,65,20,18)
 a=oldlid.common(region);b=free14[0 if sign<0 else 1].common(region)
 leaf.append(dict(side=sign,symmetric_difference_mm3=a.cut(b).Volume+b.cut(a).Volume))
stls={p.name:Mesh.Mesh(str(p)).isSolid() for p in (O/'parts').glob('*.stl')}
v=dict(classification='CALCULATED_SAVED_CAD_DISCRETE_PATHS',native_sha256=build['native_sha256'],source_sha256=sha(Path(__file__)),paths=paths,socket_access=tools,unchanged_print_sha256=identity,core_and_PCB_symmetric_difference_mm3=core,free_leaf_symmetric_difference=leaf,stl_closed=stls,
 limitations=['Discrete samples are not continuous collision proof. Threads, friction and deformation excluded.','OD12 socket access verified on the bare subassembly in specified order, not with every installed module.','Lap mating planes must be fully seated; loose screws do not define precision alignment.','Process/global warpage may exceed open-lap allowances; local nominal fit is not a printer guarantee.','Screw supplier dimensions, stripping, nylon creep, contact force and RF behavior not verified.'])
v['pass']=build['pass_geometry'] and all(stls.values()) and all(identity.values()) and max(core.values())<1e-5 and all(x['symmetric_difference_mm3']<1e-4 for x in leaf) and all(not x['collisions'] for x in tools) and all(not x['collisions'] for p in paths.values() for x in p)
(O/'verification.json').write_text(json.dumps(v,indent=2));print('A14_VERIFY_PASS',v['pass'],flush=True)
