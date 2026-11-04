"""Coarse raster audit of the four saved A04 copper layers.

This setup-only model isolates CSXCAD/openEMS rasterization from the expensive
RF solve.  It is diagnostic evidence only and does not produce S-parameters.
"""
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import json
import os

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "openems" / "v0.37.0-rc2" / "runtime" / "openEMS"
os.environ["OPENEMS_INSTALL_PATH"] = str(RUNTIME)
os.environ["CSXCAD_INSTALL_PATH"] = str(RUNTIME)

import numpy as np
from shapely import constrained_delaunay_triangles, union_all
from shapely.geometry import Polygon
from shapely.geometry import Point
from CSXCAD import ContinuousStructure
from openEMS import openEMS


def shape(row):
    return Polygon(row["outer"], row.get("holes", []))


def add_area(prop, area, z, priority=10):
    n = 0
    for tri in constrained_delaunay_triangles(area).geoms:
        if not area.covers(tri.representative_point()):
            continue
        prop.AddPolygon(priority=priority,
                        points=np.asarray(tri.exterior.coords[:-1]).T.tolist(),
                        norm_dir=2, elevation=z)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dielectric", action="store_true")
    ap.add_argument("--vias", action="store_true")
    ap.add_argument("--ports", action="store_true")
    ap.add_argument("--structural-mesh", action="store_true")
    ap.add_argument("--pml", action="store_true")
    ap.add_argument("--probes", action="store_true")
    ap.add_argument("--priority12", action="store_true")
    ap.add_argument("--npth", action="store_true")
    args = ap.parse_args()
    suffix = "_" + "_".join(k for k, v in vars(args).items() if v) if any(vars(args).values()) else ""
    out = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em" / ("a04_layer_raster_audit" + suffix)
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "reviews" / "fixture_structural_redesign_20260922" /
                       "a04_saved_geometry.json").read_text())
    zmap = {"B.Cu": 0.0, "In2.Cu": 0.2104,
            "In1.Cu": 1.3896, "F.Cu": 1.6}
    csx = ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)
    if args.structural_mesh:
        src = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em" / "structural_connectivity_prism_m080" / "model.xml"
        xml = ET.parse(src).getroot()
        def axis_values(tag):
            node = next(xml.iter(tag))
            return [float(v) for v in node.text.split(",")]
        xs, ys, zs = axis_values("XLines"), axis_values("YLines"), axis_values("ZLines")
    else:
        xs = np.unique(np.r_[np.arange(-76, 77, 2), -72, -51, -4, 0, 4, 51, 72])
        ys = np.unique(np.r_[np.arange(-50, 51, 2), -46.35, -34.35, -7.5, 0,
                             7.5, 34.35, 46.35])
        zs = [-2, -1, 0, 0.2104, 0.8, 1.3896, 1.6, 2, 3]
    for axis, lines in zip("xyz", [xs, ys, zs]):
        grid.SetLines(axis, lines)
    if args.dielectric:
        fr4 = csx.AddMaterial("FR4", epsilon=4.4)
        air = csx.AddMaterial("AIR_CUTOUT", epsilon=1.0)
        outline = data["outline"][0]
        outer = np.asarray(outline["outer"]).T.tolist()
        for z0, z1 in [(0, 0.2104), (0.2104, 1.3896), (1.3896, 1.6)]:
            fr4.AddLinPoly(priority=1, points=outer, norm_dir=2,
                           elevation=z0, length=z1-z0)
        for ring in outline.get("holes", []):
            air.AddLinPoly(priority=5, points=np.asarray(ring).T.tolist(),
                           norm_dir=2, elevation=0, length=1.6)
        if args.npth:
            for pad in data["pads"]:
                if pad["plated"]:
                    continue
                ring = Point(pad["x"], pad["y"]).buffer(
                    pad["drill"] / 2, quad_segs=12).exterior.coords[:-1]
                air.AddLinPoly(priority=5, points=np.asarray(ring).T.tolist(),
                               norm_dir=2, elevation=0, length=1.6)
    count = {}
    for layer, z in zmap.items():
        for net in ["/GND", "/SIG"]:
            parts = [shape(poly) for zone in data["zones"]
                     if zone["layer"] == layer and zone["net"] == net
                     for poly in zone["polygons"]]
            if not parts:
                continue
            prop = csx.AddMetal((layer + net).replace(".", "_").replace("/", "_"))
            count[layer + net] = add_area(prop, union_all(parts), z,
                                           12 if args.priority12 else 10)
    if args.vias:
        via_prop = csx.AddMetal("GND_VIAS")
        for via in data["vias"]:
            if via["net"] == "/GND":
                via_prop.AddCylinder(priority=18,
                                     start=[via["x"], via["y"], 0],
                                     stop=[via["x"], via["y"], 1.6],
                                     radius=via["drill"] / 2)
    fdtd = openEMS(NrTS=1000, EndCriteria=1e-4)
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(300e6, 300e6)
    fdtd.SetBoundaryCond((["PML_8"] if args.pml else ["MUR"]) * 6)
    if args.ports:
        for number, y in [(1, -30.0), (2, 30.0)]:
            fdtd.AddLumpedPort(number, 50, [-0.179324, y-0.25, 1.3896],
                               [0.179324, y+0.25, 1.6], "z",
                               excite=number == 1, priority=40)
    if args.probes:
        for i, y in enumerate([-5.0, 0.0, 5.0]):
            probe = csx.AddProbe(f"probe_{i}", p_type=1, weight=1, norm_dir=1)
            probe.AddBox(start=[-4.5, y, -0.5], stop=[4.5, y, 2.1])
    (out / "primitive_counts.json").write_text(json.dumps(count, indent=2))
    csx.Write2XML(str(out / "model.xml"))
    fdtd.Run(str(out), setup_only=True, debug_PEC=True, verbose=1)


if __name__ == "__main__":
    main()
