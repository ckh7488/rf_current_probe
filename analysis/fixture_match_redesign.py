"""CALCULATED screening for a passively compensated calibration fixture.

This is a transmission-line/lumped-element candidate reducer, not a 3-D EM
result and not a measurement.  It reads the independently checked central
cross-section result, represents the 33.75 mm SIG-only bridge as a uniform
lossless line, and evaluates shunt C0G capacitors placed outside the core at
the two bridge transitions.  The core current is calculated explicitly; a
good port S11 is not treated as proof that the current is ideal.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np
from scipy.constants import c
from scipy.optimize import differential_evolution


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reviews" / "fixture_impedance_20260918" / "results.json"
OUT = ROOT / "reviews" / "fixture_match_redesign_20260922"
ZREF = 50.0


@dataclass(frozen=True)
class CapacitorModel:
    c_f: float
    esr_ohm: float = 0.05
    esl_h: float = 0.40e-9

    def admittance(self, omega: np.ndarray) -> np.ndarray:
        if self.c_f <= 0:
            return np.zeros_like(omega, dtype=complex)
        z = self.esr_ohm + 1j * omega * self.esl_h + 1 / (1j * omega * self.c_f)
        return 1 / z


def cascade(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.einsum("fij,fjk->fik", a, b)


def shunt(y: np.ndarray) -> np.ndarray:
    out = np.zeros((len(y), 2, 2), dtype=complex)
    out[:, 0, 0] = 1
    out[:, 1, 0] = y
    out[:, 1, 1] = 1
    return out


def line_abcd(freq_hz: np.ndarray, z_line: float, effective_er: float,
              length_m: float) -> tuple[np.ndarray, np.ndarray]:
    theta = 2 * np.pi * freq_hz * np.sqrt(effective_er) * length_m / c
    out = np.zeros((len(freq_hz), 2, 2), dtype=complex)
    out[:, 0, 0] = np.cos(theta)
    out[:, 0, 1] = 1j * z_line * np.sin(theta)
    out[:, 1, 0] = 1j * np.sin(theta) / z_line
    out[:, 1, 1] = np.cos(theta)
    return out, theta


def evaluate(freq_hz: np.ndarray, z_line: float, effective_er: float,
             length_m: float, c_in_pf: float, c_out_pf: float,
             esr_ohm: float = 0.05, esl_nh: float = 0.40) -> dict[str, np.ndarray]:
    omega = 2 * np.pi * freq_hz
    line, theta = line_abcd(freq_hz, z_line, effective_er, length_m)
    yin = CapacitorModel(c_in_pf * 1e-12, esr_ohm, esl_nh * 1e-9).admittance(omega)
    yout = CapacitorModel(c_out_pf * 1e-12, esr_ohm, esl_nh * 1e-9).admittance(omega)
    network = cascade(cascade(shunt(yin), line), shunt(yout))
    aa, bb = network[:, 0, 0], network[:, 0, 1]
    cc, dd = network[:, 1, 0], network[:, 1, 1]
    den = aa + bb / ZREF + cc * ZREF + dd
    s11 = (aa + bb / ZREF - cc * ZREF - dd) / den
    s21 = 2 / den

    # Unit incident voltage wave at the input reference plane.  The line input
    # current excludes the current diverted by the input shunt capacitor.
    vin = 1 + s11
    i_port = (1 - s11) / ZREF
    i_line_in = i_port - yin * vin
    i_center = i_line_in * np.cos(theta / 2) - 1j * vin * np.sin(theta / 2) / z_line
    return {
        "s11": s11,
        "s21": s21,
        "i_center_over_matched": i_center * ZREF,
    }


def metrics(result: dict[str, np.ndarray], freq_hz: np.ndarray,
            band_max_hz: float) -> dict[str, float]:
    use = freq_hz <= band_max_hz
    gamma = np.abs(result["s11"][use])
    i_mag = np.abs(result["i_center_over_matched"][use])
    return {
        "band_max_MHz": band_max_hz / 1e6,
        "worst_S11_dB": float(20 * np.log10(np.max(gamma))),
        "max_current_magnitude_error_percent": float(100 * np.max(np.abs(i_mag - 1))),
        "min_current_magnitude_ratio": float(np.min(i_mag)),
        "max_current_magnitude_ratio": float(np.max(i_mag)),
    }


def optimize(freq_hz: np.ndarray, z_line: float, effective_er: float,
             length_m: float, symmetric: bool) -> dict[str, float]:
    def objective(x: np.ndarray) -> float:
        c_in = float(x[0])
        c_out = c_in if symmetric else float(x[1])
        result = evaluate(freq_hz, z_line, effective_er, length_m, c_in, c_out)
        gamma = np.max(np.abs(result["s11"]))
        i_error = np.max(np.abs(np.abs(result["i_center_over_matched"]) - 1))
        # Equal normalized weight: -20 dB reflection and +/-1% raw centre
        # current are design-screening targets, not demonstrated accuracy.
        return float(max(gamma / 0.1, i_error / 0.01))

    bounds = [(0.0, 15.0)] if symmetric else [(0.0, 15.0), (0.0, 15.0)]
    fit = differential_evolution(objective, bounds, seed=20260922, tol=1e-10,
                                 polish=True, workers=1)
    c_in = float(fit.x[0])
    c_out = c_in if symmetric else float(fit.x[1])
    return {"c_in_pF": c_in, "c_out_pF": c_out, "normalized_worst": float(fit.fun)}


def candidate_rows(freq_hz: np.ndarray, z_line: float, effective_er: float,
                   length_m: float, cases: list[dict[str, float]]) -> list[dict[str, float]]:
    anchors_mhz = [1, 10, 30, 100, 150, 200, 300, 500]
    rows: list[dict[str, float]] = []
    for case in cases:
        result = evaluate(freq_hz, z_line, effective_er, length_m,
                          case["c_in_pF"], case["c_out_pF"])
        for mhz in anchors_mhz:
            i = int(np.argmin(np.abs(freq_hz - mhz * 1e6)))
            rows.append({
                "case": case["name"],
                "c_in_pF": case["c_in_pF"],
                "c_out_pF": case["c_out_pF"],
                "f_MHz": float(freq_hz[i] / 1e6),
                "S11_dB": float(20 * np.log10(abs(result["s11"][i]))),
                "S21_dB": float(20 * np.log10(abs(result["s21"][i]))),
                "I_center_over_matched_mag": float(abs(result["i_center_over_matched"][i])),
                "I_center_over_matched_phase_deg": float(np.angle(result["i_center_over_matched"][i], deg=True)),
            })
    return rows


def monte_carlo(freq_hz: np.ndarray, z_line: float, effective_er: float,
                length_m: float, case: dict[str, float], samples: int = 4000) -> dict[str, float]:
    rng = np.random.default_rng(20260922)
    worst_s11 = []
    worst_current = []
    for _ in range(samples):
        # Screening envelope for small C0G parts plus mounting parasitics.  It
        # is not a vendor tolerance guarantee.
        cin = max(0, rng.normal(case["c_in_pF"], 0.10))
        cout = max(0, rng.normal(case["c_out_pF"], 0.10))
        esl = max(0.05, rng.normal(0.40, 0.08))
        esr = max(0.0, rng.normal(0.05, 0.02))
        result = evaluate(freq_hz, z_line, effective_er, length_m, cin, cout, esr, esl)
        worst_s11.append(float(np.max(np.abs(result["s11"]))))
        worst_current.append(float(np.max(np.abs(np.abs(result["i_center_over_matched"]) - 1))))
    return {
        "samples": samples,
        "assumed_C_sigma_pF": 0.10,
        "assumed_ESL_mean_nH": 0.40,
        "assumed_ESL_sigma_nH": 0.08,
        "assumed_ESR_mean_ohm": 0.05,
        "assumed_ESR_sigma_ohm": 0.02,
        "p95_worst_S11_dB": float(20 * np.log10(np.quantile(worst_s11, 0.95))),
        "p95_max_current_magnitude_error_percent": float(100 * np.quantile(worst_current, 0.95)),
        "max_observed_current_magnitude_error_percent": float(100 * np.max(worst_current)),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    nominal = source["cases"][2]
    z_line = float(nominal["Z_ohm"])
    effective_er = float(nominal["effective_er"])
    length_m = float(source["geometry_mm"]["window_length"]) * 1e-3
    freq = np.unique(np.r_[np.geomspace(1e6, 500e6, 1201),
                           np.array([1, 10, 30, 100, 150, 200, 300, 500]) * 1e6])
    fit_freq = freq[freq <= 200e6]
    asym = optimize(fit_freq, z_line, effective_er, length_m, symmetric=False)
    sym = optimize(fit_freq, z_line, effective_er, length_m, symmetric=True)
    cases = [
        {"name": "A03_no_compensation", "c_in_pF": 0.0, "c_out_pF": 0.0},
        {"name": "continuous_asymmetric_fit", **asym},
        {"name": "continuous_symmetric_fit", **sym},
        {"name": "practical_6p8_2p7", "c_in_pF": 6.8, "c_out_pF": 2.7},
        {"name": "practical_6p2_2p7", "c_in_pF": 6.2, "c_out_pF": 2.7},
    ]
    rows = candidate_rows(freq, z_line, effective_er, length_m, cases)
    with (OUT / "frequency_anchors.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    case_results = []
    for case in cases:
        result = evaluate(freq, z_line, effective_er, length_m,
                          case["c_in_pF"], case["c_out_pF"])
        case_results.append({
            **case,
            "metrics_1_200_MHz": metrics(result, freq, 200e6),
            "metrics_1_500_MHz": metrics(result, freq, 500e6),
        })
    practical = next(x for x in cases if x["name"] == "practical_6p2_2p7")
    report = {
        "classification": "CALCULATED_CANDIDATE_NOT_3D_EM_NOT_MEASURED",
        "source_cross_section": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
        "model": {
            "central_line_Z_ohm": z_line,
            "central_effective_er": effective_er,
            "central_length_mm": length_m * 1e3,
            "reference_impedance_ohm": ZREF,
            "capacitor_nominal_ESR_ohm": 0.05,
            "capacitor_nominal_ESL_nH": 0.40,
        },
        "screening_targets": {
            "band_MHz": [1, 200],
            "port_S11_dB_at_or_below": -20,
            "raw_center_current_magnitude_error_percent": 1,
            "status": "design screening only; not a product accuracy specification",
        },
        "cases": case_results,
        "practical_candidate_tolerance_screen": monte_carlo(
            fit_freq, z_line, effective_er, length_m, practical
        ),
        "limitations": [
            "Uniform 2-D central section; the SMA launches, tapers, vias, ferrite core, probe winding, fixture holder and losses are omitted.",
            "The capacitor parasitics and statistical envelope are assumptions, not selected-part data.",
            "Asymmetric values make the fixture directional; IN and OUT must be marked and reverse use must be characterized separately.",
            "The central mode remains high impedance. Compensation improves the port match but does not turn the local cross-section into a physical 50 ohm line.",
            "Any KiCad change requires exact 3-D openEMS runs, convergence checks, ERC/DRC, mechanical insertion review and later VNA measurement.",
        ],
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Fixture passive-match candidate screening",
        "",
        "`CALCULATED` only. This is a uniform-line plus lumped-C reduction of the existing A03 central section.",
        "",
        f"Central model: {z_line:.2f} ohm, effective er {effective_er:.4f}, length {length_m*1e3:.2f} mm.",
        "",
        "| Case | Cin pF | Cout pF | Worst S11 1-200 MHz | Max raw center-current magnitude error |",
        "|---|---:|---:|---:|---:|",
    ]
    for case in case_results:
        m = case["metrics_1_200_MHz"]
        lines.append(
            f"| {case['name']} | {case['c_in_pF']:.3f} | {case['c_out_pF']:.3f} | "
            f"{m['worst_S11_dB']:.2f} dB | {m['max_current_magnitude_error_percent']:.3f}% |"
        )
    lines += [
        "",
        "The continuous asymmetric fit is a topology check. The 6.2 pF / 2.7 pF row is a practical starting point for 3-D EM, not a released BOM value.",
        "The fixture remains directional and the local central section is not physically 50 ohm. KiCad and openEMS verification must precede fabrication.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "cases": case_results,
                      "tolerance": report["practical_candidate_tolerance_screen"]}, indent=2))


if __name__ == "__main__":
    main()
