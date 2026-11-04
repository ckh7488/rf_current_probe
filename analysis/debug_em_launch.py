"""Isolate launch discretization; diagnostic only, not a DUT simulation."""
import os
from pathlib import Path
R=Path(__file__).resolve().parents[1];rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
from CSXCAD import ContinuousStructure
from openEMS import openEMS
for case in ['launch_only','without_shell']:
 print('CASE:',case,flush=True)
 c=ContinuousStructure();c.ReadFromXML(str(R/'reviews/fixture_em_20260921/aligned_ports/model.xml'))
 for p in list(c.GetAllProperties()):
  n=p.GetName()
  if n in ['FR4_assumed_lossless','SIG_PEC','GND_PEC','ideal_via_PEC'] or n.startswith('core_') or (case=='without_shell' and n=='connector_shell_PEC'):c.RemoveProperty(p)
 if case=='without_curves':
  for p in list(c.GetAllProperties()):
   for prim in list(p.GetAllPrimitives()):
    if prim.GetTypeName()=='Curve':p.RemovePrimitive(prim)
 f=openEMS(NrTS=2000);f.SetCSX(c);f.SetGaussExcite(0,1e9);f.SetBoundaryCond(['PML_8']*6)
 f.Run(str(R/'reviews/fixture_em_20260921'/('debug_'+case)),setup_only=True,verbose=1,numThreads=8,engine='multithreaded',dump_statistics=True)
