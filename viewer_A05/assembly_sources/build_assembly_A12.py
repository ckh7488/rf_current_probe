"""A12 integrated review assembly. FreeCAD 1.0; no fabrication approval.
CAD uses the nominal CLOSED (deflected) lid. The lid print is the FREE shape.
Deflection geometry is an imposed beam curve, NOT a structural simulation.
"""
from pathlib import Path
import math,json,hashlib,itertools,sys
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];O=R/'mechanical/assembly_A12_DRAFT';(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector;D=A.newDocument('RFCP_A12_Integrated_DRAFT');S={};M={};FREE={}
STATUS='DRAFT - NOT FOR FABRICATION';DELTA=1.8
sys.path.insert(0,str(R/'mechanical'))
from common_nut_cap import make_nut_cap_system
CAP_RECEIVER,CAP_SHAPE,CAP_DIMS=make_nut_cap_system()
CAPS=[]
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cy(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def flip(s):q=s.copy();m=A.Matrix();m.A22=-1;q.transformShape(m);return q
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter()
def hexz(x,y,z,af,h):
 rr=af/math.sqrt(3);p=[V(x+rr*math.cos(i*math.pi/3),y+rr*math.sin(i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def add(n,s,c,g,printed=False,free=None,**kw):
 s=s.removeSplitter();o=D.addObject('PartDesign::Feature',n);o.Shape=s
 for k,v in [('Status',STATUS),('Group',g),('DisplayColorHex',c)]:o.addProperty('App::PropertyString',k);setattr(o,k,v)
 S[n]=s;M[n]=dict(color=c,group=g,printed=printed,**kw)
 if printed:
  q=free if free is not None else s;FREE[n]=q
  q.exportStep(str(O/'parts'/(n+'_FREE_DRAFT.step')));b=q.BoundBox
  MeshPart.meshFromShape(Shape=mv(q,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(O/'parts'/(n+'_FREE_DRAFT.stl')))
 return s
def side_place(s,x,y,z,sign):
 q=s.copy();q.rotate(V(),V(0,1,0),90*sign);q.translate(V(x,y,z));return q
def save_print(n,s):
 FREE[n]=s;s.exportStep(str(O/'parts'/(n+'_DRAFT.step')));b=s.BoundBox
 MeshPart.meshFromShape(Shape=mv(s,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(O/'parts'/(n+'_DRAFT.stl')))
def common_cap(name,origin,sign,group):
 x,y,z=origin;sh=side_place(CAP_SHAPE,x,y,z,sign);add(name,sh,'#edc76d',group)
 M[name].update(printed=True,print_source='CommonNutCap_DRAFT.stl',service_direction=[sign,0,0]);CAPS.append(name)
def open_receiver(start=0.0,length=14.2):
 # Top loading hatch: nut remains visible at the rear of the receiver, rather than pushed down a closed 34mm tube.
 return CAP_RECEIVER.cut(box(-9,5.9,start-.1,18,4,length)).removeSplitter()

def head_receiver():
 # One extra millimetre BELOW the receiver opens the finger window downward
 # without touching the L datum or leaving a thin lower wall (2mm remains).
 q=open_receiver(8,14.2).fuse(box(-15,-10,0,30,1,34))
 for side in [-1,1]:
  q=q.cut(box(11.9 if side>0 else -15.1,-8,-.1,3.2,15,12.7))
  q=q.cut(box(14 if side>0 else -15.1,-8,12.6,1.1,15,7.4))
 return q.removeSplitter()
def wing_nut(x,z,dx=0,dy=0,dz=0):
 # SMO-3(N) dimensioned conservative envelope: D6.4x4 hub,15.96x2.3x8 wings.
 # The un-dimensioned rounded/sloped wing outline is intentionally not claimed exact.
 hub=cy((6.4+dx)/2,4+dy,x,-7.2-(4+dy),z,V(0,1,0))
 wings=box(x-(2.3+dx)/2,-7.2-(8+dy),z-(15.96+dz)/2,2.3+dx,8+dy,15.96+dz)
 return hub.fuse(wings).cut(cy(1.6,12,x,-18,z,V(0,1,0))).removeSplitter()
a07=A.openDocument(str(R/'mechanical/clamp_A07_DRAFT/RFCP_Clamp_A07_DRAFT.FCStd'))
a05=A.openDocument(str(R/'mechanical/clamp_A05_DRAFT/RFCP_A05_Fixture_REVIEW.FCStd'))
# Lower body retained, with integral broad seating lands replacing loose pads.
lower=a07.getObject('LowerShell').Shape.copy()
for x in [-9,9]:lower=lower.fuse(box(x-3,-32,2,6,2.3582,8))
for x in [-29.5,21]:lower=lower.fuse(box(x,-15,-1.5,8.5,8,1.5))
# Move the closure anchors outward; fill obsolete holes and remove old stop towers.
for sign in [-1,1]:
 lower=lower.cut(box(82 if sign>0 else -100,-6,-8,18,6,32))
 lower=lower.fuse(box(82 if sign>0 else -121,-38,-8,39,32,22))
 lower=lower.fuse(box(103 if sign>0 else -121,-6,-8,18,6,32))
 lower=lower.cut(cy(3.1,45,sign*111,-40,6.35,V(0,1,0)))
 lower=lower.cut(box(107.5 if sign>0 else -125,-12,2.15,17.5,5.6,8.4))
# Wider keeper bosses, moved out 1 mm. Remove the old counterbore's feather edge.
for sign in [-1,1]:
 x=sign*37;left=32.5 if sign>0 else -42
 lower=lower.fuse(box(left,-30,-4.5,9.5,14,20))
 lower=lower.cut(box(31.5 if sign>0 else -43,-29,-10,11.5,12,5.5))
 lower=lower.cut(cy(2.1,36,x,-23,-12))
 lower=lower.cut(box(left,-30,10.5,9.5,14,8))
# Thicken the inherited 0.75 mm PCB relief roof toward its empty rear clearance.
lower=lower.fuse(box(-18.5,-37,13.1,37,2,2.4))
# Open central wire access through the old 0.15mm Z lip (A07 overlapping reliefs).
# The rear wall remains2.5mm thick; PCB mounting bosses/core seats are outside this window.
lower=lower.cut(box(-6,-40,-2,12,8.1,17.8))
lower=lower.fuse(box(-21,-68,-4.5,42,3,12))
# One visible L datum at LEFT closure foot; seat gently left/back before tightening.
# Opposite foot remains free to accommodate span tolerance. No tight printed pin fit.
# Walls are 6mm thick; at least 3mm remains at the flared top. 4mm straight seating land, then a 4mm flared lead-in.
pts=[V(-127,-4,-8),V(-121,-4,-8),V(-121,4,-8),V(-124,8,-8),V(-127,8,-8)]
leftguide=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,32))
pts=[V(-121,-4,-14),V(-121,-4,-8),V(-121,4,-8),V(-121,8,-11),V(-121,8,-14)]
backguide=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(18,0,0))
# Fill the L corner continuously: edge-only contact between two walls produces a non-manifold STL.
def datum_wire(y,xmax,zmax):
 pts=[V(-127,y,-14),V(xmax,y,-14),V(xmax,y,zmax),V(-127,y,zmax)]
 return Part.makePolygon(pts+[pts[0]])
corner=box(-127,-4,-14,6,8,6).fuse(Part.makeLoft([datum_wire(4,-121,-8),datum_wire(8,-124,-11)],True))
lower=lower.fuse(leftguide).fuse(backguide).fuse(corner)
# Head square nuts now load from the outside X, with a common visible release cap.
for sign in [-1,1]:
 # Lower the cap/receiver by1mm for finger clearance below the unmodified L datum.
 origin=(sign*119.3,-10,6.35)
 lower=lower.cut(side_place(box(-15,-10,0,30,19,34).cut(head_receiver()),*origin,sign))
 lower=lower.fuse(side_place(head_receiver(),*origin,sign))
 common_cap('HeadNutCover'+('1' if sign<0 else '2'),origin,sign,'HEAD_FIXED')
# Keep the A11 datum roots intact above the nut-cap tunnel.
lower=lower.fuse(leftguide).fuse(backguide).fuse(corner)
add('LowerBody',lower,'#356e84','HEAD_FIXED',True)
carrier=box(-40,3,-4.5,80,34,20).cut(box(-32.5,0,-1.5,65,32,25)).cut(cy(18,30,0,0,-7))
for x in [-9,9]:carrier=carrier.fuse(box(x-3,29.6418,2,6,2.3582,8))
for x in [-29.5,21]:carrier=carrier.fuse(box(x,7,-1.5,8.5,8,1.5))
for sign in [-1,1]:
 x=sign*37;left=32.5 if sign>0 else -42
 carrier=carrier.fuse(box(left,16,-4.5,9.5,14,20))
 carrier=carrier.cut(cy(2.1,36,x,23,-12)).cut(box(left,16,10.5,9.5,14,8))
# One printed lid: remote hard-stop pillars, two broad leaf beams, open core carrier.
def lid(deflection):
 ss=[mv(carrier,y=deflection-DELTA)]
 for sign in [-1,1]:
  stop=box(103 if sign>0 else -121,0,-8,18,40,32).cut(cy(2.6,44,sign*111,-2,6.35,V(0,1,0)))
  ss.append(stop)
  # Cantilever span between X=40 and 103; extra overlap into carrier/anchor.
  top=[];bottom=[]
  for i in range(74):
   x=32+i;u=max(0,min(1,(103-x)/63));f=u*u*(3-2*u)
   y=32+deflection*f
   bottom.append(V(sign*x,y,-3));top.append(V(sign*x,y+2.4,-3))
  if abs(deflection)<1e-12:
   # Preserve the exact A10 printable/free shape for its scoped FEA source.
   p=bottom+top[::-1];wire=Part.makePolygon(p+[p[0]])
  else:
   # Exact cubic deflection curve avoids tiny faceted edges under the root fillet.
   # The old 1mm polyline produced an unorientable CLOSED solid after filleting.
   y0=32+deflection;y1=32
   b=Part.BezierCurve();b.setPoles([V(sign*40,y0,-3),V(sign*61,y0,-3),V(sign*82,y1,-3),V(sign*103,y1,-3)])
   t=Part.BezierCurve();t.setPoles([V(sign*103,y1+2.4,-3),V(sign*82,y1+2.4,-3),V(sign*61,y0+2.4,-3),V(sign*40,y0+2.4,-3)])
   wire=Part.Wire([Part.makeLine(V(sign*32,y0,-3),V(sign*40,y0,-3)),b.toShape(),Part.makeLine(V(sign*103,y1,-3),V(sign*105,y1,-3)),Part.makeLine(V(sign*105,y1,-3),V(sign*105,y1+2.4,-3)),Part.makeLine(V(sign*105,y1+2.4,-3),V(sign*103,y1+2.4,-3)),t.toShape(),Part.makeLine(V(sign*40,y0+2.4,-3),V(sign*32,y0+2.4,-3)),Part.makeLine(V(sign*32,y0+2.4,-3),V(sign*32,y0,-3))])
  ss.append(Part.Face(wire).extrude(V(0,0,18)))
 q=fuse(ss)
 roots=[e for e in q.Edges if abs(abs(e.BoundBox.Center.x)-103)<1e-5 and abs(e.BoundBox.ZLength-18)<1e-5 and e.BoundBox.XLength<1e-5 and e.BoundBox.YLength<1e-5]
 if len(roots)!=4:raise ValueError('Expected four outer flexure root edges')
 return q.makeFillet(1.5,roots)
loaded=lid(DELTA);free=lid(0)
carrier.exportStep(str(O/'CarrierLoaded_INTERNAL.step'))
add('UpperLid',loaded,'#58a0b5','HEAD_CAP',True,free=free)
# A12 keeper bar moves above coil-pad solder/tool zone. Bare-core toes and catch lips unchanged.
# Visible keepers screw down to bare OUTER ferrite face; no concealed shim stack.
keeper=fuse([box(-44,-33.5,16.5,88,6,4),box(-44,-33.5,16.5,12,26.5,4),box(32,-33.5,16.5,12,26.5,4)])
for x in [-40,20]:keeper=keeper.fuse(box(x,-15,16.5,20,8,4))
for x in [-31,20]:keeper=keeper.fuse(box(x,-15,12.7,11,8,3.8))
for x in [-37,37]:keeper=keeper.cut(cy(2.1,12,x,-23,11))
# Mirror the loose catch lips onto both keepers, clear of central winding.
for x in [-10,10]:keeper=keeper.fuse(box(x-2,-12.5,-.5,4,2.0,21)).fuse(box(x-2,-33,16.5,4,22.5,4))
add('LowerKeeper',keeper,'#7bb9c1','HEAD_FIXED',True)
upkeeper=flip(keeper)
# Upper and lower keepers are mirrored, printed separately for clear assembly labels.
add('UpperKeeper',upkeeper,'#7bb9c1','HEAD_CAP',True)
for n in ['FixedCore','MovingCore','Winding','PCB','SMAEnvelope','PCBScrews','PCBNuts']:
 obj=a07.getObject(n);add(n,obj.Shape.copy(),obj.DisplayColorHex,'HEAD_CAP' if n=='MovingCore' else 'HEAD_FIXED')
for sign in [-1,1]:
 bolts=[];nuts=[]
 for x in [-37,37]:
  bolts.append(cy(1.5,35,x,sign*23,-14.5).fuse(cy(3.25,3.3,x,sign*23,20.5)))
  nuts.append(hexz(x,sign*23,-6.9,5.5,2.4).cut(cy(1.6,5,x,sign*23,-8)))
 for suffix,ss in [('KeeperScrews',bolts),('KeeperNuts',nuts)]:add(('Lower' if sign<0 else 'Upper')+suffix,Part.makeCompound(ss),'#ded8c3','HEAD_FIXED' if sign<0 else 'HEAD_CAP')
bolts=[];nuts=[]
for x in [-111,111]:
 bolts.append(cy(2,50,x,-10,6.35,V(0,1,0)).fuse(cy(10,10,x,40,6.35,V(0,1,0))))
 nuts.append(box(x-3.5,-9.6,2.85,7,3.2,7).cut(cy(2.1,6,x,-12,6.35,V(0,1,0))))
add('HeadHandScrews',Part.makeCompound(bolts),'#bac5cd','HEAD_SCREW')
add('HeadSquareNuts',Part.makeCompound(nuts),'#a7b3bc','HEAD_FIXED')
# Flat common datum. All three modules have underside Y=-72.
base=box(-127,-84,-136,254,12,314)
for x in [-104,-54,-4,46]:
 for z in [-125,-75,-25,25,75,125]:base=base.cut(box(x,-85,z,38,8,38))
for x in [-65,65]:
 for z in [-32,44.7]:
  # Larger nylon wing nut gives a geometric rotation stop without a tiny precision hex socket.
  sign=1 if x>0 else -1
  post=box(x-7,-72,z-7,14,52,14).fuse(box(x-7,-20,z-11,14,18,22))
  # An outward shoulder joins the rear of the common receiver; no inward widening toward the probe.
  post=post.fuse(box(x+5 if sign>0 else x-10,-20,z-11,5,18,22))
  post=post.cut(box(x-3.8 if sign>0 else x-12,-16.1,z-8.6,15.8,8.9,17.2))
  post=post.cut(cy(1.9,24,x,-24,z,V(0,1,0)))
  origin=(x+sign*8.0,-11,z)
  post=post.cut(side_place(box(-15,-9,0,30,18,34).cut(open_receiver()),*origin,sign)).fuse(side_place(open_receiver(),*origin,sign))
  base=base.fuse(post)
  common_cap('CalibrationNutCover'+str(1+len([q for q in CAPS if q.startswith('Calibration')])),origin,sign,'BASE')
# Local solid bosses prevent base nuts entering open underside pockets.
mounts=[(-48,75,'Head'),(48,75,'Head')]
for ci,offset in enumerate([-118.65,121.35]):
 for x in [-54,80]:mounts.append((x,offset+4,'Cable'+str(ci+1)))
 # Broad open registration shoulders, 1 mm side clearance, no press-fit dowels.
 base=base.fuse(box(-67,-72,offset-8,3,3,51)).fuse(box(-63,-72,offset+44,158,3,3))
# One recessed service panel retains all six base nuts; no six individual caps.
panel_specs=[(-62,-130,16,271),(72,-130,16,271),(-62,-130,150,16),(-62,125,150,16),(-62,67,150,16),(-122,-1.65,244,16)]
panel=fuse([box(x,-83.2,z,w,2.4,l) for x,z,w,l in panel_specs])
for x,z,g in mounts:panel=panel.cut(cy(3.2,12,x,-88,z,V(0,1,0)))
for x,z,w,l in panel_specs:
 base=base.cut(box(x-2,-85,z-2,w+4,4.8,l+4))
for x,z,g in mounts:
 # Thick roof carries the bolt load; the panel only prevents loose-nut loss.
 base=base.fuse(box(x-8,-80.2,z-8,16,8.2,16)).cut(cy(2.7,20,x,-88,z,V(0,1,0))).cut(box(x-4,-85,z-4,8,8,8))
for i,x in enumerate([-115,113]):
 z=6.35
 # Wide raised panel boss keeps 2.6mm under the socket-head counterbore.
 panel=panel.fuse(box(x-(10 if i else 7),-83.2,z-7,20 if i else 14,6.2,14))
 if i==0:
  panel=panel.cut(cy(2.6,20,x,-90,z,V(0,1,0))).cut(cy(4.1,5.4,x,-85,z,V(0,1,0)))
 else:
  # One X slot releases the long panel's two-hole spacing constraint.
  shaft_slot=cy(2.6,20,x-2,-90,z,V(0,1,0)).fuse(cy(2.6,20,x+2,-90,z,V(0,1,0))).fuse(box(x-2,-90,z-2.6,4,20,5.2))
  head_slot=cy(4.1,5.4,x-2,-85,z,V(0,1,0)).fuse(cy(4.1,5.4,x+2,-85,z,V(0,1,0))).fuse(box(x-2,-85,z-4.1,4,5.4,8.2))
  panel=panel.cut(shaft_slot).cut(head_slot)
 base=base.fuse(box(x-(12 if i else 10),-84,z-10,24 if i else 20,16.6,20)).cut(box(x-(11 if i else 9),-85,z-9,22 if i else 18,8,18))
 base=base.cut(cy(2.3,24,x,-90,z,V(0,1,0))).cut(box(x-4.2,-72,z-4.2,8.4,6,8.4))
 add('BasePanelScrew'+str(i+1),cy(2,12,x,-79.6,z,V(0,1,0)).fuse(cy(3.5,4,x,-83.6,z,V(0,1,0))),'#bac5cd','BASE')
 add('BasePanelNut'+str(i+1),box(x-3.5,-72,z-3.5,7,3.2,7).cut(cy(2.1,6,x,-73,z,V(0,1,0))),'#bac5cd','BASE')
for x,z,w,l in panel_specs:base=base.cut(box(x-2,-85,z-2,w+4,4.8,l+4))
add('BaseNutRetainer',panel,'#d1af63','BASE',True)
add('CommonBase',base,'#6f8592','BASE',True)
for i,(x,z,g) in enumerate(mounts):
 top=-63 if g=='Head' else -62
 add('MountScrew'+str(i),cy(2,20,x,top-20,z,V(0,1,0)).fuse(cy(6,7.5,x,top,z,V(0,1,0))),'#bac5cd','MOUNT_'+g)
 add('MountNut'+str(i),box(x-3.5,-80.2,z-3.5,7,3.2,7).cut(cy(2.1,6,x,-83,z,V(0,1,0))),'#bac5cd','BASE')
for n in ['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput']:
 ob=a05.getObject(n);add(n,ob.Shape.copy(),ob.DisplayColorHex,'CALIBRATION')
corners=[];nuts=[]
for x in [-65,65]:
 for z in [-32,44.7]:
  corners.append(cy(1.5,12,x,-12.4,z,V(0,1,0)).fuse(cy(3,3,x,-.4,z,V(0,1,0))))
  nuts.append(wing_nut(x,z))
add('CalibrationScrews',Part.makeCompound(corners),'#ded8c3','CALIBRATION_SCREW')
add('CalibrationNuts',Part.makeCompound(nuts),'#ded8c3','BASE')
M['CalibrationNuts'].update(manufacturer='KangYang',part_number='SMO-3(N)',quantity=4,model_kind='CONSERVATIVE_CATALOG_ENVELOPE',source_url='https://www.kangyang-europe.com/wp-content/uploads/product_files/pdf/SMO-3.pdf')
# Import actual C06 CAD twice, preserving the actual jaw groups for motion.
cpath=R/'mechanical/cable_clamp_C06_DRAFT';cm=json.loads((cpath/'mesh.json').read_text());cd=A.openDocument(str(cpath/'Cable_Clamp_C06_DRAFT.FCStd'))
for k,z in enumerate([-118.65,121.35]):
 for n,p in cm.items():
  sh=cd.getObject(n).Shape.copy();add('Cable'+str(k+1)+'_'+n,mv(sh,z=z),p['color'],'CABLE',clamp=k,local=n,subgroup=p['group'],offset_z=z)
  M['Cable'+str(k+1)+'_'+n]['printed']=p['printed']
  if n.startswith('BridgeNutCover'):
   M['Cable'+str(k+1)+'_'+n].update(printed=True,print_source='CommonNutCap_DRAFT.stl')
   CAPS.append('Cable'+str(k+1)+'_'+n)
  if k==0 and p['printed'] and not n.startswith('BridgeNutCover'):
   FREE['C06_'+n]=sh
   for ext in ['step','stl']:(O/'parts'/('C06_'+n+'_DRAFT.'+ext)).write_bytes((cpath/'parts'/(n+'_DRAFT.'+ext)).read_bytes())
save_print('CommonNutCap',CAP_SHAPE)
D.recompute();native=O/'RFCP_A12_Integrated_DRAFT.FCStd';D.saveAs(str(native))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A12_Integrated_DRAFT.step'))
mesh={}
for n,s in S.items():
 vs,tr=s.tessellate(.2);mesh[n]={'vertices':[list(v) for v in vs],'triangles':tr,**M[n]}
(O/'mesh.json').write_text(json.dumps(mesh))
# Explicit free/closed lid snapshots make imposed compliance reviewable.
free.exportStep(str(O/'UpperLid_UNLOADED_DRAFT.step'))
def vol(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def collisions(ss):
 bad=[]
 for a,b in itertools.combinations(ss,2):
  # PCB copper is intentionally embedded in laminate in the imported display CAD.
  if a=='FlatPCB' and b in ['SignalCopper','ReturnCopper']:continue
  v=vol(ss[a],ss[b])
  if v>1e-4:bad.append(dict(a=a,b=b,volume_mm3=round(v,5)))
 return bad
bad=collisions(S);print('STATIC',json.dumps(bad),flush=True)
# Centerline and nearest actual metal distances are geometry, not RF certification.
core=Part.makeCompound([S['FixedCore'],S['MovingCore']]);metal={n:s for n,s in S.items() if n.startswith('Cable') and not M[n].get('printed',False)}
nearest=min((core.distToShape(s)[0],n) for n,s in metal.items())
valid={n:dict(valid=s.isValid(),solids=len(s.Solids),volume_mm3=s.Volume) for n,s in FREE.items()}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status=STATUS,classification='CALCULATED_CAD_WITH_IMPOSED_LID_DEFLECTION',freecad=A.Version(),source_sha256=sha(Path(__file__)),shared_cap_source_sha256=sha(R/'mechanical/common_nut_cap.py'),native_sha256=sha(native),mesh_sha256=sha(O/'mesh.json'),printed_unique=len(FREE),printed_total=16+len(CAPS),parts=valid,static_collisions=bad,
 parameters=dict(base_mm=[254,314,12],bottom_y=-84,datum_y=-72,axis_y=0,axis_height_from_bench_mm=84,clamp_contact_z=[-113.65,126.35],core_mid_z=6.35,clamp_center_distance_mm=240,core_to_nearest_clamp_metal_mm=nearest[0],nearest_clamp_metal=nearest[1],base_mount_screw_length_mm=20,lid_datum='Left foot L stop, seat left/back manually before tightening; opposite foot floats',lower_closure_hole_diameter_mm=6.2,lower_closure_nut_slot_width_mm=8.4,keeper_bar_y_mm=[-33.5,-27.5],calibration_nut_holding='SMO-3(N) nylon66 wing nut, geometric wing stop plus common removable cap',retainer_panel_thickness_mm=2.4,retainer_panel_bottom_y_mm=-83.2,retainer_panel_bolts='2x M4x12 socket head D7xH4; initial assembly only',nut_cap_quantity=len(CAPS),lid_preload_mm=DELTA,leaf_span_mm=63,leaf_width_mm=18,leaf_thickness_mm=2.4),
 limits=['No RF, print process, hand assembly or durability test. Separate linear FEA is scoped in reviews/functionality_20260918.','Lid geometry is imposed deflection. FREE lid is the only printable lid shape.','Nylon keeper hardware and broad bare-ferrite contact need torque/friction validation.','Common axis is nominal. Cam clearance, manufacturing tolerances and core dimensions cause offsets.','C06 uses candidate hardware envelopes; purchasing part numbers not finalized.','Closed lid translates less than whole upper core in operation; actual flexure deformation and core self-seating not proven.'])
report['common_cap_dimensions']=CAP_DIMS
report['print_quantities']={n:(len(CAPS) if n=='CommonNutCap' else 2 if n.startswith('C06_') else 1) for n in FREE}
for n,q in report['print_quantities'].items():report['parts'][n]['quantity']=q
report['input_sha256']={str(p.relative_to(R)):sha(p) for p in [R/'mechanical/common_nut_cap.py',cpath/'Cable_Clamp_C06_DRAFT.FCStd',cpath/'mesh.json',R/'reviews/a12_20260918/sources/SMO-3.pdf']}
report['display_part_validity']={n:s.isValid() for n,s in S.items()}
report['pass']=not bad and all(report['display_part_validity'].values()) and all(x['valid'] and x['solids']==1 for x in valid.values())
(O/'build_report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pass'],flush=True)
