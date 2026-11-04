"""Run with FreeCADCmd. Read-only inspection of extracted manufacturer STEP."""
import json
from pathlib import Path
import FreeCAD as App
import Part

root = Path(__file__).resolve().parents[1]
shape = Part.read(str(root / 'docs/references/2644181281.STEP'))
box = shape.BoundBox
data = {'data_kind': 'CALCULATED', 'source': 'Manufacturer nominal STEP; no physical measurement',
        'freecad_version': App.Version(), 'valid_shape': shape.isValid(), 'solids': len(shape.Solids),
        'bounding_box_mm': {k: getattr(box, k) for k in ['XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax', 'XLength', 'YLength', 'ZLength']},
        'volume_mm3': shape.Volume,
        'planar_faces': []}
for face in shape.Faces:
    if isinstance(face.Surface, Part.Plane):
        data['planar_faces'].append({'area_mm2': face.Area, 'center_mm': list(face.CenterOfMass), 'normal': list(face.normalAt(0, 0))})
(root / 'mechanical/manufacturer_step_inspection.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
print(json.dumps(data), flush=True)
