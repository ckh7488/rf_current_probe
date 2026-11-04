"""Bounded transmission-line reducer for the A05 taper-overlap seed.

This is an explanatory seed model.  It does not replace the saved-geometry
openEMS result and is not used to claim a manufactured S-parameter.
"""
from pathlib import Path
import json

import numpy as np
from scipy.constants import c, epsilon_0


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews/fixture_structural_redesign_20260922/a05_reducer_seed.json"
F = np.linspace(100e6, 500e6, 4001)
Z0 = 130.49207823865697
ER_EFF = 1.0469291620576775
LENGTH = 15e-3
ZREF = 50.0
LAUNCH_W = 0.358648
WIDE_W = 30.0
H = 0.2104
ER_PREPREG = 4.4
OVERLAP = 0.40


def response(cap_f: float) -> np.ndarray:
    theta = 2*np.pi*F*np.sqrt(ER_EFF)/c*LENGTH
    a = np.cos(theta)
    b = 1j*Z0*np.sin(theta)
    cc = 1j*np.sin(theta)/Z0
    d = a.copy()
    y = 1j*2*np.pi*F*cap_f
    # shunt(Y) * line * shunt(Y), ABCD convention.
    at = a + b*y
    bt = b
    ct = y*a + cc + (y*b+d)*y
    dt = y*b+d
    den = at + bt/ZREF + ct*ZREF + dt
    return (at + bt/ZREF - ct*ZREF - dt) / den


triangle_area_mm2 = (WIDE_W-LAUNCH_W)/2*OVERLAP
geometric_cap = epsilon_0*ER_PREPREG*triangle_area_mm2*1e-6/(H*1e-3)
caps = np.linspace(0.5e-12, 1.5e-12, 101)
scores = np.asarray([np.max(20*np.log10(np.maximum(abs(response(x)), 1e-30)))
                     for x in caps])
i = int(np.argmin(scores))


def anchors(gamma: np.ndarray) -> list[dict]:
    return [{"frequency_MHz": x/1e6,
             "S11_dB": float(20*np.log10(abs(gamma[np.argmin(abs(F-x))])))}
            for x in [100e6, 200e6, 300e6, 400e6, 500e6]]


payload = {
    "classification": "CALCULATED_REDUCER_SEED_NOT_MEASURED",
    "line": {"Z_ohm": Z0, "effective_er": ER_EFF, "length_mm": LENGTH*1e3},
    "bounded_capacitance_screen": {
        "range_pF": [0.5, 1.5], "samples": len(caps),
        "best_equal_shunt_C_pF": float(caps[i]*1e12),
        "best_worst_S11_dB": float(scores[i]),
    },
    "selected_geometry": {
        "taper_total_length_mm": 2.0,
        "taper_plane_overlap_mm": OVERLAP,
        "triangular_excess_area_mm2": triangle_area_mm2,
        "parallel_plate_seed_C_pF_each_end": geometric_cap*1e12,
        "predicted_worst_S11_dB": float(np.max(20*np.log10(abs(response(geometric_cap))))),
        "anchors": anchors(response(geometric_cap)),
    },
    "limits": [
        "The line is uniform and lossless; the real transition is 3-D and fringing is not a parallel plate.",
        "The bounded screen selects one physical seed and is not a threshold optimizer.",
        "Saved-geometry openEMS dense-frequency results take precedence.",
    ],
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
