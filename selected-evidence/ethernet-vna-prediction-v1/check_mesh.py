"""Check all signal paths and sampled copper shorts before an FDTD run."""
from pathlib import Path
from collections import defaultdict
import argparse
import json
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    args = ap.parse_args()
    folder = HERE/'runs'/args.name
    d = json.loads((HERE/'input/brj2-pcb-model.json').read_text())
    meta = json.loads((folder/'model.json').read_text())
    g = np.load(folder/'grid.npz')
    x, y = g['x'], g['y']
    ny, count = len(y), len(x)*len(y)
    xm, ym = (x[:-1]+x[1:])/2, (y[:-1]+y[1:])/2
    xx, yy = np.meshgrid(xm, y, indexing='ij')
    xx2, yy2 = np.meshgrid(x, ym, indexing='ij')
    shapes = defaultdict(lambda: defaultdict(list))
    for t in d['tracks']:
        shapes[t['net']][t['layer']].append(LineString([t['start'], t['end']]).buffer(t['width']/2, quad_segs=12))
    for z in d['zones']:
        shapes[z['net']][z['layer']].extend(Polygon(p['outer'], p['holes']) for p in z['polygons'])
    for p in d['pads']:
        if not p['npth']:
            for layer, polys in p['polygons'].items():
                shapes[p['net']][layer].extend(Polygon(q['outer'], q['holes']) for q in polys)
    for v in d['vias']:
        for layer in LAYERS:
            shapes[v['net']][layer].append(Point(v['xy']).buffer(v['diameter']/2, quad_segs=12))
    owner_x = [np.zeros(xx.shape, dtype=np.int16) for _ in LAYERS]
    owner_y = [np.zeros(xx2.shape, dtype=np.int16) for _ in LAYERS]
    results, conflicts = [], []
    names = sorted(shapes)
    for ni, net in enumerate(names, 1):
        adjacency = defaultdict(list)
        ports = [p for p in meta['ports'] if p['net'] == net]
        for li, layer in enumerate(LAYERS):
            geometry = unary_union(shapes[net][layer])
            for ox, px, py, delta in [(owner_x[li], xx, yy, ny), (owner_y[li], xx2, yy2, 1)]:
                mask = shapely.intersects_xy(geometry, px, py)
                overlap = mask & (ox != 0) & (ox != ni)
                if np.any(overlap):
                    conflicts.append({'layer': layer, 'net': net, 'other_nets': [names[i-1] for i in np.unique(ox[overlap])], 'edges': int(overlap.sum())})
                ox[mask] = ni
                if len(ports) == 2:
                    a, b = np.where(mask)
                    nodes = li*count+a*ny+b
                    for u, v in zip(nodes.tolist(), (nodes+delta).tolist()):
                        adjacency[u].append(v)
                        adjacency[v].append(u)
        if len(ports) != 2:
            continue
        barrels = [v for v in d['vias'] if v['net'] == net]
        barrels += [p for p in d['pads'] if p['net'] == net and p['drill'][0]]
        for v in barrels:
            drill = v['drill'][0] if isinstance(v['drill'], list) else v['drill']
            a, b = np.where((x[:, None]-v['xy'][0])**2+(y[None, :]-v['xy'][1])**2 <= (drill/2+.025)**2)
            for li in range(3):
                for u in (li*count+a*ny+b).tolist():
                    adjacency[u].append(u+count)
                    adjacency[u+count].append(u)
        ids = []
        for p in ports:
            li = LAYERS.index(p['signal_layer'])
            # Port trim puts the signal vertex at the dielectric/metal edge.
            # The original pad point is attached through adjacent metal edges.
            q = p['original_stop']
            ids.append(li*count+int(np.argmin(abs(x-q[0])))*ny+int(np.argmin(abs(y-q[1]))))
        seen, todo = {ids[0]}, [ids[0]]
        while todo:
            current = todo.pop()
            for node in adjacency[current]:
                if node not in seen:
                    seen.add(node)
                    todo.append(node)
        results.append({'net': net, 'connected': ids[1] in seen, 'nodes': len(seen)})
    report = {'paths': results, 'sampled_shorts': conflicts,
              'pass': len(results) == 12 and all(r['connected'] for r in results) and not conflicts}
    (folder/'mesh-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    assert report['pass'], 'Mesh topology failed; do not use this extraction.'


if __name__ == '__main__':
    main()
