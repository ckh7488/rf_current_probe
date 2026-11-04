"""Extract the saved, filled Fixture A04 KiCad geometry for EM modelling.

The board is opened read-only.  Coordinates are translated to the mechanical
datum used by the existing fixture simulations: board centre is x=0 and the
midpoint between J1/J2 is y=0.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pcbnew as p


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "hardware" / "calibration_fixture_PCB_A04_DRAFT"
          / "RFCP_Fixture_Flat_A04_DRAFT.kicad_pcb")
OUT = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
       / "a04_saved_geometry.json")


def ring(poly) -> list[list[float]]:
    return [[p.ToMM(poly.CPoint(i).x) - 72,
             p.ToMM(poly.CPoint(i).y) - 46.35]
            for i in range(poly.PointCount())]


def polygons(polyset) -> list[dict]:
    return [
        {
            "outer": ring(polyset.COutline(i)),
            "holes": [ring(polyset.CHole(i, j))
                      for j in range(polyset.HoleCount(i))],
        }
        for i in range(polyset.OutlineCount())
    ]


def main() -> None:
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    board = p.LoadBoard(str(SOURCE))
    outline = p.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outline, False)

    zones = []
    for zone in board.Zones():
        layer = zone.GetLayer()
        zones.append({
            "net": zone.GetNetname(),
            "layer": board.GetLayerName(layer),
            "polygons": polygons(zone.GetFilledPolysList(layer)),
        })

    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pos = pad.GetPosition()
            pads.append({
                "ref": fp.GetReference(),
                "number": pad.GetNumber(),
                "net": pad.GetNetname(),
                "x": p.ToMM(pos.x) - 72,
                "y": p.ToMM(pos.y) - 46.35,
                "diameter": p.ToMM(pad.GetSize().x),
                "drill": p.ToMM(pad.GetDrillSize().x),
                "plated": pad.GetAttribute() == p.PAD_ATTRIB_PTH,
            })

    vias = []
    for track in board.GetTracks():
        if not isinstance(track, p.PCB_VIA):
            continue
        pos = track.GetPosition()
        vias.append({
            "net": track.GetNetname(),
            "x": p.ToMM(pos.x) - 72,
            "y": p.ToMM(pos.y) - 46.35,
            "diameter": p.ToMM(track.GetWidth(p.F_Cu)),
            "drill": p.ToMM(track.GetDrillValue()),
        })

    result = {
        "classification": "CAD_EXTRACTED_SAVED_FILLED_BOARD",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "sha256": before,
        "kicad": p.GetBuildVersion(),
        "units": "mm",
        "axes": "board x-72; board y-46.35; z=bottom copper to top copper",
        "thickness": p.ToMM(board.GetDesignSettings().GetBoardThickness()),
        "copper_layers": board.GetCopperLayerCount(),
        "outline": polygons(outline),
        "zones": zones,
        "pads": pads,
        "vias": vias,
        "ports": [[0, -34.35], [0, 34.35]],
        "core_center_y": 0,
        "stack_mm": {"L4": 0.0, "L3": 0.2104,
                     "L2": 1.3896, "L1": 1.6},
    }
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT.relative_to(ROOT)),
        "zones": len(zones),
        "pads": len(pads),
        "vias": len(vias),
        "copper_layers": result["copper_layers"],
        "source_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()
