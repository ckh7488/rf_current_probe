"""Nine-point final reducer check for the already drawn A04 geometry.

This is the bounded stop check, not another continuous optimizer.  It keeps the
15 mm return interruption fixed and perturbs each constant-width overlap by
only -0.20/0/+0.20 mm.  The centre point is the saved KiCad A04 dimension.
"""
from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json

import numpy as np
from scipy.constants import epsilon_0

from fixture_match_redesign import evaluate


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews" / "fixture_structural_redesign_20260922"
GEOMETRY = ROOT / "hardware" / "calibration_fixture_PCB_A04_DRAFT" / "design_geometry.json"
CROSS = OUT / "a04_cross_section.json"


def cap_pf(overlap_mm: float, taper_mm: float, wide_mm: float,
           launch_mm: float, h_mm: float, er: float) -> float:
    pf_per_mm2 = epsilon_0 * er / h_mm * 1e9
    excess_area = (wide_mm - launch_mm) * (overlap_mm + taper_mm / 2)
    return float(pf_per_mm2 * excess_area)


def metrics(freq: np.ndarray, result: dict) -> dict:
    current = abs(result["i_center_over_matched"])
    return {
        "worst_S11_dB": float(20 * np.log10(max(abs(result["s11"])))),
        "max_center_current_error_100_200_percent": float(
            100 * max(abs(current[freq <= 200e6] - 1))),
        "max_center_current_error_100_500_percent": float(
            100 * max(abs(current - 1))),
    }


def main() -> None:
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    cross = json.loads(CROSS.read_text(encoding="utf-8"))["selected"]
    seed = geometry["RF_seed"]
    freq = np.linspace(100e6, 500e6, 401)
    rows = []
    for din in [-0.20, 0.0, 0.20]:
        for dout in [-0.20, 0.0, 0.20]:
            in_mm = seed["IN_overlap_mm"] + din
            out_mm = seed["OUT_overlap_mm"] + dout
            cin = cap_pf(in_mm, seed["taper_mm"], seed["wide_SIG_mm"],
                         seed["launch_width_mm"],
                         geometry["stackup"]["L1_L2_prepreg_mm"],
                         geometry["stackup"]["prepreg_Dk"])
            cout = cap_pf(out_mm, seed["taper_mm"], seed["wide_SIG_mm"],
                          seed["launch_width_mm"],
                          geometry["stackup"]["L1_L2_prepreg_mm"],
                          geometry["stackup"]["prepreg_Dk"])
            result = evaluate(freq, cross["Z_ohm"], cross["effective_er"],
                              seed["unreferenced_gap_mm"] * 1e-3, cin, cout)
            rows.append({
                "delta_IN_overlap_mm": din,
                "delta_OUT_overlap_mm": dout,
                "IN_overlap_mm": in_mm,
                "OUT_overlap_mm": out_mm,
                "equivalent_Cin_pF": cin,
                "equivalent_Cout_pF": cout,
                **metrics(freq, result),
            })
    centre = next(row for row in rows
                  if row["delta_IN_overlap_mm"] == 0
                  and row["delta_OUT_overlap_mm"] == 0)
    report = {
        "classification": "CALCULATED_NINE_POINT_STOP_CHECK_NOT_3D_EM_NOT_MEASURED",
        "purpose": "Confirm that the saved A04 seed is not accepted solely by polishing the -20.00 dB boundary.",
        "cases": 9,
        "perturbation_mm": [-0.2, 0, 0.2],
        "saved_geometry_case": centre,
        "neighbourhood_range": {
            key: [min(row[key] for row in rows), max(row[key] for row in rows)]
            for key in ["worst_S11_dB", "max_center_current_error_100_200_percent",
                        "max_center_current_error_100_500_percent"]
        },
        "stop_rule": "Use this bounded neighbourhood and the two saved-copper openEMS meshes; do not continue iterations merely to cross exactly -20.00 dB.",
        "source_geometry_sha256": hashlib.sha256(GEOMETRY.read_bytes()).hexdigest(),
        "source_cross_section_sha256": hashlib.sha256(CROSS.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "stop_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (OUT / "stop_check.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
