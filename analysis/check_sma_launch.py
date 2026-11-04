"""Isolated connector-launch sanity with a short conductive thru path."""
from pathlib import Path
import os,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
import numpy as np
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data
O=R/'reviews/fixture_em_20260921/launch_thru';O.mkdir(exist_ok=True)
tree=ET.parse(R/'reviews/fixture_em_20260921/aligned_ports/model.xml');props=tree.find('Properties')
for p in list(props):
 if p.get('Name') not in ['connector_shell_PEC','connector_pin_PEC','connector_PTFE_assumed']:props.remove(p);continue
 prims=p.find('Primitives')
 for pr in list(prims):
  if pr.tag=='Curve':prims.remove(pr)
tree.write(O/'stripped.xml');c=ContinuousStructure();c.ReadFromXML(str(O/'stripped.xml'));g=c.GetGrid();g.SetDeltaUnit(1e-3)
for d,a in [('x',np.r_[-60,np.arange(-7,7.01,.5),60]),('y',np.r_[-80,np.arange(-40,-28.99,.5),np.arange(-28,29,2),np.arange(29,40.01,.5),80]),('z',np.r_[-50,np.arange(-2,10.01,.5),50])]:g.SetLines(d,SmoothMeshLines(np.unique(a),6,1.5))
sig=c.AddMetal('thru_signal');gnd=c.AddMetal('thru_return')
sig.AddBox(priority=25,start=[-.5,-35,1.5],stop=[.5,35,1.5])
for x0,x1 in [(-5,-2),(2,5)]:gnd.AddBox(priority=25,start=[x0,-38,0],stop=[x1,38,0])
gnd.AddBox(priority=25,start=[-5,-38,0],stop=[5,-37.5,0]);gnd.AddBox(priority=25,start=[-5,37.5,0],stop=[5,38,0])
f=openEMS(NrTS=30000,EndCriteria=1e-5);f.SetCSX(c);f.SetGaussExcite(0,1e9);f.SetBoundaryCond(['PML_8']*6)
ports=[]
for k,y in enumerate([-34.35,34.35],1):
 # Solid lead boxes replace the diagnostic curve leads.
 sig.AddBox(priority=24,start=[.5,y-.5,6],stop=[1,y+.5,7]);gnd.AddBox(priority=24,start=[2,y-.5,6],stop=[2.5,y+.5,7])
 ports.append(f.AddLumpedPort(k,50,[2,y-.5,6],[1,y+.5,7],'x',excite=k==1,priority=30))
probe=c.AddProbe('I_centre',p_type=1,norm_dir=1);probe.AddBox(start=[-1,0,.5],stop=[1,0,2.5])
c.Write2XML(str(O/'model.xml'));f.Run(str(O),numThreads=8,verbose=1,engine='multithreaded')
freq=np.array([1e6,10e6,100e6,300e6,500e6]);[p.CalcPort(str(O),freq,ref_impedance=50) for p in ports]
a,b=ports;I=UI_data('I_centre',str(O),freq).ui_f_val[0]
rows=[dict(f_Hz=float(fr),s11_abs=float(abs(a.uf_ref[k]/a.uf_inc[k])),s21_abs=float(abs(b.uf_ref[k]/a.uf_inc[k])),i_ratio_re=float((I[k]/a.if_tot[k]).real),i_ratio_im=float((I[k]/a.if_tot[k]).imag)) for k,fr in enumerate(freq)]
(O/'result.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
