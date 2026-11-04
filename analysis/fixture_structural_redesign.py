"""CALCULATED reducer for the A04 structure-first fixture redesign.

This model does not represent a discrete matching capacitor.  It represents
the only section in which the close L2 return plane is forbidden: the ferrite
axial thickness plus a small registration guard.  The wide L1 SIG conductor
overlaps L2 immediately outside each ferrite face, creating a controlled
distributed capacitance before tapering to the 50-ohm launch trace.

The calculation is a candidate reducer for 3-D openEMS and is not measured
performance, a JLC impedance coupon result, or fabrication approval.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np
from scipy.constants import epsilon_0
from scipy.optimize import differential_evolution

from fixture_match_redesign import evaluate


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews" / "fixture_structural_redesign_20260922"
CROSS_SECTION = OUT / "a04_cross_section.json"
CROSS_SECTION_DATA = json.loads(CROSS_SECTION.read_text(encoding="utf-8"))
Z_CENTRE = float(CROSS_SECTION_DATA["selected"]["Z_ohm"])
ER_CENTRE = float(CROSS_SECTION_DATA["selected"]["effective_er"])
CORE_AXIAL_MM = 12.7
CORE_AXIAL_TOLERANCE_MM = 0.635
GAP_MM = 15.0
GUARD_EACH_MM = (GAP_MM - CORE_AXIAL_MM) / 2
STACK_H_MM = 0.2104
PREPREG_ER = 4.4
WIDE_SIG_MM = 6.8
LAUNCH_SIG_MM = 0.358648
TAPER_MM = 1.0


def band_metrics(result: dict[str, np.ndarray],
                 freq: np.ndarray) -> dict[str, float]:
    gamma = np.abs(result["s11"])
    current = np.abs(result["i_center_over_matched"])
    low = freq <= 200e6
    return {
        "worst_S11_dB": float(20 * np.log10(np.max(gamma))),
        "max_center_current_magnitude_error_percent": float(100 * np.max(np.abs(current - 1))),
        "max_center_current_magnitude_error_100_200_MHz_percent": float(
            100 * np.max(np.abs(current[low] - 1))),
        "min_center_current_ratio": float(np.min(current)),
        "max_center_current_ratio": float(np.max(current)),
    }


def optimize(freq: np.ndarray, gap_mm: float) -> dict[str, float]:
    # Equal normalized weight is deliberate: do not chase the last fraction
    # of a dB at the expense of the known current through the ferrite.
    def objective(x: np.ndarray) -> float:
        r = evaluate(freq, Z_CENTRE, ER_CENTRE, gap_mm * 1e-3, float(x[0]), float(x[1]))
        reflection = np.max(np.abs(r["s11"])) / 0.1
        current = np.abs(r["i_center_over_matched"])
        current_100_200 = np.max(np.abs(current[freq <= 200e6] - 1)) / 0.01
        current_100_500 = np.max(np.abs(current - 1)) / 0.03
        return float(max(reflection, current_100_200, current_100_500))

    fit = differential_evolution(
        objective,
        [(0, 8), (0, 8)],
        seed=20260922,
        popsize=10,
        maxiter=120,
        tol=1e-7,
        polish=True,
        workers=1,
    )
    return {"cin_pF": float(fit.x[0]), "cout_pF": float(fit.x[1]), "objective": float(fit.fun)}


def overlap_for_cap_mm(c_pf: float, er: float = PREPREG_ER,
                       h_mm: float = STACK_H_MM,
                       wide_mm: float = WIDE_SIG_MM,
                       launch_mm: float = LAUNCH_SIG_MM,
                       taper_mm: float = TAPER_MM) -> float:
    """Convert excess shunt C to constant-width overlap after taper area.

    The reducer's fitted capacitor is additional capacitance relative to the
    ordinary 50-ohm launch.  Both the wide rectangle and the linear taper add
    L1/L2 plate area, so subtract the taper's triangular *excess* area before
    assigning the remaining value to the straight wide overlap.
    """
    c_per_area_pf_per_mm2 = epsilon_0 * er / h_mm * 1e9
    taper_excess_pf = (c_per_area_pf_per_mm2
                       * (wide_mm - launch_mm) * taper_mm / 2)
    straight_excess_pf_per_mm = c_per_area_pf_per_mm2 * (wide_mm - launch_mm)
    if c_pf <= taper_excess_pf:
        raise ValueError("Taper alone exceeds the requested structural capacitance")
    return float((c_pf - taper_excess_pf) / straight_excess_pf_per_mm)


def anchors(freq: np.ndarray, name: str, result: dict[str, np.ndarray]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for mhz in [100, 150, 200, 300, 400, 500]:
        i = int(np.argmin(np.abs(freq - mhz * 1e6)))
        rows.append({
            "case": name,
            "f_MHz": mhz,
            "S11_dB": float(20 * np.log10(abs(result["s11"][i]))),
            "S21_dB": float(20 * np.log10(abs(result["s21"][i]))),
            "I_center_over_matched_mag": float(abs(result["i_center_over_matched"][i])),
            "I_center_over_matched_phase_deg": float(np.angle(result["i_center_over_matched"][i], deg=True)),
        })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    freq = np.linspace(100e6, 500e6, 1601)
    fit = optimize(freq, GAP_MM)
    cases = [
        ("A04_local_mode_33p75mm_reference", 33.75, 0.0, 0.0),
        ("A04_15p0mm_no_overlap", GAP_MM, 0.0, 0.0),
        ("A04_15p0mm_structure_fit", GAP_MM, fit["cin_pF"], fit["cout_pF"]),
    ]
    reports = []
    rows: list[dict[str, float | str]] = []
    for name, gap, cin, cout in cases:
        result = evaluate(freq, Z_CENTRE, ER_CENTRE, gap * 1e-3, cin, cout)
        reports.append({
            "name": name,
            "unreferenced_centre_length_mm": gap,
            "equivalent_structural_Cin_pF": cin,
            "equivalent_structural_Cout_pF": cout,
            "metrics_100_500_MHz": band_metrics(result, freq),
        })
        rows += anchors(freq, name, result)

    sensitivity = []
    for gap in [13.5, 14.0, 14.5, 15.0, 16.0]:
        q = optimize(freq, gap)
        result = evaluate(freq, Z_CENTRE, ER_CENTRE, gap * 1e-3, q["cin_pF"], q["cout_pF"])
        sensitivity.append({"gap_mm": gap, **q, **band_metrics(result, freq)})

    cin_overlap = overlap_for_cap_mm(fit["cin_pF"])
    cout_overlap = overlap_for_cap_mm(fit["cout_pF"])
    report = {
        "classification": "CALCULATED_STRUCTURE_CANDIDATE_NOT_3D_EM_NOT_MEASURED",
        "band_MHz": [100, 500],
        "design_intent": {
            "close_return": "L2 ground follows L1 SIG from each SMA launch to just outside the ferrite axial faces",
            "forbidden_return_region": "No L2/L3/L4 return copper beneath the SIG inside the ferrite axial span",
            "centre_SIG": "L1 6.8 mm wide copper through the ferrite; return remains outside the core",
            "matching_structure": "Asymmetric lengths of wide L1 SIG over L2 ground; no discrete capacitor in the primary candidate",
            "direction": "negative-y connector is IN; positive-y connector is OUT",
        },
        "source_central_cross_section": str(CROSS_SECTION.relative_to(ROOT)),
        "source_central_cross_section_sha256": sha256(CROSS_SECTION.read_bytes()).hexdigest(),
        "model": {
            "central_Z_ohm": Z_CENTRE,
            "central_effective_er": ER_CENTRE,
            "core_axial_mm": CORE_AXIAL_MM,
            "core_axial_tolerance_plus_minus_mm": CORE_AXIAL_TOLERANCE_MM,
            "registration_guard_each_mm": GUARD_EACH_MM,
            "minimum_guard_each_at_max_core_if_centred_mm": (
                (GAP_MM - (CORE_AXIAL_MM + CORE_AXIAL_TOLERANCE_MM)) / 2),
            "unreferenced_gap_mm": GAP_MM,
            "JLC04161H_7628_L1_L2_dielectric_mm": STACK_H_MM,
            "prepreg_er_assumed": PREPREG_ER,
            "wide_SIG_mm": WIDE_SIG_MM,
            "launch_SIG_mm": LAUNCH_SIG_MM,
            "linear_taper_mm": TAPER_MM,
        },
        "fit": {
            **fit,
            "parallel_plate_seed_Cin_overlap_mm": cin_overlap,
            "parallel_plate_seed_Cout_overlap_mm": cout_overlap,
            "note": "Overlap lengths include the linear taper's excess parallel-plate area relative to the narrow launch. Fringe fields remain for 3-D EM.",
        },
        "cases": reports,
        "gap_sensitivity": sensitivity,
        "stop_rule": "Use a small geometry sweep and two mesh levels; stop near -20 dB while keeping calculated centre-current magnitude error near 1% through 200 MHz and near 3% through 500 MHz, without threshold polishing.",
        "limitations": [
            "The 50-ohm launches, plane-edge fringe fields, tapers, vias, SMA internals and material loss require 3-D openEMS.",
            "The ferrite, sensing winding and probe head are absent; this is the empty-fixture current path only.",
            "The parallel-plate conversion is a seed, not a fabrication dimension or controlled-impedance coupon result.",
            "A good port match is accepted only together with the explicitly calculated current through the ferrite span.",
        ],
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (OUT / "frequency_anchors.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    readme = [
        "# A04 structure-first fixture reducer",
        "",
        "`CALCULATED` only. No discrete capacitor is used in the primary candidate.",
        "",
        f"The L2 return-plane interruption is reduced from A03's 33.75 mm to {GAP_MM:.2f} mm: 12.7+/-0.635 mm ferrite thickness plus a nominal {GUARD_EACH_MM:.2f} mm guard at each face.",
        f"The initial asymmetric constant-width overlaps are IN {cin_overlap:.2f} mm and OUT {cout_overlap:.2f} mm, after counting each {TAPER_MM:.1f} mm linear taper's excess L1/L2 area.",
        "",
        "| Case | Worst S11, 100-500 MHz | Maximum centre-current magnitude error |",
        "|---|---:|---:|",
    ]
    for row in reports:
        m = row["metrics_100_500_MHz"]
        readme.append(f"| {row['name']} | {m['worst_S11_dB']:.2f} dB | {m['max_center_current_magnitude_error_percent']:.2f}% |")
    readme += [
        "",
        "The values above reduce candidates only. Plane cutback, taper and overlap must be solved together in 3-D before KiCad release.",
    ]
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    colors = ["#8a99a6", "#d28b31", "#167a70"]
    for (name, gap, cin, cout), color in zip(cases, colors):
        result = evaluate(freq, Z_CENTRE, ER_CENTRE, gap * 1e-3, cin, cout)
        axes[0].plot(freq / 1e6, 20 * np.log10(np.abs(result["s11"])), label=name, color=color)
        axes[1].plot(freq / 1e6, np.abs(result["i_center_over_matched"]), label=name, color=color)
    axes[0].axhline(-20, color="#333333", linestyle="--", linewidth=0.9)
    axes[0].set_ylabel("S11 (dB)")
    axes[0].set_ylim(-45, 0)
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(fontsize=8)
    axes[1].axhspan(0.99, 1.01, color="#167a70", alpha=0.10)
    axes[1].axhline(1, color="#333333", linestyle="--", linewidth=0.9)
    axes[1].set_xlabel("Frequency (MHz)")
    axes[1].set_ylabel("Centre current / matched current")
    axes[1].grid(True, alpha=0.25)
    fig.suptitle("A04 structure-first reducer — CALCULATED, not 3-D EM or measured")
    fig.tight_layout()
    fig.savefig(OUT / "structural_reducer.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"out": str(OUT), "fit": report["fit"], "cases": reports}, indent=2))


if __name__ == "__main__":
    main()
