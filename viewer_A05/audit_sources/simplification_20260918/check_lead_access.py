"""C07 single M6 locknut: geometry of loading, one wrench, and rotation."""
from pathlib import Path
import json,hashlib,math
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
p=R/'mechanical/cable_clamp_C07_DRAFT/Cable_Clamp_C07_DRAFT.FCStd';d=A.openDocument(str(p));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
meta=json.loads((p.parent/'mesh.json').read_text())
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def rot(s,angle):q=s.copy();q.rotate(V(80,0,26),V(0,1,0),angle);return q
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def check(s,obs):return [dict(part=n,overlap_mm3=v) for n,b in obs.items() if (v:=vol(s,b))>1e-4]
result={'classification':'CALCULATED_NOMINAL_ACCESS_NOT_LOCKING_TORQUE_TEST','native_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
# Open-end 10 mm spanner gauge: 10.5 mm mouth, 18 mm head width, 4 mm
# thickness. Approach from +X while nut is held; adjust by rotating the knob,
# so a full wrench-swing arc is not required inside this bracket.
wrench=box(74,36,17,20,4,18).cut(box(72,35,20.75,15,6,10.5)).fuse(box(94,36,22,66,4,8))
result['wrench_gauge']={'nominal_size_mm':10,'mouth_mm':10.5,'head_width_mm':18,'thickness_mm':4,'y_mm':[36,40],'approach':'+X; hold wrench still and turn large knob','qualification':'Envelope gauge only, not a selected commercial tool or contact-pressure check.'}
obs={n:s for n,s in S.items() if n not in ['LeadLockNut','LeadScrewKnob']}
result['one_wrench_insertion']=[dict(x_offset_mm=x,collisions=check(mv(wrench,x=x),obs)) for x in range(0,61,3)]
# Load washer/nut from the open FRONT before passing the M6 shaft down through
# them. The locknut cannot be moved sideways over an already fitted shaft.
obs={n:s for n,s in S.items() if n not in ['LeadLockNut','LeadScrewKnob','ThrustWasher']}
result['nut_and_washer_loading_before_shaft']=[dict(part=n,z_mm=z,collisions=check(mv(S[n],z=z),obs)) for n in ['LeadLockNut','ThrustWasher'] for z in range(0,61,2)]
result['shaft_insertion_nut_and_washer_preset']=[dict(y_mm=y,collisions=check(mv(S['LeadScrewKnob'],y=y),{n:s for n,s in S.items() if n!='LeadScrewKnob'})) for y in range(0,121,3)]
norm=[(math.cos(math.radians(a)),math.sin(math.radians(a))) for a in [210,330]]
def pose(n,r):
 g=meta[n]['group'];t=r-8
 if g in ['DRIVE','TOP','TOPSCREW']:return mv(S[n],y=t)
 if g.startswith('JAW'):
  nx,ny=norm[int(g[-1])-1];return mv(S[n],nx*t,ny*t)
 return S[n]
rows=[]
for r in [3,8,13]:
 Q={n:pose(n,r) for n in S}
 for a in range(-360,361,30):
  moving=Part.makeCompound([rot(Q[n],a) for n in ['LeadScrewKnob','LeadLockNut']])
  rows.append(dict(diameter_mm=2*r,angle_deg=a,collisions=check(moving,{n:s for n,s in Q.items() if n not in ['LeadScrewKnob','LeadLockNut']})))
result['shaft_and_locknut_both_direction_rotation']=rows
result['axial_geometry']={'locknut_y_mm':[35,41],'nut_height_mm':6,'catalog_metal_height_candidate_mm':4,'shaft_y_mm':[-60,50],
 'full_nut_height_thread_overlap_mm':6,'washer_y_mm':[41,41.8],'frame_seat_y_mm':[42,50],'nominal_washer_frame_gap_mm':.2,
 'drive_nut_pocket_clearance_mm':1.0,'note':'Fully threaded shaft required through the locknut and square drive nut. Insert orientation and actual nylon engagement must be checked against final SKU.'}
result['sources']=[{'title':'Bossard BN33024 DIN985 M6 catalog entry: M6/P1/M6/M1=4/S10, article5813950; dimensional candidate, not purchase approval','url':'https://bossard.partcommunity.com/3d-cad-models/?info=bossard%2F01%2F01_300%2F01_300_600%2F01_300_600_30%2Fbn_637_33024_1722_2082%2Fbn_33024.prj&languageIso=ko','accessed':'2026-09-18'}]
result['limits']=['A nylon locknut is not a keyed shaft collar. Relative shaft/nut slip depends on prevailing torque versus washer/frame drag under load and cannot be proved from CAD.',
 'Initial adjustment: turn knob while holding locknut with one wrench, stop short of clamping the bracket, confirm free bidirectional rotation and small axial endplay. Nominal 0.2 mm is a trial setting target.',
 'Witness-mark nut/shaft and verify marks and endplay through repeated forward/reverse cycles under expected cable force before use. No such physical test has been run.',
 'Do not tighten the locknut harder to remove 1 mm drive-pocket reversal slack; that would clamp the shaft bearing and jam the mechanism.',
 'Nylon insert, helical threads, prevailing torque, wear, hand force and commercial wrench geometry are not modeled.']
result['pass_geometry_only']=all(not row['collisions'] for key in ['one_wrench_insertion','nut_and_washer_loading_before_shaft','shaft_insertion_nut_and_washer_preset','shaft_and_locknut_both_direction_rotation'] for row in result[key])
(O/'lead_access.json').write_text(json.dumps(result,indent=2)+'\n');print('LEAD_ACCESS_PASS',result['pass_geometry_only'],flush=True)
for key in ['one_wrench_insertion','nut_and_washer_loading_before_shaft','shaft_insertion_nut_and_washer_preset','shaft_and_locknut_both_direction_rotation']:
 print(key,[r for r in result[key] if r['collisions']][:3],flush=True)
