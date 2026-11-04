"""A06 independent slotted dock and protective guard, based on saved A05 CAD.
CALCULATED_CAD only. No purchase or fabrication release.
"""
import json,math,hashlib,shutil
from pathlib import Path
import FreeCAD as A
import Part,MeshPart
R=Path(__file__).resolve().parents[1];P=R/'mechanical/clamp_A05_DRAFT';O=R/'mechanical/clamp_A06_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True);V=A.Vector
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cy(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter()
def hexz(x,y,z,af,h):
 r=af/math.sqrt(3);p=[V(x+r*math.cos(math.pi/6+i*math.pi/3),y+r*math.sin(math.pi/6+i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def put(doc,n,s,c,g,printed=False):
 o=doc.addObject('PartDesign::Feature',n);o.Shape=s
 for key,val in [('Status','DRAFT - NOT FOR FABRICATION'),('Category',g),('DisplayColorHex',c)]:o.addProperty('App::PropertyString',key);setattr(o,key,val)
 if printed:
  s.exportStep(str(O/'parts'/(n+'_DRAFT.step')));q=s.copy();b=q.BoundBox;q.translate(V(-b.XMin,-b.YMin,-b.ZMin))
  MeshPart.meshFromShape(Shape=q,LinearDeflection=.1,AngularDeflection=.15,Relative=False).write(str(O/'parts'/(n+'_DRAFT.stl')))
 return o
old=A.openDocument(str(P/'RFCP_Clamp_A05_DRAFT.FCStd'));B=json.loads((P/'build_report.json').read_text())
d=A.newDocument('RFCP_Clamp_A06_DRAFT');meta={}
lower=old.getObject('FixedTray').Shape.copy()
for sign in [-1,1]:
 x=sign*45
 # Independent dock tabs: M4 slots open toward -Y. Loosen 3 mm, slide +Y 22 mm.
 ear=box(18 if sign>0 else -52,-63,-4,34,17,5)
 ear=ear.cut(box(x-2.6,-65,-6,5.2,11,10).fuse(cy(2.6,10,x,-54,-6)))
 lower=lower.fuse(ear)
 for y in [-61,-40]:
  lower=lower.fuse(box(18 if sign>0 else -29,y-5,-4,11,10,4)).fuse(cy(4,24,sign*25,y,-4))
  lower=lower.cut(cy(2.1,35,sign*25,y,-10))
lower=lower.removeSplitter()
for o in old.Objects:
 if not hasattr(o,'Shape'):continue
 m=B['parts'][o.Name];s=lower if o.Name=='FixedTray' else o.Shape.copy()
 put(d,o.Name,s,o.DisplayColorHex,m['group'],m['printed']);meta[o.Name]={**m,'notes':m.get('notes','')}
# One removable front guard. Tongue covers winding front, without closing bore.
guard=fuse([box(-34,-65.5,20,68,31.5,3),box(-14,-36,20,28,36,3).cut(cy(18,8,0,0,18)),
 box(-34,-65.5,10,3,27.5,10),box(31,-65.5,10,3,27.5,10),box(-20,-65.5,10,40,3,10)])
guard=guard.cut(cy(9,10,0,-49,18))
for x in [-25,25]:
 for y in [-61,-40]:guard=guard.cut(cy(2.1,10,x,y,18))
# Open cable saddle: connector stays below Z53.15, cable rests at Z58..64.
saddle=box(-16,-57,58,32,13,6)
saddle=saddle.cut(cy(4.5,12,0,-49,55)).cut(box(-4.5,-49,55,9,12,12))
for x in [-8,8]:saddle=saddle.cut(box(x-1.8,-59,59.5,3.6,18,3))
guard=fuse([guard,box(-16,-56,22,4,4,42),box(12,-56,22,4,4,42),saddle])
bolts=[];nuts=[]
for x in [-25,25]:
 for y in [-61,-40]:
  bolts.append(cy(1.5,30,x,y,-7).fuse(cy(3.25,3.3,x,y,23)))
  nuts.append(hexz(x,y,-6.4,5.5,2.4).cut(cy(1.5,5,x,y,-8)))
for n,s,c,pr in [('FrontGuard',guard,'#487e97',True),('GuardScrews',Part.makeCompound(bolts),'#bbc6cf',False),('GuardNuts',Part.makeCompound(nuts),'#a6b3bf',False)]:
 put(d,n,s,c,'FIXED',pr);meta[n]={'group':'FIXED','printed':pr,'notes':'A06 independent protective guard / ordinary through hardware'}
d.recompute();d.saveAs(str(O/'RFCP_Clamp_A06_DRAFT.FCStd'))
Part.makeCompound([o.Shape for o in d.Objects if hasattr(o,'Shape')]).exportStep(str(O/'RFCP_Clamp_A06_DRAFT.step'))
# New dock, independent of PCB screws. Square nuts load from rear before base mount.
br=box(-52,-67,-18,104,6,10)
thumbs=[];sqnuts=[]
for x in [-45,45]:
 br=br.fuse(box(x-7,-64,-14,14,18,10))
 br=br.cut(cy(2.6,30,x,-54,-23)).cut(box(x-3.9,-68,-10.6,7.8,17.9,4.6))
 thumbs.append(cy(2,20,x,-54,-19).fuse(cy(6,7.5,x,-54,1)))
 sqnuts.append(box(x-3.5,-57.5,-9.9,7,7,3.2).cut(cy(2,6,x,-54,-11)))
for x in [-12,12]:br=br.cut(cy(1.9,12,x,-70,-12,V(0,1,0)))
br=br.removeSplitter()
fixold=A.openDocument(str(P/'RFCP_A05_Fixture_REVIEW.FCStd'));f=A.newDocument('RFCP_A06_Fixture_REVIEW')
for o in fixold.Objects:
 if not hasattr(o,'Shape') or o.Name.startswith('Head_') or o.Name in ['HeadBracket_A05','BenchM2x16','BenchM2Nuts']:continue
 put(f,o.Name,o.Shape.copy(),o.DisplayColorHex,'BENCH')
for o in d.Objects:
 if hasattr(o,'Shape'):put(f,'Head_'+o.Name,o.Shape.copy(),o.DisplayColorHex,o.Category)
for n,s,c,pr in [('DockBracket_A06',br,'#62788e',True),('DockHandScrews',Part.makeCompound(thumbs),'#cbd3db',False),('DockSquareNuts',Part.makeCompound(sqnuts),'#afbac5',False)]:put(f,n,s,c,'BENCH',pr)
f.recompute();f.saveAs(str(O/'RFCP_A06_Fixture_REVIEW.FCStd'))
Part.makeCompound([o.Shape for o in f.Objects if hasattr(o,'Shape')]).exportStep(str(O/'RFCP_A06_Fixture_REVIEW.step'))
def meshout(doc,name):
 out={}
 for o in doc.Objects:
  if not hasattr(o,'Shape'):continue
  v,t=o.Shape.tessellate(.22);out[o.Name]={'vertices':[list(p) for p in v],'triangles':t,'color':o.DisplayColorHex,'group':o.Category}
 (O/name).write_text(json.dumps(out))
meshout(d,'assembly_mesh.json');meshout(f,'fixture_mesh.json')
report={'classification':'CALCULATED_CAD','status':'DRAFT - NOT FOR FABRICATION','freecad_version':A.Version(),
 'source_hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),P/'RFCP_Clamp_A05_DRAFT.FCStd',P/'RFCP_A05_Fixture_REVIEW.FCStd']},
 'parts':{o.Name:{**meta[o.Name],'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume} for o in d.Objects if hasattr(o,'Shape')},
 'dock':{'valid':br.isValid(),'solids':len(br.Solids),'screw_centres_mm':[[-45,-54],[45,-54]],'loosen_mm':3,'head_slide_y_mm':22,'head_lift_z_mm':60},
 'unchanged':['Core, winding, spring mechanism, Head PCB A03, calibration PCB A02, base and columns','Permanent M2x10 PCB fasteners stay installed in bench and field configurations'],
 'added_hardware':['M4x20 D12 hand screws x2 for dock','M4 square nut s7 m3.2 x2 for dock','M3x30 D<=6.5 H<=3.3 x4 and AF<=5.5 H<=2.4 nuts x4 for guard','2.5mm wide nonconductive cable tie x1; actual fit required'],
 'limitations':['No physical print, assembly, load, drop, friction or RF qualification.','Front guard is mechanical protection, not a certified electrical enclosure. Bore-side winding still needs prescribed insulating tape.','Cable saddle assumes connector <=D16x45 and jacket OD<=6; actual owned cable must be checked.']}
(O/'build_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'head_parts':len(meta),'invalid':[n for n,p in report['parts'].items() if not p['valid']],'printed_non_single':[n for n,p in report['parts'].items() if p['printed'] and p['solids']!=1],'dock_valid':br.isValid(),'dock_solids':len(br.Solids)}),flush=True)
