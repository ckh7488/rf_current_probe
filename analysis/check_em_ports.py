"""Low-frequency thru sanity for lumped-port V/I and Ampere current extraction."""
from pathlib import Path
import os,json
R=Path(__file__).resolve().parents[1];rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
import numpy as np
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data
O=R/'reviews/fixture_em_20260921/port_reference';O.mkdir(exist_ok=True)
c=ContinuousStructure();m=c.GetGrid();m.SetDeltaUnit(1e-3)
for d,lines in [('x',np.r_[-40,np.arange(-6,6.01,.5),40]),('y',np.r_[-50,np.arange(-12,12.01,.5),50]),('z',np.r_[-35,np.arange(-2,4.01,.5),35])]:m.SetLines(d,SmoothMeshLines(lines,5,1.5))
f=openEMS(NrTS=30000,EndCriteria=1e-6,MaxTime=30e-9);f.SetCSX(c);f.SetGaussExcite(0,1e9);f.SetBoundaryCond(['PML_8']*6)
c.AddMetal('ground').AddBox(priority=10,start=[-6,-12,0],stop=[6,12,0])
c.AddMetal('signal').AddBox(priority=10,start=[-1,-10.5,2],stop=[1,10.5,2])
ports=[]
for k,y in enumerate([-10,10],1):ports.append(f.AddLumpedPort(k,50,[-1,y-.5,0],[1,y+.5,2],'z',excite=k==1,priority=20))
p=c.AddProbe('I_centre',p_type=1,norm_dir=1,weight=1);p.AddBox(start=[-2,0,1],stop=[2,0,3])
c.Write2XML(str(O/'model.xml'));f.Run(str(O),verbose=0,numThreads=4,engine='multithreaded')
freq=np.array([1e6,10e6,100e6,300e6,500e6]);[p.CalcPort(str(O),freq,ref_impedance=50) for p in ports]
i=UI_data('I_centre',str(O),freq).ui_f_val[0];a,b=ports
rows=[]
for k,fr in enumerate(freq):
 s11=a.uf_ref[k]/a.uf_inc[k];s21=b.uf_ref[k]/a.uf_inc[k];ratio=i[k]/a.if_tot[k]
 rows.append(dict(f_Hz=float(fr),S11_abs=float(abs(s11)),S21_abs=float(abs(s21)),current_ratio_re=float(ratio.real),current_ratio_im=float(ratio.imag),power=float(abs(s11)**2+abs(s21)**2)))
result=dict(classification='SIMULATED_LOW_FREQUENCY_THRU_SANITY_NOT_FULL_SOLVER_VALIDATION',rows=rows,pass_low_frequency=rows[0]['S11_abs']<.02 and abs(rows[0]['S21_abs']-1)<.02 and abs(abs(complex(rows[0]['current_ratio_re'],rows[0]['current_ratio_im']))-1)<.02)
(O/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
