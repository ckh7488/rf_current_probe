"""A14 split-print patch of saved A13; nominal CAD, not fabrication approval.
Run with FreeCAD 1.0.2 freecadcmd. Never overwrite A13 supplier files.
"""
from pathlib import Path
import json, math, hashlib, itertools, shutil
import FreeCAD as A
import Part, MeshPart, Mesh

R=Path(__file__).resolve().parents[1]
OLD=R/'mechanical/assembly_A13_DRAFT'
O=R/'mechanical/assembly_A14_DRAFT'
(O/'parts').mkdir(parents=True,exist_ok=True)
V=A.Vector
old=A.openDocument(str(OLD/'RFCP_A13_Integrated_DRAFT.FCStd'))
meta=json.loads((OLD/'mesh.json').read_text())
S={o.Name:o.Shape.copy() for o in old.Objects if hasattr(o,'Shape')}
M={n:{k:v for k,v in p.items() if k not in ['vertices','triangles']} for n,p in meta.items()}
D=A.newDocument('RFCP_A14_Split_Print_DRAFT')
FREE={};CHANGED=[];HW=[]
STATUS='DRAFT - NOT FOR FABRICATION; supplier re-review and physical fit required'
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cyl(r,h,x,y,z,axis=V(0,0,1)):return Part.makeCylinder(r,h,V(x,y,z),axis)
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def union(ss):return ss[0].multiFuse(ss[1:]).removeSplitter()
def mirrorx(s):m=A.Matrix();m.A11=-1;return s.transformGeometry(m)
def clip(s,x0=-1000,x1=1000,y0=-1000,y1=1000,z0=-1000,z1=1000):return s.common(box(x0,y0,z0,x1-x0,y1-y0,z1-z0)).removeSplitter()
def put(n,s,parent,color,free=None,explode=(0,0,0)):
 S[n]=s.removeSplitter();FREE[n]=(free if free is not None else s).removeSplitter()
 M[n]=dict(color=color,group=M[parent]['group'],printed=True,parent=parent,explode=explode)
 CHANGED.append(n)
