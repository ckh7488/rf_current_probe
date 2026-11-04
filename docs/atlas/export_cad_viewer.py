"""Package the saved CAD tessellation without remodelling or decimation."""
import hashlib
import argparse
import json
import shutil
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--atlas', type=Path, default=Path(r"C:\Users\artzy\Documents\ChatGPT\test_board\showcase"))
args = parser.parse_args()
design = json.loads((ROOT / 'docs/atlas/source/design.json').read_text(encoding='utf-8'))
ATLAS = args.atlas
REPORT = ATLAS / "reports/rf-current-probe"
SOURCE = ROOT / design['fixture']['cad_source']
asset = design['fixture']['asset']
model = json.loads(SOURCE.read_text())
chunks, parts, offset, maximum_error = [], [], 0, 0.0
for name, part in model.items():
    original = np.asarray(part["vertices"], dtype=np.float64)
    vertices = original.astype("<f4")
    maximum_error = max(maximum_error, float(np.abs(original - vertices).max()))
    triangles = np.asarray(part["triangles"], dtype="<u4")
    vb, tb = vertices.tobytes(), triangles.tobytes()
    parts.append(dict(name=name, color=part["color"], category=part["category"],
                      vertex_offset=offset, vertex_count=len(vertices),
                      index_offset=offset+len(vb), index_count=triangles.size,
                      bounds=[original.min(axis=0).tolist(), original.max(axis=0).tolist()]))
    chunks.extend([vb, tb]); offset += len(vb)+len(tb)
binary = b"".join(chunks)
target = REPORT / 'assets' / (asset + '.bin')
target.write_bytes(binary)
metadata = dict(format="RFCP CAD indexed mesh v1", units="mm", binary=asset + '.bin',
                source=design['fixture']['cad_source'],
                source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                binary_sha256=hashlib.sha256(binary).hexdigest(),
                precision="float32 position; uint32 triangle indices; little endian",
                maximum_coordinate_rounding_mm=maximum_error,
                triangle_count=sum(len(p["triangles"]) for p in model.values()),
                geometry_reduction=False, parts=parts)
(REPORT / 'assets' / (asset + '.json')).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
(REPORT / "vendor").mkdir(exist_ok=True)
for filename in ["three.min.js", "OrbitControls.js", "LICENSE-three.txt"]:
    if not (REPORT / 'vendor' / filename).exists():
        shutil.copy2(ATLAS / "reports/porta-pcb/vendor" / filename, REPORT / "vendor" / filename)
print(json.dumps({k: v for k, v in metadata.items() if k != "parts"}, indent=2))
print("Parts:", len(parts), "Binary bytes:", len(binary))
