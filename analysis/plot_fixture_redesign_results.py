"""Create the review figure from saved simulation/calculation outputs."""
from __future__ import annotations

from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"reviews"/"fixture_structural_redesign_20260922"
EM = BASE/"em"


RUNS = [
    ("A04 flat, 0.60 mm", "a04_validated_vias_m060", "#64748b"),
    ("A05 close return", "a05_screen_m100_fast", "#d97706"),
    ("A06 10 mm wedge", "a06_wedge10_m120_screen", "#0ea5e9"),
    ("A06 cage + 28×18 wedge", "a06_cage44p5_wedge28x18_m120_screen", "#dc2626"),
]


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True)
    ax = axes[0]
    for label, name, color in RUNS:
        data = json.loads((EM/name/"results.json").read_text(encoding="utf-8"))
        f = np.asarray([r["f_Hz"] for r in data["rows"]])/1e6
        s11 = np.asarray([r["S11_dB"] for r in data["rows"]])
        ax.plot(f, s11, label=label, lw=2, color=color)
    ax.axhline(-20, color="black", ls="--", lw=1.2, label="−20 dB goal")
    ax.set(xlabel="Frequency (MHz)", ylabel="S11 (dB)",
           title="Saved openEMS topology screens")
    ax.set_xlim(100, 500); ax.set_ylim(-55, 0)
    ax.grid(True, alpha=.25); ax.legend(fontsize=8, loc="lower right")
    ax.text(.01, .02, "SIMULATED · empty ideal-port models · not measured",
            transform=ax.transAxes, fontsize=8, color="#475569")

    ax = axes[1]
    rows = []
    from fixture_a07_uniform_cross_section import solve
    from scipy.constants import c
    for diameter in [20, 24, 26, 28, 30, 32, 34, 35]:
        result = solve(.18, 44.5, 34.5, diameter, diameter,
                       diameter/2, 0, 1)
        z = 1/(c*result["C_F_per_m"])
        ratio = z/50
        rl = 20*np.log10(abs((ratio*ratio-1)/(ratio*ratio+1)))
        rows.append((diameter, z, rl))
    d, z, rl = map(np.asarray, zip(*rows))
    ax.plot(d, z, marker="o", lw=2, color="#0f766e", label="Local Z0")
    ax.axhline(50, color="#0f766e", ls="--", lw=1)
    ax.set(xlabel="Round current-bar diameter (mm)", ylabel="Local Z0 (Ω)",
           title="Uniform cage: aperture trade-off")
    ax.set_xlim(19, 36); ax.set_ylim(45, 90); ax.grid(True, alpha=.25)
    ax2 = ax.twinx()
    ax2.plot(d, rl, marker="s", lw=1.8, color="#7c3aed",
             label="Worst two-interface S11")
    ax2.axhline(-20, color="#7c3aed", ls=":", lw=1)
    ax2.set_ylabel("Conservative section S11 bound (dB)", color="#7c3aed")
    ax2.set_ylim(-36, -4); ax2.tick_params(axis="y", labelcolor="#7c3aed")
    ax.axvspan(20, 26, color="#f59e0b", alpha=.14,
               label="20 mm target / 26 mm nominal opening")
    lines = [x for x in ax.get_lines()+ax2.get_lines()
             if not x.get_label().startswith("_")]
    labels = [x.get_label() for x in lines]
    ax.legend(lines+[ax.patches[0]], labels+["20–26 mm usable range"],
              fontsize=8, loc="upper right")
    ax.text(.01, .02, "CALCULATED · 89×69 mm empty cage · no probe loading",
            transform=ax.transAxes, fontsize=8, color="#475569")

    out = BASE/"fixture_redesign_result.png"
    fig.savefig(out, dpi=180)
    print(out)


if __name__ == "__main__":
    main()