def hexnut(x,y,z,af=7,h=3.2):
 rr=af/math.sqrt(3);pts=[V(x+rr*math.cos(i*math.pi/3),y+rr*math.sin(i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h)).cut(cyl(2.05,h+2,x,y,z-1))
def hardware_z(name,x,y,start,length,grip,group):
 # Essentra PA66 maximum head D8 H3.1, washer ID4.3 OD9 t0.8, nut AF7 H3.2.
 shapes={'Screw':cyl(2,length,x,y,start-.8).fuse(cyl(4,3.1,x,y,start-3.9)),
         'RearWasher':cyl(4.5,.8,x,y,start-.8).cut(cyl(2.15,2,x,y,start-1)),
         'FrontWasher':cyl(4.5,.8,x,y,start+grip).cut(cyl(2.15,2,x,y,start+grip-.1)),
         'Nut':hexnut(x,y,start+grip+.8)}
 for suffix,s in shapes.items():
  n=name+suffix;S[n]=s;M[n]=dict(color='#e0c36a',group=group,printed=False,new_hardware=True,material='nonconductive PA M4 candidate envelope',joint=name);HW.append(n)

# LOWER: keep the core cradle, PCB holder and sole as one piece. Only closure wings separate.
lower=S['LowerBody']
center=clip(lower,x0=-58,x1=58)
for side in [-1,1]:
 arm=clip(lower,x0=58 if side>0 else -1000,x1=1000 if side>0 else -58)
 # Open stepped lap, 28 mm long, 11 mm through-thickness. Bottom ledge takes vertical load.
 tongue=box(58,-34,3,28,23.2,11)
 socket=box(58,-34,3,29,24.2,12)
 if side<0:tongue=mirrorx(tongue);socket=mirrorx(socket)
 center=center.fuse(tongue)
 arm=arm.cut(socket)
 for ax in [66,78]:
  x=side*ax;drill=cyl(2.7,60,x,-22,-25)
  center=center.cut(drill);arm=arm.cut(drill)
  hardware_z('LowerJoint'+('L' if side<0 else 'R')+str(ax),x,-22,-8,30,22,'HEAD_FIXED')
 put('LowerArmLeft' if side<0 else 'LowerArmRight',arm,'LowerBody','#528ea0',explode=(side*65,0,25))
# Preserve a broad minimum 3mm roof at the PCB rear relief; no narrow edge patch.
# This stays behind the PCB and outside the SMA/coil-pad access opening.
center=center.fuse(box(-18.5,-38.1,13.1,12.5,3.1,2.4)).fuse(box(6,-38.1,13.1,12.5,3.1,2.4))
# Broaden the PCB window rim outward, preserving the PCB opening and mounting axes.
# Supplier DFM highlighted these projecting edges despite longer normal-chord samples.
center=center.fuse(box(-24,-70,-8,48,5,20)).fuse(box(-24,-65,-4.5,5.5,30,12)).fuse(box(18.5,-65,-4.5,5.5,30,12))
put('LowerCenter',center,'LowerBody','#356e84')

# UPPER: two halves joined in the thick middle, never across the 63mm leaf spans.
# Existing free and closed shapes are split with the same local joint. No new spring/hinge.
def split_lid(source,dy):
 b=box(-18,37+dy,-4.5,36,18,20)
 full=source.fuse(b)
 left=clip(full,x1=-.4);right=clip(full,x0=.4)
 # Front/back half-lap above the core. Each leaf in the joint is 10 mm thick.
 # Horizontal shelf aligns Y; one open side datum aligns Z when tightened.
 lap=box(-12,37+dy,5.5,24,18,10)
 left=left.fuse(lap)
 right=right.cut(box(-13,36.5+dy,5.5,26,19,11))
 # Right half's rear tongue overlaps into the left half with 0.8mm end clearance.
 rear=box(-11.2,41+dy,-4.5,23.2,14,10)
 right=right.fuse(rear)
 left=left.cut(box(-12,36.5+dy,-5.5,24,19,11))
 # A 4mm lower shelf makes the height datum visible and seats the halves without eye alignment.
 left=left.fuse(box(-12,37+dy,-4.5,24,4,10))
 right=right.cut(box(-13,36.5+dy,-5.5,25.8,4.5,11))
 for x in [-6,6]:
  h=cyl(2.7,40,x,48+dy,-14)
  left=left.cut(h);right=right.cut(h)
 return left.removeSplitter(),right.removeSplitter()
closed=split_lid(S['UpperLid'],0)
free=split_lid(Part.read(str(OLD/'parts/UpperLid_FREE_DRAFT.step')),-1.8)
for i,(n,c) in enumerate([('UpperLeft','#5e9fad'),('UpperRight','#8cbfc6')]):
 put(n,closed[i],'UpperLid',c,free=free[i],explode=((-1 if i==0 else 1)*65,50,0))
for x in [-6,6]:hardware_z('UpperJoint'+str(abs(x))+('L' if x<0 else 'R'),x,48,-4.5,30,20,'HEAD_CAP')

# BASE: three recognizable stations, same Y=-72 module datum. Narrow unused margins.
# Lower face becomes -88 (88 mm nominal axis height). Open ribs, no sealed cavities.
base=S['CommonBase']
base=clip(base,x0=-83,x1=103,y0=-72)
base=base.fuse(box(-83,-88,-136,186,16,314))
for x in [-74,-30,14,58]:
 for z in [-126,-82,-38,6,50,94,138]:
  base=base.cut(box(x,-89,z,32,12,30))
# Continuous 8mm perimeter and solid seam bands restore ribs cut by the new outline.
base=base.fuse(box(-83,-88,-136,8,16,314)).fuse(box(95,-88,-136,8,16,314))
for seam in [-50,94]:base=base.fuse(box(-83,-88,seam-16,186,16,32))
# Preserve original mounting bosses and under-base nut access with increased floor depth.
mounts=[(-48,75),(48,75),(-54,-114.65),(80,-114.65),(-54,125.35),(80,125.35)]
for x,z in mounts:
 base=base.fuse(box(x-8,-88,z-8,16,16,16)).cut(cyl(2.7,24,x,-92,z,V(0,1,0))).cut(box(x-4,-89,z-4,8,11,8))
front=clip(base,z1=-50);middle=clip(base,z0=-50,z1=94);back=clip(base,z0=94)
pieces={'BaseFront':front,'BaseCenter':middle,'BaseRear':back}
for seam,end,sgn in [(-50,'BaseFront',-1),(94,'BaseRear',1)]:
 band=box(-83,-88,seam-16,186,16,32)
 # Whole-width open half-lap; outer station is bottom 10mm, central station top 6mm.
 bottom=box(-83,-88,seam-16,186,10,32)
 top=box(-83,-78,seam-15.2 if sgn<0 else seam-16,186,6,31.2)
 pieces[end]=pieces[end].cut(band).fuse(bottom)
 pieces['BaseCenter']=pieces['BaseCenter'].cut(band).fuse(top)
 for x in ([-45,45] if seam<0 else [-68,68]):
  h=cyl(2.7,30,x,-94,seam,V(0,1,0))
  # Wide open underside recess for a 7mm socket; not a captive nut trap.
  pocket=cyl(12,6,x,-88,seam,V(0,1,0))
  for n in [end,'BaseCenter']:pieces[n]=pieces[n].cut(h).cut(pocket)
  # Insert from the underside: M4x20 head in the open recess, nut visible above.
  # Reverse hardware only; print geometry and the 4mm remaining lap wall are unchanged.
  stem='BaseJoint'+('F' if seam<0 else 'R')+('L' if x<0 else 'R')
  before=set(HW);hardware_z(stem,0,0,0,20,10,'BASE')
  for n in set(HW)-before:
   q=S[n];q.rotate(V(),V(1,0,0),-90);q.translate(V(x,-82,seam));S[n]=q
for n in pieces:
 for x,z in mounts:
  pieces[n]=pieces[n].cut(cyl(2.7,24,x,-92,z,V(0,1,0))).cut(box(x-4,-89,z-4,8,11,8))
for n,c,e in [('BaseFront','#7a9eab',(0,0,-80)),('BaseCenter','#6f8592',(0,0,0)),('BaseRear','#91aeba',(0,0,80))]:put(n,pieces[n],'CommonBase',c,explode=e)

for n in ['CommonBase','LowerBody','UpperLid']:S.pop(n);M.pop(n)
# Catalog hardware: no press fitting or stud cutting. Knob shown as its maximum envelope.
def hex_y(x,y,z,af,h):
 rr=af/math.sqrt(3);pts=[V(x+rr*math.cos(math.radians(30+i*60)),y,z+rr*math.sin(math.radians(30+i*60))) for i in range(6)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,h,0)).cut(cyl(3.1,h+2,x,y-1,z,V(0,1,0)))
