"""Graph-check openEMS' actual PEC edge dump, not the nominal CAD polygons."""
from pathlib import Path
import json, argparse
import numpy as np
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from scipy.spatial import cKDTree
p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();d=Path(a.directory)
r=vtkXMLPolyDataReader();r.SetFileName(str(d/'PEC_dump.vtp'));r.Update();poly=r.GetOutput()
assert poly.GetNumberOfPoints()>0
points=vtk_to_numpy(poly.GetPoints().GetData()).astype(float)
if np.max(abs(points))<1:points*=1000
lines=vtk_to_numpy(poly.GetLines().GetData()).reshape(-1,3)
assert np.all(lines[:,0]==2)
edges=lines[:,1:]
roi=(abs(points[:,0])<80)&(abs(points[:,1])<55)&(abs(points[:,2])<15)
edges=edges[np.all(roi[edges],axis=1)]
rows=np.r_[edges[:,0],edges[:,1]];cols=np.r_[edges[:,1],edges[:,0]]
graph=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(points),len(points))).tocsr()
_,labels=connected_components(graph,directed=False)
active=np.unique(edges);tree=cKDTree(points[active])
targets={'pin1':[0,-34.35,6.4],'shell1':[3,-34.35,6.4],
         'pin2':[0,34.35,6.4],'shell2':[3,34.35,6.4],'centre':[0,0,1.6]}
ids={name:int(active[tree.query(xyz)[1]]) for name,xyz in targets.items()}
result={'classification':'DISCRETIZED_PEC_GRAPH','source':str(d/'PEC_dump.vtp'),
        'points':len(points),'edges_roi':len(edges),'targets':{k:{'node':v,'xyz_mm':points[v].tolist(),'component':int(labels[v]),'snap_mm':float(np.linalg.norm(points[v]-targets[k]))} for k,v in ids.items()},'connections':{}}
paths={}
for name,start,end in [('signal_thru','pin1','pin2'),('return_thru','shell1','shell2'),('input_short','pin1','shell1'),('output_short','pin2','shell2'),('centre_signal','pin1','centre')]:
 s,t=ids[start],ids[end];connected=labels[s]==labels[t];result['connections'][name]=bool(connected)
 if connected:
  dist,pred=shortest_path(graph,directed=False,indices=s,unweighted=True,return_predecessors=True)
  path=[t]
  while path[-1]!=s:path.append(int(pred[path[-1]]))
  paths[name]=points[path[::-1]].tolist()
result['paths_mm']=paths
(d/'pec_connectivity.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='paths_mm'},indent=2))
if paths.get('input_short'):print('SHORTEST INPUT SHORT PATH',json.dumps(paths['input_short']))
