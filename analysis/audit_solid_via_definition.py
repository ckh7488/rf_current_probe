"""Read back actual solver XML: all finite vias, dimensions and grid placement."""
import argparse,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--geometry',required=True);a=p.parse_args();d=Path(a.directory)
tree=ET.parse(d/'model.xml');geo=json.loads(Path(a.geometry).read_text())
prop=tree.find(".//Metal[@Name='solid_via_PEC']")
assert prop is not None
cylinders=prop.findall('.//Cylinder');assert len(cylinders)==len(geo['vias'])==45
assert not prop.findall('.//Curve'),'Via source still contains zero-radius curves'
grid={axis:np.array([float(x) for x in tree.find('.//'+axis.upper()+'Lines').text.split(',')]) for axis in 'xyz'}
checks=[]
for c in cylinders:
 start=c.find('P1');stop=c.find('P2');x=float(start.get('X'));y=float(start.get('Y'));radius=float(c.get('Radius'))
 v=next(v for v in geo['vias'] if abs(v['x']-x)<1e-7 and abs(v['y']-y)<1e-7)
 assert abs(radius-v['drill']/2)<1e-7 and float(start.get('Z'))==0 and float(stop.get('Z'))==geo['thickness']
 assert float(stop.get('X'))==x and float(stop.get('Y'))==y
 required={'x':[x-radius,x,x+radius],'y':[y-radius,y,y+radius],'z':[0,geo['thickness']]}
 error=max(float(min(abs(grid[axis]-q))) for axis,vals in required.items() for q in vals)
 assert error<1e-7,(v,error)
 checks.append(dict(x=x,y=y,radius_mm=radius,net=v['net'],max_grid_alignment_error_mm=error))
out=dict(classification='CALCULATED_SOLVER_XML_READBACK',xml_sha256=hashlib.sha256((d/'model.xml').read_bytes()).hexdigest(),solid_via_count=len(checks),all_vias=checks,pass_finite_cylinder_dimensions_and_mesh=True)
(d/'solid_via_definition.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='all_vias'},indent=2))
