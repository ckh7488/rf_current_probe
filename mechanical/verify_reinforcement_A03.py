"""A0.3 added-material/fit/wall checks against saved A0.2 and fixture CAD."""
from pathlib import Path
import hashlib, json, math
import FreeCAD as A
import Part

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/clamp_A03_DRAFT'
V=A.Vector
old_path=ROOT/'mechanical/clamp_A02_DRAFT/RFCP_Clamp_A02_DRAFT.FCStd'
new_path=OUT/'RFCP_Clamp_A03_DRAFT.FCStd'
jig_path=ROOT/'hardware/calibration_fixture/F_A_A01_DRAFT/RFCP_F_A_A01_DRAFT.FCStd'
paths=[old_path,new_path,jig_path]
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
old,new,jig=[A.openDocument(str(p)) for p in paths]
checks=[]
def check(name,value,limit=1e-5):
    checks.append({'name':name,'value':value,'pass':abs(value)<limit})
def hexprism(x,y,z,af,h):
    r=af/math.sqrt(3)
    p=[V(x+r*math.cos(math.pi/6+i*math.pi/3),y+r*math.sin(math.pi/6+i*math.pi/3),z) for i in range(6)]
    return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
for obj in old.Objects:
    if not hasattr(obj,'Shape') or obj.Name in ['FixedTray','MovingTray']: continue
    a=obj.Shape; b=new.getObject(obj.Name).Shape
    check('unchanged_'+obj.Name,a.cut(b).Volume+b.cut(a).Volume)
local=[]
for name,sy in [('FixedTray',1),('MovingTray',-1)]:
    a=old.getObject(name).Shape; b=new.getObject(name).Shape
    removed=a.cut(b)
    allowed_fin=Part.makeBox(20.6,17.0,10,V(-10.3,-48.3,8))
    check(name+'_no_unintended_removed_material',removed.cut(allowed_fin).Volume if name=='FixedTray' else removed.Volume)
    allowed=[]
    for sx in [-1,1]:
        x=sx*24; y=sy*-25
        boss=Part.makeCylinder(4.2,3,V(x,y,-3))
        allowed.append(boss)
        trap=hexprism(x,y,-3,4.1,1.8)
        bore=Part.makeCylinder(1.1,4,V(x,y,-3))
        expected=boss.cut(trap).cut(bore)
        check(f'{name}_{sx}_complete_boss_wall_and_roof',expected.cut(b).Volume)
        p=V(sx*26.05,sy*-25.4,-2.1)
        n=V(sx*21.5,sy*-17.5,0);n.normalize()
        segments=b.common(Part.makeLine(p-n*.2,p+n*5)).Edges
        assert len(segments)==1
        local.append({'part':name,'point_mm':list(p),'old_local_mm':0.44820269284239705,'new_local_mm':segments[0].Length})
    check(name+'_addition_outside_allowed_bosses',b.cut(a).cut(Part.makeCompound(allowed)).Volume)

fixture_shapes=[o.Shape for o in jig.Objects if hasattr(o,'Shape') and not o.Name.startswith('Head_')]
fixture=Part.makeCompound(fixture_shapes)
head_names=['FixedTray','MovingTray','FixedKeeper','MovingKeeper','FixedCore','MovingCore','Winding','PCB','SMAEnvelope']
head=Part.makeCompound([new.getObject(n).Shape for n in head_names])
check('new_head_to_unchanged_fixture_overlap',head.common(fixture).Volume)
moving_names=['MovingTray','MovingKeeper','MovingCore','LatchNut']
pieces=[new.getObject(n).Shape for n in moving_names]
for name in ['KeeperScrews','KeeperNuts','BackingPads','RadialPads','FrontPads']:
    pieces.extend(s for s in new.getObject(name).Shape.Solids if s.CenterOfMass.y>0)
moving=Part.makeCompound(pieces)
motion=[]
for angle in range(0,91,5):
    q=moving.copy();q.rotate(V(-40,0,0),V(0,0,1),angle)
    volume=q.common(fixture).Volume
    motion.append({'angle_deg':angle,'overlap_mm3':volume})
    check('fixture_motion_'+str(angle),volume)
unchanged=all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in paths)
assert unchanged
r={'data_kind':'CALCULATED','source_hashes':hashes,'source_files_unchanged':unchanged,
   'checks':checks,'old_wall_sample_comparison':local,'fixture_motion':motion,
   'nut_trap_radial_wall_lower_bound_mm':4.2-4.1/math.sqrt(3),
   'nut_trap_roof_thickness_mm':1.2,
   'all_pass':all(c['pass'] for c in checks),
   'limits':['Boss containment proves only the reinforced nut-trap wall/roof; not a global wall-thickness certificate.',
             'Nominal geometry and 5-degree motion samples; not continuous motion, strength, print tolerance or physical fit.',
             'JLC re-review is still required; no risk acceptance, fabrication or RF testing.']}
(OUT/'reinforcement_checks.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_pass':r['all_pass'],'checks':len(checks),'local_wall_comparison':local,'failed':[c for c in checks if not c['pass']]}),flush=True)
assert r['all_pass']
