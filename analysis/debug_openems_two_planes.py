"""Minimal openEMS regression for two zero-thickness inner copper sheets.

This is a solver-representation diagnostic, not an RF result.  It reproduces
the A04 z stack without the board outline, ports, vias, or tapers and asks the
solver to dump the rasterized PEC edges.
"""
from pathlib import Path
import argparse
import os

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "openems" / "v0.37.0-rc2" / "runtime" / "openEMS"
os.environ["OPENEMS_INSTALL_PATH"] = str(RUNTIME)
os.environ["CSXCAD_INSTALL_PATH"] = str(RUNTIME)

from CSXCAD import ContinuousStructure
from openEMS import openEMS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", action="store_true")
    args = ap.parse_args()
    name = "two_plane_port_regression" if args.port else "two_plane_regression"
    out = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em" / name
    out.mkdir(parents=True, exist_ok=True)
    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)
    for axis, lines in {
        "x": [-6, -5, -4, -2, 0, 2, 4, 5, 6],
        "y": [-6, -5, -4, -2, 0, 2, 4, 5, 6],
        "z": [-2, -1, 0, 0.2104, 0.5, 1.0, 1.3896, 1.6, 2, 3],
    }.items():
        grid.SetLines(axis, lines)

    lower = csx.AddMaterial("lower_dielectric", epsilon=4.4)
    middle = csx.AddMaterial("middle_dielectric", epsilon=4.6)
    upper = csx.AddMaterial("upper_dielectric", epsilon=4.4)
    lower.AddBox(priority=1, start=[-5, -5, 0], stop=[5, 5, 0.2104])
    middle.AddBox(priority=1, start=[-5, -5, 0.2104], stop=[5, 5, 1.3896])
    upper.AddBox(priority=1, start=[-5, -5, 1.3896], stop=[5, 5, 1.6])

    pts = [[-4, 4, 4, -4], [-4, -4, 4, 4]]
    l3 = csx.AddMetal("L3_sheet")
    l2 = csx.AddMetal("L2_sheet")
    top = csx.AddMetal("L1_signal")
    l3.AddPolygon(priority=10, points=pts, norm_dir=2, elevation=0.2104)
    l2.AddPolygon(priority=10, points=pts, norm_dir=2, elevation=1.3896)
    top.AddBox(priority=12, start=[-1, -4, 1.6], stop=[1, 4, 1.6])

    fdtd = openEMS(NrTS=1000, EndCriteria=1e-4)
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond(["MUR"] * 6)
    if args.port:
        fdtd.AddLumpedPort(1, 50, [-1, -0.5, 1.3896],
                           [1, 0.5, 1.6], "z", excite=1, priority=40)
    csx.Write2XML(str(out / "model.xml"))
    fdtd.Run(str(out), setup_only=True, debug_PEC=True, verbose=1)


if __name__ == "__main__":
    main()
