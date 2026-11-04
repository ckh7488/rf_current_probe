"""Read-only KiCad validation of Fixture A05 current path and interfaces."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pcbnew as p


ROOT = Path(__file__).resolve().parents[1]
A04 = ROOT / "hardware/calibration_fixture_PCB_A04_DRAFT/RFCP_Fixture_Flat_A04_DRAFT.kicad_pcb"
A05_DIR = ROOT / "hardware/calibration_fixture_PCB_A05_DRAFT"
A05 = A05_DIR / "RFCP_Fixture_Flat_A05_DRAFT.kicad_pcb"
OUT = A05_DIR / "review/current_path_validation.json"


def zone_contains(board: p.BOARD, net: str, layer: int,
                  x_model: float, y_model: float) -> bool:
    point = p.VECTOR2I(p.FromMM(x_model + 72), p.FromMM(y_model + 46.35))
    return any(z.GetNetname() == net and z.GetLayer() == layer
               and z.GetFilledPolysList(layer).Contains(point)
               for z in board.Zones())


def pads(board: p.BOARD, reference: str) -> list[dict]:
    fp = next(fp for fp in board.GetFootprints() if fp.GetReference() == reference)
    return [{
        "number": pad.GetNumber(),
        "x_mm": p.ToMM(pad.GetPosition().x),
        "y_mm": p.ToMM(pad.GetPosition().y),
        "drill_mm": p.ToMM(pad.GetDrillSize().x),
        "net": pad.GetNetname(),
    } for pad in fp.Pads()]


def outline_bounds(board: p.BOARD) -> list[list[float]]:
    poly = p.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(poly, False)
    rows = []
    for i in range(poly.OutlineCount()):
        ring = poly.COutline(i)
        xs = [p.ToMM(ring.CPoint(j).x)-72 for j in range(ring.PointCount())]
        ys = [p.ToMM(ring.CPoint(j).y)-46.35 for j in range(ring.PointCount())]
        rows.append([min(xs), max(xs), min(ys), max(ys)])
        for k in range(poly.HoleCount(i)):
            hole = poly.CHole(i, k)
            xs = [p.ToMM(hole.CPoint(j).x)-72 for j in range(hole.PointCount())]
            ys = [p.ToMM(hole.CPoint(j).y)-46.35 for j in range(hole.PointCount())]
            rows.append([min(xs), max(xs), min(ys), max(ys)])
    return sorted(rows)


def main() -> None:
    old = p.LoadBoard(str(A04))
    board = p.LoadBoard(str(A05))
    checks: dict[str, object] = {}
    checks["four_copper_layers"] = board.GetCopperLayerCount() == 4
    checks["board_thickness_mm"] = p.ToMM(board.GetDesignSettings().GetBoardThickness())
    bounds = outline_bounds(board)
    checks["outer_board_144x92p7_mm"] = any(
        abs(row[0]+72) < 1e-3 and abs(row[1]-72) < 1e-3
        and abs(row[2]+46.35) < 1e-3 and abs(row[3]-46.35) < 1e-3
        for row in bounds)
    checks["two_close_return_windows"] = sum(
        abs(row[2]+16.1) < 1e-3 and abs(row[3]-17.65) < 1e-3
        and ((abs(row[0]+34) < 1e-3 and abs(row[1]+15.5) < 1e-3)
             or (abs(row[0]-15.5) < 1e-3 and abs(row[1]-34) < 1e-3))
        for row in bounds) == 2
    checks["outline_intentionally_differs_from_A04"] = bounds != outline_bounds(old)

    for reference in ["J1", "J2"]:
        rows = pads(board, reference)
        checks[f"{reference}_centre_drill_1p70"] = all(
            abs(r["drill_mm"]-1.7) < 1e-6 for r in rows if r["number"] == "1")
        checks[f"{reference}_ground_drill_1p90"] = all(
            abs(r["drill_mm"]-1.9) < 1e-6 for r in rows if r["number"] == "2")

    layers = {"F.Cu": p.F_Cu, "In1.Cu": p.In1_Cu,
              "In2.Cu": p.In2_Cu, "B.Cu": p.B_Cu}
    core_samples = []
    for y_model in [-6.35, -4, 0, 4, 6.35]:
        for x_model in [-14, -8, -3, 0, 3, 8, 14]:
            core_samples.append({
                "x_model_mm": x_model,
                "y_model_mm": y_model,
                "F_SIG": zone_contains(board, "/SIG", p.F_Cu, x_model, y_model),
                "GND": {name: zone_contains(board, "/GND", layer, x_model, y_model)
                        for name, layer in layers.items()},
            })
    checks["no_GND_inside_30mm_aperture_over_core_span"] = not any(
        any(row["GND"].values()) for row in core_samples)
    checks["SIG_continuous_at_core_axis"] = all(
        row["F_SIG"] for row in core_samples if row["x_model_mm"] == 0)
    checks["30mm_SIG_present_at_core_midplane"] = all(
        row["F_SIG"] for row in core_samples if row["y_model_mm"] == 0)
    checks["no_BCu_SIG_zone"] = not any(
        z.GetNetname() == "/SIG" and z.GetLayer() == p.B_Cu for z in board.Zones())
    checks["GND_via_count"] = sum(isinstance(t, p.PCB_VIA) and t.GetNetname() == "/GND"
                                   for t in board.GetTracks())

    plane_edges = []
    for y_model in [-7.51, -7.49, 7.49, 7.51]:
        plane_edges.append({
            "y_model_mm": y_model,
            "In1_GND_at_x0": zone_contains(board, "/GND", p.In1_Cu, 0, y_model),
            "In2_GND_at_x0": zone_contains(board, "/GND", p.In2_Cu, 0, y_model),
        })
    checks["inner_plane_edges_at_plus_minus_7p50"] = all(
        (row["In1_GND_at_x0"] and row["In2_GND_at_x0"]) ==
        (abs(row["y_model_mm"]) > 7.5) for row in plane_edges)
    checks["catalogue_min_ID_clearance_each_side_mm"] = (37.21-0.89)/2-15.5
    checks["catalogue_max_OD_clearance_each_side_mm"] = 34-(60.96+1.27)/2

    drc = json.loads((A05_DIR / "review/drc.json").read_text(encoding="utf-8"))
    erc = json.loads((A05_DIR / "review/erc.json").read_text(encoding="utf-8"))
    checks["DRC_violations"] = len(drc["violations"])
    checks["DRC_unconnected"] = len(drc["unconnected_items"])
    checks["DRC_schematic_parity"] = len(drc["schematic_parity"])
    checks["ERC_violations"] = sum(len(sheet["violations"]) for sheet in erc["sheets"])
    booleans = [v for v in checks.values() if isinstance(v, bool)]
    passed = (all(booleans) and checks["GND_via_count"] == 34
              and all(checks[k] == 0 for k in
                      ["DRC_violations", "DRC_unconnected", "DRC_schematic_parity", "ERC_violations"])
              and abs(checks["board_thickness_mm"]-1.6) < 1e-6
              and checks["catalogue_min_ID_clearance_each_side_mm"] > 2.5
              and checks["catalogue_max_OD_clearance_each_side_mm"] > 2.5)
    payload = {
        "classification": "CALCULATED_CAD_CURRENT_PATH_AUDIT_NOT_MEASURED",
        "pass": passed,
        "checks": checks,
        "outline_and_hole_bounds_model_mm": bounds,
        "core_samples": core_samples,
        "plane_edge_samples": plane_edges,
        "source": str(A05.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(A05.read_bytes()).hexdigest(),
        "kicad": p.GetBuildVersion(),
        "limitations": [
            "Saved-zone and nominal catalogue checks are not etch, registration or form-tolerance measurements.",
            "The core must be centred axially so the 15 mm plane cut clears its maximum 13.335 mm thickness.",
            "RF performance is decided separately from the 3-D dense-frequency model and physical VNA test.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"pass": passed, "checks": checks}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
