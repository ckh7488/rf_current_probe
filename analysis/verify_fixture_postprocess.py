"""Analytic delayed-Gaussian check of V/I wave signs, DFT timing and HI units."""
from pathlib import Path
import os,json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
from openEMS.utilities import DFT_time2freq
freq=np.geomspace(1e6,500e6,71);t=np.arange(0,12e-9,2e-12);ti=t+1e-12
sig=.4e-9;t0=3e-9
def g(t,delay=0):return np.exp(-.5*((t-t0-delay)/sig)**2)
def ft(delay=0):return 2*np.sqrt(2*np.pi)*sig*np.exp(-.5*(2*np.pi*freq*sig)**2)*np.exp(-2j*np.pi*freq*(t0+delay))
def df(t,x):return DFT_time2freq(t,x,freq)
reflection=.2;reflection_delay=.8e-9;through=.9;through_delay=.5e-9
u=df(t,g(t)+reflection*g(t,reflection_delay));i=df(ti,(g(ti)-reflection*g(ti,reflection_delay))/50)
uo=df(t,through*g(t,through_delay));io=df(ti,-through*g(ti,through_delay)/50)
inc=(u+50*i)/2;sref=(u-50*i)/2/inc;sthru=(uo-50*io)/2/inc
hi=df(ti,g(ti,.25e-9)/50)/inc*np.sqrt(50)
hi_reverse=df(ti,-g(ti,.25e-9)/50)/inc*np.sqrt(50)
checks=dict(DFT_vs_analytic=float(np.max(abs(df(t,g(t))/ft()-1))),reflected_wave=float(np.max(abs(sref-reflection*ft(reflection_delay)/ft()))),through_wave=float(np.max(abs(sthru-through*ft(through_delay)/ft()))),HI_normalization=float(np.max(abs(hi-(1/np.sqrt(50))*ft(.25e-9)/ft()))),reverse_sign_alignment=float(np.max(abs(hi+hi_reverse))))
assert max(checks.values())<1e-10,checks
out=dict(classification='SYNTHETIC_ANALYTIC_VERIFICATION_NOT_MEASURED',checks=checks,tolerance=1e-10,description='Closed-form Fourier transform of delayed Gaussian; voltage and current sampled half a time-step apart; known reflection, through delay, 50 ohm normalization and reverse physical-current sign.',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(R/'reviews/design_closure_20260921/postprocess_verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
