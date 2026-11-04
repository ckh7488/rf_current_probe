"""Full saved-board Fixture A04 openEMS model with idealized SMA launches.

This complements ``fixture_structural_em.py``.  The structural model isolates
the L1/L2 transition; this model reads the saved KiCad filled copper and adds
the actual plated-hole locations plus an explicitly assumed GCT connector
interior.  It is still a simulation model, not a supplier field-solver result
or a substitute for VNA measurement of the manufactured fixture.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "openems" / "v0.37.0-rc2" / "runtime" / "openEMS"
os.environ["OPENEMS_INSTALL_PATH"] = str(RUNTIME)
os.environ["CSXCAD_INSTALL_PATH"] = str(RUNTIME)

import numpy as np
from shapely import constrained_delaunay_triangles, union_all
from shapely.geometry import Point, Polygon
import CSXCAD
import openEMS as openems_package
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="a04_full_seed_m040")
    p.add_argument("--xy-mesh-mm", type=float, default=0.40)
    p.add_argument("--z-mesh-mm", type=float, default=0.10)
    p.add_argument("--margin-mm", type=float, default=35.0)
    p.add_argument("--connector-height-mm", type=float, default=6.4)
    p.add_argument("--connector-bore-radius-mm", type=float, default=2.2)
    p.add_argument("--max-steps", type=int, default=240000)
    p.add_argument("--max-ns", type=float, default=20.0)
    p.add_argument("--end-criteria", type=float, default=1e-5)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--setup", action="store_true")
    p.add_argument("--post", action="store_true")
    p.add_argument("--debug-pec", action="store_true")
    return p.parse_args()


def shape(row: dict) -> Polygon:
    return Polygon(row["outer"], row.get("holes", []))


def add_polygons(prop, area, z: float, priority: int = 10,
                 thickness: float = 0.0) -> int:
    count = 0
    if area.is_empty:
        return count
    for tri in constrained_delaunay_triangles(area).geoms:
        if not area.covers(tri.representative_point()):
            continue
        points = np.asarray(tri.exterior.coords[:-1]).T.tolist()
        if thickness:
            prop.AddLinPoly(priority=priority, points=points, norm_dir=2,
                            elevation=z, length=thickness)
        else:
            prop.AddPolygon(priority=priority, points=points, norm_dir=2,
                            elevation=z)
        count += 1
    return count


def smooth(anchors: list[float], regions: list[tuple[float, float, float]],
           extent: float) -> np.ndarray:
    values = list(anchors) + [-extent, extent]
    for lo, hi, step in regions:
        values.extend(np.linspace(lo, hi,
                                  max(2, int(np.ceil((hi - lo) / step)) + 1)))
    values = np.sort(np.unique(np.round(values, 7)))
    keep = [values[0]]
    for value in values[1:]:
        if value - keep[-1] > 0.045:
            keep.append(value)
    return SmoothMeshLines(np.asarray(keep), max_res=7.0, ratio=1.45)


def force(lines: np.ndarray, required: list[float],
          clearance: float = 0.065) -> np.ndarray:
    req = np.unique(np.round(np.asarray(required, dtype=float), 7))
    kept = [value for value in lines
            if np.min(np.abs(req - value)) >= clearance]
    return np.unique(np.r_[kept, req])


def main() -> None:
    args = arguments()
    out = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
           / "em" / args.name)
    if out.exists() and not args.post:
        raise RuntimeError(f"Refuse to overwrite {out}")
    out.mkdir(parents=True, exist_ok=args.post)

    geometry_path = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
                     / "a04_saved_geometry.json")
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    board = union_all([shape(row) for row in geometry["outline"]])
    npth = [Point(p["x"], p["y"]).buffer(p["drill"] / 2, quad_segs=12)
            for p in geometry["pads"] if not p["plated"]]
    if npth:
        board = board.difference(union_all(npth))

    stack = geometry["stack_mm"]
    z_by_layer = {"F.Cu": stack["L1"], "In1.Cu": stack["L2"],
                  "In2.Cu": stack["L3"], "B.Cu": stack["L4"]}
    h = stack["L1"]

    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)
    fdtd = openEMS(NrTS=args.max_steps, EndCriteria=args.end_criteria,
                   MaxTime=args.max_ns * 1e-9)
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond(["PML_8"] * 6)

    prepreg = csx.AddMaterial("prepreg_Dk4p4_lossless", epsilon=4.4)
    core = csx.AddMaterial("core_Dk4p6_lossless", epsilon=4.6)
    ptfe = csx.AddMaterial("connector_PTFE_assumed_Dk2p1", epsilon=2.1)
    sig = csx.AddMetal("SIG_PEC")
    gnd = csx.AddMetal("GND_PEC")
    barrel = csx.AddMetal("PLATED_HOLES_SOLID_PEC")
    shell = csx.AddMetal("SMA_SHELL_ASSUMED_PEC")
    pin = csx.AddMetal("SMA_PIN_ASSUMED_PEC")

    primitive_count = 0
    primitive_count += add_polygons(prepreg, board, stack["L4"], 1,
                                    stack["L3"] - stack["L4"])
    primitive_count += add_polygons(core, board, stack["L3"], 1,
                                    stack["L2"] - stack["L3"])
    primitive_count += add_polygons(prepreg, board, stack["L2"], 1,
                                    stack["L1"] - stack["L2"])

    for layer, z in z_by_layer.items():
        for net, prop in [("/SIG", sig), ("/GND", gnd)]:
            parts = [shape(poly) for zone in geometry["zones"]
                     if zone["layer"] == layer and zone["net"] == net
                     for poly in zone["polygons"]]
            # Through-hole annular pads exist on every copper layer even when
            # they are not part of the filled-zone polygon returned by KiCad.
            parts += [Point(pad["x"], pad["y"]).buffer(
                        pad["diameter"] / 2, quad_segs=12)
                      for pad in geometry["pads"]
                      if pad["plated"] and pad["net"] == net]
            if parts:
                primitive_count += add_polygons(prop, union_all(parts), z, 12)

    # Solid PEC cylinders deliberately represent solder-filled plated holes.
    # This is an EM connectivity approximation, not a fabrication request.
    for via in geometry["vias"]:
        prop = sig if via["net"] == "/SIG" else barrel
        prop.AddCylinder(priority=15,
                         start=[via["x"], via["y"], 0],
                         stop=[via["x"], via["y"], h],
                         radius=via["drill"] / 2)
    for pad_row in geometry["pads"]:
        if not pad_row["plated"]:
            continue
        prop = sig if pad_row["net"] == "/SIG" else gnd
        prop.AddCylinder(priority=16,
                         start=[pad_row["x"], pad_row["y"], -0.35],
                         stop=[pad_row["x"], pad_row["y"], h + 0.35],
                         radius=pad_row["drill"] / 2 + 0.025)

    # Same bounded connector approximation used in the A03 review.  The
    # exterior is 7 mm square; unseen bore/height values remain assumptions.
    ports_xy = geometry["ports"]
    for x, y in ports_xy:
        shell.AddBox(priority=20, start=[x - 3.5, y - 3.5, 3.6],
                     stop=[x + 3.5, y + 3.5, 8.4])
        ptfe.AddCylinder(priority=21, start=[x, y, 3.6], stop=[x, y, 8.4],
                         radius=args.connector_bore_radius_mm)
        pin.AddCylinder(priority=22, start=[x, y, -0.35], stop=[x, y, 8.4],
                        radius=0.635)
        for dx in [-2.54, 2.54]:
            for dy in [-2.54, 2.54]:
                shell.AddBox(priority=22,
                             start=[x + dx - 0.5, y + dy - 0.5, -0.35],
                             stop=[x + dx + 0.5, y + dy + 0.5, 3.6])
        zc = args.connector_height_mm
        pin.AddBox(priority=23, start=[x + 0.5, y - 0.5, zc - 0.5],
                   stop=[x + 1.0, y + 0.5, zc + 0.5])
        shell.AddBox(priority=23, start=[x + 2.0, y - 0.5, zc - 0.5],
                     stop=[x + 2.5, y + 0.5, zc + 0.5])

    m = args.xy_mesh_mm
    xs = smooth([-72, -56, -8, -4.01, -3.5, -2.54, -0.635,
                 -0.179324, 0, 0.179324, 0.635, 2.54, 3.5, 4.01, 8, 56, 72],
                [(-76, -8, 1.8), (-8, 8, m), (8, 76, 1.8)],
                76 + args.margin_mm)
    ys = smooth([-46.35, -36.89, -34.35, -31.81,
                 -15, -7.5, 0, 7.5, 15, 31.81, 34.35, 36.89,
                 46.35],
                [(-51, -40, 1.2), (-40, -28, m), (-28, 28, m),
                 (28, 40, m), (40, 51, 1.2)],
                51 + args.margin_mm)
    zs = smooth([-2, 0, stack["L3"], stack["L2"], h, 3.6, 5.9,
                 args.connector_height_mm, 6.9, 8.4, 10],
                [(-3, 3, args.z_mesh_mm), (3, 10, 0.25)],
                args.margin_mm)

    # Resolve all through-hole centres and finished-bore surfaces.  Removing
    # nearby nonessential lines avoids pathological sub-0.05 mm cells.
    xs_required = [0, 0.5, 1.0, 2.0]
    # A04 removes the close return for exactly 15.0 mm.  These planes must
    # coincide with the saved copper edge rather than the superseded A03/A04
    # 13.5 mm exploratory seed (which used +/-6.75 mm).
    ys_required: list[float] = [0, -7.5, 7.5]
    # The connector PTHs are required electrical transitions and are resolved
    # exactly.  Remote plane-stitching vias remain in the geometry but are not
    # all promoted to mesh anchors: doing that creates accidental 0.04 mm
    # slivers where unrelated cylinder surfaces nearly coincide and does not
    # improve the 100--500 MHz launch/current-path question.
    for row in [p for p in geometry["pads"] if p["plated"]]:
        radius = row["drill"] / 2
        xs_required += [row["x"] - radius, row["x"], row["x"] + radius]
        ys_required += [row["y"] - radius, row["y"], row["y"] + radius]
    for x, y in ports_xy:
        ys_required += [y - 0.5, y, y + 0.5]
    zs_required = [0, stack["L3"], stack["L2"], h, 3.6,
                   args.connector_height_mm - 0.5,
                   args.connector_height_mm,
                   args.connector_height_mm + 0.5, 8.4]
    xs = force(xs, xs_required, clearance=0.12)
    ys = force(ys, ys_required, clearance=0.12)
    zs = force(zs, zs_required, clearance=0.12)
    for axis, values in zip("xyz", [xs, ys, zs]):
        grid.SetLines(axis, values)

    ports = {}
    for number, (x, y) in enumerate(ports_xy, 1):
        zc = args.connector_height_mm
        ports[number] = fdtd.AddLumpedPort(
            number, 50,
            [x + 2.0, y - 0.5, zc - 0.5],
            [x + 1.0, y + 0.5, zc + 0.5],
            "x", excite=1 if number == 1 else 0, priority=30)

    probe_names = []
    for i, y in enumerate([-5.0, 0.0, 5.0]):
        name = f"core_{i}"
        probe = csx.AddProbe(name, p_type=1, weight=1, norm_dir=1)
        probe.AddBox(start=[-4.5, y, -0.5], stop=[4.5, y, 2.1])
        probe_names.append(name)

    mesh = [len(grid.GetLines(axis)) for axis in "xyz"]
    min_cell = [float(np.min(np.diff(grid.GetLines(axis)))) for axis in "xyz"]
    meta = {
        "classification": "SIMULATED_FULL_SAVED_BOARD_NOT_MEASURED",
        "parameters": vars(args),
        "mesh": mesh,
        "min_cell_mm": min_cell,
        "cells": int(np.prod([n - 1 for n in mesh])),
        "polygon_primitives": primitive_count,
        "source_geometry": str(geometry_path.relative_to(ROOT)),
        "source_geometry_sha256": hashlib.sha256(
            geometry_path.read_bytes()).hexdigest(),
        "source_board_sha256": geometry["sha256"],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "openems": openems_package.__version__,
        "csxcad": CSXCAD.__version__,
        "reference_plane": (
            "idealized radial lumped feed inside assumed 7 mm SMA body; "
            "not the physical mating plane"),
        "materials": (
            "lossless Dk4.4 outer prepreg, Dk4.6 core, PEC copper and "
            "solid plated holes, assumed Dk2.1 SMA dielectric"),
        "limitations": [
            "Actual connector internal dimensions are unavailable and assumed.",
            "No ferrite, winding, probe head, cable, solder mask, copper roughness, or dielectric/conductor loss.",
            "Solid PEC cylinders approximate solder-filled plated holes; they do not request via fill in manufacture.",
            "This model checks the empty fixture topology and connector sensitivity, not finished calibration accuracy.",
        ],
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if not args.post:
        (out / "model_source.py").write_bytes(Path(__file__).read_bytes())
        csx.Write2XML(str(out / "model.xml"))
        fdtd.Write2XML(str(out / "solver.xml"))
        print(json.dumps({"out": str(out), "mesh": mesh,
                          "min_cell_mm": min_cell,
                          "cells": meta["cells"]}), flush=True)
        fdtd.Run(str(out), cleanup=False, setup_only=args.setup, verbose=1,
                 numThreads=args.threads, engine="multithreaded",
                 dump_statistics=True, debug_PEC=args.debug_pec)
    if args.setup:
        return

    freq = np.unique(np.r_[np.linspace(100e6, 500e6, 401),
                           np.asarray([100, 150, 200, 300, 400, 500]) * 1e6])
    for port in ports.values():
        port.CalcPort(str(out), freq, ref_impedance=50)
    p1, p2 = ports[1], ports[2]
    s11 = p1.uf_ref / p1.uf_inc
    s21 = p2.uf_ref / p1.uf_inc
    currents = {name: UI_data(name, str(out), freq).ui_f_val[0]
                for name in probe_names}
    centre = currents["core_1"]
    ratio = centre / (p1.uf_inc / 50)
    rows = []
    for i, f in enumerate(freq):
        rows.append({
            "f_Hz": float(f),
            "S11_dB": float(20 * np.log10(abs(s11[i]))),
            "S21_dB": float(20 * np.log10(abs(s21[i]))),
            "S11_re": float(s11[i].real),
            "S11_im": float(s11[i].imag),
            "S21_re": float(s21[i].real),
            "S21_im": float(s21[i].imag),
            "I_center_over_matched_mag": float(abs(ratio[i])),
            "I_center_over_matched_phase_deg": float(np.angle(ratio[i], deg=True)),
            "along_core_current_variation_percent": float(
                100 * max(abs(currents[n][i] - centre[i])
                          for n in probe_names) / max(abs(centre[i]), 1e-30)),
            "passivity_sum": float(abs(s11[i]) ** 2 + abs(s21[i]) ** 2),
        })
    meta["rows"] = rows
    meta["metrics_100_500_MHz"] = {
        "worst_S11_dB": float(max(row["S11_dB"] for row in rows)),
        "max_center_current_magnitude_error_percent": float(
            100 * max(abs(row["I_center_over_matched_mag"] - 1)
                      for row in rows)),
        "max_along_core_current_variation_percent": float(
            max(row["along_core_current_variation_percent"] for row in rows)),
        "max_passivity_sum": float(max(row["passivity_sum"] for row in rows)),
    }
    (out / "results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out / "response.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    anchors = [row for row in rows
               if row["f_Hz"] in {100e6, 150e6, 200e6, 300e6, 400e6, 500e6}]
    print(json.dumps({"metrics": meta["metrics_100_500_MHz"],
                      "anchors": anchors}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
