"""Saved CAD connection-access rehearsal. Assumed envelopes, not mating CAD."""
from pathlib import Path
import hashlib
import json
import FreeCAD as A
import Part

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/clamp_A01_DRAFT'
path = OUT / 'RFCP_Clamp_A01_DRAFT.FCStd'
doc = A.openDocument(str(path))
V = A.Vector
fixed = Part.makeCompound([doc.getObject(n).Shape for n in ['FixedTray', 'FixedKeeper', 'FixedCore']])
moving = Part.makeCompound([doc.getObject(n).Shape for n in ['MovingTray', 'MovingKeeper', 'MovingCore']])
housing = Part.makeCompound([fixed, moving])
def collision(a, b):
    return {'overlap_mm3': a.common(b).Volume, 'minimum_distance_mm': a.distToShape(b)[0]}

# R4.7 encloses the nominal 7.92 mm AF VAT coupling hex. Axial ranges
# intentionally overlap the keeper: actual male thread engagement is unknown.
# No collision with the SMA jack itself is tested (mating overlap is intentional).
plugs = {}
for name, radius in [('slim_coupling_assumption', 4.7), ('large_body_low_assumption', 6.0)]:
    envelope = Part.makeCylinder(radius, 35, V(0, -41, 8))
    plugs[name] = dict(radius_mm=radius, z_span_mm=[8, 43], **collision(housing, envelope))
raised = Part.makeCylinder(6, 35, V(0, -41, 17.0))
plugs['large_body_above_keeper_assumption'] = dict(radius_mm=6, z_span_mm=[17, 52], **collision(housing, raised))

# F-A current axis is Z. Review copper-only assumed shapes; no SMA launches,
# fasteners or endplate solids are present in the current fixture concept.
center = Part.makeBox(8, .5, 60, V(-4, -.25, -23.65))
returns = Part.makeCompound([Part.makeBox(10, .5, 60, V(x, -.25, -23.65)) for x in [-60, 50]])
fixture = Part.makeCompound([center, returns])
motion = []
for angle in range(0, 121, 5):
    body = moving.copy()
    body.rotate(V(-40, 0, 0), V(0, 0, 1), angle)
    motion.append(dict(angle_deg=angle, **collision(body, fixture)))
result = {'data_kind': 'CALCULATED', 'status': 'DRAFT - NOT FOR FABRICATION',
          'native_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'plug_envelopes': plugs, 'fixture_closed': collision(housing, fixture),
          'fixture_opening_samples': motion,
          'limitations': ['Assumed envelopes only; actual connector engagement/tool access/strain relief unverified.',
                         'Copper-only fixture. Endplates, SMA launches, support and complete insertion route unverified.',
                         'Collision results are not a physical force, tolerance or RF simulation.']}
(OUT / 'connection_access_review.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result), flush=True)
