"""Read-only KiCad validation of Fixture A04 current path and interface."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pcbnew as p


ROOT = Path(__file__).resolve().parents[1]
A03 = ROOT / "hardware" / "calibration_fixture_PCB_A03_DRAFT" / "RFCP_Fixture_Flat_A03_DRAFT.kicad_pcb"
A04_DIR = ROOT / "hardware" / "calibration_fixture_PCB_A04_DRAFT"
A04 = A04_DIR / "RFCP_Fixture_Flat_A04_DRAFT.kicad_pcb"
OUT = A04_DIR / "review" / "current_path_validation.json"


def edge_signature(board: p.BOARD) -> list[tuple]:
    rows = []
    for item in board.GetDrawings():
        if item.GetLayer() != p.Edge_Cuts:
            continue
        start, end = item.GetStart(), item.GetEnd()
        row = [int(item.GetShape()), round(p.ToMM(start.x), 6), round(p.ToMM(start.y), 6),
               round(p.ToMM(end.x), 6), round(p.ToMM(end.y), 6)]
        if item.GetShape() == p.SHAPE_T_ARC:
            middle = item.GetArcMid()
            row += [round(p.ToMM(middle.x), 6), round(p.ToMM(middle.y), 6)]
        rows.append(tuple(row))
    return sorted(rows)


def zone_contains(board: p.BOARD, net: str, layer: int, x_model: float, y_model: float) -> bool:
    point = p.VECTOR2I(p.FromMM(x_model + 72), p.FromMM(y_model + 46.35))
    for zone in board.Zones():
        if zone.GetNetname() == net and zone.GetLayer() == layer:
            if zone.GetFilledPolysList(layer).Contains(point):
                return True
    return False


def pads(board: p.BOARD, reference: str) -> list[dict]:
    fp = next(fp for fp in board.GetFootprints() if fp.GetReference() == reference)
    rows = []
    for pad in fp.Pads():
        pos = pad.GetPosition()
        rows.append({
            "number": pad.GetNumber(),
            "x_mm": p.ToMM(pos.x),
            "y_mm": p.ToMM(pos.y),
            "drill_mm": p.ToMM(pad.GetDrillSize().x),
            "net": pad.GetNetname(),
        })
    return rows


old = p.LoadBoard(str(A03))
board = p.LoadBoard(str(A04))
checks: dict[str, object] = {}
checks["four_copper_layers"] = board.GetCopperLayerCount() == 4
checks["external_outline_identical_to_A03"] = edge_signature(board) == edge_signature(old)
checks["board_thickness_mm"] = p.ToMM(board.GetDesignSettings().GetBoardThickness())

for reference in ["J1", "J2"]:
    rows = pads(board, reference)
    checks[f"{reference}_centre_drill_1p70"] = all(abs(r["drill_mm"] - 1.7) < 1e-6 for r in rows if r["number"] == "1")
    checks[f"{reference}_ground_drill_1p90"] = all(abs(r["drill_mm"] - 1.9) < 1e-6 for r in rows if r["number"] == "2")

layers = {"F.Cu": p.F_Cu, "In1.Cu": p.In1_Cu, "In2.Cu": p.In2_Cu, "B.Cu": p.B_Cu}
core_samples = []
for y_model in [-6.35, -4, 0, 4, 6.35]:
    for x_model in [-14, -8, -3, 0, 3, 8, 14]:
        gnd = {name: zone_contains(board, "/GND", layer, x_model, y_model)
               for name, layer in layers.items()}
        sig = zone_contains(board, "/SIG", p.F_Cu, x_model, y_model)
        core_samples.append({"x_model_mm": x_model, "y_model_mm": y_model,
                             "F_SIG": sig, "GND": gnd})
checks["no_GND_copper_inside_30mm_aperture_over_core_axial_span"] = not any(
    any(row["GND"].values()) for row in core_samples
)
checks["L1_SIG_continuous_at_core_axis"] = all(
    zone_contains(board, "/SIG", p.F_Cu, 0, yy) for yy in [-6.35, -4, 0, 4, 6.35]
)
checks["no_BCu_SIG_zone"] = not any(z.GetNetname() == "/SIG" and z.GetLayer() == p.B_Cu for z in board.Zones())

plane_edge_samples = []
for y_model in [-8.9, -7.6, -7.51, -7.49, 7.49, 7.51, 7.6, 8.9]:
    plane_edge_samples.append({
        "y_model_mm": y_model,
        "In1_GND_at_x0": zone_contains(board, "/GND", p.In1_Cu, 0, y_model),
        "In2_GND_at_x0": zone_contains(board, "/GND", p.In2_Cu, 0, y_model),
        "F_SIG_at_x0": zone_contains(board, "/SIG", p.F_Cu, 0, y_model),
    })
checks["inner_plane_cut_edges_at_plus_minus_7p50"] = (
    all(row["In1_GND_at_x0"] and row["In2_GND_at_x0"] for row in plane_edge_samples if abs(row["y_model_mm"]) > 7.5)
    and all(not row["In1_GND_at_x0"] and not row["In2_GND_at_x0"] for row in plane_edge_samples if abs(row["y_model_mm"]) < 7.5)
)
checks["nominal_core_face_guard_mm"] = 7.5 - 6.35
checks["max_thickness_centred_core_face_guard_mm"] = 7.5 - (12.7 + 0.635) / 2

drc = json.loads((A04_DIR / "review" / "drc.json").read_text(encoding="utf-8"))
erc = json.loads((A04_DIR / "review" / "erc.json").read_text(encoding="utf-8"))
checks["DRC_violations"] = len(drc["violations"])
checks["DRC_unconnected"] = len(drc["unconnected_items"])
checks["DRC_schematic_parity"] = len(drc["schematic_parity"])
checks["ERC_violations"] = sum(len(sheet["violations"]) for sheet in erc["sheets"])

boolean_checks = {key: value for key, value in checks.items() if isinstance(value, bool)}
passed = (all(boolean_checks.values()) and checks["DRC_violations"] == 0
          and checks["DRC_unconnected"] == 0 and checks["DRC_schematic_parity"] == 0
          and checks["ERC_violations"] == 0 and abs(checks["board_thickness_mm"] - 1.6) < 1e-6)
report = {
    "classification": "CALCULATED_CAD_CURRENT_PATH_AUDIT_NOT_MEASURED",
    "pass": passed,
    "checks": checks,
    "core_samples": core_samples,
    "plane_edge_samples": plane_edge_samples,
    "source": str(A04.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(A04.read_bytes()).hexdigest(),
    "baseline_A03_sha256": hashlib.sha256(A03.read_bytes()).hexdigest(),
    "kicad": p.GetBuildVersion(),
    "limitations": [
        "Filled-zone point tests verify saved nominal copper, not etch/registration tolerance.",
        "The 15.0 mm cut leaves 0.8325 mm per face for a centred maximum-thickness core; physical placement must be checked.",
        "This check does not establish S-parameters or calibration accuracy.",
    ],
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"pass": passed, "checks": checks}, indent=2))
if not passed:
    raise SystemExit(1)
