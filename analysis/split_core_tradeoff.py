"""CALCULATED design comparison, not measured or RF-simulated performance.

Run: python analysis/split_core_tradeoff.py
AL values are relative identification values at 1 or 10 kHz, closed cores,
from Fair-Rite's Snap-It identification guide R02 (2023-10-11), pages 1-2.
Constant AL and ideal coupling omit loss, gaps, leakage, resistance and
capacitance. No upper bandwidth, accuracy or safety rating is predicted.
"""

import json
import math
import platform
from pathlib import Path


def calculate():
    burden_ohm = 50.0
    rows = []
    for part, al_uh in (("2644181281", 1.1), ("2631181381", 9.1), ("0431177081", 6.2)):
        for turns in (3, 5, 7):
            lm_h = al_uh * 1e-6 * turns**2
            fl_hz = burden_ohm / (2 * math.pi * lm_h)
            rows.append({
                "part": part,
                "turns": turns,
                "AL_relative_uH_per_turn_squared": al_uh,
                "Lm_uH": lm_h * 1e6,
                "ZT_ideal_plateau_ohm": burden_ohm / turns,
                "ideal_reflected_resistance_ohm": burden_ohm / turns**2,
                "fL_Hz": fl_hz,
                "gain_at_1MHz_relative_to_plateau_dB": -10 * math.log10(1 + (fl_hz / 1e6)**2),
            })
    return {
        "classification": "CALCULATED",
        "python_version": platform.python_version(),
        "burden_ohm": burden_ohm,
        "source": "https://fair-rite.com/wp-content/uploads/2023/10/FR_IndentifyingUnknownFair-RiteRoundCableSnapIts_R02.pdf",
        "source_access_date": "2026-09-15",
        "model": "Constant relative AL, ideal coupling; no loss, gap, leakage, capacitance or winding resistance. No upper-bandwidth prediction.",
        "results": rows,
    }


if __name__ == "__main__":
    destination = Path(__file__).with_name("split_core_tradeoff_calculated.json")
    destination.write_text(json.dumps(calculate(), indent=2) + "\n", encoding="utf-8")
    print(f"CALCULATED: {destination} (9 ideal-model cases; no hardware tests)")
