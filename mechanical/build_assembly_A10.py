"""A10 integrated review assembly. FreeCAD 1.0; no fabrication approval.
CAD uses the nominal CLOSED (deflected) lid. The lid print is the FREE shape.
Deflection geometry is an imposed beam curve, NOT a structural simulation.
"""
from pathlib import Path
import math,json,hashlib,itertools
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];O=R/'mechanical/assembly_A10_DRAFT';(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector;D=A.newDocument('RFCP_A10_Integrated_DRAFT');S={};M={};FREE={}
STATUS='DRAFT - NOT FOR FABRICATION';DELTA=1.8
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
 lower=lower.cut(cy(2.6,45,sign*111,-40,6.35,V(0,1,0)))
 lower=lower.cut(box(sign*111-3.9,-11,2.45,7.8,4.6,23))
# Wider keeper bosses, moved out 1 mm. Remove the old counterbore's feather edge.
for sign in [-1,1]:
 x=sign*37;left=32.5 if sign>0 else -42
 lower=lower.fuse(box(left,-30,-4.5,9.5,14,20))
 lower=lower.cut(box(31.5 if sign>0 else -43,-29,-10,11.5,12,5.5))
 lower=lower.cut(cy(2.1,36,x,-23,-12))
 lower=lower.cut(box(left,-30,10.5,9.5,14,8))
# Thicken the inherited 0.75 mm PCB relief roof toward its empty rear clearance.
lower=lower.fuse(box(-18.5,-37,13.1,37,2,2.4))
lower=lower.cut(box(-6,-35,7.8,12,3.1,8))
lower=lower.fuse(box(-21,-68,-4.5,42,3,12))
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
  p=bottom+top[::-1];ss.append(Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,18)))
 q=fuse(ss)
 roots=[e for e in q.Edges if abs(abs(e.BoundBox.Center.x)-103)<1e-5 and abs(e.BoundBox.ZLength-18)<1e-5 and e.BoundBox.XLength<1e-5 and e.BoundBox.YLength<1e-5]
 if len(roots)!=4:raise ValueError('Expected four outer flexure root edges')
 return q.makeFillet(1.5,roots)
loaded=lid(DELTA);free=lid(0)
carrier.exportStep(str(O/'CarrierLoaded_INTERNAL.step'))
add('UpperLid',loaded,'#58a0b5','HEAD_CAP',True,free=free)
# Visible keepers screw down to bare OUTER ferrite face; no concealed shim stack.
keeper=fuse([box(-44,-43,16.5,88,6,4),box(-44,-43,16.5,12,36,4),box(32,-43,16.5,12,36,4)])
for x in [-40,20]:keeper=keeper.fuse(box(x,-15,16.5,20,8,4))
for x in [-31,20]:keeper=keeper.fuse(box(x,-15,12.7,11,8,3.8))
for x in [-37,37]:keeper=keeper.cut(cy(2.1,12,x,-23,11))
# Mirror the loose catch lips onto both keepers, clear of central winding.
for x in [-10,10]:keeper=keeper.fuse(box(x-2,-12.5,-.5,4,2.0,21)).fuse(box(x-2,-42.5,16.5,4,32,4))
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
 nuts.append(box(x-3.5,-10.2,2.85,7,3.2,7).cut(cy(2.1,6,x,-12,6.35,V(0,1,0))))
add('HeadHandScrews',Part.makeCompound(bolts),'#bac5cd','HEAD_SCREW')
add('HeadSquareNuts',Part.makeCompound(nuts),'#a7b3bc','HEAD_FIXED')
# Flat common datum. All three modules have underside Y=-72.
base=box(-127,-84,-136,254,12,314)
for x in [-104,-54,-4,46]:
 for z in [-125,-75,-25,25,75,125]:base=base.cut(box(x,-85,z,38,8,38))
for x in [-65,65]:
 for z in [-32,44.7]:
  base=base.fuse(box(x-7,-72,z-7,14,70,14)).cut(cy(1.9,21,x,-20,z,V(0,1,0))).cut(box(x-4,-11,z-4,8,3.8,13))
# Local solid bosses prevent base nuts entering open underside pockets.
mounts=[(-48,75,'Head'),(48,75,'Head')]
for ci,offset in enumerate([-118.65,121.35]):
 for x in [-54,80]:mounts.append((x,offset+4,'Cable'+str(ci+1)))
 # Broad open registration shoulders, 1 mm side clearance, no press-fit dowels.
 base=base.fuse(box(-67,-72,offset-8,3,3,51)).fuse(box(-63,-72,offset+44,158,3,3))
