"""Check port/current spectral stability with increasing time windows.

Independent of the global energy termination. This is a diagnostic, never a
claim of FDTD completion. Snapshot raw input bytes so in-progress reads remain
reproducible. Formulas match the installed openEMS Port.CalcPort.
"""
from pathlib import Path
import argparse,json,os,datetime
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'reviews/fixture_em_20260921'
rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
from openEMS.utilities import DFT_time2freq
p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('snapshot');a=p.parse_args()
d=O/a.run;dest=d/a.snapshot;dest.mkdir(exist_ok=False)
names=['port_ut_1','port_it_1','port_ut_2','port_it_2']+[f'core_{i}_{j}' for i in range(5) for j in range(2)]
data={}
for name in names:
 raw=(d/name).read_bytes();raw=raw[:raw.rfind(b'\n')+1];(dest/name).write_bytes(raw)
 lines=[x for x in raw.decode().splitlines() if x and not x.startswith('%') and not x.startswith('#')]
 data[name]=np.array([[float(v) for v in x.split()[:2]] for x in lines])
last=min(x[-1,0] for x in data.values());end=np.floor(last*1e9)*1e-9
freq=np.unique(np.r_[np.geomspace(1e6,500e6,151),[1e6,10e6,30e6,100e6,200e6,300e6,500e6]])
windows=[];responses=[]
for t in [end-2e-9,end-1e-9,end]:
 assert t>0
 f={}
 for name,x in data.items():
  v=x[x[:,0]<=t];f[name]=DFT_time2freq(v[:,0],v[:,1],freq)
 inc=(f['port_ut_1']+50*f['port_it_1'])/2
 s11=(f['port_ut_1']-50*f['port_it_1'])/2/inc
 s21=(f['port_ut_2']-50*f['port_it_2'])/2/inc
 hi=f['core_2_0']/inc*50
 rows=[dict(f_Hz=float(fr),S11_re=float(s11[i].real),S11_im=float(s11[i].imag),S21_re=float(s21[i].real),S21_im=float(s21[i].imag),I_over_matched_re=float(hi[i].real),I_over_matched_im=float(hi[i].imag),power_fraction=float(abs(s11[i])**2+abs(s21[i])**2),nested_delta_percent=float(abs(f['core_2_1'][i]/f['core_2_0'][i]-1)*100)) for i,fr in enumerate(freq)]
 windows.append(dict(end_ns=float(t*1e9),rows=rows));responses.append((s11,s21,hi))
changes=[]
for old,new in zip(responses,responses[1:]):
 changes.append(dict(s11_abs_max=float(np.max(abs(new[0]-old[0]))),s21_abs_max=float(np.max(abs(new[1]-old[1]))),hi_relative_max=float(np.max(abs(new[2]/old[2]-1)))))
out=dict(classification='IN_PROGRESS_TIME_WINDOW_DIAGNOSTIC_NOT_COMPLETED_RUN',run=a.run,last_common_ns=last*1e9,windows=windows,changes=changes)
(dest/'window_stability.json').write_text(json.dumps(out,indent=2));(dest/'analysis_source.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'last_common_ns':last*1e9,'changes':changes,'samples':[x for x in windows[-1]['rows'] if x['f_Hz'] in [1e6,100e6,300e6,500e6]]},indent=2))
