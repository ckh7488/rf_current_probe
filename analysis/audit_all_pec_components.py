"""Audit every active PEC edge, including floating islands and via net membership."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--geometry',required=True);p.add_argument('--expect-two',action='store_true');a=p.parse_args();d=Path(a.directory)
source=d/'PEC_dump.vtp';r=vtkXMLPolyDataReader();r.SetFileName(str(source));r.Update();poly=r.GetOutput()
xyz=vtk_to_numpy(poly.GetPoints().GetData()).astype(float)
if np.max(abs(xyz))<1:xyz*=1000
e=vtk_to_numpy(poly.GetLines().GetData()).reshape(-1,3)[:,1:]
# Verify shared physical endpoints even if VTK emitted duplicate point IDs.
points,inverse=np.unique(np.round(xyz,4),axis=0,return_inverse=True);e=inverse[e]
roi=(abs(points[:,0])<80)&(abs(points[:,1])<55)&(abs(points[:,2])<15);e=e[np.all(roi[e],axis=1)]
g=coo_matrix((np.ones(2*len(e)),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(points),len(points))).tocsr()
_,labels=connected_components(g,directed=False);active=np.unique(e);ids,counts=np.unique(labels[active],return_counts=True);tree=cKDTree(points[active])
def lookup(x):
 dist,index=tree.query(x);idx=active[index]
 return dict(component=int(labels[idx]),snap_mm=float(dist),xyz_mm=points[idx].tolist())
sig=lookup([0,-34.35,6.4]);gnd=lookup([3,-34.35,6.4]);assert sig['component']!=gnd['component'],'Artificial SIG/GND short'
components=[]
for k in np.argsort(-counts):
 v=points[active[labels[active]==ids[k]]]
 components.append(dict(id=int(ids[k]),nodes=int(counts[k]),bbox_min_mm=v.min(0).tolist(),bbox_max_mm=v.max(0).tolist()))
geo=json.loads(Path(a.geometry).read_text());vias=[]
# A nearest-node membership test alone can pass a completely missing via:
# the nearest copper plane can have the right net. Independently require an
# uninterrupted vertical PEC edge chain at the exact physical via centre.
vertical=e[(np.abs(points[e[:,0],0]-points[e[:,1],0])<1e-4)&(np.abs(points[e[:,0],1]-points[e[:,1],1])<1e-4)]
for v in geo['vias']:
 found=lookup([v['x'],v['y'],geo['thickness']/2]);expected=sig['component'] if v['net']=='/SIG' else gnd['component']
 centre=vertical[(np.abs(points[vertical[:,0],0]-v['x'])<1e-4)&(np.abs(points[vertical[:,0],1]-v['y'])<1e-4)]
 intervals=sorted([sorted(points[edge,2].tolist()) for edge in centre])
 end=0.;used=0;correct=True
 for lo,hi in intervals:
  if hi<=0 or lo>=geo['thickness']:continue
  if lo>end+1e-4:break
  end=max(end,hi);used+=1
  edge=centre[[sorted(points[e0,2].tolist()) for e0 in centre].index([lo,hi])]
  correct=correct and bool(np.all(labels[edge]==expected))
 connected=end>=geo['thickness']-1e-4 and used>0 and correct
 vias.append(dict(x=v['x'],y=v['y'],net=v['net'],**found,correct_component=found['component']==expected,vertical_edges=used,vertical_coverage_mm=end,continuous_centre_column_on_expected_net=connected))
result=dict(classification='CALCULATED_FULL_DISCRETIZED_PEC_TOPOLOGY_NOT_PHYSICAL_RF_TEST',vtk_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),raw_points=len(xyz),unique_points=len(points),component_count=len(components),components=components,signal=sig,ground=gnd,vias=vias,all_vias_in_correct_net=all(v['correct_component'] for v in vias),pass_exactly_two_conducting_components=len(components)==2 and all(v['correct_component'] for v in vias))
result['all_vias_have_continuous_vertical_PEC']=all(v['continuous_centre_column_on_expected_net'] for v in vias)
result['pass_exactly_two_conducting_components']=result['pass_exactly_two_conducting_components'] and result['all_vias_have_continuous_vertical_PEC']
(d/'all_pec_components.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['components','vias']},indent=2))
if a.expect_two:assert result['pass_exactly_two_conducting_components'],'Floating or wrongly connected PEC remains'
