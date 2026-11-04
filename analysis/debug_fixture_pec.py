"""Inspect the actual discretized PEC before interpreting FDTD results."""
from pathlib import Path
import os, argparse, json
R=Path(__file__).resolve().parents[1]
rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt)
os.environ['CSXCAD_INSTALL_PATH']=str(rt)
from CSXCAD import ContinuousStructure
from openEMS import openEMS
p=argparse.ArgumentParser()
p.add_argument('--source',default='finite_leads')
p.add_argument('--name',default='pec_original')
a=p.parse_args()
root=R/'reviews/fixture_em_20260921'
d=root/a.name
d.mkdir(exist_ok=False)
c=ContinuousStructure();c.ReadFromXML(str(root/a.source/'model.xml'))
f=openEMS(NrTS=1);f.SetCSX(c);f.SetGaussExcite(0,1e9);f.SetBoundaryCond(['PML_8']*6)
(d/'model_source.py').write_bytes(Path(__file__).read_bytes())
c.Write2XML(str(d/'model.xml'))
f.Run(str(d),setup_only=True,numThreads=8,verbose=1,debug_PEC=True,debug_operator=True)
print(json.dumps({'files':[x.name for x in d.iterdir()]}))
