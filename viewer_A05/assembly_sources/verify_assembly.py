"""Saved-CAD path checks and explicit dimensional sensitivity; no measured data."""
from pathlib import Path
import json,hashlib,math,itertools,ast
import FreeCAD as A
import Part,Mesh
O=Path(__file__).resolve().parent;R=O.parents[1];V=A.Vector
d=A.openDocument(str(O/'RFCP_A13_Integrated_DRAFT.FCStd'));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
meta=json.loads((O/'mesh.json').read_text());build=json.loads((O/'build_report.json').read_text());native=O/'RFCP_A13_Integrated_DRAFT.FCStd'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(native)==build['native_sha256']
src=ast.parse((R/'mechanical/build_assembly_A13.py').read_text());env=dict(Part=Part,A=A,V=V,DELTA=1.8,carrier=Part.read(str(O/'CarrierLoaded_INTERNAL.step')))
exec(compile(ast.Module(body=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ['box','cy','mv','fuse','lid']],type_ignores=[]),'lid_geometry','exec'),env)
mv=env['mv'];lid=env['lid'];paths={}
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def sweep(name,moving,obstacles,points,fn):
 rows=[]
 for t in points:
  ss={n:fn(n,s,t) for n,s in moving.items()};bad=[]
  for n,s in ss.items():
   for k,q in obstacles.items():
    vv=vol(s,q)
    if vv>1e-4:bad.append(dict(moving=n,fixed=k,volume_mm3=round(vv,5)))
  rows.append(dict(travel_mm=t,collisions=bad))
 paths[name]=rows;print(name,'cases',len(rows),'failed',sum(bool(x['collisions']) for x in rows),flush=True)
def group(g):return {n:s for n,s in S.items() if meta[n]['group']==g}
headcap=group('HEAD_CAP');fixed={n:s for n,s in S.items() if meta[n]['group'] not in ['HEAD_CAP','HEAD_SCREW']}
sweep('head_screws_withdraw',group('HEAD_SCREW'),{n:s for n,s in S.items() if meta[n]['group']!='HEAD_SCREW'},range(0,56,5),lambda n,s,t:mv(s,y=t))
def opening(n,s,h):return mv(lid(max(0,1.8-h)),y=h) if n=='UpperLid' else mv(s,y=max(0,h-1.8))
sweep('head_lid_release_and_lift',headcap,fixed,[i*.3 for i in range(7)]+list(range(5,121,5)),opening)
opened={n:opening(n,s,120) for n,s in headcap.items()}
cal={n:s for n,s in S.items() if meta[n]['group'].startswith('CALIBRATION')};obs={n:s for n,s in fixed.items() if n not in cal};obs.update(opened)
sweep('calibration_PCB_lift_with_head_open',cal,obs,range(0,81,4),lambda n,s,t:mv(s,y=t))
sweep('calibration_PCB_side_removal_after_lift',cal,obs,range(0,201,10),lambda n,s,t:mv(s,x=t,y=80))
head={n:s for n,s in S.items() if meta[n]['group'].startswith('HEAD_') and meta[n]['group']!='HEAD_SCREW'}
obs={n:s for n,s in S.items() if n not in head and n not in cal and meta[n]['group'] not in ['HEAD_SCREW','MOUNT_Head']}
sweep('head_from_base_lift_PCB_removed',head,obs,range(0,101,5),lambda n,s,t:mv(s,y=t))
for sign,prefix in [(-1,'Lower'),(1,'Upper')]:
 name=prefix+'Keeper';other={n:s for n,s in S.items() if n not in [name,prefix+'KeeperScrews']}
 sweep(prefix+'_keeper_front_removal', {name:S[name]},other,range(0,61,3),lambda n,s,t:mv(s,z=t))
for name,body in [('FixedCore','LowerBody'),('MovingCore','UpperLid')]:
 sweep(name+'_bare_front_insertion_keeper_off',{name:S[name]},{body:S[body]},range(0,61,3),lambda n,s,t:mv(s,z=t))
# Integrated cable module motion; C06's separate report checks its internal pairs.
normals=[(math.cos(math.radians(a)),math.sin(math.radians(a))) for a in [210,330]]
clamps={n:s for n,s in S.items() if meta[n]['group']=='CABLE'};external={n:s for n,s in S.items() if n not in clamps and n not in cal}
def cablepose(n,s,r):
 p=meta[n];g=p['subgroup'];t=r-8
 if g in ['DRIVE','TOP','TOPSCREW']:return mv(s,y=t)
 if g.startswith('JAW'):x,y=normals[int(g[-1])-1];return mv(s,x*t,y*t)
 return s
