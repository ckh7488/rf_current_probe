"""Reusable screw-free nut-port cap. FreeCAD geometry; DRAFT, untested print.

Local axes: X width, Y height, +Z outward. Receiver rear Z=0, front Z=34.
Insert the cap from +Z toward -Z. Press both exposed side hooks inward to
remove it. Main nut load must remain in the host part, not in this cap.
"""
import math
import FreeCAD as A
import Part
V=A.Vector
DIMENSIONS={
 'receiver_width_mm':30.0,'receiver_height_mm':18.0,'receiver_depth_mm':34.0,
 'cap_face_width_mm':32.0,'cap_face_height_mm':20.0,'cap_face_thickness_mm':4.0,
 'receiver_front_z_mm':34.0,'cap_face_rear_z_mm':34.6,
 'arm_free_length_mm':30.0,'arm_thickness_mm':2.4,'arm_width_mm':6.0,
 'arm_root_radius_mm':1.2,'arm_inner_x_mm':9.0,'arm_outer_x_mm':11.4,
 'receiver_inner_x_mm':12.0,'hook_outer_x_mm':13.4,'hook_shoulder_z_mm':12.0,
 'receiver_latch_z_mm':12.6,'hook_leading_z_mm':4.6,
 'side_release_window_y_mm':[-7.0,7.0],'side_release_window_z_mm':[0.0,12.6],
 'release_outer_wall_relief_x_mm':14.0,'release_outer_wall_relief_z_mm':[12.6,20.0],
 'stem_width_mm':9.6,'stem_height_mm':10.0,'nose_width_mm':6.6,'nose_height_mm':3.4,
 'nose_rear_z_mm':-4.2,'stem_rear_z_mm':0.6,
 'nominal_running_gap_mm':0.6,'nominal_hook_engagement_mm':1.4,
 'assumed_each_wall_position_error_mm':0.3,
 'worst_illustrative_hook_engagement_mm':0.8,
 'nominal_hook_deflection_for_insertion_mm':1.4,
 'worst_illustrative_hook_deflection_mm':2.0,
 'relaxed_installed_arm_deflection_mm':0.0,
 'status':'DRAFT - NOT FOR FABRICATION',
}
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def prism_xz(points,y,h):
 p=[V(x,y,z) for x,z in points]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,h,0))
def make_nut_cap_system(arm_tip_deflection_mm=0.0):
 receiver=box(-15,-9,0,30,18,34).cut(box(-12,-6,-1,24,12,36))
 # Large open rear side windows make the actual hooks reachable by a fingertip.
 for side in [-1,1]:
  receiver=receiver.cut(box(11.9 if side>0 else -15.1,-7,-.1,3.2,14,12.7))
  # Recess only the OUTER wall for finger clearance. The square inner latch
  # shoulder at X=12 / Z=12.6 remains vertical; it is not a pull-out ramp.
  receiver=receiver.cut(box(14 if side>0 else -15.1,-7,12.6,1.1,14,7.4))
 cap=box(-16,-10,34.6,32,20,4).fuse(box(-4.8,-5,.6,9.6,10,34))
 cap=cap.fuse(box(-3.3,-1.7,-4.2,6.6,3.4,4.8))
 for idx,side in enumerate([-1,1]):
  delta=arm_tip_deflection_mm[idx] if isinstance(arm_tip_deflection_mm,(tuple,list)) else arm_tip_deflection_mm
  if abs(delta)<1e-12:
   arm=box(9 if side>0 else -11.4,-3,4.6,2.4,6,30)
   pts=[(side*11.4,4.6),(side*13.4,7.0),(side*13.4,12.0),(side*11.4,12.0)]
   hook=prism_xz(pts,-3,6)
  else:
   # Piecewise-linear samples of an imposed cubic beam curve, for geometric
   # clearance only. It is not a contact/structural simulation or print geometry.
   def fraction(z):
    u=(34.6-z)/30
    return u*u*(3-u)/2
   pts=[(9,34.6-i) for i in range(31)]
   pts.extend([(11.4,4.6),(13.4,7),(13.4,12),(11.4,12)])
   pts.extend((11.4,12+(34.6-12)*i/24) for i in range(1,25))
   arm=prism_xz([(side*(x-delta*fraction(z)),z) for x,z in pts],-3,6)
   hook=None
  cap=cap.fuse(arm)
  if hook is not None:cap=cap.fuse(hook)
 cap=cap.removeSplitter()
 root_edges=[]
 for edge in cap.Edges:
  b=edge.BoundBox
  if abs(b.ZMin-34.6)<1e-5 and b.ZLength<1e-5 and abs(b.YLength-6)<1e-5 and b.XLength<1e-5 and any(abs(abs(b.Center.x)-x)<1e-5 for x in [9,11.4]):root_edges.append(edge)
 relaxed=all(abs(x)<1e-12 for x in arm_tip_deflection_mm) if isinstance(arm_tip_deflection_mm,(tuple,list)) else abs(arm_tip_deflection_mm)<1e-12
 if relaxed and len(root_edges)!=4:raise ValueError('Expected four flexure-root edges, got '+str(len(root_edges)))
 # Printed relaxed geometry always has four R1.2 roots. For imposed deflection
 # sweeps use unfilleted beams to avoid unstable kernel edge labels. This is a
 # clearance surrogate, not an elastic/contact solution of the printed fillet.
 if relaxed:cap=cap.makeFillet(1.2,root_edges).removeSplitter()
 receiver=receiver.removeSplitter()
 if not cap.isValid() or len(cap.Solids)!=1:raise ValueError('Invalid cap')
 if not receiver.isValid() or len(receiver.Solids)!=1:raise ValueError('Invalid receiver')
 # Conservative cantilever sensitivity: load at the hook shoulder, subtract
 # root-radius transition. This is NOT a material allowable or force test.
 leff=34.6-12.0-1.2
 dims=dict(DIMENSIONS,root_fillet_in_this_geometry=relaxed,effective_length_for_strain_bound_mm=leff,
  illustrative_outer_fiber_strain_nominal=1.5*2.4*1.4/leff**2,
  illustrative_outer_fiber_strain_worst=1.5*2.4*2.0/leff**2)
 return receiver,cap,dims
