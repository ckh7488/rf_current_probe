"""Bounded lossless matching feasibility diagnostic around a simulated 2-port.

The elements are mathematical direction tests for a smoother geometric
transition.  They are not an instruction to populate discrete components.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.optimize import differential_evolution

ROOT = Path(__file__).resolve().parents[1]


def mm(x1, x2):
    return (x1[0]*x2[0]+x1[1]*x2[2], x1[0]*x2[1]+x1[1]*x2[3],
            x1[2]*x2[0]+x1[3]*x2[2], x1[2]*x2[1]+x1[3]*x2[3])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_name")
    args = ap.parse_args()
    run = ROOT/"reviews/fixture_structural_redesign_20260922/em"/args.run_name
    data = json.loads((run/"results.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    f = np.asarray([r["f_Hz"] for r in rows]); w = 2*np.pi*f
    s11 = np.asarray([complex(r["S11_re"], r["S11_im"]) for r in rows])
    s21 = np.asarray([complex(r["S21_re"], r["S21_im"]) for r in rows])
    z0 = 50.; s22=s11; s12=s21
    model = (((1+s11)*(1-s22)+s12*s21)/(2*s21),
             z0*((1+s11)*(1+s22)-s12*s21)/(2*s21),
             ((1-s11)*(1-s22)-s12*s21)/(2*z0*s21),
             ((1-s11)*(1+s22)+s12*s21)/(2*s21))

    def series(l_nh):
        return (np.ones_like(w), 1j*w*l_nh*1e-9,
                np.zeros_like(w), np.ones_like(w))

    def shunt(c_pf):
        return (np.ones_like(w), np.zeros_like(w),
                1j*w*c_pf*1e-12, np.ones_like(w))

    def response(x, topology):
        if topology == "series_shunt":
            edge = mm(series(x[0]), shunt(x[1]))
        elif topology == "shunt_series":
            edge = mm(shunt(x[1]), series(x[0]))
        elif topology == "series_shunt_series":
            edge = mm(mm(series(x[0]), shunt(x[1])), series(x[2]))
        else:
            edge = mm(mm(shunt(x[0]), series(x[1])), shunt(x[2]))
        aa,bb,cc,dd = mm(mm(edge, model), edge)
        den=aa+bb/z0+cc*z0+dd
        return (aa+bb/z0-cc*z0-dd)/den

    specs = {
        "series_shunt": ([(-50,50),(-20,20)], ["series_L_nH", "shunt_C_pF"]),
        "shunt_series": ([(-50,50),(-20,20)], ["series_L_nH", "shunt_C_pF"]),
        "series_shunt_series": ([(-50,50),(-20,20),(-50,50)],
                                ["series_L1_nH", "shunt_C_pF", "series_L2_nH"]),
        "shunt_series_shunt": ([(-20,20),(-50,50),(-20,20)],
                                ["shunt_C1_pF", "series_L_nH", "shunt_C2_pF"]),
    }
    cases=[]
    for topology,(bounds,names) in specs.items():
        fit=differential_evolution(lambda x: float(np.max(abs(response(x,topology)))),
                                   bounds,seed=7488,popsize=12,maxiter=120,
                                   tol=1e-7,polish=True)
        g=response(fit.x,topology)
        case={"topology_each_side":topology,
              **{n:float(v) for n,v in zip(names,fit.x)},
              "worst_S11_dB":float(20*np.log10(max(abs(g)))),
              "anchors":[]}
        for target in [100,150,200,300,400,500]:
            j=int(np.argmin(abs(f-target*1e6)))
            case["anchors"].append({"frequency_MHz":target,
                                     "S11_dB":float(20*np.log10(abs(g[j])))})
        cases.append(case)
    out={"classification":"CALCULATED_MATCHING_FEASIBILITY_DIAGNOSTIC_NOT_MEASURED",
         "source_run":args.run_name,
         "bounds":"signed elements; negative values mean removal/opposite reactance, not literal parts",
         "cases":cases,
         "decision_rule":"A further geometric transition is justified only if a low-order lossless diagnostic is broadly near -20 dB.",
         "limitations":["S22=S11 and S12=S21 symmetry assumption.",
                        "Reference-plane lumped elements do not reproduce a realizable 3-D taper.",
                        "The diagnostic cannot approve passives, fabrication or calibration accuracy."]}
    (run/"matching_feasibility_diagnostic.json").write_text(
        json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))


if __name__ == "__main__": main()
