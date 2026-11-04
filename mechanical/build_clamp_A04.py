"""FreeCADCmd: reproducible A0.4 mechanical prototype, all dimensions in mm.

DRAFT - NOT FOR FABRICATION. Nominal manufacturer core + actual printable-part
geometry; no claim of print fit, force, insulation or RF performance. The first
fit prototype uses a removable nylon M3 screw latch, not a tested cam latch.
"""
import hashlib
import json
import math
from pathlib import Path
import FreeCAD as A
import Part
import MeshPart

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/clamp_A04_DRAFT'
OUT.mkdir(exist_ok=True)
(OUT / 'parts').mkdir(exist_ok=True)
G = json.loads((ROOT / 'hardware/probe_head_A03/design_geometry.json').read_text(encoding='utf-8'))
STATUS = 'DRAFT - NOT FOR FABRICATION'
P = {
    'head_board_mm': [36,28,1.6],
    'head_mount_holes_mm': 2.8,
    'head_mount_nut_recess_af_mm': 4.6,
    'aperture_radius': 15.75,
    'target_gauge_diameter': 30.0,
    'base_z': -3.0,
    'pocket_floor_z': -1.5,
    'keeper_bottom_z': 14.0,
    'keeper_thickness': 2.4,
    'seam_setback': 0.4,
    'hinge_x': -40.0,
    'hinge_outer_radius': 4.5,
    'hinge_hole_diameter': 3.4,
    'hinge_pin_diameter': 3.0,
    'hinge_axial_gap': 0.3,
    'latch_x': 40.0,
    'latch_z': 7.0,
    'latch_clearance_diameter': 3.4,
    'coil_turns': 5,
    'coil_pitch': 1.6,
    'coil_outer_y': -31.2,
    'coil_inner_y': -17.6,
    'coil_back_z': -0.8,
    'coil_front_z': 13.5,
    'assumed_wire_outer_diameter': 0.4,
    'keeper_holes': [[-24.0, -25.0], [24.0, -25.0]],
    'max_review_open_angle_deg': 90,
    'keeper_nut_boss_radius': 4.2,
    'keeper_nut_boss_top_z': 0.0,
    'keeper_nut_trap_af': 4.1,
    'keeper_nut_trap_depth': 1.8,
    'print_clearance_assumptions': '0.3-0.4 nominal sliding gaps; calibrate with coupon; no shrink compensation',
}
V = A.Vector

def box(x0,y0,z0,dx,dy,dz):
    return Part.makeBox(dx,dy,dz,V(x0,y0,z0))

def cyl(r,h,x,y,z,axis=V(0,0,1)):
    return Part.makeCylinder(r,h,V(x,y,z),axis)

def prism(points,z,h):
    wire=Part.makePolygon([V(x,y,z) for x,y in points+[points[0]]])
    return Part.Face(wire).extrude(V(0,0,h))

def flip_y(s):
    # Cores and housings are symmetric about z=6.35 / center XY seam.
    # Mirror across Y=0 preserves front/back and avoids swapping tray/keeper.
    m=A.Matrix(); m.A22=-1
    return s.transformGeometry(m)

def hex_z(x,y,z,af,h):
    r=af/math.sqrt(3)
    return prism([(x+r*math.cos(math.pi/6+i*math.pi/3),y+r*math.sin(math.pi/6+i*math.pi/3)) for i in range(6)],z,h)

def hex_y(x,y,z,af,h):
    s=hex_z(0,0,0,af,h)
    s.rotate(V(),V(1,0,0),-90)
    s.translate(V(x,y,z))
    return s

def fuse(shapes):
    return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]

outer=[(-35.5,-.4),(-35.5,-14.5),(-18,-36),(18,-36),(35.5,-14.5),(35.5,-.4)]
cavity=[(-31.7,1),(-31.7,-12),(-14,-31.5),(14,-31.5),(31.7,-12),(31.7,1)]
aperture=cyl(P['aperture_radius'],45,0,0,-12)
raw_frame=prism(outer,-3,17).cut(aperture)
pocket=prism(cavity,-1.5,16).cut(cyl(17.9,20,0,0,-2))
frame=raw_frame.cut(pocket)
# Two elastomer backing-pad recesses, away from the magnetic mating seam.
for x in [-21,21]:
    frame=frame.cut(box(x-2,-14,-2,4,4,1))
