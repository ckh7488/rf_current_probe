from pathlib import Path
import math,json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
ad=A.openDocument(str(R/'mechanical/assembly_A10_DRAFT/RFCP_A10_Integrated_DRAFT.FCStd'));S={o.Name:o.Shape for o in ad.Objects if hasattr(o,'Shape')}
cd=A.openDocument(str(R/'mechanical/cable_clamp_C04_DRAFT/Cable_Clamp_C04_DRAFT.FCStd'));C={o.Name:o.Shape for o in cd.Objects if hasattr(o,'Shape')}
meta=json.loads((R/'mechanical/assembly_A10_DRAFT/mesh.json').read_text())
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
rows=[]
def path(name,shape,obs,axis,positions):
 bad=[]
 for t in positions:
  v=[0,0,0];v[axis]=t;q=mv(shape,*v)
  for n,s in obs.items():
   vv=vol(q,s)
   if vv>1e-4:bad.append(dict(travel_mm=t,part=n,overlap_mm3=vv))
 rows.append(dict(name=name,positions=len(positions),collisions=bad));print(name,len(bad),flush=True)
path('closure_square_nuts_slide_from_front',S['HeadSquareNuts'],{'LowerBody':S['LowerBody']},2,list(range(0,51,2)))
for prefix in ['Lower','Upper']:
 body=S['LowerBody' if prefix=='Lower' else 'UpperLid']
 path(prefix+'_keeper_nuts_rear_access',S[prefix+'KeeperNuts'],{'body':body},2,list(range(0,-41,-2)))
path('M6_drive_nut_front_before_lead',C['DriveNut'],{'yoke':C['DriveYoke']},2,list(range(0,41,2)))
for i in [1,2]:
 path('bridge_nut_'+str(i)+'_front_before_bridge',C['BridgeNut'+str(i)],{'yoke':C['DriveYoke'],'frame':C['Frame']},2,list(range(0,41,2)))
 path('follower_nut_'+str(i)+'_before_jaw_install',C['FollowerNut'+str(i)],{'jaw':C['Jaw'+str(i)]},2,list(range(0,-31,-2)))
 path('follower_screw_'+str(i)+'_front_insert',C['Follower'+str(i)],{n:C[n] for n in ['Frame','DriveYoke','Jaw1','Jaw2']},2,list(range(0,41,2)))
path('lead_from_above_without_nuts',C['LeadScrewKnob'],{n:C[n] for n in ['Frame','DriveYoke']},1,list(range(0,121,4)))
for n in ['JamNut1','JamNut2','ThrustWasher']:
 path(n+'_front_place_below_seat_before_lead',C[n],{k:C[k] for k in ['Frame','DriveYoke']},2,list(range(0,41,2)))
# Head and both bridge caps removed, calibration board removed; lower jaw radius 13.
obs={}
for n,s in S.items():
 m=meta[n];g=m['group']
 if g in ['HEAD_CAP','HEAD_SCREW'] or g.startswith('CALIBRATION'):continue
 if g=='CABLE':
  sg=m['subgroup']
  if sg in ['TOP','TOPSCREW']:continue
  if sg=='DRIVE':s=mv(s,y=5)
  elif sg.startswith('JAW'):
   a=math.radians(210 if sg=='JAW1' else 330);s=mv(s,5*math.cos(a),5*math.sin(a))
 obs[n]=s
for radius in [3,6,10,13]:
 cable=Part.makeCylinder(radius,400,V(0,0,-180),V(0,0,1))
 path('cable_D'+str(radius*2)+'_top_insertion_caps_removed',cable,obs,1,list(range(0,61,2)))
result=dict(classification='CALCULATED_SAVED_NOMINAL_CAD',native_sha256=hashlib.sha256((R/'mechanical/assembly_A10_DRAFT/RFCP_A10_Integrated_DRAFT.FCStd').read_bytes()).hexdigest(),paths=rows,pass_nominal=all(not r['collisions'] for r in rows),limits=['Straight paths sampled every 2–4 mm; not swept-volume proof.','Threads omitted. Place washer/jam nuts from the front under the seat before threading the lead through them and the drive nut.','Cable treated as rigid cylinder; no connector, bend radius, friction or crushing model.','Physical tools, nut rotation, tightening force and long-span print warpage still require a trial assembly.'])
(O/'use_paths.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',result['pass_nominal'],flush=True)
