"""C01: openable, three-jaw translating-cam cable centering prototype.
FreeCAD 1.0.2. Geometry/kinematics only, not print/force/RF qualification.
XYZ: cable axis Z; Y vertical; nominal cable radius 8 mm.
"""
from pathlib import Path
import math,json,hashlib,itertools
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];O=R/'mechanical/cable_clamp_C01_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector;D=A.newDocument('Cable_Clamp_C01_DRAFT');S={};M={}
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
# Rear datum frame and integral front-open guide rails. No closed cable ring.
frame=box(-59,-62,12,150,99,5).cut(cy(21,9,0,0,10)).cut(box(-21,0,10,42,45,10))
# Remove unnecessary upper left/right central panels, preserving cam pin travel.
frame=frame.cut(box(-43,12,11,22,27,8)).cut(box(21,12,11,22,27,8))
for x in [-54,44]:
 frame=frame.fuse(box(x-4,5,17,3.5,15,15)).fuse(box(x+10.5,5,17,3.5,15,15))
# Open toward +Z: insert the yoke from the front, then install follower screws.
# Follower heads retain the yoke axially. Actual play/load still requires testing.
# Side lead screw accessible from above, clear of the removable top bridge.
frame=frame.fuse(box(71,-62,12,20,112,5)).fuse(box(71,42,17,20,8,16))
frame=frame.cut(cy(3.5,15,80,39,23,V(0,1,0)))
# Foot holes mount the independent module on a later common datum base.
frame=frame.fuse(box(-63,-70,-8,158,8,51))
for x in [-54,80]:frame=frame.cut(cy(2.7,14,x,-73,4,V(0,1,0)))
angles=[210,330];normals=[]
for a in angles:
 th=math.radians(a);nx,ny=math.cos(th),math.sin(th);normals.append((nx,ny))
 # Back plate slots and radial guide walls. 0.6 mm side clearance, 0.2 mm front.
 frame=frame.cut(slot((nx*20,ny*20),(nx*49,ny*49),2.9,10,10))
 for lo in [-9,4.6]:frame=frame.fuse(rot(box(20,lo,-2,29,4.4,14),a))
 for lo in [-9,3.5]:frame=frame.fuse(rot(box(23,lo,-2,22,5.5,-.2-(-2)),a))
# Drive yoke moves vertically; two straight cam slots produce equal radial travel.
yoke=fuse([box(-54,-54,18,108,10,10),box(-54,-44,18,10,70,10),box(44,-44,18,10,70,10),box(-54,-44,18,36,38,10),box(18,-44,18,36,38,10),box(54,-35,18,34,10,10)])
for nx,ny in normals:
 p=(nx*34+(nx)*-5.6,ny*34+(ny-1)*-5.6);q=(nx*34+nx*5.6,ny*34+(ny-1)*5.6)
 yoke=yoke.cut(slot(p,q,2.9,16,15))
# Captured M6 nut, slid in from the visible front. No printed working thread.
yoke=yoke.cut(cy(3.5,22,80,-40,23,V(0,1,0))).cut(box(74.2,-33.4,17,11.6,6.8,14))
for x in [-49,49]:
 yoke=yoke.cut(cy(2.7,24,x,9,23,V(0,1,0))).cut(box(x-3.9,16.8,19.1,7.8,4.6,12))
# Lift-off top bridge is also the third jaw. No hinge, separate spring or pad.
bridge=fuse([box(-54,26,18,108,10,10),box(-6,24,0,12,12,28),prism([(-1.5,8),(1.5,8),(4,14),(4,30),(-4,30),(-4,14)],0,10)])
for x in [-49,49]:bridge=bridge.cut(cy(2.7,16,x,23,23,V(0,1,0)))
add('Frame',frame,'#547e90','FIXED',True)
add('DriveYoke',yoke,'#91b8b6','DRIVE',True)
add('TopBridgeJaw',bridge,'#deac65','TOP',True)
for i,(a,(nx,ny)) in enumerate(zip(angles,normals)):
 jaw=rot(prism([(8,-1.5),(8,1.5),(14,4),(44,4),(44,-4),(14,-4)],0,10),a)
 jaw=jaw.cut(cy(2.2,14,nx*34,ny*34,-2)).cut(box(nx*34-4.4,ny*34-4.4,-1,8.8,8.8,7.8))
 add('Jaw'+str(i+1),jaw,'#dfae66','JAW'+str(i+1),True)
 # Dimensional candidate: M4 thread / D5x20 shoulder / D9x4 head; not threaded CAD.
 follower=fuse([cy(2,7,nx*34,ny*34,3),cy(2.5,20,nx*34,ny*34,10),cy(4.5,4,nx*34,ny*34,30)])
 add('Follower'+str(i+1),follower,'#abb7c0','JAW'+str(i+1))
 add('FollowerNut'+str(i+1),hexnut(nx*34,ny*34,3.5,7,3.2),'#abb7c0','JAW'+str(i+1))
# Bridge M4 screws release before cap moves. Nuts remain in visible yoke pockets.
for i,x in enumerate([-49,49]):
 add('BridgeScrew'+str(i+1),cy(2,20,x,16,23,V(0,1,0)).fuse(cy(6,7,x,36,23,V(0,1,0))),'#aebbc3','TOPSCREW')
 add('BridgeNut'+str(i+1),box(x-3.5,17.5,19.5,7,3.2,7).cut(cy(2.1,6,x,16,23,V(0,1,0))),'#aebbc3','DRIVE')
lead=cy(3,104,80,-54,23,V(0,1,0)).fuse(cy(14,12,80,50,23,V(0,1,0)))
add('LeadScrewKnob',lead,'#b5c0c6','LEAD')
add('DriveNut',hexnut(80,-32.8,23,10,5.2,'y'),'#aebbc3','DRIVE')
# Fixed thrust collar idealization; exact shaft retention/bearing product pending.
collar=cy(5.5,3,80,38.5,23,V(0,1,0)).cut(cy(3.05,5,80,37.5,23,V(0,1,0)))
add('ThrustCollar',collar,'#b5c0c6','FIXED')
D.recompute();native=O/'Cable_Clamp_C01_DRAFT.FCStd';D.saveAs(str(native))
Part.makeCompound(list(S.values())).exportStep(str(O/'Cable_Clamp_C01_DRAFT.step'))
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
report={'status':'DRAFT - NOT FOR FABRICATION','classification':'CALCULATED_NOMINAL_CAD','freecad':A.Version(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'printed_parts':prints,'radius_sweep':rows,'top_lift_screw_removed':paths,
 'pass':all(not x['collisions'] and x['cable_overlap_mm3']<1e-4 for x in rows) and all(x['overlap_mm3']<1e-4 for x in paths) and all(x['valid'] and x['solids']==1 for x in prints.values()),
 'limits':['Nominal CAD only. No contact-force, friction, wear, print-tolerance, RF or physical tests.','Exact lead screw, thrust retention, follower shoulder screws and material are not selected.','Sharp nominal edges require specified print finishing/radii before fabrication; no hand cutting pads.','Front/rear common base attachment and clearance to actual coax/fixture are not yet detailed.','Cap must be removed to insert a connected cable; two M4 knobs per cap.','Screw force can crush cable: no torque limiter is implemented.']}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pass'],flush=True)