keeper=prism(outer,14,2.4).cut(cyl(27,5,0,0,13))
for x,y in P['keeper_holes']:
    frame=frame.cut(cyl(1.1,25,x,y,-5)).cut(hex_z(x,y,-3,P['keeper_nut_trap_af'],P['keeper_nut_trap_depth']))
    keeper=keeper.cut(cyl(1.1,5,x,y,13))

# Hinge: lower two knuckles, upper center knuckle. All hardware is nylon.
def knuckle(z,h,upper=False):
    ring=cyl(4.5,h,-40,0,z).cut(cyl(1.7,h+2,-40,0,z-1))
    bridge=box(-40,.4 if upper else -5.5,z,8,5.1,h)
    return ring.fuse(bridge).cut(cyl(1.7,h+2,-40,0,z-1)).removeSplitter()
lower_hinge=fuse([knuckle(-3,5.7),knuckle(10.9,5.5)])
upper_hinge=knuckle(3,7.6,True)

lower_latch=box(32,-7,2.5,13,7,9).cut(cyl(1.7,12,40,-9,7,V(0,1,0)))
upper_latch=flip_y(lower_latch).cut(hex_y(40,4.2,7,5.8,3.5))
# Touching latch shoulders at y=0 set the nominal closed housing position.
lower=fuse([frame,lower_hinge,lower_latch])
upper=fuse([flip_y(frame),upper_hinge,upper_latch])
# Integral nominal 90-degree stop. Bridge clears the moving knuckle axially.
stop_bridge=box(-48,1,10.9,6,2.5,3)
stop_finger=box(-48,1,3,2.5,2.5,7.9)
stop=fuse([stop_bridge,stop_finger])
lower=lower.fuse(stop).removeSplitter()
lower_keeper=keeper
upper_keeper=flip_y(keeper)

# PCB tray shares geometry with KiCad. Board top z=6.35, mounting holes M2.
tray=box(-20,-62.2,-3,40,31.5,11).cut(box(-18.3,-60.3,0,36.6,28.6,20))
for px,py in G['mounting_holes']:
    x=px-18; y=-32-py
    tray=tray.fuse(cyl(3.5,4.75,x,y,0))
    tray=tray.cut(cyl(1.4,16,x,y,-5)).cut(hex_z(x,y,-3,4.6,1.8))
lower=lower.cut(box(-18.3,-60.3,0,36.6,28.6,20)).fuse(tray)
# Continuous winding and paired leads get dedicated reliefs.
coil_channel=box(-6,-33,-1.25,12,16.2,15.5)
lead_channel=box(-6,-36,4.9,12,6,2.9)
lower=lower.cut(coil_channel).cut(lead_channel).removeSplitter()
lower_keeper=lower_keeper.cut(box(-6,-33,13,12,16,5)).removeSplitter()

# A0.4: build analytic bosses separately on each tray after mirroring.
# Preserve the original screw centers, core mating faces and keepers.
# Radius 4.2 encloses AF4.1 nut trap with >=1.83 mm radial material;
# top z=0 leaves 1.2 mm over the trap roof and stays below nominal core.
def reinforce_nut_traps(shape, sign_y):
    for x,y in P['keeper_holes']:
        y *= sign_y
        shape=shape.fuse(cyl(P['keeper_nut_boss_radius'],3,x,y,-3))
        shape=shape.cut(cyl(1.1,25,x,y,-5)).cut(hex_z(x,y,-3,P['keeper_nut_trap_af'],P['keeper_nut_trap_depth']))
    return shape.removeSplitter()
lower=reinforce_nut_traps(lower,1)
upper=reinforce_nut_traps(upper,-1)

# Remove the unsupported 0.2 mm fin where the PCB pocket (y=-31.7)
# nearly met the core pocket (y=-31.5) above the cradle top at z=8.
# The PCB remains held by its two screws and the original lower cradle.
# Broad shoulders replace the thin wedges where the enlarged pocket meets
# the old diagonal frame. They remain outside the PCB and ferrite envelopes.
for side_x in [-22.5,18.3]:
    lower=lower.fuse(box(side_x,-38,-3,4.2,7.5,17))
lower=lower.cut(box(-18.3,-60.3,8,36.6,29.8,10)).removeSplitter()
# Round the two acute vertical tips created by that upper relief; leaving
# them sharp creates thin triangular fins beside the old diagonal pocket.
rim_edges=[]
for edge in lower.Edges:
    b=edge.BoundBox
    if b.ZLength>5.9 and b.XLength<.001 and b.YLength<.001 and abs(abs(b.XMin)-14.9076923)<.01 and abs(b.YMin+30.5)<.01:
        rim_edges.append(edge)
