"""Validated saved-geometry openEMS model for A04, 100--500 MHz.

The CSX construction order in this file is intentionally identical to the
four-layer raster audit that retained every copper sheet in openEMS
0.37.0-rc2.  Do not pre-create empty Metal properties or construct the FDTD
object before the CSX geometry is complete without repeating the PEC audit.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

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
from openEMS import openEMS
from openEMS.ports import UI_data


# The ideal ports de-embed the unknown physical SMA at y = +/-30 mm. End the
# model at each 0.5 mm lumped-port box's outer face so no artificial
# connector-side open stub remains in parallel with the fixture.
REFERENCE_Y_MM = 30.0
MODEL_Y_MIN_MM = -30.25
MODEL_Y_MAX_MM = 30.25


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--mesh-xml", required=True)
    p.add_argument("--setup", action="store_true")
    p.add_argument("--post", action="store_true")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--max-steps", type=int, default=260000)
    p.add_argument("--max-ns", type=float, default=30.0)
    p.add_argument("--end-criteria", type=float, default=1e-5)
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


def axis_values(xml: ET.Element, tag: str) -> list[float]:
    node = next(xml.iter(tag))
    return [float(value) for value in node.text.split(",")]


def main() -> None:
    args = parse_args()
    out = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em" / args.name
    if out.exists() and not args.post:
        raise RuntimeError(f"Refuse to overwrite {out}")
    out.mkdir(parents=True, exist_ok=args.post)

    geometry_path = (ROOT / "reviews" / "fixture_structural_redesign_20260922" /
                     "a04_saved_geometry.json")
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    mesh_path = (ROOT / args.mesh_xml).resolve()
    mesh_xml = ET.parse(mesh_path).getroot()
    xs, ys, zs = (axis_values(mesh_xml, tag)
                  for tag in ("XLines", "YLines", "ZLines"))

    zmap = {"B.Cu": 0.0, "In2.Cu": 0.2104,
            "In1.Cu": 1.3896, "F.Cu": 1.6}
    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)
    for axis, lines in zip("xyz", [xs, ys, zs]):
        grid.SetLines(axis, lines)

    # Same live-object order as debug_openems_a04_layers.py.
    prepreg = csx.AddMaterial("PREPREG_7628", epsilon=4.4)
    core = csx.AddMaterial("CORE_1065", epsilon=4.6)
    air = csx.AddMaterial("AIR_CUTOUT", epsilon=1.0)
    outline = geometry["outline"][0]
    model_clip = box(-1000, MODEL_Y_MIN_MM, 1000, MODEL_Y_MAX_MM)
    clipped_outer = Polygon(outline["outer"]).intersection(model_clip)
    assert clipped_outer.geom_type == "Polygon"
    outer = np.asarray(clipped_outer.exterior.coords[:-1]).T.tolist()
    for material, z0, z1 in [
            (prepreg, 0, 0.2104),
            (core, 0.2104, 1.3896),
            (prepreg, 1.3896, 1.6)]:
        material.AddLinPoly(priority=1, points=outer, norm_dir=2,
                            elevation=z0, length=z1-z0)
    for ring in outline.get("holes", []):
        clipped = Polygon(ring).intersection(model_clip)
        for part in ([clipped] if clipped.geom_type == "Polygon" else clipped.geoms):
            if not part.is_empty:
                air.AddLinPoly(priority=5,
                               points=np.asarray(part.exterior.coords[:-1]).T.tolist(),
                               norm_dir=2, elevation=0, length=1.6)
    for pad in geometry["pads"]:
        if pad["plated"]:
            continue
        hole = Point(pad["x"], pad["y"]).buffer(
            pad["drill"] / 2, quad_segs=12).intersection(model_clip)
        if hole.is_empty:
            continue
        for part in ([hole] if hole.geom_type == "Polygon" else hole.geoms):
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
            prop = csx.AddMetal((layer + net).replace(".", "_").replace("/", "_"))
            primitive_counts[layer + net] = add_area(
                prop, union_all(parts).intersection(model_clip), z, priority=12)

    via_prop = csx.AddMetal("GND_VIAS")
    gnd_vias = [
        via for via in geometry["vias"]
        if via["net"] == "/GND"
        and MODEL_Y_MIN_MM <= via["y"] <= MODEL_Y_MAX_MM
    ]
    for via in gnd_vias:
        via_prop.AddCylinder(priority=18,
                             start=[via["x"], via["y"], 0],
                             stop=[via["x"], via["y"], 1.6],
                             radius=via["drill"] / 2)

    fdtd = (openEMS(NrTS=1000, EndCriteria=1e-4) if args.setup else
            openEMS(NrTS=args.max_steps, EndCriteria=args.end_criteria,
                    MaxTime=args.max_ns * 1e-9))
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond(["PML_8"] * 6)
    ports = {}
    for number, y in [(1, -REFERENCE_Y_MM), (2, REFERENCE_Y_MM)]:
        ports[number] = fdtd.AddLumpedPort(
            number, 50, [-0.179324, y-0.25, 1.3896],
            [0.179324, y+0.25, 1.6], "z",
            excite=number == 1, priority=40)
    probe_names = []
    for i, y in enumerate([-5.0, 0.0, 5.0]):
        name = f"probe_{i}"
        probe = csx.AddProbe(name, p_type=1, weight=1, norm_dir=1)
        probe.AddBox(start=[-4.5, y, -0.5], stop=[4.5, y, 2.1])
        probe_names.append(name)

    mesh = [len(grid.GetLines(axis)) for axis in "xyz"]
    meta = {
        "classification": "SIMULATED_STRUCTURE_TOPOLOGY_NOT_MEASURED",
        "parameters": vars(args),
        "mesh": mesh,
        "min_cell_mm": [float(np.min(np.diff(grid.GetLines(axis)))) for axis in "xyz"],
        "cells": int(np.prod([n - 1 for n in mesh])),
        "primitive_counts": primitive_counts,
        "gnd_vias": len(gnd_vias),
        "source_geometry": str(geometry_path.relative_to(ROOT)),
        "source_geometry_sha256": hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
        "mesh_template": str(mesh_path.relative_to(ROOT)),
        "mesh_template_sha256": hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "openems": openems_package.__version__,
        "csxcad": CSXCAD.__version__,
        "reference_plane": (
            "ideal 50-ohm vertical lumped ports at y=+/-30 mm between saved "
            "L1 SIG and In1 return; copper and dielectric end at the port-box "
            "outer edges y=+/-30.25 mm so no connector-side open stub remains"
        ),
        "reference_plane_clip_mm": [MODEL_Y_MIN_MM, MODEL_Y_MAX_MM],
        "dielectric_model": {
            "outer_prepreg_er": 4.4,
            "central_core_er": 4.6,
            "layer_boundaries_mm": [0, 0.2104, 1.3896, 1.6],
            "note": "Nominal JLC04161H-7628 seed; copper thickness and resin/glass dispersion are not separately resolved.",
        },
        "limitations": [
            "Empty de-embedded fixture: no ferrite, winding, head, cable, SMA body, loss or solder mask.",
            "Saved A04 copper is clipped only outside the y=+/-30 mm reference planes; the omitted 4.35 mm launch remainder and physical SMA require measurement.",
            "Lossless nominal Dk4.4 outer prepreg and Dk4.6 central core are structural screening materials without dispersion.",
            "PEC connectivity must be accepted from PEC_dump.vtp before RF results are used.",
        ],
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if not args.post:
        (out / "model_source.py").write_bytes(Path(__file__).read_bytes())
        csx.Write2XML(str(out / "model.xml"))
        print(json.dumps({"out": str(out), "mesh": mesh,
                          "cells": meta["cells"]}), flush=True)
        if args.setup:
            fdtd.Run(str(out), setup_only=True, debug_PEC=True, verbose=1)
        else:
            fdtd.Run(str(out), setup_only=False, debug_PEC=True, verbose=1,
                     numThreads=args.threads, engine="multithreaded",
                     dump_statistics=True)
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
    currents = {name: UI_data(name, str(out), freq).ui_f_val[0]
                for name in probe_names}
    centre = currents["probe_1"]
    ratio = centre / (p1.uf_inc / 50)
    rows = []
    for i, frequency in enumerate(freq):
        rows.append({
            "f_Hz": float(frequency),
            "S11_dB": float(20*np.log10(max(abs(s11[i]), 1e-30))),
            "S21_dB": float(20*np.log10(max(abs(s21[i]), 1e-30))),
            "S11_re": float(s11[i].real), "S11_im": float(s11[i].imag),
            "S21_re": float(s21[i].real), "S21_im": float(s21[i].imag),
            "I_center_over_matched_mag": float(abs(ratio[i])),
            "I_center_over_matched_phase_deg": float(np.angle(ratio[i], deg=True)),
            "along_core_current_variation_percent": float(
                100*max(abs(currents[name][i]-centre[i]) for name in probe_names)
                / max(abs(centre[i]), 1e-30)),
            "passivity_sum": float(abs(s11[i])**2 + abs(s21[i])**2),
        })
    meta["rows"] = rows
    meta["metrics_100_500_MHz"] = {
        "worst_S11_dB": float(max(row["S11_dB"] for row in rows)),
        "max_center_current_magnitude_error_percent": float(
            100*max(abs(row["I_center_over_matched_mag"]-1) for row in rows)),
        "max_along_core_current_variation_percent": float(
            max(row["along_core_current_variation_percent"] for row in rows)),
        "max_passivity_sum": float(max(row["passivity_sum"] for row in rows)),
    }
    (out / "results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out / "response.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    anchors = [row for row in rows if row["f_Hz"] in
               {100e6, 150e6, 200e6, 300e6, 400e6, 500e6}]
    print(json.dumps({"metrics": meta["metrics_100_500_MHz"],
                      "anchors": anchors}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
