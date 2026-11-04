"""Audit rasterized A06 cage/bar PEC topology from the openEMS VTK dump."""
from pathlib import Path
import argparse
import json

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    dump = args.run_dir / "PEC_dump.vtp"
    model = json.loads((args.run_dir / "model.json").read_text(encoding="utf-8"))
    bar_z0, bar_z1 = model["geometry_mm"]["current_bar"]["z"]
    cage_geometry = model["geometry_mm"].get("cage")
    reader = vtk.vtkXMLPolyDataReader(); reader.SetFileName(str(dump)); reader.Update()
    poly = reader.GetOutput()
    points = vtk_to_numpy(poly.GetPoints().GetData())*1e3
    raw = vtk_to_numpy(poly.GetLines().GetData())
    edges, cursor = [], 0
    while cursor < len(raw):
        n = int(raw[cursor]); ids = raw[cursor+1:cursor+1+n]
        edges.extend((int(ids[i]), int(ids[i+1])) for i in range(n-1))
        cursor += n+1
    rows = np.array([i for e in edges for i in e])
    cols = np.array([i for e in edges for i in (e[1], e[0])])
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)),
                       shape=(len(points), len(points))).tocsr()
    count, labels = connected_components(graph, directed=False)
    sizes = np.bincount(labels)

    def query(target):
        target = np.asarray(target, dtype=float)
        index = int(np.argmin(np.linalg.norm(points-target, axis=1)))
        return {"target_mm": target.tolist(), "point_mm": points[index].tolist(),
                "distance_mm": float(np.linalg.norm(points[index]-target)),
                "component": int(labels[index]),
                "component_size": int(sizes[labels[index]])}

    q = {
        "sig_in": query([0, -30, 1.6]),
        "sig_bar_top": query([0, 0, bar_z1]),
        "sig_bar_bottom": query([0, 0, bar_z0]),
        "sig_out": query([0, 30, 1.6]),
        "gnd_plane": query([38, -25, 1.3896]),
    }
    if cage_geometry:
        q.update({
            "cage_side": query([cage_geometry["half_x"], 0, .8]),
            "cage_top": query([0, 0, cage_geometry["z"][1]]),
            "cage_bottom": query([0, 0, cage_geometry["z"][0]]),
        })
    sig_names = ["sig_in", "sig_bar_top", "sig_bar_bottom", "sig_out"]
    gnd_names = (["gnd_plane", "cage_side", "cage_top", "cage_bottom"]
                 if cage_geometry else ["gnd_plane"])
    checks = {
        "signal_bar_connected": len({q[n]["component"] for n in sig_names}) == 1,
        "cage_connected_to_planar_return": (len({q[n]["component"] for n in gnd_names}) == 1
                                              if cage_geometry else True),
        "signal_not_ground": q["sig_in"]["component"] != q["gnd_plane"]["component"],
        "all_queries_on_target_within_0p05mm": all(q[n]["distance_mm"] < .05 for n in q),
        "exactly_two_pec_nets": count == 2,
    }
    out = {"classification": "CALCULATED_FROM_SIMULATOR_PEC_DUMP",
           "dump": str(dump), "points": len(points), "components": int(count),
           "component_sizes": sorted([int(v) for v in sizes], reverse=True),
           "queries": q, "checks": checks, "pass": all(checks.values())}
    (args.run_dir/"a06_connectivity.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
