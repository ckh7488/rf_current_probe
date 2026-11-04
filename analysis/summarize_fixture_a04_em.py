"""Summarize the accepted A04 openEMS runs without promoting them to measurement.

The two saved-geometry structure meshes are directly comparable.  A local-
feature screen reports sampled peaks; absence of a reported peak is not proof
that hardware cannot resonate.
"""
from __future__ import annotations

from pathlib import Path
import cmath
import csv
import hashlib
import json
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks, peak_widths


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews" / "fixture_structural_redesign_20260922"
RUNS = {
    "structure_m060": OUT / "em" / "a04_validated_vias_m060",
    "structure_m050": OUT / "em" / "a04_validated_vias_m050",
}
ANCHORS = {100e6, 150e6, 200e6, 300e6, 400e6, 500e6}


def cpx(row: dict, name: str) -> complex:
    return complex(row[f"{name}_re"], row[f"{name}_im"])


def current(row: dict) -> complex:
    mag = row["I_center_over_matched_mag"]
    phase = math.radians(row["I_center_over_matched_phase_deg"])
    return cmath.rect(mag, phase)


def termination(run_dir: Path, model: dict) -> dict:
    fields = []
    for line in (run_dir / "openEMS_stats.txt").read_text(encoding="utf-8").splitlines():
        fields.append(float(line.split("%", 1)[0].strip()))
    cells, dt, iterations, numerical_time, wall_time, speed = fields
    p = model["parameters"]
    max_ns = float(p["max_ns"])
    max_steps = int(p["max_steps"])
    if numerical_time >= max_ns * 1e-9 * 0.995:
        kind = "MAX_TIME"
    elif iterations >= max_steps:
        kind = "MAX_STEPS"
    else:
        kind = "ENERGY_CRITERION"
    return {
        "kind": kind,
        "cells": int(cells),
        "time_step_s": dt,
        "iterations": int(iterations),
        "numerical_time_ns": numerical_time * 1e9,
        "wall_time_s": wall_time,
        "speed_cells_per_s": speed,
        "configured_max_time_ns": max_ns,
        "configured_max_steps": max_steps,
    }


def sampled_features(rows: list[dict]) -> dict:
    freq = np.asarray([r["f_Hz"] for r in rows]) / 1e6
    spacing = float(np.median(np.diff(freq)))

    def features(values: np.ndarray, invert: bool = False) -> list[dict]:
        signal = -values if invert else values
        peaks, props = find_peaks(signal, prominence=0.75)
        if not len(peaks):
            return []
        widths = peak_widths(signal, peaks, rel_height=0.5)[0] * spacing
        result = []
        for i, peak in enumerate(peaks):
            result.append({
                "f_MHz": float(freq[peak]),
                "value_dB": float(values[peak]),
                "prominence_dB": float(props["prominences"][i]),
                "half_prominence_width_MHz": float(widths[i]),
                "narrower_than_25_MHz": bool(widths[i] < 25),
            })
        return result

    s11 = np.asarray([r["S11_dB"] for r in rows])
    s21 = np.asarray([r["S21_dB"] for r in rows])
    return {
        "sample_spacing_MHz": spacing,
        "S11_local_worse_peaks_prominence_at_least_0p75_dB": features(s11),
        "S21_local_loss_notches_prominence_at_least_0p75_dB": features(s21, invert=True),
        "interpretation": (
            "A missing feature means no such local feature was present on the saved sampled curve; "
            "it is not proof that manufactured hardware has no resonance."
        ),
    }


def run_summary(run_dir: Path, data: dict) -> dict:
    rows = data["rows"]
    return {
        "directory": str(run_dir.relative_to(ROOT)),
        "results_sha256": hashlib.sha256((run_dir / "results.json").read_bytes()).hexdigest(),
        "source_geometry_sha256": data["source_geometry_sha256"],
        "script_sha256": data["script_sha256"],
        "mesh": data["mesh"],
        "min_cell_mm": data["min_cell_mm"],
        "termination": termination(run_dir, data),
        "metrics_100_500_MHz": {
            "worst_S11_dB": max(r["S11_dB"] for r in rows),
            "largest_S21_loss_dB": -min(r["S21_dB"] for r in rows),
            "max_center_current_magnitude_error_percent": 100 * max(
                abs(r["I_center_over_matched_mag"] - 1) for r in rows
            ),
            "max_along_core_current_variation_percent": max(
                r["along_core_current_variation_percent"] for r in rows
            ),
            "max_passivity_sum": max(r["passivity_sum"] for r in rows),
            "min_passivity_sum": min(r["passivity_sum"] for r in rows),
        },
        "sampled_feature_screen": sampled_features(rows),
    }


