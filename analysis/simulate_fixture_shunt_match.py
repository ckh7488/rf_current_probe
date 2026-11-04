"""SIMULATED candidate: add two ideal lumped shunt capacitors to saved A03 EM.

The saved, independently audited A03 CSX geometry and mesh are loaded without
changing the PCB conductors.  Ideal lumped capacitors are connected from SIG
to the adjacent GND copper on the top face, outside the core window.  This is
an intermediate topology check before drawing A04 pads and stack-up in KiCad.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "openems" / "v0.37.0-rc2" / "runtime" / "openEMS"
os.environ["OPENEMS_INSTALL_PATH"] = str(RUNTIME)
os.environ["CSXCAD_INSTALL_PATH"] = str(RUNTIME)

import numpy as np
import CSXCAD
import openEMS as openems_package
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.ports import Port, UI_data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="reviews/document_full_audit_20260922/em/z020")
    p.add_argument("--name", default="c62_c27_z020")
    p.add_argument("--cin-pf", type=float, default=6.2)
    p.add_argument("--cout-pf", type=float, default=2.7)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--setup", action="store_true")
    p.add_argument("--post", action="store_true")
    return p.parse_args()


def read_port(csx: ContinuousStructure, number: int) -> Port:
    port = Port(
        csx,
        port_nr=number,
        start=[0, 0, 0],
        stop=[1, 1, 1],
        excite=number == 1,
        U_filenames=[f"port_ut_{number}"],
        I_filenames=[f"port_it_{number}"],
    )
    port.Z_ref = 50.0
    return port


def main() -> None:
    args = parse_args()
    source = ROOT / args.source
    out = ROOT / "reviews" / "fixture_match_redesign_20260922" / "em" / args.name
    if out.exists() and not args.post:
        raise RuntimeError(f"Refuse to overwrite {out}")
    out.mkdir(parents=True, exist_ok=args.post)

    csx = ContinuousStructure()
    csx.ReadFromXML(str(source / "model.xml"))
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)

    # Input is J1 at negative y.  At y=-26/+26 mm the existing F.Cu SIG edge
    # is x=+0.5 mm and GND begins at x=+0.856 mm.  The boxes overlap each PEC
    # terminal by 0.05 mm and span a thin volume above/below F.Cu; this is
    # required for an active Yee-cell RLC load after reloading the saved XML.
    # Physical 0402 pads, solder and component ESL are deferred to A04 EM.
    locations = [
        ("C_IN_ideal", args.cin_pf, -26.0),
        ("C_OUT_ideal", args.cout_pf, 26.0),
    ]
    for name, value_pf, y in locations:
        # ``caps`` adds PEC end caps to the lumped box; it is useful for the
        # port feed resistor but can short a shunt capacitor into the adjacent
        # sheet copper.  The capacitance itself is selected by ``C``.
        cap = csx.AddLumpedElement(name, ny="x", C=value_pf * 1e-12)
        cap.AddBox(start=[0.45, y - 0.30, 1.55], stop=[0.906, y + 0.30, 1.65], priority=40)
        grid.AddLine("x", [0.45, 0.5, 0.856, 0.906])
        grid.AddLine("y", [y - 0.30, y, y + 0.30])
        grid.AddLine("z", [1.55, 1.6, 1.65])

    source_meta = json.loads((source / "model.json").read_text(encoding="utf-8"))
    params = source_meta["parameters"]
    fdtd = openEMS(
        NrTS=int(params["max_steps"]),
        EndCriteria=float(params["end_criteria"]),
        MaxTime=float(params["max_ns"]) * 1e-9,
    )
    fdtd.SetCSX(csx)
    fdtd.SetGaussExcite(float(params["f0_mhz"]) * 1e6, float(params["fmax_mhz"]) * 1e6)
    fdtd.SetBoundaryCond(["PML_8"] * 6)

    meta = {
        "classification": "SIMULATED_TOPOLOGY_CANDIDATE_NOT_MEASURED",
        "source_model": str(source.relative_to(ROOT)),
        "source_model_xml_sha256": hashlib.sha256((source / "model.xml").read_bytes()).hexdigest(),
        "source_board_sha256": source_meta["source_board_sha256"],
        "capacitors": [
            {"name": name, "C_pF": value, "y_mm": y, "model": "ideal lumped, no ESR/ESL/package"}
            for name, value, y in locations
        ],
        "mesh": [len(grid.GetLines(axis)) for axis in "xyz"],
        "cells": int(np.prod([len(grid.GetLines(axis)) - 1 for axis in "xyz"])),
        "openems": openems_package.__version__,
        "csxcad": CSXCAD.__version__,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limitations": [
            "Existing A03 two-layer copper and idealized SMA model are retained; this is not the future four-layer A04 launch.",
            "Capacitors are ideal lumped elements connected at the existing copper gap; package pads, solder, ESR and ESL are absent.",
            "No ferrite core, winding, probe head, real connector internals, conductor loss or bench cable is included.",
            "Results screen the passive-match topology only and cannot authorize fabrication or claim calibration accuracy.",
        ],
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if not args.post:
        (out / "model_source.py").write_bytes(Path(__file__).read_bytes())
        csx.Write2XML(str(out / "model.xml"))
        print(json.dumps({"out": str(out), "mesh": meta["mesh"], "cells": meta["cells"]}), flush=True)
        fdtd.Run(
            str(out),
            cleanup=False,
            setup_only=args.setup,
            verbose=1,
            numThreads=args.threads,
            engine="multithreaded",
            dump_statistics=True,
        )
    if args.setup:
        return

    freq = np.unique(np.r_[
        np.geomspace(1e6, 500e6, 301),
        np.array([1, 10, 30, 100, 150, 200, 300, 500]) * 1e6,
    ])
    p1, p2 = read_port(csx, 1), read_port(csx, 2)
    p1.CalcPort(str(out), freq, ref_impedance=50)
    p2.CalcPort(str(out), freq, ref_impedance=50)
    s11 = p1.uf_ref / p1.uf_inc
    s21 = p2.uf_ref / p1.uf_inc
    core = UI_data("core_2_0", str(out), freq).ui_f_val[0]
    ideal_current = p1.uf_inc / 50
    ratio = core / ideal_current
    rows = []
    for i, f in enumerate(freq):
        rows.append({
            "f_Hz": float(f),
            "S11_re": float(s11[i].real),
            "S11_im": float(s11[i].imag),
            "S11_dB": float(20 * np.log10(abs(s11[i]))),
            "S21_re": float(s21[i].real),
            "S21_im": float(s21[i].imag),
            "S21_dB": float(20 * np.log10(abs(s21[i]))),
            "I_center_over_matched_re": float(ratio[i].real),
            "I_center_over_matched_im": float(ratio[i].imag),
            "I_center_over_matched_mag": float(abs(ratio[i])),
            "I_center_over_matched_phase_deg": float(np.angle(ratio[i], deg=True)),
        })
    meta["rows"] = rows
    (out / "results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    import csv
    with (out / "response.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    anchors = [r for r in rows if r["f_Hz"] in {1e6, 10e6, 30e6, 100e6, 150e6, 200e6, 300e6, 500e6}]
    print(json.dumps(anchors, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