assert len(rim_edges)==2, 'Upper-relief topology changed; inspect before filleting'
lower=lower.makeFillet(1.0,rim_edges).removeSplitter()


core_source=ROOT/'docs/references/2644181281.STEP'
core=Part.read(str(core_source))
moving_core=flip_y(core)
gauge=cyl(15,34,0,0,-9)

# Model a single continuous winding, with x advancing throughout every turn.
start=V(-4,-31.2,6.35)
pts=[start]
cross_section=[(-31.2,13.5),(-17.6,13.5),(-17.6,-.8),(-31.2,-.8),(-31.2,6.35)]
for turn in range(5):
    for j,(y,z) in enumerate(cross_section):
        pts.append(V(-4+(turn+(j+1)/5)*1.6,y,z))
coil_terminals=[V(px-18,-32-py,6.35) for px,py in G['coil_pads']]
wire_pts=[coil_terminals[0]]+pts+[coil_terminals[1]]
wire_solids=[]
for a,b in zip(wire_pts,wire_pts[1:]):
    delta=b-a
    wire_solids.append(Part.makeCylinder(.2,delta.Length,a,delta))
for pt in wire_pts: wire_solids.append(Part.makeSphere(.2,pt))
winding=fuse(wire_solids)

board_source=ROOT/'hardware/probe_head_A03/review/board_only.step'
board=Part.read(str(board_source))
bb=board.BoundBox
assert abs(bb.XLength-36)<.001 and abs(bb.YLength-28)<.001 and 1.4<bb.ZLength<1.7, 'KiCad board dimensions changed: review cradle before rebuilding'
# KiCad STEP user origin 0x0: +X right, -Y down the PCB; preserve this orientation.
assert abs(bb.XMin)<.001 and abs(bb.YMax)<.001, 'Unexpected KiCad export origin'
native_board_thickness=bb.ZLength
# --board-only exports the dielectric body (1.51 mm with KiCad's current
# default stack-up). Use its exact XY outline/drills and a nominal 1.6 mm
# finished-board collision envelope. Do not label this as a measured stack-up.
matrix=A.Matrix(); matrix.A33=1.6/native_board_thickness
board=board.transformGeometry(matrix)
board.translate(V(-18,-32,6.35-board.BoundBox.ZMax))

# Drawn dimensional envelope, not the manufacturer's detailed connector CAD.
sma_local=box(-3.5,-3.5,0,7,7,1.8).fuse(cyl(3.25,7.8,0,0,1.8))
sma_local=sma_local.cut(cyl(.8,11,0,0,-.5))
stakes=[cyl(.65,3.9,dx,dy,-3.9) for dx in [-2.54,2.54] for dy in [-2.54,2.54]]
sma_local=Part.makeCompound([sma_local]+stakes+[cyl(.635,3.9,0,0,-3.9)])
modeldir=OUT/'models'
modeldir.mkdir(exist_ok=True)
sma_local.exportStep(str(modeldir/'GCT_RFPC_SMA28_F_envelope.step'))
sma=sma_local.copy(); sma.translate(V(0,-45,6.35))

hinge_pin=cyl(1.5,25,-40,0,-3).fuse(cyl(2.75,2.5,-40,0,-5.5))
hinge_nut=hex_z(-40,0,16.9,5.5,2.4).cut(cyl(1.5,5,-40,0,16))
latch_screw=cyl(1.5,16,40,-7,7,V(0,1,0)).fuse(cyl(4,2.5,40,-9.5,7,V(0,1,0)))
latch_nut=hex_y(40,4.2,7,5.5,2.4).cut(cyl(1.5,4,40,3.5,7,V(0,1,0)))
back_pads=[]
for sign in [-1,1]:
    for x in [-21,21]:
        back_pads.append(box(x-2,10 if sign==1 else -14,-2,4,4,2))
radial_pads=[]
for sign in [-1,1]:
    for x in [-9,9]:
        pad=box(x-2,-31.5,1,4,31.5-29.6418,10)
        radial_pads.append(flip_y(pad) if sign==1 else pad)
