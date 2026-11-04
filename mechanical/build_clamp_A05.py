"""A05 detachable cap / spring-floated ferrite cassette. FreeCADCmd.

DRAFT: dimensional design and algebra, NOT a tested clamp or approved print.
Prior revisions are read-only inputs. No order/upload side effects.
"""
import json, math, hashlib
from pathlib import Path
import FreeCAD as A
import Part, MeshPart
R=Path(__file__).resolve().parents[1]; O=R/'mechanical/clamp_A05_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector; STATUS='DRAFT - NOT FOR FABRICATION'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldpath=R/'mechanical/clamp_A04_DRAFT/RFCP_Clamp_A04_DRAFT.FCStd'
old=A.openDocument(str(oldpath))
doc=A.newDocument('RFCP_Clamp_A05_DRAFT'); S={}; meta={}; meshes={}
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cy(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def comp(ss):return Part.makeCompound(ss)
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter() if len(ss)>1 else ss[0]
def trans(s,x=0,y=0,z=0):
 s=s.copy();s.translate(V(x,y,z));return s
def flip(s):
 # A rigid reflection preserves analytic cylinders. transformGeometry converts
 # them to splines and produced a non-manifold tessellation after later cuts.
 m=A.Matrix();m.A22=-1;q=s.copy();q.transformShape(m);return q
def hexz(x,y,z,af,h):
 r=af/math.sqrt(3);vv=[V(x+r*math.cos(math.pi/6+i*math.pi/3),y+r*math.sin(math.pi/6+i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(0,0,h))
def capsule(x,y,z,w,length,h):
 d=(length-w)/2
 return fuse([box(x-w/2,y-d,z,w,2*d,h),cy(w/2,h,x,y-d,z),cy(w/2,h,x,y+d,z)])
def add(n,s,c,group,printed=False,notes=''):
 S[n]=s;meta[n]={'group':group,'printed':printed,'notes':notes}
 o=doc.addObject('PartDesign::Feature',n);o.Shape=s
 for key,val in [('Status',STATUS),('Category',group),('DisplayColorHex',c)]:o.addProperty('App::PropertyString',key);setattr(o,key,val)
 vv,ff=s.tessellate(.22);meshes[n]={'vertices':[list(v) for v in vv],'triangles':ff,'color':c,'group':group}
 if printed:
  s.exportStep(str(O/'parts'/(n+'_DRAFT.step')))
  q=trans(s,-s.BoundBox.XMin,-s.BoundBox.YMin,-s.BoundBox.ZMin)
  MeshPart.meshFromShape(Shape=q,LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(O/'parts'/(n+'_DRAFT.stl')))

# Roomy rectangular cassette, with open mating ends. No ferrite trapped against
# a fixed-height roof. Two separate keeper bars adjust in Z on through bolts.
def cradle():
 floor=box(-38,3,-4,76,33.64,3).cut(cy(17.7,6,0,0,-5))
 walls=fuse([box(-38,3,-1,6,33.64,13),box(32,3,-1,6,33.64,13),box(-38,31.64,-1,76,5,13)])
 s=floor.fuse(walls)
 for x in [-34,34]:
  for y in [7,15]:s=s.cut(cy(2.1,30,x,y,-8))
 return s.removeSplitter()
carrier=cradle()
carrier=carrier.cut(cy(19,6,0,0,-5))
# Two slotted ears retain the cassette without squeezing its sliding surface.
for x in [-25,25]:
 carrier=carrier.fuse(box(x-9,32,-4,18,29,3))
 carrier=carrier.cut(capsule(x,51.35,-6,11.2,17.2,8))
carrier=carrier.removeSplitter()
lower=flip(cradle())
# Case-stop blocks at both sides carry closing load. A loose square-nut pocket
# is covered by each keeper bar; no undersize hex press fit or printed threads.
for x in [-45.5,45.5]:
 lug=fuse([box(x-7,-12,2,14,9,9.5),box(x-4.5,-3,2,9,3,9.5)])
 # Broad rear block connects to the cradle; only the narrow stop crosses
 # the fixture PCB plane, staying inside its existing x=+/-51 windows.
 lug=lug.fuse(box(35 if x>0 else -46,-12,2,11,9,9.5))
 lug=lug.cut(cy(2.6,18,x,-15,7,V(0,1,0)))
 lug=lug.cut(box(x-3.9,-10,3.5,7.8,4.6,12))
 lower=lower.fuse(lug)

# A03 board is unchanged electrically; its placement moves 4 mm outward.
# An open 8.5 mm counterbore replaces each tight nut trap, accessible from back.
tray=box(-20,-66.2,-4,40,32,12).cut(box(-18.5,-64.5,0,37,29,20))
for x in [-14.5,14.5]:
 # Positive overlap with both pocket walls, not a tangent line contact.
 tray=tray.fuse(cy(5,4.75,x,-60.5,0))
 tray=tray.cut(cy(1.6,20,x,-60.5,-7)).cut(cy(4.25,2,x,-60.5,-4))
lower=lower.cut(box(-18.5,-64.5,0,37,30.5,20)).fuse(tray)
for x in [-23,18.5]:lower=lower.fuse(box(x,-40,-4,4.5,7.5,16))
lower=lower.cut(box(-6,-34,-2,12,17.2,16.25)).cut(box(-6,-40,4.9,12,10,2.9)).removeSplitter()
for x in [-34,34]:
 for y in [-7,-15]:lower=lower.cut(cy(2.1,30,x,y,-8))
lower=lower.removeSplitter()

fixed_bars=[]; moving_bars=[]; core_bolts=[]; core_nuts=[]; pads=[]
for sign in [-1,1]:
 for side in [-1,1]:
  x=side*34; y=sign*8
  # Pad reaches the outer ferrite leg, never the bare mating face.
  lo,hi=(25.5,53) if sign<0 else (25.5,40)
  bx=lo if side>0 else -hi
  bar=box(bx,-19 if sign<0 else 3,13.7,hi-lo,16,3)
  for yy in [sign*7,sign*15]:
   bar=bar.cut(cy(2.1,7,x,yy,12))
   core_bolts.append(cy(1.5,25,x,yy,-8.3).fuse(cy(3.25,3.3,x,yy,16.7)))
   core_nuts.append(hexz(x,yy,-6.4,5.5,2.4).cut(cy(1.5,4,x,yy,-7)))
  (fixed_bars if sign<0 else moving_bars).append(bar)
  px=27 if side>0 else -30
  pads.append(box(px,-9.5 if sign<0 else 5.5,12.7,3,4,1))
  pads.append(box(side*24-2,-14 if sign<0 else 10,-1,4,4,1))
 for x in [-9,9]:pads.append(box(x-2,-31.64 if sign<0 else 29.64,1,4,2,10))

# The cap is a separate rigid cage. Guide collars establish retainer height;
# guide screws cannot pinch the slotted cassette when tightened.
cage=box(-48,3,-9,96,67,3).cut(cy(21,6,0,0,-10))
cage=fuse([cage,box(-48,3,-6,4,67,23),box(44,3,-6,4,67,23),box(-48,64.5,-6,96,5.5,23),box(-13,54,-6,26,16,23)])
for x in [-34,34]:cage=cage.cut(capsule(x,9.5,-12,11,29,9))
for x in [-26,26]:cage=cage.fuse(cy(3,2,x,14,-6))
collars=[];retainers=[];guide_bolts=[];guide_nuts=[]
for x in [-25,25]:
 cage=cage.fuse(cy(5,2,x,52,-6)).cut(cy(2.1,10,x,52,-12))
 # Broad side lands support the cassette OUTSIDE the oversized guide slot.
 for dx in [-7.5,7.5]:cage=cage.fuse(box(x+dx-1,38,-6,2,25,2))
 collar=cy(4,3.5,x,52,-4).cut(cy(2.1,7,x,52,-5));collars.append(collar)
 retainers.append(cy(9,3,x,52,-.5).cut(cy(2.1,5,x,52,-1)))
 guide_bolts.append(cy(1.5,16,x,52,-9).fuse(cy(3.25,3.3,x,52,-12.3)))
 guide_nuts.append(hexz(x,52,2.5,5.5,2.4).cut(cy(1.5,4,x,52,2)))
# Side pads are broad stops, not locating pins requiring close printed fits.
for x in [-45.5,45.5]:
 cage=cage.fuse(box(x-4.5,0,2,9,8,10.7)).cut(cy(2.6,12,x,-1,7,V(0,1,0)))
 cage=cage.cut(cy(7.2,15,x,8,7,V(0,1,0)))
# Two tunnel guides suppress gross spring buckling. Spring ends remain isolated
# from ferrite and screws; tubes have no continuous metal path around core.
for x in [-9,9]:
 tube=cy(7,18,x,36,6.35,V(0,1,0)).cut(cy(5,19,x,35.5,6.35,V(0,1,0)))
 # Opening begins beyond the carrier's +3 mm endpoint (rear y=39.64).
 tube=tube.cut(box(-60,30,-20,120,10.5,60))
 cage=cage.fuse(tube)
cage=cage.removeSplitter()

core=Part.read(str(R/'docs/references/2644181281.STEP'))
board=trans(old.getObject('PCB').Shape,y=-4)
sma=trans(old.getObject('SMAEnvelope').Shape,y=-4)
pts=[V(-4,-31.2,6.35)]
cross=[(-31.2,13.5),(-17.6,13.5),(-17.6,-.8),(-31.2,-.8),(-31.2,6.35)]
for i in range(5):
 for j,(y,z) in enumerate(cross):pts.append(V(-4+(i+(j+1)/5)*1.6,y,z))
pts=[V(-1.27,-38.5,6.35),V(-1.27,-38.5,7.1),V(-1.27,-34.5,7.1)]+pts+[V(1.27,-34.5,7.1),V(1.27,-38.5,7.1),V(1.27,-38.5,6.35)]
wire=fuse([Part.makeCylinder(.2,(b-a).Length,a,b-a) for a,b in zip(pts,pts[1:])]+[Part.makeSphere(.2,p) for p in pts])

# Smooth annular spring envelopes, not a fictitious detailed helix. Reference
# spring: MISUMI UR6-25, OD6/free25; dimensions/force checked separately.
springs=[]
for x in [-9,9]:springs.append(cy(3,17.36,x,36.64,6.35,V(0,1,0)).cut(cy(2.4,18,x,36.4,6.35,V(0,1,0))))
thumbs=[];square_nuts=[]
for x in [-45.5,45.5]:
 thumbs.append(cy(2,20,x,-12,7,V(0,1,0)).fuse(cy(6,7.5,x,8,7,V(0,1,0))))
 square_nuts.append(box(x-3.5,-9.2,3.5,7,3.2,7).cut(cy(2,5,x,-10,7,V(0,1,0))))
pcbscrews=[];pcbnuts=[]
for x in [-14.5,14.5]:
 pcbscrews.append(cy(1,10,x,-60.5,-3.65).fuse(cy(1.9,1.3,x,-60.5,6.35)))
 pcbnuts.append(hexz(x,-60.5,-3.2,3.9,1.2).cut(cy(1,3,x,-60.5,-4)))

add('FixedTray',lower,'#285f78','FIXED',True)
add('UpperCage',cage,'#448ca3','CAP',True)
add('FloatingCassette',carrier,'#edb14f','FLOAT',True)
for i,b in enumerate(fixed_bars):add('FixedKeeper'+str(i+1),b,'#72b8c6','FIXED',True)
for i,b in enumerate(moving_bars):add('FloatingKeeper'+str(i+1),b,'#efc371','FLOAT',True)
for i,b in enumerate(collars):add('GuideCollar'+str(i+1),b,'#b0bcce','CAP',True)
for i,b in enumerate(retainers):add('GuideRetainer'+str(i+1),b,'#93a9bf','CAP',True)
for n,s,c,g in [('FixedCore',core,'#333e49','FIXED'),('MovingCore',flip(core),'#424e59','FLOAT'),('PCB',board,'#318f59','FIXED'),('SMAEnvelope',sma,'#d6bd72','FIXED'),('Winding',wire,'#db9f48','FIXED'),('SpringsEnvelope',comp(springs),'#b34e79','SPRING'),('HandScrewsEnvelope',comp(thumbs),'#cbd3db','REMOVE'),('SquareNutsEnvelope',comp(square_nuts),'#afbac5','FIXED'),('GuideBolts',comp(guide_bolts),'#bdc7d1','CAP'),('GuideNuts',comp(guide_nuts),'#a7b4c2','CAP'),('PCBScrews',comp(pcbscrews),'#bdc7d1','FIXED'),('PCBNuts',comp(pcbnuts),'#a7b4c2','FIXED')]:add(n,s,c,g)
for sign in [-1,1]:
 for label,items,c in [('KeeperBolts',core_bolts,'#bec7cf'),('KeeperNuts',core_nuts,'#aab7c2'),('Pads',pads,'#95aa86')]:
  selected=[s for s in items if ((s.BoundBox.YMin+s.BoundBox.YMax)<0)==(sign<0)]
  add(('Fixed' if sign<0 else 'Moving')+label,comp(selected),c,'FIXED' if sign<0 else 'FLOAT')

doc.recompute();native=O/'RFCP_Clamp_A05_DRAFT.FCStd';doc.saveAs(str(native))
comp(list(S.values())).exportStep(str(O/'RFCP_Clamp_A05_DRAFT.step'))
(O/'assembly_mesh.json').write_text(json.dumps(meshes),encoding='utf-8')
report={'classification':'CALCULATED_CAD','status':STATUS,'source_hashes':{str(p.relative_to(R)):sha(p) for p in [Path(__file__),oldpath,R/'docs/references/2644181281.STEP',R/'hardware/probe_head_A03/review/board_only.step']},'native_sha256':sha(native),'freecad_version':A.Version(),'parts':{n:{**meta[n],'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume} for n,s in S.items()},'parameters':{'cap_type':'detachable, two hand screws; not a one-hand hinged clip','normal_float_design_range_mm':[-3,3],'keeper_height_nominal_mm':13.7,'keeper_height_adjusts_to_core_thickness':True,'M3_through_hole_mm':4.2,'M4_through_hole_mm':5.2,'M2_head_hole_print_mm':3.2,'square_nut_pocket_mm':[7.8,4.6],'PCB_A03_placement_shift_y_mm':-4,'SMA_center_mm':[0,-49,6.35],'spring_nominal_installed_length_mm':17.36,'spring_part':'MISUMI UR6-25 (qualification candidate)','user_metal_machining_required':False},'limitations':['Not physically assembled. Print process fit, sliding friction, hand force, wear and RF response require tests.','Hardware envelopes are acceptance limits, not manufacturer CAD; exact knobs/nuts must meet assembly list.','Core holder Y float/yaw accommodates mismatch; it does not automatically prove flat, debris-free magnetic contact.','No guaranteed ferrite pressure or elastic housing strength, creep, temperature or dielectric rating.']}
(O/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'parts':len(S),'invalid':[n for n,s in S.items() if not s.isValid()],'printed_non_single':[n for n,s in S.items() if meta[n]['printed'] and len(s.Solids)!=1]}),flush=True)
