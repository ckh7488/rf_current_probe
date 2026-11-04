"""Extract a symmetric T equivalent from A05/A06 full-wave S data.

This is a diagnosis of the controlling discontinuity, not a claim that the
distributed 3-D fixture is literally a frequency-independent lumped circuit.
"""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "em"


def main():
    output = {"classification": "CALCULATED_EQUIVALENT_NETWORK_DIAGNOSTIC_NOT_MEASURED",
              "assumptions": ["reciprocal symmetric two-port: S22=S11 and S12=S21",
                              "50 ohm real reference impedance",
                              "symmetric T extraction at each frequency; elements are frequency-dependent diagnostics"]}
    for name in ["a05_screen_m100_fast", "a06_cagebar_m100_screen"]:
        data = json.loads((BASE/name/"results.json").read_text(encoding="utf-8"))
        rows = []
        for src in data["rows"]:
            f = src["f_Hz"]
            s11 = complex(src["S11_re"], src["S11_im"])
            s21 = complex(src["S21_re"], src["S21_im"])
            z0 = 50.0
            a = (1-s11*s11+s21*s21)/(2*s21)
            b = z0*((1+s11)**2-s21*s21)/(2*s21)
            cc = ((1-s11)**2-s21*s21)/(2*z0*s21)
            zseries_total = 2*(a-1)/cc if abs(cc) > 1e-15 else complex(float("nan"), float("nan"))
            rows.append({
                "f_Hz": f,
                "A_re": a.real, "A_im": a.imag,
                "B_ohm_re": b.real, "B_ohm_im": b.imag,
                "C_S_re": cc.real, "C_S_im": cc.imag,
                "T_series_total_ohm_re": zseries_total.real,
                "T_series_total_ohm_im": zseries_total.imag,
                "series_L_equiv_nH": zseries_total.imag/(2*np.pi*f)*1e9,
                "shunt_C_equiv_pF": cc.imag/(2*np.pi*f)*1e12,
            })
        output[name] = {"rows": rows,
                        "anchors": [min(rows, key=lambda r: abs(r["f_Hz"]-f))
                                    for f in [100e6, 200e6, 300e6, 400e6, 500e6]]}
    path = ROOT / "reviews" / "fixture_structural_redesign_20260922" / "a06_equivalent_network_diagnostic.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({k: v["anchors"] for k, v in output.items()
                      if isinstance(v, dict) and "anchors" in v}, indent=2))


if __name__ == "__main__":
    main()
