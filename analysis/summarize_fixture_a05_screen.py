"""Summarize the dense A05 screen and detect narrow local defects."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def local_extrema(freq_mhz: np.ndarray, values: np.ndarray,
                  kind: str, neighborhood_mhz: float = 5.0,
                  prominence_db: float = 0.75) -> list[dict]:
    rows = []
    step = float(np.median(np.diff(freq_mhz)))
    n = max(2, int(round(neighborhood_mhz / step)))
    for i in range(1, len(values)-1):
        is_extreme = ((values[i] >= values[i-1] and values[i] > values[i+1])
                      if kind == "peak" else
                      (values[i] <= values[i-1] and values[i] < values[i+1]))
        if not is_extreme:
            continue
        lo, hi = i-n, i+n
        if lo < 0 or hi >= len(values):
            continue
        baseline = (values[lo] + values[hi]) / 2
        prominence = values[i]-baseline if kind == "peak" else baseline-values[i]
        if prominence >= prominence_db:
            rows.append({"frequency_MHz": float(freq_mhz[i]),
                         "value_dB": float(values[i]),
                         "prominence_dB": float(prominence)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_name")
    args = ap.parse_args()
    run = ROOT / "reviews/fixture_structural_redesign_20260922/em" / args.run_name
    data = json.loads((run / "results.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    f = np.asarray([r["f_Hz"] for r in rows]) / 1e6
    s11 = np.asarray([r["S11_dB"] for r in rows])
    s21 = np.asarray([r["S21_dB"] for r in rows])
    current = np.asarray([r["I_center_over_matched_mag"] for r in rows])
    anchors = []
    for target in [100, 150, 200, 300, 400, 500]:
        i = int(np.argmin(abs(f-target)))
        anchors.append({k: rows[i][k] for k in
                        ["f_Hz", "S11_dB", "S21_dB",
                         "I_center_over_matched_mag",
                         "I_center_over_matched_phase_deg",
                         "along_core_current_variation_percent",
                         "passivity_sum"]})
    worst_i = int(np.argmax(s11))
    payload = {
        "classification": "SIMULATED_DENSE_FREQUENCY_SCREEN_NOT_MEASURED",
        "run": args.run_name,
        "frequency_grid": {"start_MHz": float(f[0]), "stop_MHz": float(f[-1]),
                           "points": len(f),
                           "median_step_MHz": float(np.median(np.diff(f)))},
        "metrics": {
            "worst_S11_dB": float(s11[worst_i]),
            "worst_S11_frequency_MHz": float(f[worst_i]),
            "median_S11_dB": float(np.median(s11)),
            "worst_S21_dB": float(np.min(s21)),
            "max_center_current_magnitude_error_percent": float(
                100*np.max(abs(current-1))),
            "max_passivity_sum": float(max(r["passivity_sum"] for r in rows)),
        },
        "local_S11_worse_peaks_ge_0p75dB_within_5MHz":
            local_extrema(f, s11, "peak"),
        "local_S21_notches_ge_0p75dB_within_5MHz":
            local_extrema(f, s21, "notch"),
        "anchors": anchors,
        "interpretation_limits": [
            "This screen omits physical SMA, ferrite, winding, probe head, cable and material loss.",
            "A finite time window and one coarse mesh establish trend only; a promising candidate requires a longer/finer confirmation.",
            "The 0.5 MHz samples detect sampled local extrema; they are not a mathematical proof that no sub-bin resonance exists.",
        ],
    }
    out = run / "dense_summary.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (run / "anchor_summary.csv").open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=list(anchors[0]))
        writer.writeheader(); writer.writerows(anchors)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