for x,z,g in mounts:
 base=base.fuse(box(x-8,-84,z-8,16,12,16)).cut(cy(2.7,20,x,-88,z,V(0,1,0))).cut(box(x-4,-85,z-4,8,7,8))
add('CommonBase',base,'#6f8592','BASE',True)
for i,(x,z,g) in enumerate(mounts):
 top=-63 if g=='Head' else -62
 add('MountScrew'+str(i),cy(2,25,x,top-25,z,V(0,1,0)).fuse(cy(6,7.5,x,top,z,V(0,1,0))),'#bac5cd','MOUNT_'+g)
 add('MountNut'+str(i),box(x-3.5,-81.8,z-3.5,7,3.2,7).cut(cy(2.1,6,x,-83,z,V(0,1,0))),'#bac5cd','BASE')
for n in ['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput']:
 ob=a05.getObject(n);add(n,ob.Shape.copy(),ob.DisplayColorHex,'CALIBRATION')
corners=[];nuts=[]
for x in [-65,65]:
 for z in [-32,44.7]:
  corners.append(cy(1.5,12,x,-12.4,z,V(0,1,0)).fuse(cy(3,3,x,-.4,z,V(0,1,0))))
  n=hexz(0,0,0,5.5,2.4).cut(cy(1.6,5,0,0,-1));n.rotate(V(),V(1,0,0),-90);n.translate(V(x,-10.3,z));nuts.append(n)
add('CalibrationScrews',Part.makeCompound(corners),'#ded8c3','CALIBRATION_SCREW')
add('CalibrationNuts',Part.makeCompound(nuts),'#ded8c3','BASE')
# Import actual C04 CAD twice, preserving the actual jaw groups for motion.
cpath=R/'mechanical/cable_clamp_C04_DRAFT';cm=json.loads((cpath/'mesh.json').read_text());cd=A.openDocument(str(cpath/'Cable_Clamp_C04_DRAFT.FCStd'))
for k,z in enumerate([-118.65,121.35]):
 for n,p in cm.items():
  sh=cd.getObject(n).Shape.copy();add('Cable'+str(k+1)+'_'+n,mv(sh,z=z),p['color'],'CABLE',clamp=k,local=n,subgroup=p['group'],offset_z=z)
  if k==0 and p['printed']:
   FREE['C04_'+n]=sh
   for ext in ['step','stl']:(O/'parts'/('C04_'+n+'_DRAFT.'+ext)).write_bytes((cpath/'parts'/(n+'_DRAFT.'+ext)).read_bytes())
D.recompute();native=O/'RFCP_A10_Integrated_DRAFT.FCStd';D.saveAs(str(native))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A10_Integrated_DRAFT.step'))
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
core=Part.makeCompound([S['FixedCore'],S['MovingCore']]);metal={n:s for n,s in S.items() if n.startswith('Cable') and not any(q in n for q in ['Frame','DriveYoke','TopBridgeJaw','Jaw1','Jaw2'])}
nearest=min((core.distToShape(s)[0],n) for n,s in metal.items())
valid={n:dict(valid=s.isValid(),solids=len(s.Solids),volume_mm3=s.Volume) for n,s in FREE.items()}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status=STATUS,classification='CALCULATED_CAD_WITH_IMPOSED_LID_DEFLECTION',freecad=A.Version(),source_sha256=sha(Path(__file__)),native_sha256=sha(native),mesh_sha256=sha(O/'mesh.json'),printed_unique=10,printed_total=15,parts=valid,static_collisions=bad,
 parameters=dict(base_mm=[254,314,12],bottom_y=-84,datum_y=-72,axis_y=0,axis_height_from_bench_mm=84,clamp_contact_z=[-113.65,126.35],core_mid_z=6.35,clamp_center_distance_mm=240,core_to_nearest_clamp_metal_mm=nearest[0],nearest_clamp_metal=nearest[1],lid_preload_mm=DELTA,leaf_span_mm=63,leaf_width_mm=18,leaf_thickness_mm=2.4),
 limits=['No RF, print process, hand assembly or durability test. Separate linear FEA is scoped in reviews/functionality_20260918.','Lid geometry is imposed deflection. FREE lid is the only printable lid shape.','Nylon keeper hardware and broad bare-ferrite contact need torque/friction validation.','Common axis is nominal. Cam clearance, manufacturing tolerances and core dimensions cause offsets.','C04 uses candidate hardware envelopes; purchasing part numbers not finalized.','Closed lid translates less than whole upper core in operation; actual flexure deformation and core self-seating not proven.'])
report['pass']=not bad and all(x['valid'] and x['solids']==1 for x in valid.values())
(O/'build_report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pass'],flush=True)