sweep('both_clamps_radius_vs_probe_and_base',clamps,external,[3+i*.5 for i in range(21)],cablepose)
caps={n:s for n,s in clamps.items() if meta[n]['subgroup']=='TOP'};obs={n:s for n,s in S.items() if n not in caps and meta[n].get('subgroup')!='TOPSCREW'}
sweep('both_clamp_bridges_lift_screws_removed',caps,obs,range(0,66,3),lambda n,s,t:mv(s,y=t))
# Actual core A/D/C extreme scaling, seated on lower nominal support plane.
tol=[];Dnom=29.6418
for sa,sd,sc in itertools.product([-1,1],repeat=3):
 dl=sd*.31;dm=A.Matrix();dm.A11=(60.96+sa*1.27)/60.96;dm.A22=(Dnom+dl)/Dnom;dm.A33=(12.7+sc*.635)/12.7
 core=S['FixedCore'].transformGeometry(dm);core=mv(core,y=dl)
 keeper=mv(S['LowerKeeper'],z=sc*.635);bad=[]
 for n,q in [('LowerBody',S['LowerBody']),('LowerKeeper_adjusted',keeper)]:
  vv=vol(core,q)
  if vv>1e-4:bad.append(dict(part=n,volume_mm3=vv))
 tol.append(dict(A_sign=sa,D_sign=sd,C_sign=sc,seam_y_mm=dl,collisions=bad))
upper_tol=[]
for sa,sl,su,sc in itertools.product([-1,1],repeat=4):
 dl=sl*.31;du=su*.31;dm=A.Matrix();dm.A11=(60.96+sa*1.27)/60.96;dm.A22=(Dnom+du)/Dnom;dm.A33=(12.7+sc*.635)/12.7
 core=mv(S['MovingCore'].transformGeometry(dm),y=dl);l=lid(1.8+dl+du);keeper=mv(S['UpperKeeper'],y=dl+du,z=sc*.635);bad=[]
 for n,q in [('UpperLid_adjusted',l),('UpperKeeper_adjusted',keeper)]:
  vv=vol(core,q)
  if vv>1e-4:bad.append(dict(part=n,volume_mm3=vv))
 upper_tol.append(dict(A_sign=sa,lower_D_sign=sl,upper_D_sign=su,C_sign=sc,deflection_mm=1.8+dl+du,collisions=bad))
grips=[]
for x in [-111,111]:
 gauge=Part.makeCylinder(16,16,V(x,42,6.35),V(0,1,0));bad=[]
 for n,q in S.items():
  if n=='HeadHandScrews':continue
  vv=vol(gauge,q)
  if vv>1e-4:bad.append(dict(part=n,volume_mm3=vv))
 grips.append(dict(x=x,diameter_mm=32,y_range=[42,58],collisions=bad))
stls={p.name:Mesh.Mesh(str(p)).isSolid() for p in (O/'parts').glob('*.stl')}
# These are explicit sensitivity assumptions, not process guarantees.
beam=[]
for E,t,h in itertools.product([1300,1800],[2.1,2.7],[.58,3.02]):
 I=18*t**3/12;F=2*12*E*I*h/63**3;strain=3*t*h/63**2
 beam.append(dict(E_MPa=E,thickness_mm=t,deflection_mm=h,total_force_N=F,surface_strain=strain))
v=dict(classification='CALCULATED_SAVED_CAD_AND_SENSITIVITY',native_sha256=sha(native),source_sha256=sha(Path(__file__)),paths=paths,core_ADC_corners=tol,stl_closed=stls,
 lid_stack=dict(core_half_D_tolerance_mm=.31,two_printed_seat_errors_mm=.6,nominal_deflection_mm=1.8,deflection_range_mm=[.58,3.02]),beam_sensitivity=beam,
 jaw_clearance=dict(front_clearance_mm=.8,side_clearance_mm=.8,assumed_independent_surface_errors_mm=[-.3,.3],local_worst_remaining_mm=.2,cam_slot_width_mm=5.8,follower_diameter_mm=5,cam_only_radial_play_mm=.8,cam_only_opposite_lower_jaw_center_error_mm=.8/math.cos(math.pi/6)),
 limitations=['Discretized rigid geometry paths, not swept-volume proof; screw threads omitted.','Core ADC scaling does not cover independent B/E/flatness, rocking or all print distortions.','Keeper z position is adjusted by screw seating; force and ferrite damage untested.','Beam estimates use fixed-guided ends; root fillets, anisotropy and actual joint stiffness are not solved by FEA.','Beam thickness/printed seat tolerances are sensitivity inputs, not measured distribution. No force guarantee.','0.2 mm local residual clearance does not cover full guide parallelism or 100+ mm warpage.','Friction, cable crush, repeated clamping, SMA connector locking and real RF pickup remain untested.'])
v['upper_core_ADC_corners']=upper_tol;v['head_grip_envelopes']=grips
v['pass']=build['pass'] and all(stls.values()) and all(not x['collisions'] for rows in paths.values() for x in rows) and all(not r['collisions'] for r in tol+upper_tol+grips)
(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('PASS',v['pass'],'tolerance failures',[t for t in tol if t['collisions']],flush=True)