catalog=dict(LeadStud=cyl(3,120,80,-53.4,26,V(0,1,0)),
 HandKnob=cyl(16,20,80,56.6,26,V(0,1,0)).cut(cyl(3.1,10,80,56.6,26,V(0,1,0))),
 TopWasher=cyl(6,1.6,80,50,26,V(0,1,0)).cut(cyl(3.2,3,80,49.5,26,V(0,1,0))),
 TopJamNut=hex_y(80,51.6,26,10,5))
for k,off in [(1,-118.65),(2,121.35)]:
 oldname=f'Cable{k}_LeadScrewKnob';parent=M.pop(oldname);S.pop(oldname)
 for suffix,q in catalog.items():
  n=f'Cable{k}_{suffix}';S[n]=mv(q,z=off)
  M[n]=dict(parent,color='#b5c0c6',printed=False,subgroup='FIXED' if suffix=='TopWasher' else 'LEAD',catalog_envelope=True)
  HW.append(n)
# 2026-09-21 catalogue-only update: use the same Fabory t1.6 washer above/below.
# Keep its upper thrust face at Y41.8 and the nominal frame gap at 0.2 mm.
# Shift the lower nyloc with the washer's lower face; print geometry is unchanged.
for k,off in [(1,-118.65),(2,121.35)]:
 n=f'Cable{k}_ThrustWasher'
 S[n]=cyl(6,1.6,80,40.2,26+off,V(0,1,0)).cut(cyl(3.2,3.6,80,39.2,26+off,V(0,1,0)))
 M[n].update(catalog_envelope=True,manufacturer='Fabory',mpn='50060.060.001',thickness_mm=1.6)
 HW.append(n)
 n=f'Cable{k}_LeadLockNut';S[n]=mv(S[n],y=-.8);M[n].update(catalog_position_update_y_mm=-.8);HW.append(n)
# Essentra 50M020040P012 maximum head D4/H1.6 replaces the old D3.8/H1.3 envelope.
# Extend the original M2x10 shank to12; keep seating plane and mounting axes.
pcb_screws=[]
for s in S['PCBScrews'].Solids:
 b=s.BoundBox;x=(b.XMin+b.XMax)/2;y=(b.YMin+b.YMax)/2;head_base=b.ZMax-1.3
 pcb_screws.append(s.fuse(cyl(2,1.6,x,y,head_base)).fuse(cyl(1,2.05,x,y,b.ZMin-2)).removeSplitter())
