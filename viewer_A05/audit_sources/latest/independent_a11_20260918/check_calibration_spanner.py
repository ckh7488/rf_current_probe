"""A11 independent open-end spanner approach audit.
Generic gauge, not procurement approval of a real hand tool. Read-only product.
"""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
p=R/'mechanical/assembly_A11_DRAFT/RFCP_A11_Integrated_DRAFT.FCStd'
d=A.openDocument(str(p));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def volume(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def check(s,obs):return [dict(part=n,overlap_mm3=v) for n,b in obs.items() if (v:=volume(s,b))>1e-4]
rows=[]
# Nuts are free to rotate before being held. Orient their flats along Z for
# direct X tool access through the existing full-width post windows.
newnuts=[]
for n in S['CalibrationNuts'].Solids:
 n=n.copy()
 if n.BoundBox.ZLength>5.6:n.rotate(n.BoundBox.Center,V(0,1,0),90)
 newnuts.append(n)
S['CalibrationNuts']=Part.makeCompound(newnuts)
for x in [-65,65]:
 for z in [-32,44.7]:
  sign=-1 if z<0 else 1
  # Jaw mouth opens toward the nut; handle points outward. This permits
  # withdrawing the tool while an installed bolt remains in the nut.
  head=Part.makeCylinder(7,3,V(x,-10.3,z),V(0,1,0))
  handle=box(x-4,-10.3,z if sign>0 else z-55,8,3,55)
  mouth=box(x-2.9,-11,z-8 if sign>0 else z-4,5.8,5,12)
  tool=head.fuse(handle).cut(mouth)
  tool.rotate(V(x,0,z),V(0,1,0),90*(1 if x>0 else -1)*sign)
  nuts=[n for n in S['CalibrationNuts'].Solids if abs(n.BoundBox.Center.x-x)<.1 and abs(n.BoundBox.Center.z-z)<.1]
  assert len(nuts)==1
  nut=nuts[0]
  loaded=tool.fuse(nut)
  obs={n:s for n,s in S.items() if n not in ['CalibrationNuts','CalibrationScrews']}
  insertion=[];withdraw=[]
  # Straight sideways approach uses the existing full-width post opening.
  # A long Z-directed spanner can hit a neighboring clamp during removal.
  path=[((1 if x>0 else -1)*i*2,0) for i in range(46)]
  for dx,dz in path:
   insertion.append(dict(offset_x_mm=dx,offset_z_mm=sign*dz,collisions=check(mv(loaded,x=dx,z=sign*dz),obs)))
   withdraw.append(dict(offset_x_mm=dx,offset_z_mm=sign*dz,collisions=check(mv(tool,x=dx,z=sign*dz),S)))
  rows.append(dict(x_mm=x,z_mm=z,open_mouth_toward='-X' if x>0 else '+X',
   loaded_nut_insertion_screws_absent=insertion,empty_tool_withdraw_screws_present=withdraw))
  print(x,z,'loaded',sum(bool(r['collisions']) for r in insertion),'empty',sum(bool(r['collisions']) for r in withdraw),flush=True)
result={'classification':'CALCULATED_NOMINAL_GENERIC_TOOL_NOT_MEASURED',
 'native_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'generic_spanner_mm':dict(head_diameter=14,thickness=3,jaw_opening=5.8,handle_width=8,handle_length_from_center=55),
 'assembly_order':['Position PCB on posts without M3 screws extending into nut windows.',
 'Orient free nylon nut flats along Z; hold with spanner pointing outward X through full-width post opening.',
 'Slide nut and spanner straight inward from the outside X edge to seat the nut.',
 'Insert M3 screw through PCB and post; hold nut while tightening.',
 'Withdraw open-end spanner straight outward X.'],
 'rows':rows,
 'limits':['Discretized straight approach, not full swept volume or human dexterity.',
 'Generic spanner envelope is not an identified purchased tool. Actual 5.5mm tool must fit this envelope and nylon nut.',
 'No torque or polymer creep assessment.']}
result['pass']=all(not pose['collisions'] for row in rows for key in ['loaded_nut_insertion_screws_absent','empty_tool_withdraw_screws_present'] for pose in row[key])
(O/'calibration_spanner.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',result['pass'],flush=True)
