"""3-D openEMS mesh template for the close-return A05 fixture.

The model deliberately removes the connector internals so the L1/L2 launch,
ferrite-span return interruption, copper overlaps and tapers can be judged
without confusing them with the previous assumed vertical SMA model.  Ports
are 50-ohm vertical lumped reference planes on the controlled microstrip.

This is an empty-fixture model.  It contains no ferrite permeability, winding,
probe head or bench cable and cannot be used as measured calibration data.
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
from shapely.geometry import Polygon, Point, box
from shapely import union_all, constrained_delaunay_triangles
import CSXCAD
import openEMS as openems_package
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="a05_mesh_template_m080")
    p.add_argument("--gap-mm", type=float, default=15.0)
    p.add_argument("--in-overlap-mm", type=float, default=-1.6)
    p.add_argument("--out-overlap-mm", type=float, default=-1.6)
    p.add_argument("--taper-mm", type=float, default=2.0)
    p.add_argument("--launch-width-mm", type=float, default=0.358648)
    p.add_argument("--wide-width-mm", type=float, default=30.0)
    p.add_argument("--xy-mesh-mm", type=float, default=0.80)
    p.add_argument("--z-mesh-mm", type=float, default=0.1052)
    p.add_argument("--margin-mm", type=float, default=45.0)
    p.add_argument("--max-steps", type=int, default=260000)
    p.add_argument("--max-ns", type=float, default=16.0)
    p.add_argument("--end-criteria", type=float, default=1e-5)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--setup", action="store_true")
    p.add_argument("--mesh-only", action="store_true")
    p.add_argument("--post", action="store_true")
    p.add_argument("--debug-pec", action="store_true")
    return p.parse_args()


def shp(row: dict) -> Polygon:
    return Polygon(row["outer"], row.get("holes", []))


def add_polygons(prop, area, z: float, priority: int = 10) -> int:
    count = 0
    if area.is_empty:
        return count
    for tri in constrained_delaunay_triangles(area).geoms:
        # Constrained triangulation may include triangles inside holes on some
        # GEOS versions.  Retain only triangles whose representative point is
        # inside the intended metal/dielectric area.
        if not area.covers(tri.representative_point()):
            continue
        pts = np.asarray(tri.exterior.coords[:-1]).T.tolist()
        prop.AddPolygon(priority=priority, points=pts, norm_dir=2, elevation=z)
        count += 1
    return count


def add_dielectric(prop, area, z: float, thickness: float, priority: int = 1) -> int:
    count = 0
    for tri in constrained_delaunay_triangles(area).geoms:
        if not area.covers(tri.representative_point()):
            continue
        pts = np.asarray(tri.exterior.coords[:-1]).T.tolist()
        prop.AddLinPoly(priority=priority, points=pts, norm_dir=2, elevation=z, length=thickness)
        count += 1
    return count


def add_prism(prop, ring, z: float, thickness: float, priority: int) -> int:
    """Add one continuous polygon prism without triangulating its faces."""
    pts = np.asarray(ring).T.tolist()
    prop.AddLinPoly(priority=priority, points=pts, norm_dir=2,
                    elevation=z, length=thickness)
    return 1


def signal_polygon(args: argparse.Namespace, y_min: float = -34.35, y_max: float = 34.35) -> tuple[Polygon, dict]:
    half_gap = args.gap_mm / 2
    # Negative-y connector is IN.  Wide copper continues over L2 by the
    # specified overlap, then changes width with a linear taper.
    in_wide_end = -half_gap - args.in_overlap_mm
    in_taper_end = in_wide_end - args.taper_mm
    out_wide_end = half_gap + args.out_overlap_mm
    out_taper_end = out_wide_end + args.taper_mm
    hw_n = args.launch_width_mm / 2
    hw_w = args.wide_width_mm / 2
    profile = [
        (y_min, hw_n),
        (in_taper_end, hw_n),
        (in_wide_end, hw_w),
        (out_wide_end, hw_w),
        (out_taper_end, hw_n),
        (y_max, hw_n),
    ]
    right = [(hw, y) for y, hw in profile]
    left = [(-hw, y) for y, hw in reversed(profile)]
    return Polygon(right + left), {
        "in_taper_start_y_mm": in_taper_end,
        "in_wide_start_y_mm": in_wide_end,
        "gap_start_y_mm": -half_gap,
        "gap_end_y_mm": half_gap,
        "out_wide_end_y_mm": out_wide_end,
        "out_taper_end_y_mm": out_taper_end,
    }


def smooth_axis(anchors: list[float], regions: list[tuple[float, float, float]], extent: float) -> np.ndarray:
    values = list(anchors) + [-extent, extent]
    for lo, hi, step in regions:
        values.extend(np.linspace(lo, hi, max(2, int(np.ceil((hi - lo) / step)) + 1)))
    values = np.sort(np.unique(np.round(values, 7)))
    keep = [values[0]]
    for value in values[1:]:
        if value - keep[-1] > 0.045:
            keep.append(value)
    return SmoothMeshLines(np.asarray(keep), max_res=5.0, ratio=1.45)


def force_required(lines: np.ndarray, required: list[float], clearance: float = 0.065) -> np.ndarray:
    """Insert exact geometry planes without leaving adjacent mesh slivers."""
    req = np.unique(np.round(np.asarray(required, dtype=float), 7))
    kept = [value for value in lines if np.min(np.abs(req - value)) >= clearance]
    return np.unique(np.r_[kept, req])


def main() -> None:
    args = parse_args()
    out = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em" / args.name
    if out.exists() and not args.post:
        raise RuntimeError(f"Refuse to overwrite {out}")
    out.mkdir(parents=True, exist_ok=args.post)

    geometry_path = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
                     / "a05_saved_geometry.json")
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    board = union_all([shp(row) for row in geometry["outline"]])
    # Retain only actual non-plated mechanical holes in the dielectric model.
    npth = [Point(p["x"], p["y"]).buffer(p["drill"] / 2, quad_segs=12)
            for p in geometry["pads"] if not p["plated"]]
    if npth:
        board = board.difference(union_all(npth))

    h = 1.6
    l1_z = h
    l2_z = h - 0.2104
    l3_z = 0.2104
    l4_z = 0.0
    analytical_signal, signal_dims = signal_polygon(args)
    saved_signal = union_all([
        shp(poly) for zone in geometry["zones"]
        if zone["layer"] == "F.Cu" and zone["net"] == "/SIG"
        for poly in zone["polygons"]
    ])
    if saved_signal.is_empty:
        raise RuntimeError("Saved F.Cu /SIG zone is missing")
    signal = saved_signal
    signal_geometry_delta_mm2 = analytical_signal.symmetric_difference(saved_signal).area
    half_gap = args.gap_mm / 2
    # Read the inner returns from the saved KiCad zones.  Reconstructing them
    # as ``board - centre box`` made a convenient early sweep model, but it is
    # not the fabrication geometry and one RC solver build failed to rasterize
    # its upper sheet.  The accepted model must follow the saved board exactly.
    inner_ground_l2 = union_all([
        shp(poly) for zone in geometry["zones"]
        if zone["layer"] == "In1.Cu" and zone["net"] == "/GND"
        for poly in zone["polygons"]
    ])
    inner_ground_l3 = union_all([
        shp(poly) for zone in geometry["zones"]
        if zone["layer"] == "In2.Cu" and zone["net"] == "/GND"
        for poly in zone["polygons"]
    ])
    forbidden_probe = box(-15.5, -half_gap + 0.01, 15.5, half_gap - 0.01)
    if (not inner_ground_l2.intersection(forbidden_probe).is_empty or
            not inner_ground_l3.intersection(forbidden_probe).is_empty):
        raise RuntimeError("Saved inner-layer return enters the ferrite span")
    top_ground_parts = [shp(poly) for zone in geometry["zones"]
                        if zone["layer"] == "F.Cu" and zone["net"] == "/GND"
                        for poly in zone["polygons"]]
    bottom_ground_parts = [shp(poly) for zone in geometry["zones"]
                           if zone["layer"] == "B.Cu" and zone["net"] == "/GND"
                           for poly in zone["polygons"]]
    top_ground = union_all(top_ground_parts)
    bottom_ground = union_all(bottom_ground_parts)

    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)

    fr4 = csx.AddMaterial("FR4", epsilon=4.4, kappa=0.0)
    cutout_air = csx.AddMaterial("AIR_CUTOUT", epsilon=1.0, kappa=0.0)
    # Keep each dielectric slab as one continuous outer prism.  Triangulating
    # the dielectric into hundreds of coincident prisms caused the RC solver's
    # primitive-priority rasterizer to discard embedded L2 polygons.  The two
    # board windows and NPTHs are restored as higher-priority air volumes.
    outline = geometry["outline"][0]
    triangles = add_prism(fr4, outline["outer"], l4_z,
                          l3_z - l4_z, 1)
    triangles += add_prism(fr4, outline["outer"], l3_z,
                           l2_z - l3_z, 1)
    triangles += add_prism(fr4, outline["outer"], l2_z,
                           l1_z - l2_z, 1)
    for ring in outline.get("holes", []):
        triangles += add_prism(cutout_air, ring, l4_z, l1_z - l4_z, 5)
    for hole in npth:
        triangles += add_prism(cutout_air, hole.exterior.coords[:-1],
                               l4_z, l1_z - l4_z, 5)
    # Create each metal property immediately before adding its primitives,
    # bottom-to-top.  This matches the validated CSX live-object construction
    # path; the RC wrapper produced a different raster when all empty Metal
    # objects were pre-created, despite writing byte-identical XML.
    sheet_priority = 12
    gnd_l4 = csx.AddMetal("B_Cu_GND")
    triangles += add_polygons(gnd_l4, bottom_ground, l4_z, sheet_priority)
    gnd_l3 = csx.AddMetal("In2_Cu_GND")
    triangles += add_polygons(gnd_l3, inner_ground_l3, l3_z, sheet_priority)
    gnd_l2 = csx.AddMetal("In1_Cu_GND")
    triangles += add_polygons(gnd_l2, inner_ground_l2, l2_z, sheet_priority)
    gnd_l1 = csx.AddMetal("F_Cu_GND")
    triangles += add_polygons(gnd_l1, top_ground, l1_z, sheet_priority)
    sig = csx.AddMetal("F_Cu_SIG")
    triangles += add_polygons(sig, signal, l1_z, sheet_priority)

    # Existing GND drill centres provide distributed L1-L4 return stitching.
    vias = csx.AddMetal("GND_VIAS")
    gnd_vias = [p for p in geometry["vias"] if p["net"] == "/GND"]
    for p in gnd_vias:
        vias.AddCylinder(priority=18, start=[p["x"], p["y"], 0], stop=[p["x"], p["y"], h], radius=p["drill"] / 2)

    xm = args.xy_mesh_mm
    x_anchors = [-72, -34.3, -15.51, -args.wide_width_mm / 2,
                 -args.launch_width_mm / 2, 0, args.launch_width_mm / 2,
                 args.wide_width_mm / 2, 15.51, 34.3, 72]
    y_anchors = [-46.35, -34.35, 34.35, 46.35] + list(signal_dims.values())
    xs = smooth_axis(x_anchors, [(-76, -36, 1.6), (-36, 36, xm), (36, 76, 1.6)], 76 + args.margin_mm)
    ys = smooth_axis(y_anchors, [(-51, -18, 1.2), (-18, 18, xm), (18, 51, 1.2)], 51 + args.margin_mm)
    z_anchors = [0, l3_z, l2_z, l1_z, 3]
    zs = smooth_axis(z_anchors, [(-3, 3, args.z_mesh_mm)], args.margin_mm)
    # Lumped reference planes are on uniform 50-ohm L1/L2 microstrip, away
    # from both tapers.  Their small boxes are forced onto mesh nodes.
    x_required = [-args.wide_width_mm / 2, -args.launch_width_mm / 2, 0,
                  args.launch_width_mm / 2, args.wide_width_mm / 2]
    y_required = [-46.35, 46.35] + list(signal_dims.values())
    z_required = [0, l3_z, l2_z, l1_z]
    for y in [-30.0, 30.0]:
        y_required += [y - 0.25, y, y + 0.25]
    # Resolve every solid 0.3 mm GND via at its centre and wall.  Without
    # these anchors the cylinders can fall wholly between x/y grid lines and
    # disappear from the PEC operator.
    for via in gnd_vias:
        radius = via["drill"] / 2
        x_required += [via["x"] - radius, via["x"], via["x"] + radius]
        y_required += [via["y"] - radius, via["y"], via["y"] + radius]
    xs = force_required(xs, x_required, clearance=0.12)
    ys = force_required(ys, y_required, clearance=0.12)
    zs = force_required(zs, z_required, clearance=0.12)
    for axis, lines in zip("xyz", [xs, ys, zs]):
        grid.SetLines(axis, lines)

    # Construct openEMS only after CSX geometry and grid are complete.  In the
    # 0.37.0-rc2 Python wrapper, constructing the FDTD object before adding the
    # multilayer properties produced a different live raster even when the
    # subsequently written CSX XML was byte-equivalent.
    fdtd = (openEMS(NrTS=1000, EndCriteria=1e-4) if args.setup else
            openEMS(NrTS=args.max_steps, EndCriteria=args.end_criteria,
                    MaxTime=args.max_ns * 1e-9))
    # Attach the completed CSX geometry before creating FDTD ports.  Attaching
    # an empty CSX and then adding multilayer sheets produced a different PEC
    # raster in openEMS 0.37.0-rc2 despite byte-equivalent saved XML.
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond(["PML_8"] * 6)
    ports = {}
    for number, y in [(1, -30.0), (2, 30.0)]:
        start = [-args.launch_width_mm / 2, y - 0.25, l2_z]
        stop = [args.launch_width_mm / 2, y + 0.25, l1_z]
        ports[number] = fdtd.AddLumpedPort(number, 50, start, stop, "z", excite=1 if number == 1 else 0, priority=40)

    probe_names = []
    for i, y in enumerate([-5.0, 0.0, 5.0]):
        name = f"probe_{i}"
        probe = csx.AddProbe(name, p_type=1, weight=1, norm_dir=1)
        probe.AddBox(start=[-16.0, y, -0.5], stop=[16.0, y, 2.1])
        probe_names.append(name)

    mesh = [len(grid.GetLines(axis)) for axis in "xyz"]
    min_cell = [float(np.min(np.diff(grid.GetLines(axis)))) for axis in "xyz"]
    meta = {
        "classification": "SIMULATED_STRUCTURE_TOPOLOGY_NOT_MEASURED",
        "parameters": vars(args),
        "stack_mm": {"L1": l1_z, "L2": l2_z, "L3": l3_z, "L4": l4_z},
        "signal_geometry": signal_dims,
        "signal_geometry_source": "saved KiCad F.Cu /SIG zone polygons",
        "analytical_to_saved_signal_symmetric_difference_mm2": signal_geometry_delta_mm2,
        "mesh": mesh,
        "min_cell_mm": min_cell,
        "cells": int(np.prod([n - 1 for n in mesh])),
        "triangle_primitives": triangles,
        "gnd_vias": len(gnd_vias),
        "source_geometry": str(geometry_path.relative_to(ROOT)),
        "source_geometry_sha256": hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
        "inner_return_source": "saved KiCad In1.Cu/In2.Cu GND zone polygons",
        "dielectric_segmentation": "three continuous outer prisms at copper elevations; saved windows/NPTHs are air prisms",
        "copper_sheet_priority": sheet_priority,
        "copper_insertion_order": "L4, L3, L2, L1 GND, L1 SIG",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "openems": openems_package.__version__,
        "csxcad": CSXCAD.__version__,
        "reference_plane": "ideal 50-ohm vertical lumped port on L1/L2 microstrip; connector omitted",
        "limitations": [
            "No SMA body, ferrite, winding, head, cable, conductor/dielectric loss or solder mask.",
            "The homogeneous epsilon=4.4 board is a stackup screening assumption.",
            "The model verifies the return interruption and structural match topology, not finished calibration accuracy.",
        ],
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if not args.post:
        (out / "model_source.py").write_bytes(Path(__file__).read_bytes())
        csx.Write2XML(str(out / "model.xml"))
        print(json.dumps({"out": str(out), "mesh": mesh, "min_cell_mm": min_cell, "cells": meta["cells"]}), flush=True)
        if args.mesh_only:
            (out / "MESH_TEMPLATE_ONLY.txt").write_text(
                "Grid template only. No solver setup or RF result was run.\n",
                encoding="utf-8")
            return
        if args.setup:
            # Keep the connectivity audit on the wrapper's default operator;
            # it must not depend on the production thread/engine selection.
            fdtd.Run(str(out), setup_only=True, verbose=1,
                     debug_PEC=args.debug_pec)
        else:
            fdtd.Run(str(out), cleanup=False, setup_only=False, verbose=1,
                     numThreads=args.threads, engine="multithreaded",
                     dump_statistics=True, debug_PEC=args.debug_pec)
        fdtd.Write2XML(str(out / "solver.xml"))
    if args.setup:
        return

    freq = np.unique(np.r_[np.linspace(100e6, 500e6, 401),
                           np.asarray([100, 150, 200, 300, 400, 500]) * 1e6])
    for port in ports.values():
        port.CalcPort(str(out), freq, ref_impedance=50)
    p1, p2 = ports[1], ports[2]
    s11 = p1.uf_ref / p1.uf_inc
    s21 = p2.uf_ref / p1.uf_inc
    currents = {name: UI_data(name, str(out), freq).ui_f_val[0] for name in probe_names}
    centre = currents["core_1"]
    ideal = p1.uf_inc / 50
    ratio = centre / ideal
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
            "along_core_current_variation_percent": float(100 * max(abs(currents[n][i] - centre[i]) for n in probe_names) / max(abs(centre[i]), 1e-30)),
            "passivity_sum": float(abs(s11[i]) ** 2 + abs(s21[i]) ** 2),
        })
    meta["rows"] = rows
    band = {
        "worst_S11_dB": float(max(row["S11_dB"] for row in rows)),
        "max_center_current_magnitude_error_percent": float(100 * max(abs(row["I_center_over_matched_mag"] - 1) for row in rows)),
        "max_along_core_current_variation_percent": float(max(row["along_core_current_variation_percent"] for row in rows)),
    }
    meta["metrics_100_500_MHz"] = band
    (out / "results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out / "response.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    anchors = [row for row in rows if row["f_Hz"] in {100e6, 150e6, 200e6, 300e6, 400e6, 500e6}]
    print(json.dumps({"metrics": band, "anchors": anchors}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
