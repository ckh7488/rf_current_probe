"""Independent saved-CAD capture, keeper access, mount and closed-slot audit.
CALCULATED, not force/RF/physical qualification. Run with FreeCADCmd.
"""
from pathlib import Path
import json,math,hashlib,itertools
import FreeCAD as A
import Part
O=Path(__file__).resolve().parent;R=O.parents[1];V=A.Vector
d=A.openDocument(str(O/'RFCP_A13_Integrated_DRAFT.FCStd'))
S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
def mv(s,x=0,y=0,z=0):
 q=s.copy();q.translate(V(x,y,z));return q
def overlap(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
capture=[]
# Detect the first obstacle along each straight escape direction. This is not
# a proof against coupled rotation/translation, load, flexure or broken parts.
for name,body,kp in [('FixedCore','LowerBody','LowerKeeper'),('MovingCore','UpperLid','UpperKeeper')]:
 obs=Part.makeCompound([S[body],S[kp]])
 for axis,sign in itertools.product(range(3),[-1,1]):
  hit=None
  for step in range(1,41):
   dist=step*.25;q=[0.,0.,0.];q[axis]=sign*dist
   if overlap(mv(S[name],*q),obs)>1e-4:
    hit=dist;break
  capture.append(dict(core=name,axis='XYZ'[axis],sign=sign,first_interference_by_mm=hit,step_mm=.25))
# Core front face/rear seat contact area via a 0.05 mm displaced intersection.
# Area is local geometric overlap / displacement, not pressure distribution.
contacts=[]
for name,body,kp in [('FixedCore','LowerBody','LowerKeeper'),('MovingCore','UpperLid','UpperKeeper')]:
 contacts.append(dict(core=name,front_area_estimate_mm2=overlap(mv(S[name],z=.05),S[kp])/.05,rear_area_estimate_mm2=overlap(mv(S[name],z=-.05),S[body])/.05))
# Nylon M3 keeper screw heads and an assumed D8 straight driver from the front.
access=[]
for sign,prefix in [(-1,'Lower'),(1,'Upper')]:
 for x in [-37,37]:
  gauge=Part.makeCylinder(4,45,V(x,sign*23,23.8))
  bad=[]
  for n in [prefix+'Keeper','LowerBody','UpperLid','FixedCore','MovingCore','Winding','PCB','SMAEnvelope']:
   vol=overlap(gauge,S[n])
   if vol>1e-4:bad.append(dict(part=n,volume_mm3=vol))
  access.append(dict(x=x,y=sign*23,assumed_driver_diameter_mm=8,collisions=bad))
# Existing PCB hardware remains nylon, but check its actual envelope against
# the SMA/core/winding in the saved integrated model.
pcb={}
for n in ['PCBScrews','PCBNuts']:
 pcb[n]={q:round(S[n].distToShape(S[q])[0],5) for q in ['FixedCore','Winding','SMAEnvelope']}
centerdistance=math.hypot(14.5,11.5)
mount=dict(board_mm=[36,28,1.6],hardware='M2 nylon screws AND nylon nuts; no metal washers',sma_to_mount_center_mm=centerdistance,copper_keepout_radius_mm=3.0,npth_diameter_mm=2.8,modeled_screw_head_diameter_mm=3.8,
 nominal_head_to_48gon_copper_clearance_mm=3*math.cos(math.pi/48)-1.9,
 floating_M2_head_to_copper_clearance_mm=3*math.cos(math.pi/48)-1.9-(2.8-2)/2,
 envelope_distances_mm=pcb,qualification='Geometric isolation only, not RF approval for steel; nylon retained.')
cam=[]
cd=A.openDocument(str(R/'mechanical/cable_clamp_C07_DRAFT/Cable_Clamp_C07_DRAFT.FCStd'))
yoke=cd.getObject('DriveYoke').Shape
for a in [210,330]:
 nx=math.cos(math.radians(a));ny=math.sin(math.radians(a))
 x=nx*(34-5.6);y=ny*34+(ny-1)*-5.6
 # Solid strip directly above the complete rounded slot end, excluding 0.05
 # from each boundary, independently inspected in the saved shape.
 strip=Part.makeBox(5.6,3.5,9.8,V(x-2.8,y+3.0,18.1))
 cam.append(dict(angle=a,slot_end_xy=[x,y],nominal_top_ligament_mm=-2-(y+2.9),solid_strip_missing_mm3=strip.cut(yoke).Volume))
E=1500;w=18;delta=1.8
beams=[]
for rev,t,L in [('A08',1.6,42),('A12',2.4,63)]:
 beams.append(dict(revision=rev,t_mm=t,L_mm=L,E_MPa=E,deflection_mm=delta,total_force_N=2*E*w*t**3*delta/L**3,peak_strain_estimate=3*t*delta/L**2))
report=dict(classification='CALCULATED_SAVED_CAD_AND_IDEAL_BEAM_COMPARISON',native_sha256=hashlib.sha256((O/'RFCP_A13_Integrated_DRAFT.FCStd').read_bytes()).hexdigest(),straight_capture=capture,contact_area_estimates=contacts,keeper_tool_access=access,pcb_mount=mount,closed_cam_slots=cam,ideal_beam_comparison=beams,
 limitations=['Straight capture only; rotations, loosened keeper displacement, real contact pressure, creep and impact untested.','Driver is D8 straight envelope; actual tool/head fit and nearby hand clearance unverified.','PCB envelope/contact spacing does not certify RF response or replacement steel hardware.','Fixed-guided ideal beam comparison neglects roots, end compliance, anisotropy and nonlinear response.'])
report['pass']=all(x['first_interference_by_mm'] is not None for x in capture) and all(not x['collisions'] for x in access) and all(x['front_area_estimate_mm2']>1 and x['rear_area_estimate_mm2']>1 for x in contacts) and all(x['solid_strip_missing_mm3']<1e-4 for x in cam)
(O/'retention_mount_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
