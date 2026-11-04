"""Diagnose whether one symmetric geometric shunt-C adjustment can rescue A05.

The A05 geometry is symmetric, so this diagnostic assumes S22=S11 and
S12=S21 for the idealized de-embedded model.  It is CALCULATED from the coarse
simulation and is used only to decide whether one more geometry run is useful.
"""
from pathlib import Path
import json

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reviews/fixture_structural_redesign_20260922/em/a05_screen_m100_fast"
rows = json.loads((RUN / "results.json").read_text(encoding="utf-8"))["rows"]
f = np.asarray([r["f_Hz"] for r in rows])
s11 = np.asarray([complex(r["S11_re"], r["S11_im"]) for r in rows])
s21 = np.asarray([complex(r["S21_re"], r["S21_im"]) for r in rows])
z0 = 50.0
s22, s12 = s11, s21
a = ((1+s11)*(1-s22)+s12*s21)/(2*s21)
b = z0*((1+s11)*(1+s22)-s12*s21)/(2*s21)
c = ((1-s11)*(1-s22)-s12*s21)/(2*z0*s21)
d = ((1-s11)*(1+s22)+s12*s21)/(2*s21)


def adjusted(cap_f: float) -> np.ndarray:
    y = 1j*2*np.pi*f*cap_f
    # [1 0;Y 1] @ [A B;C D] @ [1 0;Y 1]
    at = a+b*y
    bt = b
    ct = y*a+c+(y*b+d)*y
    dt = y*b+d
    den = at+bt/z0+ct*z0+dt
    return (at+bt/z0-ct*z0-dt)/den


caps = np.linspace(-10e-12, 20e-12, 601)
worst = np.asarray([np.max(20*np.log10(np.maximum(abs(adjusted(x)), 1e-30)))
                    for x in caps])
i = int(np.argmin(worst))
best = adjusted(caps[i])
anchors = []
for target in [100, 150, 200, 300, 400, 500]:
    j = int(np.argmin(abs(f-target*1e6)))
    anchors.append({"frequency_MHz": target,
                    "original_S11_dB": float(20*np.log10(abs(s11[j]))),
                    "adjusted_S11_dB": float(20*np.log10(abs(best[j])))})
payload = {
    "classification": "CALCULATED_DIAGNOSTIC_FROM_COARSE_SIMULATION_NOT_MEASURED",
    "symmetry_assumption": "S22=S11 and S12=S21 for the symmetric ideal A05 model",
    "bounded_added_equal_shunt_C_screen_pF": [-10, 20, len(caps)],
    "best_added_C_pF_each_end": float(caps[i]*1e12),
    "best_worst_S11_dB": float(worst[i]),
    "anchors": anchors,
    "decision_rule": "Proceed with one overlap revision only if a positive realizable C moves the whole band near -20 dB.",
    "limits": [
        "The source run ended at -22.17 dB energy and has passivity error; exact values are provisional.",
        "A lumped shunt at the reference plane is only a direction test for a distributed taper overlap.",
        "No result from this file is a fabricated-board S-parameter.",
    ],
}
(RUN / "shunt_adjustment_diagnostic.json").write_text(
    json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