S['PCBScrews']=Part.makeCompound(pcb_screws)
M['PCBScrews'].update(catalog_envelope=True,manufacturer='Essentra',mpn='50M020040P012',shaft_length_mm=12,head_max_diameter_mm=4,head_max_height_mm=1.6)
HW.append('PCBScrews')
# Purchased through-knob closure: the 70mm stud is flush with the knob top.
# Two preassembled units replace the original short-projection M4x50 envelope.
# Add paired compounds so BOM/assembly guides can identify all four purchased parts.
closure={n:[] for n in ['HeadHandScrews','HeadClosureKnobs','HeadClosureJamNuts','HeadClosureWashers']}
for x in [-111,111]:
 closure['HeadHandScrews'].append(cyl(2,70,x,-16.5,6.35,V(0,1,0)))
 knob=cyl(4,6,x,44,6.35,V(0,1,0)).fuse(cyl(8,3.5,x,50,6.35,V(0,1,0)))
 closure['HeadClosureKnobs'].append(knob.cut(cyl(2.1,11.5,x,43,6.35,V(0,1,0))))
 rr=7/math.sqrt(3);pts=[V(x+rr*math.cos(math.radians(30+i*60)),40.8,6.35+rr*math.sin(math.radians(30+i*60))) for i in range(6)]
 nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,3.2,0)).cut(cyl(2.1,5.2,x,39.8,6.35,V(0,1,0)))
 closure['HeadClosureJamNuts'].append(nut)
 closure['HeadClosureWashers'].append(cyl(4.5,.8,x,40,6.35,V(0,1,0)).cut(cyl(2.15,2.8,x,39,6.35,V(0,1,0))))
for n,ss in closure.items():
 S[n]=Part.makeCompound(ss)
 M[n]=dict(color='#ded8c3' if n=='HeadClosureWashers' else '#bac5cd',group='HEAD_SCREW',printed=False,catalog_envelope=True,closure_unit=True,quantity=2)
 HW.append(n)
M['HeadHandScrews'].update(manufacturer='Fabory',mpn='20106.040.070',shaft_length_mm=70)
M['HeadClosureKnobs'].update(manufacturer='NBK',mpn='KNFS-16-M4',through_thread=True)
M['HeadClosureJamNuts'].update(manufacturer='Fabory',mpn='51080.040.001')
M['HeadClosureWashers'].update(manufacturer='Essentra',mpn='17M04DIN34815',material='PA66')
# Remaining seven unique print files are byte-identical A13 files.
for p in (OLD/'parts').glob('*'):
 if not p.name.startswith(('CommonBase_','LowerBody_','UpperLid_')):shutil.copy2(p,O/'parts'/p.name)