front_pads=[]
for sign in [-1,1]:
    for x in [-28.25,28.25]:
        pad=box(x-1.25,-9,12.7,2.5,4,1.3)
        front_pads.append(flip_y(pad) if sign==1 else pad)

keeper_screws=[]; keeper_nuts=[]; pcb_screws=[]; pcb_nuts=[]
for sign in [-1,1]:
    for x,y in P['keeper_holes']:
        y=sign*abs(y)
        keeper_screws.append(cyl(1,20,x,y,-3.6).fuse(cyl(1.9,1.3,x,y,16.4)))
        keeper_nuts.append(hex_z(x,y,-3,4,1.6).cut(cyl(1,3,x,y,-3.5)))
for px,py in G['mounting_holes']:
    x=px-18; y=-32-py
    pcb_screws.append(cyl(1,10,x,y,-3.65).fuse(cyl(1.9,1.3,x,y,6.35)))
    pcb_nuts.append(hex_z(x,y,-3,4,1.6).cut(cyl(1,3,x,y,-3.5)))

# An inexpensive first print for pin/hole clearance. It does not certify fit.
coupon=box(0,0,0,34,12,4).cut(cyl(1.5,6,0,0,-1))
coupon_holes=[2.0,2.2,2.4,3.0,3.2,3.4]
for i,d in enumerate(coupon_holes): coupon=coupon.cut(cyl(d/2,6,3+i*5.5,6,-1))

doc=A.newDocument('RFCP_Clamp_A04_DRAFT')
params=doc.addObject('App::FeaturePython','DesignParameters')
params.Label='A0.4 dimensions - edit source JSON/script then rebuild'
params.addProperty('App::PropertyString','Status').Status=STATUS
params.addProperty('App::PropertyString','ParametersJSON').ParametersJSON=json.dumps(P)
parts={
    'FixedTray':(lower,'SLS nylon fixed tray with PCB cradle and hinge', '#255f78'),
    'MovingTray':(upper,'SLS nylon moving tray with center hinge knuckle', '#448ca3'),
    'FixedKeeper':(lower_keeper,'SLS nylon removable fixed core keeper', '#63b8c5'),
    'MovingKeeper':(upper_keeper,'SLS nylon removable moving core keeper', '#86cdd4'),
}
references={
    'FixedCore':(core,'Fair-Rite nominal fixed half', '#303a43'),
    'MovingCore':(moving_core,'Fair-Rite nominal moving half', '#53616d'),
    'Winding':(winding,'Continuous 5-turn wire route / assumed OD 0.4', '#e1a24c'),
    'PCB':(board,'A03 enlarged 36 x 28 PCB, actual outline and drill positions', '#35975d'),
    'SMAEnvelope':(sma,'SMA dimensional envelope, threads/details omitted', '#d3ba72'),
    'HingePin':(hinge_pin,'Nylon M3 hinge fastener simplified envelope', '#c6cdd1'),
    'HingeNut':(hinge_nut,'Nylon M3 hinge nut; no thread detail', '#acb8be'),
    'LatchScrew':(latch_screw,'Removable nylon M3 screw; no thread detail', '#d4dadd'),
    'LatchNut':(latch_nut,'Nylon M3 nut; no thread detail', '#acb8be'),
    'BackingPads':(Part.makeCompound(back_pads),'2 mm elastomer backing pads; fit trim TBD', '#abbb9c'),
    'RadialPads':(Part.makeCompound(radial_pads),'2 mm stock pads shown at nominal compressed thickness', '#8ba67b'),
    'FrontPads':(Part.makeCompound(front_pads),'1.5 mm stock pads shown at 1.3 mm closed thickness', '#8ba67b'),
    'KeeperScrews':(Part.makeCompound(keeper_screws),'4 x nylon M2x20 simplified envelopes', '#d4dadd'),
    'KeeperNuts':(Part.makeCompound(keeper_nuts),'4 x nylon M2 nuts simplified envelopes', '#acb8be'),
    'PCBScrews':(Part.makeCompound(pcb_screws),'2 x nylon M2x10 simplified envelopes', '#d4dadd'),
    'PCBNuts':(Part.makeCompound(pcb_nuts),'2 x nylon M2 nuts simplified envelopes', '#acb8be'),
}
mesh={}
def add(name,shape,label,color,category):
    obj=doc.addObject('PartDesign::Feature',name)
    obj.Label=label; obj.Shape=shape
    obj.addProperty('App::PropertyString','Status').Status=STATUS
    obj.addProperty('App::PropertyString','Category').Category=category
    obj.addProperty('App::PropertyString','DisplayColorHex').DisplayColorHex=color
    vertices,faces=shape.tessellate(.22)
    mesh[name]={'vertices':[list(v) for v in vertices],'triangles':faces,'label':label,'color':color,'category':category}
    return obj

