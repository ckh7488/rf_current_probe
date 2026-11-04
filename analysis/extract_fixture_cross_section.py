"""Read-only extraction from the saved, filled KiCad board (KiCad Python)."""
from pathlib import Path
import json,hashlib
import pcbnew as p
R=Path(__file__).resolve().parents[1]
P=R/'hardware/calibration_fixture_PCB_A02/RFCP_Fixture_Flat_A02_DRAFT.kicad_pcb'
b=p.LoadBoard(str(P)); rows=[]; y=p.FromMM(47)
for z in b.Zones():
 f=z.GetFilledPolysList(z.GetLayer()); intervals=[]; start=None; previous=None
 for i in range(100001):
  x=144*i/100000;inside=f.Contains(p.VECTOR2I(p.FromMM(x),y))
  if inside and start is None:start=x
  if not inside and start is not None:intervals.append([start-72,previous-72]);start=None
  previous=x
 if start is not None:intervals.append([start-72,previous-72])
 rows.append(dict(net=z.GetNetname(),layer=z.GetLayer(),x_intervals_mm=intervals))
d=dict(kind='CAD_EXTRACTED',kicad_version=p.GetBuildVersion(),board_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),scan_z_mm=7,scan_step_mm=.00144,rows=rows)
(R/'reviews/fixture_impedance_20260918/cad_cross_section.json').write_text(json.dumps(d,indent=2))
print(json.dumps(d))
