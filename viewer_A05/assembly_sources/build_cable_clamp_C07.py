"""C07: openable, three-jaw translating-cam cable centering prototype.
FreeCAD 1.0.2. Geometry/kinematics only, not print/force/RF qualification.
XYZ: cable axis Z; Y vertical; nominal cable radius 8 mm.
"""
from pathlib import Path
import math,json,hashlib,itertools
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];O=R/'mechanical/cable_clamp_C07_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector;D=A.newDocument('Cable_Clamp_C07_DRAFT');S={};M={}
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cy(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def move(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter()
def rot(s,a):q=s.copy();q.rotate(V(),V(0,0,1),a);return q
def prism(points,z,h):
 p=[V(x,y,z) for x,y in points];return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def slot(p,q,r,z,h):
 dx=q[0]-p[0];dy=q[1]-p[1];ll=math.hypot(dx,dy);nx=-dy*r/ll;ny=dx*r/ll
 return fuse([cy(r,h,*p,z),cy(r,h,*q,z),prism([(p[0]+nx,p[1]+ny),(q[0]+nx,q[1]+ny),(q[0]-nx,q[1]-ny),(p[0]-nx,p[1]-ny)],z,h)])
def hexnut(x,y,z,af,h,axis='z'):
 rr=af/math.sqrt(3);s=prism([(rr*math.cos(i*math.pi/3),rr*math.sin(i*math.pi/3)) for i in range(6)],0,h)
 s=s.cut(cy(3.1 if af==10 else 2.1,h+2,0,0,-1))
 if axis=='y':s.rotate(V(),V(1,0,0),-90)
 return move(s,x,y,z)
def add(n,s,color,group,printed=False):
 s=s.removeSplitter();o=D.addObject('PartDesign::Feature',n);o.Shape=s
 o.addProperty('App::PropertyString','Status');o.Status='DRAFT - NOT FOR FABRICATION'
 S[n]=s;M[n]={'color':color,'group':group,'printed':printed}
 if printed:
  s.exportStep(str(O/'parts'/(n+'_DRAFT.step')));b=s.BoundBox
  MeshPart.meshFromShape(Shape=move(s,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(O/'parts'/(n+'_DRAFT.stl')))
 return s
def round_nose(s):
 edges=[]
 for e in s.Edges:
  b=e.BoundBox
  if b.ZLength>9.9 and b.XLength<1e-5 and b.YLength<1e-5 and (b.Center.x*b.Center.x+b.Center.y*b.Center.y)**.5<17:edges.append(e)
 return s.makeFillet(.8,edges) if edges else s
# Rear datum frame and integral front-open guide rails. No closed cable ring.
frame=box(-63,-62,12,154,99,5).cut(cy(21,9,0,0,10)).cut(box(-21,0,10,42,45,10))
# Remove unnecessary upper left/right central panels, preserving cam pin travel.
frame=frame.cut(box(-43,12,11,22,27,8)).cut(box(21,12,11,22,27,8))
for x in [-56,42]:
 frame=frame.fuse(box(x-4.3,5,17,3.5,15,15)).fuse(box(x+14.8,5,17,3.5,15,15))
# Open toward +Z: insert the yoke from the front, then install follower screws.
# Follower heads retain the yoke axially. Actual play/load still requires testing.
# Side lead screw accessible from above, clear of the removable top bridge.
frame=frame.fuse(box(71,-62,12,20,112,5)).fuse(box(71,42,17,20,8,16))
frame=frame.cut(cy(3.5,15,80,39,26,V(0,1,0)))
frame=frame.cut(box(72,33,16,16,9,2))
# Foot holes mount the independent module on a later common datum base.
frame=frame.fuse(box(-63,-72,-8,158,10,51))
for x in [-54,80]:frame=frame.cut(cy(2.7,14,x,-73,4,V(0,1,0)))
angles=[210,330];normals=[]
for a in angles:
 th=math.radians(a);nx,ny=math.cos(th),math.sin(th);normals.append((nx,ny))
 # 14 mm jaw bodies; 0.8 mm side and front clearance. 2.4 mm front lips.
 frame=frame.cut(slot((nx*20,ny*20),(nx*49,ny*49),2.9,10,10))
 for lo in [-12.2,7.8]:frame=frame.fuse(rot(box(20,lo,-3.2,29,4.4,15.2),a))
 for lo in [-12.2,6.5]:frame=frame.fuse(rot(box(23,lo,-3.2,22,5.7,2.4),a))
# C07 raises cam-web top from -6 to -2: closed rounded slots, 3.7 mm minimum top ligament.
# Drive yoke moves vertically; two straight cam slots produce equal radial travel.
yoke=fuse([box(-56,-54,18,112,10,10),box(-56,-44,18,14,70,11.3),box(42,-44,18,14,70,11.3),box(-54,-44,18,36,42,10),box(18,-44,18,36,42,10),box(54,-37,18,34,14,15)])
for nx,ny in normals:
 p=(nx*34+(nx)*-5.6,ny*34+(ny-1)*-5.6);q=(nx*34+nx*5.6,ny*34+(ny-1)*5.6)
 yoke=yoke.cut(slot(p,q,2.9,16,15))
# Captured M6 nut, slid in from the visible front. No printed working thread.
# C07 retains front insertion while reducing reversal slack: 6.0 mm pocket,
# 5.0 mm nominal square nut, centered at Y=-30.0. No zero-backlash claim.
DRIVE_POCKET_HEIGHT=6.0
DRIVE_NUT_HEIGHT=5.0
DRIVE_POCKET_Y=-30.0-DRIVE_POCKET_HEIGHT/2
DRIVE_NUT_Y=-30.0-DRIVE_NUT_HEIGHT/2
yoke=yoke.cut(cy(3.5,22,80,-40,26,V(0,1,0))).cut(box(74.2,DRIVE_POCKET_Y,20.4,11.6,DRIVE_POCKET_HEIGHT,16))
for x in [-49,49]:
 yoke=yoke.cut(cy(2.7,24,x,9,24.3,V(0,1,0))).cut(box(x-3.9,16.8,20.4,7.8,4.6,12))
# Lift-off top bridge is also the third jaw. No hinge, separate spring or pad.
bridge=fuse([box(-56,26,18,112,10,11.3),box(-6,24,0,12,12,28),prism([(-1.5,8),(1.5,8),(4,14),(4,30),(-4,30),(-4,14)],0,10)])
for x in [-49,49]:bridge=bridge.cut(cy(2.7,16,x,23,24.3,V(0,1,0)))
add('Frame',frame,'#547e90','FIXED',True)
add('DriveYoke',yoke,'#91b8b6','DRIVE',True)
add('TopBridgeJaw',round_nose(bridge),'#deac65','TOP',True)
for i,(a,(nx,ny)) in enumerate(zip(angles,normals)):
 jaw=prism([(8,-1.5),(8,1.5),(14,7),(44,7),(44,-7),(14,-7)],0,10)
 jaw=rot(jaw.cut(cy(2.2,14,34,0,-2)).cut(box(29.6,-4.4,-1,8.8,8.8,7.8)),a)
 add('Jaw'+str(i+1),round_nose(jaw),'#dfae66','JAW'+str(i+1),True)
 # Dimensional candidate: M4 thread / D5x20 shoulder / D9x4 head; not threaded CAD.
 follower=fuse([cy(2,8,nx*34,ny*34,2),cy(2.5,20,nx*34,ny*34,10),cy(4.5,4,nx*34,ny*34,30)])
 add('Follower'+str(i+1),follower,'#abb7c0','JAW'+str(i+1))
 add('FollowerNut'+str(i+1),rot(box(30.5,-3.5,3.5,7,7,3.2).cut(cy(2.1,5,34,0,3)),a),'#abb7c0','JAW'+str(i+1))
# Bridge screws release before the bridge moves. Open square-nut seats prevent rotation; loose nuts may fall out when unscrewed.
for i,x in enumerate([-49,49]):
 add('BridgeScrew'+str(i+1),cy(2,20,x,16,24.3,V(0,1,0)).fuse(cy(6,7,x,36,24.3,V(0,1,0))),'#aebbc3','TOPSCREW')
 add('BridgeNut'+str(i+1),box(x-3.5,17.5,20.8,7,3.2,7).cut(cy(2.1,6,x,16,24.3,V(0,1,0))),'#aebbc3','DRIVE')
lead=cy(3,110,80,-60,26,V(0,1,0)).fuse(cy(14,12,80,50,26,V(0,1,0)))
add('LeadScrewKnob',lead,'#b5c0c6','LEAD')
add('DriveNut',box(75,DRIVE_NUT_Y,21,10,DRIVE_NUT_HEIGHT,10).cut(cy(3.1,7,80,-33.5,26,V(0,1,0))),'#aebbc3','DRIVE')
# Retain C06 single M6 nyloc thrust adjustment, which has a working role.
# This is shaft endplay control, not a loose-nut cover. Rotate with lead shaft.
add('LeadLockNut',hexnut(80,35,26,10,6,'y'),'#b5c0c6','LEAD')
add('ThrustWasher',cy(6,.8,80,41,26,V(0,1,0)).cut(cy(3.2,2,80,40.5,26,V(0,1,0))),'#b5c0c6','FIXED')
D.recompute();native=O/'Cable_Clamp_C07_DRAFT.FCStd';D.saveAs(str(native))
Part.makeCompound(list(S.values())).exportStep(str(O/'Cable_Clamp_C07_DRAFT.step'))
mesh={}
for n,s in S.items():
 vs,tr=s.tessellate(.16);mesh[n]={'vertices':[list(v) for v in vs],'triangles':tr,**M[n]}
(O/'mesh.json').write_text(json.dumps(mesh))
def pose(n,r):
 t=r-8;g=M[n]['group']
 if g in ['DRIVE','TOP','TOPSCREW']:return move(S[n],y=t)
 if g.startswith('JAW'):nx,ny=normals[int(g[-1])-1];return move(S[n],nx*t,ny*t)
 return S[n]
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
rows=[]
for r in [3+i*.5 for i in range(21)]:
 ss={n:pose(n,r) for n in S};bad=[]
 for a,b in itertools.combinations(S,2):
  v=vol(ss[a],ss[b])
  if v>1e-4:bad.append({'a':a,'b':b,'volume_mm3':round(v,5)})
 cable=cy(r,70,0,0,-20);cv=sum(vol(cable,s) for s in ss.values())
 rows.append({'diameter_mm':r*2,'collisions':bad,'cable_overlap_mm3':cv})
 print('D',r*2,'collisions',bad,'cable',cv,flush=True)
paths=[]
for t in range(0,61,3):
 obs=Part.makeCompound([s for n,s in S.items() if n not in ['TopBridgeJaw','BridgeScrew1','BridgeScrew2']])
 paths.append({'lift_mm':t,'overlap_mm3':vol(move(S['TopBridgeJaw'],y=t),obs)})
prints={n:{'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume} for n,s in S.items() if M[n]['printed']}
report={'status':'DRAFT - NOT FOR FABRICATION','classification':'CALCULATED_NOMINAL_CAD','freecad':A.Version(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'printed_parts':prints,'drive_nut_fit':{'pocket_height_mm':DRIVE_POCKET_HEIGHT,'nut_nominal_height_mm':DRIVE_NUT_HEIGHT,'axial_free_play_nominal_mm':DRIVE_POCKET_HEIGHT-DRIVE_NUT_HEIGHT,'lead_pitch_assumed_mm':1.0,'classification':'CALCULATED_NOMINAL_NOT_MEASURED'},'radius_sweep':rows,'top_lift_screw_removed':paths,
 'pass':all(not x['collisions'] and x['cable_overlap_mm3']<1e-4 for x in rows) and all(x['overlap_mm3']<1e-4 for x in paths) and all(x['valid'] and x['solids']==1 for x in prints.values()),
 'limits':['C07 M6 pocket has 1.0 mm nominal reversal slack; this is not a zero-backlash mechanism. Final nut size and print tolerance require trial assembly.','Nominal CAD only. No contact-force, friction, wear, print-tolerance, RF or physical tests.','Fully threaded M6x110 knob screw + DIN985 M6 AF10/H6 locknut + washer envelopes; exact products and reversing-load adjustment require confirmation.','Nose vertical edges rounded R0.8. Surface roughness, cable pressure and print finish untested.','C07 feet remain Y=-72 for the common base. Integrated A13 verification is maintained separately.','Cap must be removed to insert a connected cable; two M4 knobs per cap.','Screw force can crush cable: no torque limiter is implemented.']}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pass'],flush=True)