for name,(shape,label,color) in parts.items():
    add(name,shape,label,color,'PRINTABLE_DRAFT')
    shape.exportStep(str(OUT/'parts'/f'{name}_DRAFT.step'))
    # Flat faces are exact; STL is tessellated at 0.10 mm linear / 0.15 rad angular.
    print_shape=shape.copy()
    bb=print_shape.BoundBox
    print_shape.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
    m=MeshPart.meshFromShape(Shape=print_shape,LinearDeflection=.10,AngularDeflection=.15,Relative=False)
    m.write(str(OUT/'parts'/f'{name}_DRAFT.stl'))
for name,(shape,label,color) in references.items(): add(name,shape,label,color,'REFERENCE')
coupon_obj=add('FitCoupon',coupon,'Print calibration coupon; hole diameters in parameters','#ccc5a5','PRINTABLE_DRAFT')
coupon_obj.Placement.Base=V(55,-45,0)
coupon.exportStep(str(OUT/'parts/FitCoupon_DRAFT.step'))
MeshPart.meshFromShape(Shape=coupon,LinearDeflection=.10,AngularDeflection=.15,Relative=False).write(str(OUT/'parts/FitCoupon_DRAFT.stl'))
gobj=doc.addObject('PartDesign::Feature','Gauge30_REFERENCE'); gobj.Shape=gauge
gobj.addProperty('App::PropertyString','Status').Status='REFERENCE - 30 mm target, not certified fit'
doc.recompute()
doc.saveAs(str(OUT/'RFCP_Clamp_A04_DRAFT.FCStd'))
Part.makeCompound([s for s,_,_ in list(parts.values())+list(references.values())]).exportStep(str(OUT/'RFCP_Clamp_A04_DRAFT.step'))
(OUT/'assembly_mesh.json').write_text(json.dumps(mesh),encoding='utf-8')

# Concrete geometric checks, deliberately separate from performance claims.
checks={}
def overlap(a,b): return a.common(b).Volume
def check_pair(name,a,b):
    checks[name]={'overlap_mm3':overlap(a,b),'minimum_distance_mm':a.distToShape(b)[0]}
check_pair('fixed_core_to_tray',core,lower)
check_pair('moving_core_to_tray',moving_core,upper)
check_pair('fixed_core_to_keeper',core,lower_keeper)
check_pair('moving_core_to_keeper',moving_core,upper_keeper)
check_pair('winding_to_core',winding,core)
check_pair('winding_to_fixed_tray',winding,lower)
check_pair('winding_to_fixed_keeper',winding,lower_keeper)
check_pair('pcb_to_tray',board,lower)
check_pair('pcb_to_sma',board,sma)
check_pair('hinge_pin_to_trays',hinge_pin,Part.makeCompound([lower,upper]))
check_pair('latch_screw_to_trays',latch_screw,Part.makeCompound([lower,upper]))
check_pair('keeper_fasteners_to_plastic',Part.makeCompound(keeper_screws+keeper_nuts),Part.makeCompound([lower,upper,lower_keeper,upper_keeper]))
check_pair('pcb_fasteners_to_tray_board',Part.makeCompound(pcb_screws+pcb_nuts),Part.makeCompound([lower,board]))
for name,(shape,_,_) in {**parts,**references}.items():
    if name not in ['BackingPads','RadialPads','FrontPads']:
        checks['gauge_to_'+name]={'overlap_mm3':overlap(gauge,shape),'minimum_distance_mm':gauge.distToShape(shape)[0]}

fixed_group=Part.makeCompound([lower,lower_keeper,core,board,sma,winding]+keeper_screws[:2]+keeper_nuts[:2]+pcb_screws+pcb_nuts)
moving_group=Part.makeCompound([upper,upper_keeper,moving_core,latch_nut]+keeper_screws[2:]+keeper_nuts[2:])
motion=[]
for angle in list(range(0,91,5)):
    s=moving_group.copy(); s.rotate(V(-40,0,0),V(0,0,1),angle)
    motion.append({'angle_deg':angle,'overlap_mm3':overlap(fixed_group,s)})
