"""Reopen the saved placement document and inspect serialized geometry."""
import json
from pathlib import Path
import FreeCAD as App

folder = Path(__file__).resolve().parent
doc = App.openDocument(str(folder / 'RFCP_layout_DRAFT.FCStd'))
expected = ['FixedCore', 'MovingCore', 'Gauge30', 'WindingSpace', 'PCBRegion', 'HingeRegion', 'LatchRegion']
assert sorted(o.Name for o in doc.Objects) == sorted(expected)
assert all(doc.getObject(name).Shape.isValid() for name in expected)
assert all(doc.getObject(name).Status == 'DRAFT — NOT FOR FABRICATION' for name in expected)
assert doc.FixedCore.Shape.common(doc.Gauge30.Shape).Volume < 1e-6
assert doc.MovingCore.Shape.common(doc.Gauge30.Shape).Volume < 1e-6
result = {'data_kind': 'CALCULATED', 'saved_document_reopened': True, 'objects': expected,
          'valid_serialized_shapes': True, 'status_labels_present': True,
          'note': 'Placement-only verification; not a manufactured housing or kinematic test.'}
(folder / 'saved_layout_verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result), flush=True)
App.closeDocument(doc.Name)
