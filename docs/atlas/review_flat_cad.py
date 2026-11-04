"""Independent read-only checks of saved A02 assembly. Run with FreeCADCmd."""
from pathlib import Path
import json,hashlib
import FreeCAD as A
import Part

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/atlas/review/a02-design'
V=A.Vector
paths={'A01':ROOT/'hardware/calibration_fixture_PCB_A01/assembly/RFCP_F_A_PCB_A01_DRAFT.FCStd',
       'A02':ROOT/'hardware/calibration_fixture_PCB_A02/assembly/RFCP_Flat_Fixture_A02_DRAFT.FCStd'}
docs={k:A.openDocument(str(p)) for k,p in paths.items()}
doc=docs['A02']
shape=lambda n:doc.getObject(n).Shape
compound=lambda names:Part.makeCompound([shape(n) for n in names])
pcb=compound(['FlatPCB','SignalCopper','ReturnCopper'])
head_names=[o.Name for o in doc.Objects if o.Name.startswith('Head_')]
head=compound(head_names)

# Check all copper inside the entire 12.7 mm core aperture length, not just one slice.
aperture=Part.makeCylinder(15,12.7,V(0,0,0),V(0,0,1))
aperture_checks={n:{'common_volume_mm3':shape(n).common(aperture).Volume,
                     'valid':shape(n).isValid(),'solids':len(shape(n).Solids)}
                 for n in ['SignalCopper','ReturnCopper']}
assert aperture_checks['SignalCopper']['common_volume_mm3']>0
assert aperture_checks['ReturnCopper']['common_volume_mm3']<1e-8
assert shape('SignalCopper').common(shape('ReturnCopper')).Volume<1e-8

moving_names=['Head_MovingTray','Head_MovingKeeper','Head_MovingCore','Head_LatchNut']
moving=[shape(n) for n in moving_names]
for n in ['Head_KeeperScrews','Head_KeeperNuts','Head_BackingPads','Head_RadialPads','Head_FrontPads']:
    moving.extend(s for s in shape(n).Solids if s.CenterOfMass.y>0)
moving=Part.makeCompound(moving)
fixed=Part.makeCompound([o.Shape for o in doc.Objects if hasattr(o,'Shape') and not o.Name.startswith('Head_')])
# Additional check: keep two assumed mating-plug envelopes fitted during opening.
plugs=Part.makeCompound([Part.makeCylinder(6,30,V(0,9.2,z),V(0,1,0)) for z in [-28,40.7]])
fixed_with_plugs=Part.makeCompound([fixed,plugs])
motion=[]
for deg in range(0,91,5):
    m=moving.copy();m.rotate(V(-40,0,0),V(0,0,1),deg)
    v=m.common(fixed_with_plugs).Volume;dist=m.distToShape(fixed_with_plugs)[0]
    motion.append({'degrees':deg,'overlap_mm3':v,'clearance_mm':dist})
    assert v<1e-7
    print('Angle',deg,'clearance',round(dist,5),flush=True)

closed={'overlap_mm3':pcb.common(head).Volume,'clearance_mm':pcb.distToShape(head)[0]}
assert closed['overlap_mm3']<1e-7
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unchanged={n:abs(docs['A01'].getObject(n).Shape.Volume-shape(n).Volume)<1e-8 for n in ['Base','HeadBracket']}
assert all(unchanged.values())
result={'data_kind':'CALCULATED','method':'Independent checks on saved FreeCAD assemblies; no regeneration or fabrication changes.',
    'source_sha256':{k:sha(p) for k,p in paths.items()},'freecad_version':A.Version()[:3],
    'aperture_cylinder_mm':{'radius':15,'z_start':0,'length':12.7},'aperture_copper':aperture_checks,
    'signal_return_clearance_mm':shape('SignalCopper').distToShape(shape('ReturnCopper'))[0],
    'closed_pcb_head':closed,'motion_with_two_assumed_plugs':motion,
    'plug_assumption':{'diameter_mm':12,'length_mm':30,'axis':'+Y','start_y_mm':9.2},
    'retained_support_volume_match_A01':unchanged,
    'base_screw_comparison_mm':{'female_depth_nominal':10,'existing_M3x12_engagement':9.4,'existing_end_margin':.6,'candidate_M3x10_engagement':7.4,'candidate_end_margin':2.6},
    'limitations':['Nominal geometry; no tolerance, load/torque/creep, solder or RF checks.',
        'Motion sampled every 5 degrees, not a continuous sweep.',
        'Plug envelopes are assumptions, not actual purchased cable dimensions.',
        'M3x10 alternative is arithmetic only, not substituted into the CAD.'], 'pass':True}
(OUT/'independent-cad.json').write_text(json.dumps(result,indent=2)+'\n')
for d in docs.values():A.closeDocument(d.Name)
print('INDEPENDENT_CAD_COMPLETE',flush=True)
