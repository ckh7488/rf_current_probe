"""Compare A03/A04 exported board solids; run with FreeCADCmd 1.0."""
from pathlib import Path
import hashlib
import json
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
a03_path = ROOT / "hardware/calibration_fixture_PCB_A03_DRAFT/review/board_only.step"
a04_path = ROOT / "hardware/calibration_fixture_PCB_A04_DRAFT/review/board_only.step"
out = ROOT / "hardware/calibration_fixture_PCB_A04_DRAFT/review/mechanical_interface.json"
a03 = Part.read(str(a03_path))
a04 = Part.read(str(a04_path))
common = a03.common(a04)
relative_delta = (a03.Volume + a04.Volume - 2 * common.Volume) / max(a03.Volume, a04.Volume)
def bounds(shape):
    bb = shape.BoundBox
    return [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax]
report = {
    "classification": "CALCULATED_STEP_BOOLEAN_NOT_PHYSICAL_FIT",
    "pass_external_solid_identical": relative_delta < 1e-10,
    "A03_volume_mm3": a03.Volume,
    "A04_volume_mm3": a04.Volume,
    "common_volume_mm3": common.Volume,
    "relative_symmetric_difference": relative_delta,
    "A03_bounds_mm": bounds(a03),
    "A04_bounds_mm": bounds(a04),
    "A03_sha256": hashlib.sha256(a03_path.read_bytes()).hexdigest(),
    "A04_sha256": hashlib.sha256(a04_path.read_bytes()).hexdigest(),
    "freecad": App.Version()[:3],
    "meaning": "PCB exterior, routed windows, all holes and nominal thickness match; copper stack is not represented in this board-only solid.",
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if not report["pass_external_solid_identical"]:
    raise SystemExit(1)
