"""A07 simple split head and flat-bottom integrated bench base.
FreeCAD 1.0.2; nominal geometry only. DRAFT, no RF/strength qualification.
"""
from pathlib import Path
import json,math,hashlib
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];O=R/'mechanical/clamp_A07_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector;S={};M={};DRAFT='DRAFT - NOT FOR FABRICATION'
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cy(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter()
def move(s,x=0,y=0,z=0):
 q=s.copy();q.translate(V(x,y,z));return q
def flip(s):
 q=s.copy();m=A.Matrix();m.A22=-1;q.transformShape(m);return q
def hexz(x,y,z,af,h):
 rr=af/math.sqrt(3);p=[V(x+rr*math.cos(i*math.pi/3),y+rr*math.sin(i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def put(doc,n,s,c,g,printed=False,material=''):
 s=s.removeSplitter();o=doc.addObject('PartDesign::Feature',n);o.Shape=s
 for key,val in [('Status',DRAFT),('Category',g),('DisplayColorHex',c),('MaterialAssumption',material)]:o.addProperty('App::PropertyString',key);setattr(o,key,val)
 S[n]=s;M[n]={'group':g,'printed':printed,'material':material}
 if printed:
  s.exportStep(str(O/'parts'/(n+'_DRAFT.step')));b=s.BoundBox;q=move(s,-b.XMin,-b.YMin,-b.ZMin)
  MeshPart.meshFromShape(Shape=q,LinearDeflection=.12,AngularDeflection=.18,Relative=False).write(str(O/'parts'/(n+'_DRAFT.stl')))
 return o
oldpath=R/'mechanical/clamp_A05_DRAFT/RFCP_Clamp_A05_DRAFT.FCStd';old=A.openDocument(str(oldpath))
d=A.newDocument('RFCP_Clamp_A07_DRAFT')
# Open rectangular core pockets: no close-fitting locating pins or printed threads.
# Floor and keeper retain Z; compliant silicone pads contact OUTER core surfaces.
cradle=box(-40,-37,-4.5,80,34,20).cut(box(-32.5,-32,-1.5,65,32,25)).cut(cy(18,30,0,0,-7))
for x in [-36,36]:cradle=cradle.cut(cy(2.1,32,x,-23,-8))
lower=cradle.copy();upper=flip(cradle)
# Broad transverse closure shoulders at the CORE plane, outside the PCB edges.
# No long forward cantilever. Metal retained far to the left/right instead.
for sign in [-1,1]:
 x=sign*90
 arm=box(34 if sign>0 else -100,-38,-8,66,32,22)
 arm=arm.fuse(box(82 if sign>0 else -100,-6,-8,18,6,32))
 lower=lower.fuse(arm);upper=upper.fuse(flip(arm))
 lower=lower.cut(cy(2.6,46,x,-42,6.35,V(0,1,0))).cut(box(x-3.9,-11,2.45,7.8,4.6,25))
 upper=upper.cut(cy(2.6,46,x,-2,6.35,V(0,1,0)))
# Existing A03 PCB, retained with nonconductive hardware; shell takes cable loads.
tray=box(-21,-66.5,-4.5,42,33,12).cut(box(-18.5,-65,0,37,30,18))
for x in [-14.5,14.5]:tray=tray.fuse(cy(5,4.75,x,-60.5,0)).cut(cy(1.6,20,x,-60.5,-8)).cut(cy(4.25,3,x,-60.5,-4.5))
lower=lower.fuse(tray).fuse(box(-24,-42,-4.5,7,10,12)).fuse(box(17,-42,-4.5,7,10,12))
lower=lower.cut(box(-6,-34,-2,12,17,16.4)).cut(box(-6,-40,4.9,12,10,2.9))
# Broad flat sole, entirely independent of PCB fasteners.
sole=box(-58,-72,-12,116,9,102).cut(box(-26,-67,-8,52,8,34))
for x in [-48,48]:sole=sole.cut(cy(2.6,20,x,-78,75,V(0,1,0)))
lower=fuse([lower,sole,box(-40,-64,-4.5,12,32,10),box(28,-64,-4.5,12,32,10)])
lower=lower.cut(box(-18.5,-65,4.75,37,30,10))
for x in [-36,36]:
 lower=lower.cut(cy(2.1,36,x,-23,-12)).cut(cy(4.25,4.5,x,-23,-9))
 upper=upper.cut(cy(2.1,36,x,23,-12)).cut(cy(4.25,4.5,x,23,-9))
# Open front retaining frame: visible core and winding, removable toward +Z.
keeper=box(-40,-37,15.5,80,34,4).cut(box(-32,-29,14,64,28,8))
for x in [-40,20]:keeper=keeper.fuse(box(x,-15,15.5,20,8,4))
keeper=keeper.cut(cy(18,9,0,0,13))
for x in [-36,36]:keeper=keeper.cut(cy(2.1,12,x,-23,12))
# No PCB front cover or projecting coax saddle. Cable load requires separate support.
lowerkeeper=keeper.copy()
put(d,'LowerShell',lower,'#356e84','FIXED',True,'nonconductive unfilled print polymer')
put(d,'UpperShell',upper,'#58a0b5','CAP',True,'nonconductive unfilled print polymer')
put(d,'LowerKeeper',lowerkeeper,'#79b3be','FIXED',True,'nonconductive unfilled print polymer')
put(d,'UpperKeeper',flip(keeper),'#79b3be','CAP',True,'nonconductive unfilled print polymer')
for n in ['FixedCore','MovingCore','Winding','PCB','SMAEnvelope']:
 o=old.getObject(n);put(d,n,o.Shape.copy(),o.DisplayColorHex,'CAP' if n=='MovingCore' else 'FIXED',False,'ferrite' if 'Core' in n else 'existing A05 source')
for sign in [-1,1]:
 for padname,local in [
  ('BackFacePads',[box(x-2,-13,-1.5,4,4,1.5) for x in [-24,24]]),
  ('FrontFacePads',[box(x-2,-13,12.7,4,4,2.8) for x in [-24,24]]),
  ('SeatPads',[box(x-3,-32,2,6,2.3582,8) for x in [-9,9]])]:
  put(d,('Lower' if sign<0 else 'Upper')+padname,Part.makeCompound(local if sign<0 else [flip(q) for q in local]),'#e8aa4e','FIXED' if sign<0 else 'CAP',False,'silicone nominal fitted envelope; adhesive/fitting/force unqualified')
 bolts=[];nuts=[]
 for x in [-36,36]:
  bolts.append(cy(1.5,30,x,sign*23,-10.5).fuse(cy(3.25,3.3,x,sign*23,19.5)))
  nuts.append(hexz(x,sign*23,-6.9,5.5,2.4).cut(cy(1.5,5,x,sign*23,-8)))
 for suffix,shapes in [('KeeperScrews',bolts),('KeeperNuts',nuts)]:
  put(d,('Lower' if sign<0 else 'Upper')+suffix,Part.makeCompound(shapes),'#ddd5bc','FIXED' if sign<0 else 'CAP',False,'nylon M3x30 + nylon nuts; strength/creep unqualified')
thumbs=[];nuts=[]
for x in [-90,90]:
 # M4x50, D20 knob. Unlike A06, fingers approach a fully exposed head.
 thumbs.append(cy(2,50,x,-12,6.35,V(0,1,0)).fuse(cy(10,10,x,38,6.35,V(0,1,0))))
 nuts.append(box(x-3.5,-10.2,2.85,7,3.2,7).cut(cy(2,6,x,-12,6.35,V(0,1,0))))
put(d,'HandScrewsEnvelope',Part.makeCompound(thumbs),'#bbc7cf','REMOVE',False,'metal M4x50 D20 H10 dimensional candidate')
put(d,'SquareNutsEnvelope',Part.makeCompound(nuts),'#a6b2be','FIXED',False,'metal M4 square nut 7x7x3.2')
for n in ['PCBScrews','PCBNuts']:
 put(d,n,old.getObject(n).Shape.copy(),'#ddd5bc','FIXED',False,'nonconductive M2 equivalent envelope; exact product pending')
d.recompute();d.saveAs(str(O/'RFCP_Clamp_A07_DRAFT.FCStd'))
Part.makeCompound([o.Shape for o in d.Objects if hasattr(o,'Shape')]).exportStep(str(O/'RFCP_Clamp_A07_DRAFT.step'))
headmeta=dict(M)
# One base includes board columns: no separate dock/bracket/standoff prints.
base=box(-83,-88,-47,166,16,145)
# Open underside pockets retain a 4mm top and perimeter/ribs; no enclosed cavities.
for x in [-72,-36,0,36]:
 for z in [-37,0,37,74]:base=base.cut(box(x,-89,z,26,13,17))
for x in [-65,65]:
 for z in [-32,44.7]:
  base=base.fuse(cy(6,70,x,-72,z,V(0,1,0)))
  base=base.cut(cy(1.9,21,x,-20,z,V(0,1,0)))
  # Upper PCB screw retains with captured nylon nut accessible from side.
  base=base.cut(box(x-4,-11,z-4,8,3.8,13))
for x in [-48,48]:
 base=base.cut(cy(2.6,25,x,-92,75,V(0,1,0))).cut(box(x-4,-89,71,8,10.2,8))
fixpath=R/'mechanical/clamp_A05_DRAFT/RFCP_A05_Fixture_REVIEW.FCStd';fix=A.openDocument(str(fixpath))
f=A.newDocument('RFCP_A07_Fixture_REVIEW')
for o in d.Objects:
 if hasattr(o,'Shape'):put(f,'Head_'+o.Name,o.Shape.copy(),o.DisplayColorHex,o.Category,False,o.MaterialAssumption)
for n in ['FlatPCB','SignalCopper','ReturnCopper','SMAInput','SMAOutput']:
 o=fix.getObject(n);put(f,n,o.Shape.copy(),o.DisplayColorHex,'BOARD')
put(f,'Base',base,'#657c8c','BENCH',True,'nonconductive unfilled print polymer')
mountbolts=[];mountnuts=[]
for x in [-48,48]:
 mountbolts.append(cy(2,20,x,-83,75,V(0,1,0)).fuse(cy(6,7.5,x,-63,75,V(0,1,0))))
 mountnuts.append(box(x-3.5,-82,71.5,7,3.2,7).cut(cy(2,6,x,-84,75,V(0,1,0))))
put(f,'BaseHandScrews',Part.makeCompound(mountbolts),'#bbc7cf','BENCH',False,'metal M4x20 D12 H7.5')
put(f,'BaseNuts',Part.makeCompound(mountnuts),'#a6b2be','BENCH',False,'metal M4 square nuts')
corner=[];cornernuts=[]
for x in [-65,65]:
 for z in [-32,44.7]:
  corner.append(cy(1.5,12,x,-12.4,z,V(0,1,0)).fuse(cy(3,3,x,-.4,z,V(0,1,0))))
  nut=hexz(0,0,0,5.5,2.4).cut(cy(1.5,5,0,0,-1));nut.rotate(V(),V(1,0,0),-90);nut.translate(V(x,-10.3,z));cornernuts.append(nut)
put(f,'CornerPCBScrews',Part.makeCompound(corner),'#ddd5bc','BOARD',False,'nylon M3x12')
put(f,'CornerPCBNuts',Part.makeCompound(cornernuts),'#ddd5bc','BENCH',False,'nylon M3 nuts, AF5.5 H2.4; pocket retained with insulating tape')
f.recompute();f.saveAs(str(O/'RFCP_A07_Fixture_REVIEW.FCStd'))
Part.makeCompound([o.Shape for o in f.Objects if hasattr(o,'Shape')]).exportStep(str(O/'RFCP_A07_Fixture_REVIEW.step'))
def meshout(doc,name):
 out={}
 for o in doc.Objects:
  if hasattr(o,'Shape'):
   v,t=o.Shape.tessellate(.25);out[o.Name]={'vertices':[list(p) for p in v],'triangles':t,'color':o.DisplayColorHex,'group':o.Category}
 (O/name).write_text(json.dumps(out))
meshout(d,'assembly_mesh.json');meshout(f,'fixture_mesh.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':DRAFT,'classification':'CALCULATED_CAD','freecad':A.Version(),'head_parts':headmeta,
 'source_hashes':{str(p.relative_to(R)):sha(p) for p in [Path(__file__),oldpath,fixpath]},
 'parts':{o.Name:{'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume} for o in f.Objects if hasattr(o,'Shape')},
 'printed_parts':['LowerShell','UpperShell','LowerKeeper','UpperKeeper','Base'],
 'limitations':['Silicone pad contact/friction/creep and core self-seating NOT qualified; A05 float mechanism deliberately removed.','RF effect of remote metal NOT measured; distance is not a no-effect guarantee.','Self-centering cable clamps not implemented in this revision.','No print strength or real assembly verification; exact nylon hardware pending.','No purchase/upload/fabrication authorization performed.']}
(O/'build_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(report['parts']),'invalid':[n for n,p in report['parts'].items() if not p['valid']],'printed':5}),flush=True)
