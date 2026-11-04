"""C05 targeted CAD audit. Run with FreeCADCmd; no physical validation."""
from pathlib import Path
import json, hashlib, math
import FreeCAD as A, Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
paths={r:R/f'mechanical/cable_clamp_{r}_DRAFT/Cable_Clamp_{r}_DRAFT.FCStd' for r in ['C04','C05']}
docs={r:A.openDocument(str(p)) for r,p in paths.items()}
models={r:{o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')} for r,d in docs.items()}
S=models['C05'];meta=json.loads((paths['C05'].parent/'mesh.json').read_text())
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def rot(s,c,axis,a):q=s.copy();q.rotate(c,axis,a);return q
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def check(s,obs):return [dict(part=n,overlap_mm3=v) for n,b in obs.items() if (v:=vol(s,b))>1e-4]
result={'classification':'CALCULATED_SAVED_NOMINAL_CAD_NOT_PHYSICAL',
 'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths.values(),R/'mechanical/build_cable_clamp_C05.py',Path(__file__)]}}
rows=[]
for n in S:
 old=models['C04'][n];new=S[n]
 rows.append(dict(part=n,changed_volume_mm3=old.cut(new).Volume+new.cut(old).Volume))
result['before_after_symmetric_difference']=rows
result['unchanged_except_drive_yoke_and_nut']=all(x['changed_volume_mm3']<1e-5 for x in rows if x['part'] not in ['DriveYoke','DriveNut'])

norm=[(math.cos(math.radians(a)),math.sin(math.radians(a))) for a in [210,330]]
def pose(n,r):
 t=r-8;g=meta[n]['group'];s=S[n]
 if g in ['DRIVE','TOP','TOPSCREW']:return mv(s,y=t)
 if g.startswith('JAW'):
  nx,ny=norm[int(g[-1])-1];return mv(s,nx*t,ny*t)
 return s

# Both loaded nut positions must fit throughout the modeled cable range.
rows=[]
for r in [3+i*.5 for i in range(21)]:
 Q={n:pose(n,r) for n in S}
 for dy in [-.5,.5]:
  rows.append(dict(diameter_mm=2*r,nut_shift_y_mm=dy,collisions=check(mv(Q['DriveNut'],y=dy),{n:q for n,q in Q.items() if n!='DriveNut'})))
result['drive_nut_bearing_positions']=rows

# The nut is inserted before the lead screw. Passing a solid nut laterally over
# an already fitted lead is not an assembly path.
result['drive_nut_front_insertion_lead_absent']=[dict(z_shift_mm=z,collisions=check(mv(S['DriveNut'],z=z),{'DriveYoke':S['DriveYoke'],'Frame':S['Frame']})) for z in range(0,61,2)]

# The 0.5 mm bearing allowance is bounded by material, not an open-ended pocket.
rows=[]
for dy in [-.55,-.5,0,.5,.55]:
 rows.append(dict(nut_shift_y_mm=dy,overlap_mm3=vol(mv(S['DriveNut'],y=dy),S['DriveYoke'])))
result['axial_stop_contact']=rows
rotation=[dict(angle_deg=a,overlap_mm3=vol(rot(S['DriveNut'],V(80,-30,26),V(0,1,0),a),S['DriveYoke'])) for a in range(0,91,5)]
result['nut_anti_rotation']=rotation

rows=[]
for r in [3,8,13]:
 Q={n:pose(n,r) for n in S}
 for a in range(0,361,15):
  moving=Part.makeCompound([rot(Q[n],V(80,0,26),V(0,1,0),a) for n in ['LeadScrewKnob','JamNut1','JamNut2']])
  rows.append(dict(diameter_mm=2*r,angle_deg=a,collisions=check(moving,{n:s for n,s in Q.items() if n not in ['LeadScrewKnob','JamNut1','JamNut2']})))
result['lead_and_locked_jam_nut_rotation']=rows
result['fit_budget']={'old_pocket_height_mm':6.8,'pocket_height_mm':6,'nominal_nut_height_mm':5,
 'nominal_axial_free_play_mm':1,'nominal_reversal_travel_at_1mm_pitch_turns':1,
 'illustrative_wall_position_error_each_mm':.3,'illustrative_gap_with_exact_5mm_nut_mm':[.4,1.6],
 'rear_wall_mm':2.4,'side_clearance_each_nominal_mm':.8,
 'note':'Wall-error range is a conservative sensitivity calculation, not a JLCPCB fit guarantee. Nut tolerance, hole/nut centering and actual print shrinkage remain unverified. Thread backlash and 0.2 mm shaft endplay add separately; gap is not a measured mechanism backlash.'}
result['limits']=['Actual nut SKU and tolerance range are not finalized. A nominal 10x10x5 nut is represented.',
 'Threads are smooth envelopes. No friction, loads, wear, torque limit, creep or measured cable centering.',
 'A smaller than modeled nut can increase free play. A larger nut can bind. Do not substitute without checking.',
 'Front nut insertion assumes the lead screw has not yet been installed.']
result['pass']=result['unchanged_except_drive_yoke_and_nut'] and all(not row['collisions'] for key in ['drive_nut_bearing_positions','drive_nut_front_insertion_lead_absent','lead_and_locked_jam_nut_rotation'] for row in result[key]) and all(row['overlap_mm3']<1e-4 for row in result['axial_stop_contact'] if abs(row['nut_shift_y_mm'])<=.5) and all(row['overlap_mm3']>1e-4 for row in result['axial_stop_contact'] if abs(row['nut_shift_y_mm'])>.5) and any(row['overlap_mm3']>1e-4 for row in rotation)
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('C05 TARGETED PASS',result['pass'],flush=True)
print('CHANGES',[(x['part'],round(x['changed_volume_mm3'],6)) for x in result['before_after_symmetric_difference'] if x['changed_volume_mm3']>1e-5],flush=True)
