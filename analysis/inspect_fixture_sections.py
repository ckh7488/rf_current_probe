from pathlib import Path
import json
from shapely import union_all
from shapely.geometry import Polygon,LineString
g=json.loads((Path(__file__).resolve().parents[1]/'reviews/fixture_em_20260921/geometry.json').read_text())
nets={net:union_all([Polygon(p['outer'],p['holes']) for z in g['zones'] if z['layer']=='F.Cu' and z['net']==net for p in z['polygons']]) for net in ['/SIG','/GND']}
for y in [-32,-30,-28,-26,-24.5,-24,-23.5,-23,-22.5,-22,-21.5,-21,-20,-18,0]:
 out={'y':y}
 for n,s in nets.items():
  x=s.intersection(LineString([[-10,y],[10,y]]));out[n]=[list(a.bounds) for a in getattr(x,'geoms',[x])]
 print(json.dumps(out))
