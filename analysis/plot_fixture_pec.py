"""Plot original copper and the solver's exported edges at the SMA input."""
from pathlib import Path
import argparse,json
import numpy as np
from shapely.geometry import Polygon,Point
from shapely import union_all
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy
R=Path(__file__).resolve().parents[1];O=R/'reviews/fixture_em_20260921'
p=argparse.ArgumentParser();p.add_argument('runs',nargs='+');p.add_argument('--region',choices=['sma','taper'],default='sma');a=p.parse_args()
g=json.loads((O/'geometry.json').read_text())
fig,axs=plt.subplots(1,len(a.runs),figsize=(6*len(a.runs),5.8),squeeze=False)
for ax,run in zip(axs[0],a.runs):
 for layer_index,(net,col) in enumerate([('/GND','#bfd7df'),('/SIG','#edb26b')]):
  areas=[Polygon(x['outer'],x['holes']) for z in g['zones'] if z['layer']=='F.Cu' and z['net']==net for x in z['polygons']]
  areas += [Point(x['x'],x['y']).buffer(x['diameter']/2) for x in g['pads']+g['vias'] if x['net']==net]
  area=union_all(areas)
  for s in getattr(area,'geoms',[area]):
   ax.fill(*s.exterior.xy,color=col,zorder=1+layer_index)
   for hole in s.interiors:ax.fill(*hole.xy,color='white',zorder=1.1+layer_index)
 for pad in g['pads']:
  ax.add_patch(plt.Circle((pad['x'],pad['y']),pad['drill']/2,color='white',zorder=3))
 r=vtkXMLPolyDataReader();r.SetFileName(str(O/run/'PEC_dump.vtp'));r.Update();poly=r.GetOutput()
 pts=vtk_to_numpy(poly.GetPoints().GetData()).astype(float)*1000
 e=vtk_to_numpy(poly.GetLines().GetConnectivityArray()).reshape(-1,2)
 keep=np.all(abs(pts[e,2]-1.6)<1e-4,axis=1)
 ax.add_collection(LineCollection(pts[e[keep],:2],colors='#152c40',linewidths=1,zorder=4))
 f=O/run/'pec_connectivity.json'
 if f.exists():
  d=json.loads(f.read_text());path=np.asarray(d['paths_mm'].get('input_short',[]))
  if len(path):
   xy=path[abs(path[:,2]-1.6)<1e-4,:2];ax.plot(xy[:,0],xy[:,1],color='#d12e2e',lw=3,zorder=5)
  status='ARTIFICIAL SHORT' if d['connections']['input_short'] else 'SIG / GND SEPARATED'
 else:status='PENDING GRAPH CHECK'
 ax.set(xlim=(-3,3) if a.region=='sma' else (-4.5,4.5),ylim=(-38,-31) if a.region=='sma' else (-26,-18),aspect='equal',xlabel='x [mm]',ylabel='y [mm]',title=run+'\n'+status)
 ax.grid(alpha=.18)
fig.suptitle('Model debugging: original copper vs discretized PEC edges\nOrange = SIG, blue = GND, lines = actual solver metal connections',fontsize=12)
fig.tight_layout(rect=[0,0,1,.9]);fig.savefig(O/('pec_comparison_'+a.region+'.png'),dpi=160)
