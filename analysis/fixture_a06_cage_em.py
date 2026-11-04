"""Bounded 3-D openEMS screens of the structure-only A06 fixture family.

The script preserves the A05 PCB launch and can vary the central current-bar
width/thickness, wedge transition and optional four-sided PEC return cage.
There are no matching components.  These idealized topology screens select or
reject a concept; they are not measured calibration data or fabrication
approval.
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
from shapely.geometry import Point, Polygon, box
import CSXCAD
import openEMS as openems_package
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data


REFERENCE_Y_MM = 30.0
MODEL_Y_MIN_MM = -30.25
MODEL_Y_MAX_MM = 30.25
CAGE_X_MM = 48.0
CAGE_CENTER_Z_MM = 0.8
CAGE_HALF_Z_MM = 38.0
CAGE_Z_MIN_MM = CAGE_CENTER_Z_MM - CAGE_HALF_Z_MM
CAGE_Z_MAX_MM = CAGE_CENTER_Z_MM + CAGE_HALF_Z_MM
CAGE_Y_MIN_MM = -16.1
CAGE_Y_MAX_MM = 17.65
BAR_Y_MIN_MM = -5.82227
BAR_Y_MAX_MM = 5.82227
BAR_Z_MIN_MM = CAGE_CENTER_Z_MM - 6.0
BAR_Z_MAX_MM = CAGE_CENTER_Z_MM + 6.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--xy-mesh-mm", type=float, default=1.0)
    p.add_argument("--z-mesh-mm", type=float, default=1.0)
    p.add_argument("--setup", action="store_true")
    p.add_argument("--post", action="store_true")
    p.add_argument("--threads", type=int, default=12)
    p.add_argument("--max-steps", type=int, default=260000)
    p.add_argument("--max-ns", type=float, default=16.0)
    p.add_argument("--end-criteria", type=float, default=1e-5)
    p.add_argument("--bar-width-mm", type=float, default=30.0)
    p.add_argument("--bar-height-mm", type=float, default=12.0)
    p.add_argument("--bar-shape", choices=["block", "wedge"], default="block")
    p.add_argument("--cage-half-x-mm", type=float, default=CAGE_X_MM)
    p.add_argument("--cage-half-z-mm", type=float, default=CAGE_HALF_Z_MM)
    p.add_argument("--omit-cage", action="store_true")
    return p.parse_args()


def shape(row: dict) -> Polygon:
    return Polygon(row["outer"], row.get("holes", []))


def add_area(prop, area, z: float, priority: int = 12) -> int:
    count = 0
    for tri in constrained_delaunay_triangles(area).geoms:
        if not area.covers(tri.representative_point()):
            continue
        prop.AddPolygon(priority=priority,
                        points=np.asarray(tri.exterior.coords[:-1]).T.tolist(),
                        norm_dir=2, elevation=z)
        count += 1
    return count


def smooth_axis(anchors: list[float], regions: list[tuple[float, float, float]],
                lo: float, hi: float) -> np.ndarray:
    values = list(anchors) + [lo, hi]
    for start, stop, step in regions:
        values.extend(np.linspace(start, stop,
                                  max(2, int(np.ceil((stop-start)/step))+1)))
    values = np.sort(np.unique(np.round(values, 7)))
    return SmoothMeshLines(values, max_res=5.0, ratio=1.45)


def force_required(lines: np.ndarray, required: list[float],
                   clearance: float = 0.065) -> np.ndarray:
    req = np.unique(np.round(np.asarray(required, dtype=float), 7))
    kept = [value for value in lines
            if np.min(np.abs(req-value)) >= clearance]
    return np.unique(np.r_[kept, req])


def enforce_min_spacing(lines: np.ndarray, required: list[float],
                        minimum: float = 0.10) -> np.ndarray:
    """Remove SmoothMeshLines artefact slivers while retaining exact geometry."""
    protected = set(np.round(np.asarray(required, dtype=float), 7))
    keep: list[float] = []
    for value in np.round(np.asarray(lines, dtype=float), 7):
        if not keep or value-keep[-1] >= minimum:
            keep.append(float(value))
        elif value in protected and keep[-1] not in protected:
            keep[-1] = float(value)
        elif value in protected and keep[-1] in protected:
            # Closely spaced required planes represent real PCB layers.
            keep.append(float(value))
    return np.asarray(keep)


def main() -> None:
    args = parse_args()
    out = (ROOT / "reviews" / "fixture_structural_redesign_20260922" /
           "em" / args.name)
    if out.exists() and not args.post:
        raise RuntimeError(f"Refuse to overwrite {out}")
    out.mkdir(parents=True, exist_ok=args.post)

    geometry_path = (ROOT / "reviews" / "fixture_structural_redesign_20260922" /
                     "a05_saved_geometry.json")
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    bar_half_x = args.bar_width_mm / 2
    cage_x = args.cage_half_x_mm
    cage_z_min = CAGE_CENTER_Z_MM - args.cage_half_z_mm
    cage_z_max = CAGE_CENTER_Z_MM + args.cage_half_z_mm
    bar_center_z = 2.0 if args.bar_shape == "wedge" else CAGE_CENTER_Z_MM
    bar_z_min = bar_center_z - args.bar_height_mm/2
    bar_z_max = bar_center_z + args.bar_height_mm/2
    zmap = {"B.Cu": 0.0, "In2.Cu": 0.2104,
            "In1.Cu": 1.3896, "F.Cu": 1.6}

    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)

    prepreg = csx.AddMaterial("PREPREG_7628", epsilon=4.4)
    core = csx.AddMaterial("CORE_1065", epsilon=4.6)
    air = csx.AddMaterial("AIR_CUTOUT", epsilon=1.0)
    outline = geometry["outline"][0]
    model_clip = box(-1000, MODEL_Y_MIN_MM, 1000, MODEL_Y_MAX_MM)
    clipped_outer = Polygon(outline["outer"]).intersection(model_clip)
    outer = np.asarray(clipped_outer.exterior.coords[:-1]).T.tolist()
    for material, z0, z1 in [(prepreg, 0, .2104),
                             (core, .2104, 1.3896),
                             (prepreg, 1.3896, 1.6)]:
        material.AddLinPoly(priority=1, points=outer, norm_dir=2,
                            elevation=z0, length=z1-z0)
    for ring in outline.get("holes", []):
        clipped = Polygon(ring).intersection(model_clip)
        parts = [clipped] if clipped.geom_type == "Polygon" else clipped.geoms
        for part in parts:
            if not part.is_empty:
                air.AddLinPoly(priority=5,
                               points=np.asarray(part.exterior.coords[:-1]).T.tolist(),
                               norm_dir=2, elevation=0, length=1.6)
    for pad in geometry["pads"]:
        if pad["plated"]:
            continue
        hole = Point(pad["x"], pad["y"]).buffer(
            pad["drill"]/2, quad_segs=12).intersection(model_clip)
        if hole.is_empty:
            continue
        parts = [hole] if hole.geom_type == "Polygon" else hole.geoms
        for part in parts:
            air.AddLinPoly(priority=5,
                           points=np.asarray(part.exterior.coords[:-1]).T.tolist(),
                           norm_dir=2, elevation=0, length=1.6)

    primitive_counts = {}
    for layer, z in zmap.items():
        for net in ["/GND", "/SIG"]:
            parts = [shape(poly) for zone in geometry["zones"]
                     if zone["layer"] == layer and zone["net"] == net
                     for poly in zone["polygons"]]
            if not parts:
                continue
            prop = csx.AddMetal((layer+net).replace(".", "_").replace("/", "_"))
            primitive_counts[layer+net] = add_area(
                prop, union_all(parts).intersection(model_clip), z)

    vias = csx.AddMetal("GND_VIAS")
    gnd_vias = [v for v in geometry["vias"] if v["net"] == "/GND"
                and MODEL_Y_MIN_MM <= v["y"] <= MODEL_Y_MAX_MM]
    for via in gnd_vias:
        vias.AddCylinder(priority=18,
                         start=[via["x"], via["y"], 0],
                         stop=[via["x"], via["y"], 1.6],
                         radius=via["drill"]/2)

    # New A06 structural conductors.  The bar touches the saved F.Cu SIG sheet
    # throughout its footprint.  All four cage sheets touch the saved planar
    # returns at x=+/-48 mm, but remain outside the entire ferrite/keeper.
    bar = csx.AddMetal("A06_SIG_CURRENT_BAR")
    if args.bar_shape == "block":
        bar.AddBox(priority=24,
                   start=[-bar_half_x, BAR_Y_MIN_MM, bar_z_min],
                   stop=[bar_half_x, BAR_Y_MAX_MM, bar_z_max])
    else:
        # Rhombic y-z section: zero thickness at the core faces where it bonds
        # to F.Cu, full height only at the centre of the ferrite.  Extrusion in
        # x makes a 30 mm wide double-wedge current conductor.
        bar.AddLinPoly(priority=24,
                       points=[[BAR_Y_MIN_MM, 0.0, BAR_Y_MAX_MM, 0.0],
                               [1.6, bar_z_max, 1.6, bar_z_min]],
                       norm_dir=0, elevation=-bar_half_x, length=2*bar_half_x)
    if not args.omit_cage:
        cage = csx.AddMetal("A06_GND_RETURN_CAGE")
        cage.AddBox(priority=22,
                    start=[-cage_x, CAGE_Y_MIN_MM, cage_z_min],
                    stop=[-cage_x, CAGE_Y_MAX_MM, cage_z_max])
        cage.AddBox(priority=22,
                    start=[cage_x, CAGE_Y_MIN_MM, cage_z_min],
                    stop=[cage_x, CAGE_Y_MAX_MM, cage_z_max])
        cage.AddBox(priority=22,
                    start=[-cage_x, CAGE_Y_MIN_MM, cage_z_min],
                    stop=[cage_x, CAGE_Y_MAX_MM, cage_z_min])
        cage.AddBox(priority=22,
                    start=[-cage_x, CAGE_Y_MIN_MM, cage_z_max],
                    stop=[cage_x, CAGE_Y_MAX_MM, cage_z_max])

    xm, zm = args.xy_mesh_mm, args.z_mesh_mm
    x_anchor = [-105, -72, -cage_x, -34.5, -bar_half_x, -0.179324,
                0, .179324, bar_half_x, 34.5, cage_x, 72, 105]
    y_anchor = [-65, MODEL_Y_MIN_MM, -REFERENCE_Y_MM,
                CAGE_Y_MIN_MM, -7.9, BAR_Y_MIN_MM, BAR_Y_MAX_MM, 7.9,
                CAGE_Y_MAX_MM, REFERENCE_Y_MM, MODEL_Y_MAX_MM, 65]
    z_anchor = [-68, cage_z_min, bar_z_min, 0, .2104, 1.3896,
                1.6, bar_z_max, cage_z_max, 68]
    xs = smooth_axis(x_anchor,
                     [(-78, -54, 2.0), (-54, 54, xm), (54, 78, 2.0)],
                     -105, 105)
    ys = smooth_axis(y_anchor,
                     [(-38, 38, args.xy_mesh_mm)], -65, 65)
    zs = smooth_axis(z_anchor,
                     [(cage_z_min, cage_z_max, zm),
                      (-3, 4, .18)], -68, 68)

    x_required = [-cage_x, -34.5, -bar_half_x, -.179324, 0,
                  .179324, bar_half_x, 34.5, cage_x]
    y_required = [MODEL_Y_MIN_MM, -REFERENCE_Y_MM-.25, -REFERENCE_Y_MM,
                  -REFERENCE_Y_MM+.25, CAGE_Y_MIN_MM, -7.9,
                  BAR_Y_MIN_MM, -5, 0, 5, BAR_Y_MAX_MM, 7.9,
                  CAGE_Y_MAX_MM, REFERENCE_Y_MM-.25, REFERENCE_Y_MM,
                  REFERENCE_Y_MM+.25, MODEL_Y_MAX_MM]
    z_required = [cage_z_min, bar_z_min, 0, .2104, 1.3896, 1.6,
                  bar_z_max, cage_z_max]
    for via in gnd_vias:
        radius = via["drill"]/2
        x_required += [via["x"]-radius, via["x"], via["x"]+radius]
        y_required += [via["y"]-radius, via["y"], via["y"]+radius]
    xs = force_required(xs, x_required, .12)
    ys = force_required(ys, y_required, .12)
    zs = force_required(zs, z_required, .10)
    xs = enforce_min_spacing(xs, x_required, .12)
    ys = enforce_min_spacing(ys, y_required, .12)
    zs = enforce_min_spacing(zs, z_required, .10)
    for axis, lines in zip("xyz", [xs, ys, zs]):
        grid.SetLines(axis, lines)

    fdtd = (openEMS(NrTS=1000, EndCriteria=1e-4) if args.setup else
            openEMS(NrTS=args.max_steps, EndCriteria=args.end_criteria,
                    MaxTime=args.max_ns*1e-9))
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond(["PML_8"]*6)
    ports = {}
    for number, y in [(1, -REFERENCE_Y_MM), (2, REFERENCE_Y_MM)]:
        ports[number] = fdtd.AddLumpedPort(
            number, 50, [-.179324, y-.25, 1.3896],
            [.179324, y+.25, 1.6], "z", excite=number == 1, priority=40)
    probe_names = []
    for i, y in enumerate([-5.0, 0.0, 5.0]):
        name = f"probe_{i}"
        probe = csx.AddProbe(name, p_type=1, weight=1, norm_dir=1)
        probe.AddBox(start=[-16, y, bar_z_min-.5],
                     stop=[16, y, bar_z_max+.5])
        probe_names.append(name)

    mesh = [len(grid.GetLines(axis)) for axis in "xyz"]
    meta = {
        "classification": "SIMULATED_IDEAL_STRUCTURE_TOPOLOGY_NOT_MEASURED",
        "concept": (("A06 saved planar return plus %.3gx%.3g mm central current bar; no matching components" % (args.bar_width_mm, args.bar_height_mm))
                    if args.omit_cage else
                    ("A06 four-sided external return cage plus %.3gx%.3g mm central current bar; no matching components" % (args.bar_width_mm, args.bar_height_mm))),
        "parameters": vars(args),
        "geometry_mm": {
            "cage": (None if args.omit_cage else
                     {"half_x": cage_x,
                      "z": [cage_z_min, cage_z_max],
                      "y": [CAGE_Y_MIN_MM, CAGE_Y_MAX_MM]}),
            "current_bar": {"x": [-bar_half_x, bar_half_x],
                            "y": [BAR_Y_MIN_MM, BAR_Y_MAX_MM],
                            "z": [bar_z_min, bar_z_max],
                            "shape": args.bar_shape,
                            "wedge_tip_z_if_applicable": 1.6},
            "nominal_clearance": ({
                "bar_corner_to_catalogue_min_core_ID_radial":
                    (37.21-.89)/2 - np.hypot(bar_half_x,
                        (args.bar_height_mm/2 if args.bar_shape == "wedge"
                         else 1.2+args.bar_height_mm/2)),
            } if args.omit_cage else {
                "cage_to_keeper_x_each_side": cage_x-44.0,
                "cage_to_keeper_board_normal_min": args.cage_half_z_mm-33.5,
                "bar_corner_to_catalogue_min_core_ID_radial":
                    (37.21-.89)/2 - np.hypot(bar_half_x,
                        (args.bar_height_mm/2 if args.bar_shape == "wedge"
                         else 1.2+args.bar_height_mm/2)),
            }),
        },
        "mesh": mesh,
        "min_cell_mm": [float(np.min(np.diff(grid.GetLines(a)))) for a in "xyz"],
        "cells": int(np.prod([n-1 for n in mesh])),
        "primitive_counts": primitive_counts,
        "gnd_vias": len(gnd_vias),
        "source_geometry": str(geometry_path.relative_to(ROOT)),
        "source_geometry_sha256": hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "openems": openems_package.__version__,
        "csxcad": CSXCAD.__version__,
        "reference_plane": "ideal 50-ohm L1/In1 lumped ports at y=+/-30 mm",
        "limitations": ([] if args.omit_cage else [
            "Ideal PEC cage with perfect four-wall seams and perfect PCB-return bond.",
        ]) + [
            "Ideal solid current bar with perfect bond to A05 F.Cu; no manufacturable attachment is yet defined.",
            "No ferrite, winding, probe head/keeper dielectric, cable, SMA body, material loss or solder mask.",
            "This topology screen cannot establish finished calibration accuracy or fabrication fit.",
        ],
    }
    (out/"model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if not args.post:
        (out/"model_source.py").write_bytes(Path(__file__).read_bytes())
        csx.Write2XML(str(out/"model.xml"))
        print(json.dumps({"out": str(out), "mesh": mesh,
                          "min_cell_mm": meta["min_cell_mm"],
                          "cells": meta["cells"]}), flush=True)
        if args.setup:
            fdtd.Run(str(out), setup_only=True, debug_PEC=True, verbose=1)
        else:
            fdtd.Run(str(out), cleanup=False, setup_only=False,
                     debug_PEC=True, verbose=1, numThreads=args.threads,
                     engine="multithreaded", dump_statistics=True)
        fdtd.Write2XML(str(out/"solver.xml"))
    if args.setup:
        return

    freq = np.unique(np.r_[np.linspace(100e6, 500e6, 801),
                           np.asarray([100, 150, 200, 300, 400, 500])*1e6])
    for port in ports.values():
        port.CalcPort(str(out), freq, ref_impedance=50)
    p1, p2 = ports[1], ports[2]
    s11, s21 = p1.uf_ref/p1.uf_inc, p2.uf_ref/p1.uf_inc
    currents = {name: UI_data(name, str(out), freq).ui_f_val[0]
                for name in probe_names}
    centre = currents["probe_1"]
    ratio = centre/(p1.uf_inc/50)
    rows = []
    for i, f in enumerate(freq):
        rows.append({
            "f_Hz": float(f),
            "S11_dB": float(20*np.log10(max(abs(s11[i]), 1e-30))),
            "S21_dB": float(20*np.log10(max(abs(s21[i]), 1e-30))),
            "S11_re": float(s11[i].real), "S11_im": float(s11[i].imag),
            "S21_re": float(s21[i].real), "S21_im": float(s21[i].imag),
            "I_center_over_matched_mag": float(abs(ratio[i])),
            "I_center_over_matched_phase_deg": float(np.angle(ratio[i], deg=True)),
            "along_core_current_variation_percent": float(
                100*max(abs(currents[n][i]-centre[i]) for n in probe_names)
                / max(abs(centre[i]), 1e-30)),
            "passivity_sum": float(abs(s11[i])**2+abs(s21[i])**2),
        })
    meta["rows"] = rows
    meta["metrics_100_500_MHz"] = {
        "worst_S11_dB": float(max(r["S11_dB"] for r in rows)),
        "max_center_current_magnitude_error_percent": float(
            100*max(abs(r["I_center_over_matched_mag"]-1) for r in rows)),
        "max_along_core_current_variation_percent": float(
            max(r["along_core_current_variation_percent"] for r in rows)),
        "max_passivity_sum": float(max(r["passivity_sum"] for r in rows)),
    }
    (out/"results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out/"response.csv").open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    anchors = [r for r in rows if r["f_Hz"] in
               {100e6, 150e6, 200e6, 300e6, 400e6, 500e6}]
    print(json.dumps({"metrics": meta["metrics_100_500_MHz"],
                      "anchors": anchors}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
