"""Independent nominal 2-D copper checks on extracted saved KiCad geometry."""
from pathlib import Path
import json, hashlib
from shapely.geometry import Polygon,Point,LineString
from shapely import union_all
R=Path(__file__).resolve().parents[1];O=R/'reviews/fixture_em_20260921'
g=json.loads((O/'geometry.json').read_text());rows=[]
for layer in ['F.Cu','B.Cu']:
 nets={}
 for net in ['/SIG','/GND']:
  areas=[Polygon(p['outer'],p['holes']) for z in g['zones'] if z['layer']==layer and z['net']==net for p in z['polygons']]
  areas += [Point(p['x'],p['y']).buffer(p['diameter']/2,quad_segs=12) for p in g['pads']+g['vias'] if p['net']==net]
  nets[net]=union_all(areas)
 sig,ground=nets['/SIG'],nets['/GND']
 chords=union_all([LineString([(p['x']-p['diameter']/2,p['y']),(p['x']+p['diameter']/2,p['y'])]) for p in g['pads'] if p['net']=='/SIG'])
 rows.append(dict(layer=layer,sig_gnd_intersection_mm2=sig.intersection(ground).area,
                  gap_mm=sig.distance(ground),nominal_solder_chord_intersects_ground=chords.intersects(ground),
                  centreline_connected=sig.covers(LineString(g['ports'])),
                  ground_at_core_centre=ground.intersects(LineString([[-8,0],[8,0]]))))
source=R/g['source'];result=dict(classification='CALCULATED_NOMINAL_GEOMETRY',
   board_hash_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==g['sha256'],rows=rows)
(O/'nominal_connectivity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['board_hash_unchanged']
assert all(x['sig_gnd_intersection_mm2']==0 and x['centreline_connected'] and not x['nominal_solder_chord_intersects_ground'] and not x['ground_at_core_centre'] for x in rows)
