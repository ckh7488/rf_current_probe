"""FreeCADCmd: nominal core pair and placement study, NOT manufacturing geometry.

All additional boxes are allocation volumes, not working hinge/latch/PCB designs.
"""
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part

root = Path(__file__).resolve().parents[1]
source = root / 'docs/references/2644181281.STEP'
doc = App.newDocument('RFCP_Layout_DRAFT')
core = Part.read(str(source))
upper = core.copy()
upper.rotate(App.Vector(0, 0, 6.35), App.Vector(1, 0, 0), 180)
gauge = Part.makeCylinder(15, 30, App.Vector(0, 0, -8))
items = [
    ('FixedCore', 'Manufacturer nominal lower core', core),
    ('MovingCore', 'Manufacturer nominal upper core', upper),
    ('Gauge30', '30 mm target gauge - reference only', gauge),
    ('WindingSpace', 'Winding allocation - not wire routing', Part.makeBox(24, 18, 15.7, App.Vector(-12, -34.3, -1.5))),
    ('PCBRegion', 'PCB allocation 16 x 10 mm - footprint TBD', Part.makeBox(16, 10, 1.6, App.Vector(-8, -45.3, 5.55))),
    ('HingeRegion', 'Nonconductive hinge allocation - kinematics TBD', Part.makeBox(12, 16, 20, App.Vector(-45, -8, -3.65))),
    ('LatchRegion', 'Cam latch allocation - kinematics TBD', Part.makeBox(12, 16, 20, App.Vector(33, -8, -3.65))),
]
mesh = {}
for name, label, shape in items:
    obj = doc.addObject('PartDesign::Feature', name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty('App::PropertyString', 'Status').Status = 'DRAFT — NOT FOR FABRICATION'
    vertices, faces = shape.tessellate(0.3)
    mesh[name] = {'vertices': [list(v) for v in vertices], 'triangles': faces, 'label': label}
doc.recompute()
result = {'data_kind': 'CALCULATED', 'status': 'DRAFT — NOT FOR FABRICATION',
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'source_is_nominal': True, 'target_aperture_mm': 30,
          'bare_core_to_gauge_min_distance_mm': min(core.distToShape(gauge)[0], upper.distToShape(gauge)[0]),
          'bare_core_gauge_overlap_mm3': core.common(gauge).Volume + upper.common(gauge).Volume,
          'winding_allocation_to_gauge_distance_mm': items[3][2].distToShape(gauge)[0],
          'winding_allocation_gauge_overlap_mm3': items[3][2].common(gauge).Volume,
          'core_pair_overlap_mm3': core.common(upper).Volume,
          'all_shapes_valid': all(s.isValid() for _, _, s in items),
          'limitations': ['No core tolerances, actual winding, insulation or closed housing fit verified',
                         'No hinge motion, force, latch, retention or fabrication detail',
                         'Allocation volumes may overlap cores intentionally; not assembled manufactured solids']}
assert result['bare_core_gauge_overlap_mm3'] < 1e-6
assert result['winding_allocation_gauge_overlap_mm3'] < 1e-6
assert result['all_shapes_valid']
doc.saveAs(str(root / 'mechanical/RFCP_layout_DRAFT.FCStd'))
(root / 'mechanical/layout_check_calculated.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
(root / 'mechanical/layout_mesh.json').write_text(json.dumps(mesh), encoding='utf-8')
print(json.dumps(result), flush=True)
