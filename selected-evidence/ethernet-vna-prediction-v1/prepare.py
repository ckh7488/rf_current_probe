"""Snapshot independent inputs and prepare the latest-board multiport geometry."""
from pathlib import Path
import hashlib
import json
import shutil
from datetime import datetime, timezone, timedelta

from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT / 'reviews/ethernet_board_review_20261113'
INPUT = HERE / 'input'
INPUT.mkdir(exist_ok=True)
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shifted(xy):
    return [round(float(v) - 20, 7) for v in xy]


def polygons(items):
    return [{'outer': [shifted(v) for v in p['shell']],
             'holes': [[shifted(v) for v in h] for h in p['holes']]} for p in items]


def shape(poly):
    return Polygon(poly['outer'], poly['holes']).buffer(0)


def serialize(geometry):
    ps = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
    return [{'outer': list(p.exterior.coords), 'holes': [list(h.coords) for h in p.interiors]}
            for p in ps if p.geom_type == 'Polygon']


def main():
    common = next(x for x in json.loads((ROOT/'reviews/jlc_renewal_preflight_20260929/final_checks/geometry.json').read_text()) if x['name']=='common')
    native = ROOT/'reviews/jlc_renewal_preflight_20260929/candidate/common/balun_eth_rj45.kicad_pcb'
    assert digest(native) == common['sha256']
    sources = [native, REVIEW/'prediction-inputs/ADT2-1T+___Plus25degC.s4p',
               REVIEW/'single-board-test-plan.json', REVIEW/'fixture-geometry.json',
               REVIEW/'fixture-photos/manifest.json', REVIEW/'fixture-photos/fixture-pair-ruler.png']
    files = []
    for src in sources:
        target = INPUT/src.name
        if target.exists():
            assert target.read_bytes() == src.read_bytes(), f'Input changed: {src}'
        else:
            shutil.copy2(src, target)
        files.append({'source': str(src), 'snapshot': target.name, 'sha256': digest(target)})
    d = {'id':'brj2', 'pcb_sha256':common['sha256'], 'bounds_mm':[0,0,80,74],
         'tracks':[], 'vias':[], 'pads':[], 'zones':[], 'outline':[], 'ports':[]}
    for t in common['tracks']:
        assert t['type'] == 'PCB_TRACK'
        d['tracks'].append({k:t[k] for k in ('net','layer','width')} |
                           {'start':shifted(t['start']), 'end':shifted(t['end'])})
    for v in common['vias']:
        d['vias'].append(v | {'xy':shifted(v['xy'])})
    for p in common['pads']:
        d['pads'].append({k:p[k] for k in ('ref','pin','net','size','drill')} |
                         {'xy':shifted(p['xy']), 'npth':p['attribute']==2,
                          'layers':[l for l in p['layers'] if l in LAYERS],
                          'polygons':{l:polygons(ps) for l,ps in p['polys'].items() if l in LAYERS}})
    for z in common['zones']:
        d['zones'].append({'net':z['net'],'layer':z['layer'],'polygons':polygons(z['polys'])})
    for e in common['outline']:
        d['outline'].append({'start':shifted(e['start']),'end':shifted(e['end'])})
    copper = {layer:[] for layer in LAYERS}
    for z in d['zones']:
        copper[z['layer']].extend(shape(p) for p in z['polygons'])
    for t in d['tracks']:
        copper[t['layer']].append(LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=12))
    for p in d['pads']:
        if not p['npth']:
            for layer, ps in p['polygons'].items():
                copper[layer].extend(shape(q) for q in ps)
    for v in d['vias']:
        for layer in LAYERS:
            copper[layer].append(Point(v['xy']).buffer(v['diameter']/2,quad_segs=12))
    merged = {layer:unary_union(items).buffer(0) for layer,items in copper.items()}
    d['copper'] = {layer:serialize(poly) for layer,poly in merged.items()}
    # Local PCB terminal interfaces. External connectors are separate blocks.
    requests = [(f'J{i}', '1', f'SMA_{"ABCD"[i-2]}') for i in range(2,6)]
    requests += [(f'T{i}', pin, f'T{i}_{pin}') for i in range(1,5) for pin in ['3','4','6']]
    requests += [('J1', str(i), f'RJ_{i}') for i in range(1,9)]
    for ref,pin,name in requests:
        pad = next(p for p in d['pads'] if p['ref']==ref and p['pin']==pin)
        reference_layer = 'In1.Cu'
        reference_z, signal_z = .2454, .035
        x,y = pad['xy']
        if pad['drill'][0] > 0:
            # The PTH signal pad is cleared from the inner GND reference.
            # Prefer a .2 mm dielectric gap beyond its outer annulus.
            radius = max(pad['size'])/2
            options=[]
            for dx,dy,axis in [(1,0,'x'),(-1,0,'x'),(0,1,'y'),(0,-1,'y')]:
                start=[x+dx*(radius+.45),y+dy*(radius+.45),reference_z]
                stop=[x+dx*(radius-.12),y+dy*(radius-.12),reference_z]
                if merged[reference_layer].covers(Point(start[:2])) and any(
                    shape(q).covers(Point(stop[:2])) for q in pad['polygons'][reference_layer]):
                    options.append((start,stop,axis))
            assert options, (name,'no grounded antipad edge found')
            start,stop,axis=options[0]
            signal_layer=reference_layer
        else:
            assert merged[reference_layer].covers(Point(x,y)), (name,'no reference plane below pad')
            start=[x,y,reference_z];stop=[x,y,signal_z];axis='z';signal_layer='F.Cu'
        d['ports'].append({'number':len(d['ports'])+1,'name':name,'ref':ref,'pin':pin,'net':pad['net'],
                           'start':start,'stop':stop,'direction':axis,'reference_layer':reference_layer,
                           'signal_layer':signal_layer,'reference_ohm':50})
    assert len(d['ports']) == 24
    (INPUT/'brj2-pcb-model.json').write_text(json.dumps(d,separators=(',',':')),encoding='utf-8')
    plan = {'date':'2026-11-13','created_at_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),
            'status':'MODEL_PREPARATION_BEFORE_RF_MEASUREMENT', 'files':files,
            'population':{'RCT1_RCT4':'DNP, confirmed by user','RSH1':'DNP, confirmed by user','CSH1':'DNP, confirmed by user'},
            'observables':['Open RJ45, SMA B input S11','Open RJ45, SMA D to C S21',
                           'A/J2 with orange-pair resistive load S11','D/J5 to C/J4 with physical loopback S21'],
            'frequency_hz':{'start':1000000,'stop':200000000,'points':1601},
            'independent_inputs':'Selected CAD, fabrication stackup, manufacturer component data, user DC resistor reading and fixture ruler photographs.',
            'new_rf_measurements_used':False,
            'method':'PCB electromagnetic multiport extraction followed by manufacturer balun network and declared connector/fixture electrical blocks.',
            'numerical_checks_before_freeze':['Port-to-copper ownership','Mesh continuity and no signal shorts','Incident-wave matrix conditioning','Reciprocity/passivity and time-window stability'],
            'prediction_release':'Write a separate input/code manifest and prediction hash before receiving the new VNA traces.'}
    (HERE/'prediction-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pcb_sha256':d['pcb_sha256'],'ports':[(p['number'],p['name']) for p in d['ports']],
                      'copper_regions':{l:len(v) for l,v in d['copper'].items()},'new_rf_measurements_used':False}))


if __name__ == '__main__':
    main()
