"""Read-only local wall samples on A0.2 STEP; not a full DFM certification."""
from pathlib import Path
import hashlib
import json
import math
import FreeCAD as A
import Part

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/clamp_A02_DRAFT'
samples = []
sources = {}
for name, sign_y in [('FixedTray', 1), ('MovingTray', -1)]:
    path = OUT / 'parts' / (name + '_DRAFT.step')
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    shape = Part.read(str(path))
    for sign_x in [-1, 1]:
        # Bottom nut trap has AF 4.1 mm, right flank x=24+2.05.
        # Probe toward the diagonal outside wall at z=-2.1 mm.
        p = A.Vector(sign_x * 26.05, sign_y * -25.4, -2.1)
        n = A.Vector(sign_x * 21.5, sign_y * -17.5, 0)
        n.normalize()
        ray = Part.makeLine(p - n * .2, p + n * 5)
        material = shape.common(ray)
        edges = [{'length_mm': edge.Length,
                  'endpoints_mm': [list(v.Point) for v in edge.Vertexes]}
                 for edge in material.Edges]
        expected = (1017 - (21.5 * 26.05 - 17.5 * -25.4)) / math.hypot(21.5, 17.5)
        assert len(edges) == 1 and abs(edges[0]['length_mm'] - expected) < 1e-5
        samples.append({'part': name, 'sample_point_mm': list(p),
                        'direction': list(n), 'material_segments': edges,
                        'analytic_thickness_mm': expected,
                        'under_0_8_mm': edges[0]['length_mm'] < .8})
    assert before == hashlib.sha256(path.read_bytes()).hexdigest()
    sources[name] = {'step_sha256': before,
                    'stl_sha256': hashlib.sha256(path.with_suffix('.stl').read_bytes()).hexdigest()}
report = {'data_kind': 'CALCULATED', 'freecad_version': A.Version(),
          'status': 'DRAFT - NOT FOR FABRICATION', 'source_files': sources,
          'samples': samples,
          'limitations': ['Four local line/solid intersection samples, not a global minimum wall search.',
                         'JLC warning dialog provides no coordinates; correspondence with its detected location is unconfirmed.',
                         'No physical strength, manufacturing tolerance or printed fit validation.',
                         'No source geometry, submitted order or risk-acceptance choice changed.']}
(OUT / 'wall_audit_20260917.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report), flush=True)