for n in ['LowerKeeper','UpperKeeper']:FREE[n]=Part.read(str(OLD/'parts'/(n+'_FREE_DRAFT.step')))
for n in ['Frame','DriveYoke','TopBridgeJaw','Jaw1','Jaw2']:FREE['C07_'+n]=Part.read(str(OLD/'parts'/('C07_'+n+'_DRAFT.step')))
for n in CHANGED:
 q=FREE[n];q.exportStep(str(O/'parts'/(n+'_A14_DRAFT.step')));b=q.BoundBox
 MeshPart.meshFromShape(Shape=mv(q,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.08,AngularDeflection=.12,Relative=False).write(str(O/'parts'/(n+'_A14_DRAFT.stl')))
mesh={}
for n,s in S.items():
 o=D.addObject('PartDesign::Feature',n);o.Shape=s
 for k,val in [('Status',STATUS),('DisplayColorHex',M[n]['color']),('Group',M[n]['group'])]:o.addProperty('App::PropertyString',k);setattr(o,k,val)
 vertices,triangles=s.tessellate(.2);mesh[n]=dict(vertices=[list(v) for v in vertices],triangles=triangles,**M[n])
D.recompute();D.saveAs(str(O/'RFCP_A14_Integrated_DRAFT.FCStd'))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A14_Integrated_DRAFT.step'))
(O/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
def overlap(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0
bad=[]
for a,b in itertools.combinations(S,2):
 if a=='FlatPCB' and b in ['SignalCopper','ReturnCopper']:continue
 if a not in CHANGED+HW and b not in CHANGED+HW:continue
 v=overlap(S[a],S[b])
 if v>1e-4:bad.append(dict(a=a,b=b,volume_mm3=round(v,5)))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parts={n:dict(valid=s.isValid(),solids=len(s.Solids),volume_mm3=s.Volume,bbox_mm=[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]) for n,s in FREE.items()}
report=dict(status=STATUS,classification='CALCULATED_CAD_NOT_PRINT_OR_STRUCTURAL_SIMULATION',freecad=A.Version(),
 source_sha256=sha(Path(__file__)),input_sha256={str(p.relative_to(R)):sha(p) for p in [OLD/'RFCP_A13_Integrated_DRAFT.FCStd',OLD/'parts/UpperLid_FREE_DRAFT.step']},
 native_sha256=sha(O/'RFCP_A14_Integrated_DRAFT.FCStd'),mesh_sha256=sha(O/'mesh.json'),parts=parts,changed_parts=CHANGED,
 printed_unique=15,printed_total=20,additional_joint_bolts=10,static_collisions=bad,
 parameters=dict(base_width_mm=186,base_length_mm=314,base_thickness_mm=16,axis_height_mm=88,module_datum_y=-72,core_unchanged=True,leaf_span_mm=63,leaf_thickness_mm=2.4),
 hardware=[dict(use='Base seams; screw from underside',qty=4,screw='M4 x 20',mpn='50M040070P020',washer='17M04DIN34815 ID4.3 OD9 t0.8 x2',nut='04M040070HNDIN34814 AF7 H3.2',material='nonconductive PA66'),dict(use='Lower arm seams',qty=4,screw='M4 x 30',mpn='50M040070P030',washer='17M04DIN34815 ID4.3 OD9 t0.8 x2',nut='04M040070HNDIN34814 AF7 H3.2',material='nonconductive PA66'),dict(use='Upper center seam',qty=2,screw='M4 x 30',mpn='50M040070P030',washer='17M04DIN34815 ID4.3 OD9 t0.8 x2',nut='04M040070HNDIN34814 AF7 H3.2',material='nonconductive PA66')],
 catalogue_only_update_20260921=dict(lower_thrust_washer='Fabory 50060.060.001 ID6.4 OD12 t1.6; qty2, same as top washer',lower_nyloc_y_mm=[34.2,40.2],lower_washer_y_mm=[40.2,41.8],frame_endplay_nominal_mm=.2,pcb_screw='Essentra 50M020040P012; qty2; maximum head D4 H1.6; M2x12 shank adopted; print geometry unchanged',changed_shape_objects=['Cable1_ThrustWasher','Cable2_ThrustWasher','Cable1_LeadLockNut','Cable2_LeadLockNut','PCBScrews']),
 closure_catalogue_20260921=dict(stud='Fabory 20106.040.070 M4x70',knob='NBK KNFS-16-M4 through-thread',jamnut='Fabory 51080.040.001 M4 AF7 H3.2',washer='Essentra 17M04DIN34815 PA66 ID4.3 OD9 t0.8',quantity_each=2,stud_y_mm=[-16.5,53.5],washer_y_mm=[40,40.8],nut_y_mm=[40.8,44],knob_y_mm=[44,53.5],nominal_effective_under_washer_length_mm=56.5,nominal_tip_projection_mm=6.9,assembly='Preassemble outside the probe: stud top flush with knob top, counter-tighten jamnut against knob hub, then place PA washer; keep each four-part unit together for routine removal.'),
 limitations=['Splitting reduces individual span; no warp magnitude/probability or supplier acceptance established.','New lap joint slip, nylon screw creep, preload, fatigue and core contact force untested.','A13 FEA cannot validate A14 joints. Existing 2.4mm flexures retained, not reinforced arbitrarily.','Open laps seat on datum faces, no press-fit; real warpage and global tolerance may exceed local gaps.','All 10 new joint fasteners nonconductive; vendor dimensions/material and wrench fit require physical confirmation.','A13 remaining DFM warning in PCB holder needs fresh supplier review.','Existing C07 candidate screw/shaft sourcing and calibration PCB impedance holds remain.'])
report['pass_geometry']=not bad and all(x['valid'] and x['solids']==1 for x in parts.values())
(O/'build_report.json').write_text(json.dumps(report,indent=2))
print('A14_REPORT',json.dumps(dict(pass_geometry=report['pass_geometry'],invalid={n:p for n,p in parts.items() if not p['valid'] or p['solids']!=1},collisions=bad)),flush=True)
