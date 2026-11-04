"""Bounded symmetric two-element diagnostic around the A05 coarse 2-port."""
from pathlib import Path
import json

import numpy as np
from scipy.optimize import differential_evolution


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reviews/fixture_structural_redesign_20260922/em/a05_screen_m100_fast"
rows = json.loads((RUN / "results.json").read_text(encoding="utf-8"))["rows"]
f = np.asarray([r["f_Hz"] for r in rows]); w = 2*np.pi*f
s11 = np.asarray([complex(r["S11_re"], r["S11_im"]) for r in rows])
s21 = np.asarray([complex(r["S21_re"], r["S21_im"]) for r in rows])
z0 = 50.; s22=s11; s12=s21
a=((1+s11)*(1-s22)+s12*s21)/(2*s21)
b=z0*((1+s11)*(1+s22)-s12*s21)/(2*s21)
c=((1-s11)*(1-s22)-s12*s21)/(2*z0*s21)
d=((1-s11)*(1+s22)+s12*s21)/(2*s21)


def mm(x1,x2):
    return (x1[0]*x2[0]+x1[1]*x2[2], x1[0]*x2[1]+x1[1]*x2[3],
            x1[2]*x2[0]+x1[3]*x2[2], x1[2]*x2[1]+x1[3]*x2[3])


M=(a,b,c,d)


def response(x, order):
    L, C = x[0]*1e-9, x[1]*1e-12
    series=(np.ones_like(w),1j*w*L,np.zeros_like(w),np.ones_like(w))
    shunt=(np.ones_like(w),np.zeros_like(w),1j*w*C,np.ones_like(w))
    edge=mm(series,shunt) if order=="series_shunt" else mm(shunt,series)
    t=mm(mm(edge,M),edge)
    aa,bb,cc,dd=t; den=aa+bb/z0+cc*z0+dd
    return (aa+bb/z0-cc*z0-dd)/den


out={"classification":"CALCULATED_DIAGNOSTIC_FROM_COARSE_SIMULATION_NOT_MEASURED",
     "bounds":{"added_series_L_nH":[-30,30],"added_shunt_C_pF":[-10,10]},"cases":[]}
for order in ["series_shunt","shunt_series"]:
    def objective(x):
        return float(np.max(abs(response(x,order))))
    fit=differential_evolution(objective,[(-30,30),(-10,10)],seed=7488,
                               popsize=10,maxiter=80,tol=1e-7,polish=True)
    g=response(fit.x,order)
    anchors=[]
    for target in [100,150,200,300,400,500]:
        j=int(np.argmin(abs(f-target*1e6)))
        anchors.append({"frequency_MHz":target,"S11_dB":float(20*np.log10(abs(g[j])))})
    out["cases"].append({"order_each_side":order,"added_series_L_nH":float(fit.x[0]),
                         "added_shunt_C_pF":float(fit.x[1]),
                         "worst_S11_dB":float(20*np.log10(max(abs(g)))),"anchors":anchors})
out["limits"]=["Symmetric S22=S11/S12=S21 assumption.",
               "Negative L/C are diagnostic removals or opposite reactance, not literal parts.",
               "The short coarse time window has passivity error; this tests feasibility direction only."]
(RUN/"two_element_adjustment_diagnostic.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