open90=moving_group.copy();open90.rotate(V(-40,0,0),V(0,0,1),90)
# Cable enters the exposed upper semicircle along +Y with the clamp open 90 deg.
cable_path=[]
for y in range(0,101,5):
    shifted=gauge.copy(); shifted.translate(V(0,y,0))
    cable_path.append({'gauge_center_y_mm':y,'overlap_mm3':overlap(Part.makeCompound([fixed_group,open90]),shifted)})

stop_samples=[]
for angle in [89,90,91,95]:
    m=upper.copy(); m.rotate(V(-40,0,0),V(0,0,1),angle)
    stop_samples.append({'angle_deg':angle,'overlap_mm3':overlap(stop,m),'minimum_distance_mm':stop.distToShape(m)[0]})
stop_function_pass=stop_samples[0]['overlap_mm3']<1e-5 and stop_samples[1]['overlap_mm3']<1e-5 and stop_samples[1]['minimum_distance_mm']<1e-5 and stop_samples[2]['overlap_mm3']>1e-3

all_shapes={k:v[0] for k,v in {**parts,**references}.items()}
report={
    'data_kind':'CALCULATED','status':STATUS,'freecad_version':A.Version(),
    'source_core_sha256':hashlib.sha256(core_source.read_bytes()).hexdigest(),
    'source_board_step_sha256':hashlib.sha256(board_source.read_bytes()).hexdigest(),
    'board_envelope':{'native_dielectric_step_thickness_mm':native_board_thickness,'nominal_finished_envelope_mm':1.6,'method':'Preserve native KiCad XY/drills; scale Z to nominal finished thickness for collision checking'},
    'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'geometry_sha256':hashlib.sha256((ROOT/'hardware/probe_head_A03/design_geometry.json').read_bytes()).hexdigest(),
    'parameters':P,
    'nominal_stop_samples':stop_samples,'nominal_stop_function_pass':stop_function_pass,
    'parts':{k:{'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume,'bbox_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]} for k,s in all_shapes.items()},
    'clearance_checks':checks,'hinge_motion_samples':motion,'cable_insertion_samples_90deg':cable_path,
    'lead_lengths_mm':[(coil_terminals[0]-start).Length,(coil_terminals[1]-pts[-1]).Length],
    'coupon_hole_diameters_left_to_right_mm':coupon_holes,
    'limitations':[
        'Nominal geometry only; core and printer tolerances are not a fit guarantee.',
        'Motion checked at 5 degree samples, not continuous swept-volume proof; screw removed before opening.',
        'Cable insertion checked at 5 mm samples for straight 30 mm circular gauge, not actual connector/boot.',
        'Thread, strength, fatigue, creep, latch force and pressure distribution not simulated or measured.',
        'Winding route assumes 0.4 mm OD and no actual bend-radius/insulation process qualification.',
        'Pads require measured fit and gentle preload; nothing may be inserted between ferrite mating faces.',
        'SMA model is an envelope only. PCB/solder/cable loads require physical strain-relief review.',
        'No electromagnetic, safety, surge, isolation or operating-temperature rating established.',
        'Audit open: legacy keeper holes/nut traps need tolerance redesign; larger head mounts alone do not qualify the whole clamp.',
        'Head PCB nut recess AF4.6 has fit allowance but retention at printer tolerance extremes is unqualified; bottom tool access must be retained.',
        'A02 dual-rail fixture insertion/removal path failed its independent audit. This head enlargement does not resolve that separate issue.'
    ]
}
report['nominal_checks_pass']=stop_function_pass and all(r['overlap_mm3']<1e-5 for r in checks.values()) and all(r['overlap_mm3']<1e-5 for r in motion+cable_path) and all(s.isValid() for s in all_shapes.values()) and all(len(s.Solids)==1 for s,_,_ in parts.values())
(OUT/'mechanical_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nominal_checks_pass':report['nominal_checks_pass'],'stop_samples':stop_samples,'overlaps':{k:v for k,v in checks.items() if v['overlap_mm3']>1e-5},'motion_collisions':[r for r in motion if r['overlap_mm3']>1e-5],'insertion_collisions':[r for r in cable_path if r['overlap_mm3']>1e-5],'invalid':[k for k,s in all_shapes.items() if not s.isValid()],'parts_solids':{k:len(s.Solids) for k,(s,_,_) in parts.items()}}),flush=True)
