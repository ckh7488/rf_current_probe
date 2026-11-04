"""A11 saved-CAD targeted review. Numerical geometry, not physical qualification."""
from pathlib import Path
import FreeCAD as A, Part
import json, hashlib, math, ast
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=R/'mechanical/assembly_A11_DRAFT';V=A.Vector
D=A.openDocument(str(P/'RFCP_A11_Integrated_DRAFT.FCStd'));S={o.Name:o.Shape.copy() for o in D.Objects if hasattr(o,'Shape')};M=json.loads((P/'mesh.json').read_text())
old=A.openDocument(str(R/'mechanical/assembly_A10_DRAFT/RFCP_A10_Integrated_DRAFT.FCStd'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def collisions(s,obs):return [dict(part=n,mm3=v) for n,q in obs.items() if (v:=vol(s,q))>1e-4]
def sym(a,b):return a.cut(b).Volume+b.cut(a).Volume
report={'classification':'CALCULATED_SAVED_CAD_NOT_PHYSICAL','source_sha256':sha(Path(__file__)),'native_sha256':sha(P/'RFCP_A11_Integrated_DRAFT.FCStd')}
# Source-equivalence uses actual BReps, not filenames or revision labels.
free_old=Part.read(str(R/'mechanical/assembly_A10_DRAFT/parts/UpperLid_FREE_DRAFT.step'));free_new=Part.read(str(P/'parts/UpperLid_FREE_DRAFT.step'))
report['lid_geometry_equivalence']={'free_symmetric_difference_mm3':sym(free_old,free_new),'closed_baseline_valid':old.getObject('UpperLid').Shape.isValid(),'closed_symmetric_difference_mm3':None,'closed_comparison_note':'A10 CLOSED baseline is invalid; Boolean difference volume is not a trustworthy comparison and is not reported.','closed_valid':S['UpperLid'].isValid(),'scope':'FREE print/FEA source is unchanged. CLOSED representation replaces the invalid faceted/filleted curve with its analytic cubic; new lower datum interaction is not solved.'}
# Keepers preserve their actual front ferrite contact and lips, bar/stems only shortened.
contacts=[]
for core,keeper in [('FixedCore','LowerKeeper'),('MovingCore','UpperKeeper')]:
 a=vol(mv(old.getObject(core).Shape,z=.05),old.getObject(keeper).Shape)/.05;b=vol(mv(S[core],z=.05),S[keeper])/.05
 contacts.append(dict(core=core,old_front_area_mm2=a,new_front_area_mm2=b,delta_mm2=b-a))
report['keeper_contacts']=contacts
# The exact inherited tiny roof lip identified by independent STL ray inspection.
sliver=Part.makeBox(12,1,.15,V(-6,-35,4.75));rear=Part.makeBox(11.8,5.8,2.3,V(-5.9,-39.9,-4.4))
report['wire_window_cleanup']={'old_sliver_mm3':vol(sliver,old.getObject('LowerBody').Shape),'new_sliver_mm3':vol(sliver,S['LowerBody']),'retained_rear_wall_gauge_missing_mm3':rear.cut(S['LowerBody']).Volume,'retained_nominal_wall_mm':2.5}

mount=[]
for i in range(6):
 s=S['MountScrew'+str(i)];n=S['MountNut'+str(i)];sb=s.BoundBox;nb=n.BoundBox;top=-63 if i<2 else -62
 mount.append(dict(index=i,length_mm=top-sb.YMin,bench_clearance_mm=sb.YMin+84,nut_bearing_gap_mm=-78-nb.YMax,nut_engagement_mm=min(top,nb.YMax)-max(sb.YMin,nb.YMin),tip_beyond_nut_mm=nb.YMin-sb.YMin))
report['mounts']=mount
report['below_bench']=[dict(part=n,below_mm=-84-s.BoundBox.YMin) for n,s in S.items() if s.BoundBox.YMin < -84-1e-5]
# Enlarged lower nut pockets must still stop a square nut turning.
angles=[]
for j,n in enumerate(S['HeadSquareNuts'].Solids):
 poses=[]
 for a in range(0,91,5):
  q=n.copy();q.rotate(n.BoundBox.Center,V(0,1,0),a);poses.append(dict(deg=a,intersection_mm3=vol(q,S['LowerBody'])))
 hits=[x['deg'] for x in poses if x['intersection_mm3']>1e-4];angles.append(dict(nut=j,first_stop_deg=min(hits) if hits else None,poses=poses))
report['head_square_nut_rotation']=angles
# Head screw + seated nut can move together to follow a one-sided datum.
follow=[]
for dx in [-.4,0,.4]:
 for dz in [-.4,0,.4]:
  group=Part.makeCompound([mv(S['HeadHandScrews'],dx,0,dz),mv(S['HeadSquareNuts'],dx,0,dz)])
  follow.append(dict(dx=dx,dz=dz,collisions=collisions(group,{'LowerBody':S['LowerBody']})))
report['loose_closure_hardware_follows_datum']=follow
# Geometric manual placement along the flared guide into its straight contact lands.
source=ast.parse((R/'mechanical/build_assembly_A11.py').read_text());env=dict(Part=Part,A=A,V=V,DELTA=1.8,carrier=Part.read(str(P/'CarrierLoaded_INTERNAL.step')))
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ['box','cy','mv','fuse','lid']],type_ignores=[]),'lid_geometry','exec'),env)
cap={n:s for n,s in S.items() if M[n]['group']=='HEAD_CAP'};obs={n:s for n,s in S.items() if M[n]['group'] not in ['HEAD_CAP','HEAD_SCREW']}
rows=[]
for i in range(41):
 h=10-i*.25;offset=-min(1.5,max(0,(h-4)*.5));bad=[]
 for n,s in cap.items():
  q=mv(env['lid'](max(0,1.8-h)),y=h) if n=='UpperLid' else mv(s,y=max(0,h-1.8))
  q=mv(q,x=offset,z=offset)
  bad.extend([dict(moving=n,**x) for x in collisions(q,obs)])
 rows.append(dict(lift_mm=h,manual_xz_offset_mm=offset,collisions=bad))
report['manual_flared_datum_placement']=rows
report['datum_limits']=['Manual gentle left/back seating before tightening; not an automatic precision-centering latch.','One L datum at the left foot; right foot span is not trapped between a second precise locator.','Nominal datum faces touch; as-printed face errors change the actual core position. No zero positional error claim.','Hardware float is nominal geometry only. Combined independent print warpage, hole errors, nut size and screw alignment still need first-article assembly verification.']
report['pass']=report['wire_window_cleanup']['new_sliver_mm3']<1e-5 and report['wire_window_cleanup']['retained_rear_wall_gauge_missing_mm3']<1e-5 and report['lid_geometry_equivalence']['free_symmetric_difference_mm3']<1e-5 and report['lid_geometry_equivalence']['closed_valid'] and not report['below_bench'] and all(x['nut_engagement_mm']>3.19 and x['nut_bearing_gap_mm']<1e-6 for x in mount) and all(x['first_stop_deg'] is not None for x in angles) and all(not x['collisions'] for x in follow+rows) and all(abs(x['delta_mm2'])<1e-4 for x in contacts)
(O/'targeted.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pass'],flush=True)
print('manual placement failed',sum(bool(x['collisions']) for x in rows),'hardware float failed',sum(bool(x['collisions']) for x in follow),flush=True)