def compare(a: dict, b: dict) -> dict:
    assert [r["f_Hz"] for r in a["rows"]] == [r["f_Hz"] for r in b["rows"]]
    rows = []
    for ra, rb in zip(a["rows"], b["rows"]):
        ia, ib = current(ra), current(rb)
        rows.append({
            "f_Hz": ra["f_Hz"],
            "S11_complex_absolute_difference": abs(cpx(rb, "S11") - cpx(ra, "S11")),
            "S21_complex_absolute_difference": abs(cpx(rb, "S21") - cpx(ra, "S21")),
            "center_current_complex_relative_difference_percent": 100 * abs(ib / ia - 1),
            "center_current_magnitude_difference_percent": 100 * abs(abs(ib) - abs(ia)),
            "center_current_phase_difference_deg": abs(math.degrees(cmath.phase(ib / ia))),
        })
    keys = [k for k in rows[0] if k != "f_Hz"]
    return {
        "classification": "TWO_MESH_DIAGNOSTIC_NOT_A_STRICT_REMAINING_ERROR_BOUND",
        "maxima_100_500_MHz": {k: max(r[k] for r in rows) for k in keys},
        "rows": rows,
    }


def main() -> None:
    data = {
        name: json.loads((path / "results.json").read_text(encoding="utf-8"))
        for name, path in RUNS.items()
    }
    assert data["structure_m060"]["source_geometry_sha256"] == data["structure_m050"]["source_geometry_sha256"]
    assert data["structure_m060"]["script_sha256"] == data["structure_m050"]["script_sha256"]
    comparison = compare(data["structure_m060"], data["structure_m050"])
    summary = {
        "classification": "SIMULATED_EMPTY_FIXTURE_A04_NOT_MEASURED_NOT_CALIBRATION_APPROVAL",
        "design": "Fixture A04, gap 15.0 mm, J1 IN / J2 OUT",
        "runs": {name: run_summary(RUNS[name], value) for name, value in data.items()},
        "structure_mesh_comparison": comparison,
        "decision_rule": (
            "Judge the 100-500 MHz curve, center-current stability, two-mesh trend and sampled sharp features; "
            "do not iterate merely to cross exactly -20.00 dB."
        ),
        "limitations": [
            "Both runs are empty-fixture simulations without ferrite, winding, probe head, SMA body or bench cable.",
            "The two runs use the same saved A04 copper clipped at the y=+/-30 mm de-embedded reference planes, solid-via model and ideal L1/In1 ports.",
            "The physical SMA, its remaining 4.35 mm launch segment and reference-plane-outside vias are excluded and require VNA verification.",
            "The nominal Dk4.4 prepreg and Dk4.6 core are lossless and non-dispersive; fabrication variation is not modeled.",
            "A 1 MHz sampled curve and finite time record cannot exclude every possible high-Q hardware resonance.",
            "Only VNA S2P and repeatable current-path checks on the manufactured A04 can establish its usable calibration range.",
        ],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "em_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with (OUT / "frequency_anchors_em.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["run", "f_MHz", "S11_dB", "S21_dB", "I_center_over_matched_mag",
                  "I_center_over_matched_phase_deg", "along_core_current_variation_percent", "passivity_sum"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for name, value in data.items():
            for row in value["rows"]:
                if row["f_Hz"] in ANCHORS:
                    writer.writerow({"run": name, "f_MHz": row["f_Hz"] / 1e6,
                                     **{key: row[key] for key in fields[2:]}})

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    colors = {"structure_m060": "#16697a", "structure_m050": "#62b6cb"}
    for name, value in data.items():
        f = np.asarray([r["f_Hz"] for r in value["rows"]]) / 1e6
        axes[0].plot(f, [r["S11_dB"] for r in value["rows"]], label=name, color=colors[name])
        axes[1].plot(f, [r["S21_dB"] for r in value["rows"]], label=name, color=colors[name])
        axes[2].plot(f, [r["I_center_over_matched_mag"] for r in value["rows"]], label=name, color=colors[name])
    axes[0].axhline(-20, color="#777", linestyle="--", linewidth=1)
    axes[0].set_ylabel("S11 (dB)")
    axes[1].set_ylabel("S21 (dB)")
    axes[2].set_ylabel("Icentre / Iincident,50Ω")
    axes[2].set_xlabel("Frequency (MHz)")
    axes[0].legend(loc="best", fontsize=8)
    for axis in axes:
        axis.grid(True, alpha=0.25)
    fig.suptitle("Fixture A04 empty-fixture openEMS — SIMULATED, not measured")
    fig.tight_layout()
    fig.savefig(OUT / "em_response.png", dpi=180)
    plt.close(fig)

    print(json.dumps({
        "runs": {name: summary["runs"][name]["metrics_100_500_MHz"] for name in RUNS},
        "mesh_comparison": comparison["maxima_100_500_MHz"],
        "terminations": {name: summary["runs"][name]["termination"]["kind"] for name in RUNS},
    }, indent=2))


if __name__ == "__main__":
    main()
