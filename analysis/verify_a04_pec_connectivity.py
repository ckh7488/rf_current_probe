"""Verify that an A04 openEMS PEC dump has one SIG and one stitched GND net."""
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
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(str(dump))
    reader.Update()
    poly = reader.GetOutput()
    points = vtk_to_numpy(poly.GetPoints().GetData()) * 1e3
    raw = vtk_to_numpy(poly.GetLines().GetData())
    edges = []
    cursor = 0
    while cursor < len(raw):
        count = int(raw[cursor])
        ids = raw[cursor + 1:cursor + 1 + count]
        edges.extend((int(ids[i]), int(ids[i + 1]))
                     for i in range(count - 1))
        cursor += count + 1
    rows = np.array([v for edge in edges for v in (edge[0], edge[1])])
    cols = np.array([v for edge in edges for v in (edge[1], edge[0])])
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)),
                       shape=(len(points), len(points))).tocsr()
    count, labels = connected_components(graph, directed=False)
    sizes = np.bincount(labels)

    def query(target, z=None):
        mask = (np.ones(len(points), dtype=bool) if z is None else
                np.isclose(points[:, 2], z, atol=2e-4))
        candidates = np.flatnonzero(mask)
        index = candidates[np.argmin(np.linalg.norm(
            points[candidates] - np.asarray(target), axis=1))]
        return {"target_mm": target, "point_mm": points[index].tolist(),
                "distance_mm": float(np.linalg.norm(points[index] - target)),
                "component": int(labels[index]),
                "component_size": int(sizes[labels[index]])}

    q = {
        "sig_in": query((0, -30, 1.6), 1.6),
        "sig_mid": query((0, 0, 1.6), 1.6),
        "sig_out": query((0, 30, 1.6), 1.6),
        "l2_in": query((2, -25, 1.3896), 1.3896),
        "l2_out": query((2, 25, 1.3896), 1.3896),
        "l3_in": query((2, -25, 0.2104), 0.2104),
        "l4_in": query((2, -25, 0), 0),
        "via_mid": query((-56, -25, 0.8)),
    }
    checks = {
        "signal_through": (q["sig_in"]["component"] ==
                           q["sig_mid"]["component"] ==
                           q["sig_out"]["component"]),
        "stitched_return": len({q[name]["component"] for name in
                                ["l2_in", "l2_out", "l3_in", "l4_in",
                                 "via_mid"]}) == 1,
        "signal_not_ground": (q["sig_mid"]["component"] !=
                              q["l2_in"]["component"]),
        "exactly_two_pec_nets": count == 2,
    }
    report = {
        "classification": "CALCULATED_FROM_SIMULATOR_PEC_DUMP",
        "dump": str(dump),
        "points": len(points),
        "components": int(count),
        "component_sizes": sorted([int(v) for v in sizes], reverse=True),
        "queries": q,
        "checks": checks,
        "pass": all(checks.values()),
    }
    (args.run_dir / "connectivity.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
