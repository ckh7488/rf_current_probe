"""Extract the selected B-RJ2 PCB network at 24 physical PCB terminals.

Connector and transformer blocks are connected after this EM extraction. Run
directories are never reused, so numerical setup revisions remain inspectable.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import time
import numpy as np
from shapely.geometry import Polygon, Point

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INSTALL = ROOT / 'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH'] = str(INSTALL)
os.environ['CSXCAD_INSTALL_PATH'] = str(INSTALL)
DLL_DIRECTORY = os.add_dll_directory(str(INSTALL))
from CSXCAD import ContinuousStructure
from CSXCAD.CSProperties import PropertyType
from openEMS import openEMS


def make_grid(model, axis, step):
    dim = 'xyz'.index(axis)
    extent = [80, 74][dim]
    # Keep every plated barrel on an electric-field mesh edge.
    mandatory = [v['xy'][dim] for v in model['vias']]
    mandatory += [p['xy'][dim] for p in model['pads'] if p['drill'][0]]
    mandatory += [p[k][dim] for p in model['ports'] for k in ['start', 'stop']]
    mandatory = sorted(set(round(x, 7) for x in mandatory))
    critical = []
    for value in mandatory:
        if not critical or value-critical[-1] >= .035:
            critical.append(value)
    # Apply symmetric edge sampling to the long single-ended and paired runs.
    # The coordinate transverse to a horizontal run is Y, and vice versa.
    features = sorted(set((float(t['start'][dim]), float(t['width']))
                         for t in model['tracks']
                         if abs(t['start'][dim]-t['end'][dim]) < 1e-8
                         and abs(t['start'][1-dim]-t['end'][1-dim]) > 8))
    protected, chosen = [], []
    for center, width in features:
        edge = .075
        inner, outer = width/2-edge/3, width/2+2*edge/3
        count = max(2, int(np.ceil(2*inner/edge)))
        chosen.extend(center+np.linspace(-inner, inner, count+1))
        chosen.extend([center-outer, center+outer])
        protected.append((center-outer-.035, center+outer+.035))
    chosen = list(np.unique(np.round(chosen, 8)))
    # Dense XY sampling covers every signal route, including the SMA side.
    background = np.arange(4, extent-2+step, step)
    local = [v['xy'][dim]+off for v in model['vias'] for off in [-.10, .10]]
    for value in critical+local+list(background):
        if any(lo-1e-8 < value < hi+1e-8 for lo, hi in protected):
            continue
        if chosen and np.min(abs(np.array(chosen)-value)) < .0349:
            continue
        chosen.append(float(value))
    return np.unique(np.round([-10, 0, *chosen, extent, extent+10], 8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--drive', type=int, default=1, choices=range(1, 25))
    ap.add_argument('--step', type=float, default=.16)
    ap.add_argument('--time-ns', type=float, default=5)
    ap.add_argument('--steps', type=int, default=1000000)
    ap.add_argument('--threads', type=int, default=24)
    ap.add_argument('--metal', choices=['pec-sheet', 'copper-sheet', 'finite-pec'], default='copper-sheet')
    ap.add_argument('--setup-only', action='store_true')
    args = ap.parse_args()
    out = HERE/'runs'/args.name
    if out.exists():
        raise SystemExit('Choose a fresh run name; existing evidence is preserved.')
    out.mkdir(parents=True)
    shutil.copy2(Path(__file__), out/'builder.py')
    source = HERE/'input/brj2-pcb-model.json'
    d = json.loads(source.read_text())
    fdtd = openEMS(NrTS=args.steps, MaxTime=args.time_ns*1e-9, EndCriteria=1e-8)
    fdtd.SetGaussExcite(0, 2e9)
    fdtd.SetOverSampling(10)
    fdtd.SetBoundaryCond(['MUR']*6)
    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)
    fr4 = csx.AddMaterial('prepreg_Dk4.4_lossless', epsilon=4.4)
    core = csx.AddMaterial('core_Dk4.36_lossless', epsilon=4.36)
    air = csx.AddMaterial('air', epsilon=1)
    pec = csx.AddMetal('barrel_PEC')
    fr4.AddBox([0, 0, .035], [80, 74, 1.5512], priority=0)
    core.AddBox([0, 0, .2454], [80, 74, 1.3408], priority=1)
    finite = args.metal == 'finite-pec'
    layers = {'F.Cu': (0 if finite else .035, .035),
              'In1.Cu': (.2454, .2454), 'In2.Cu': (1.3408, 1.3408),
              'B.Cu': (1.5512, 1.5862 if finite else 1.5512)}
    copper = {}
    for layer in layers:
        copper[layer] = (csx.AddConductingSheet('copper_'+layer, conductivity=58e6,
                         thickness=(35e-6 if layer in ['F.Cu', 'B.Cu'] else 15.2e-6))
                         if args.metal == 'copper-sheet' else pec)
    for layer, polys in d['copper'].items():
        z0, z1 = layers[layer]
        def polygon(prop, points, priority):
            if z0 == z1:
                prop.AddPolygon(np.array(points).T.tolist(), 2, z0, priority=priority)
            else:
                prop.AddLinPoly(np.array(points).T.tolist(), 2, z0, z1-z0, priority=priority)
        for poly in polys:
            polygon(copper[layer], poly['outer'], 20)
            for hole in poly['holes']:
                polygon(air if layer in ['F.Cu', 'B.Cu'] else core, hole, 21)
        for pad in d['pads']:
            # Outer-layer polygons already contain every pad and have no holes.
            # Only inner signal islands need restoring over plane clearances.
            if layer in ['In1.Cu', 'In2.Cu'] and not pad['npth'] and pad['net'] != '/GND':
                for poly in pad['polygons'].get(layer, []):
                    polygon(copper[layer], poly['outer'], 22)
    for pad in d['pads']:
        x, y = pad['xy']
        dx, dy = pad['drill']
        if not dx:
            continue
        assert abs(dx-dy) < 1e-7, 'Slotted drill needs explicit geometry'
        prop = air if pad['npth'] else pec
        prop.AddCylinder([x, y, 0], [x, y, 1.5862], dx/2+(0 if pad['npth'] else .025), priority=31)
    for via in d['vias']:
        x, y = via['xy']
        pec.AddCylinder([x, y, 0], [x, y, 1.5862], via['drill']/2+.025, priority=31)
    for axis in 'xy':
        grid.AddLine(axis, make_grid(d, axis, args.step))
        grid.SmoothMeshLines(axis, 2.0, 1.35)
    zz = [-10, -1, -.3, .035, .10513, .17527, .2454, .52, .793, 1.067,
          1.3408, 1.41093, 1.48107, 1.5512, 1.8512, 2.55, 11.5862]
    if finite:
        zz += [0, 1.5862]
    grid.AddLine('z', zz)
    grid.SmoothMeshLines('z', 2.0, 1.35)
    lines = {axis: np.array(grid.GetLines(axis)) for axis in 'xyz'}
    assert not csx.Update()
    snap = lambda v, axis: float(lines[axis][np.argmin(abs(lines[axis]-v))])
    is_copper = lambda prop: prop is not None and (prop.GetName().startswith('copper_') or prop.GetName() == 'barrel_PEC')
    ports, pm = [], []
    for p in d['ports']:
        start = [snap(p['start'][i], axis) for i, axis in enumerate('xyz')]
        stop = [snap(p['stop'][i], axis) for i, axis in enumerate('xyz')]
        original_start, original_stop = start.copy(), stop.copy()
        axis = p['direction']
        dim = 'xyz'.index(axis)
        lo, hi = sorted([start[dim], stop[dim]])
        indices = np.flatnonzero((lines[axis] >= lo-1e-8) & (lines[axis] <= hi+1e-8))
        free, audit = [], []
        for i in indices[:-1]:
            q = start.copy()
            q[dim] = float((lines[axis][i]+lines[axis][i+1])/2)
            prop = csx.GetPropertyByCoordPriority(q, prop_type=PropertyType.MATERIAL | PropertyType.METAL)
            audit.append({'edge': int(i), 'material': prop.GetName() if prop else 'default air'})
            if not is_copper(prop):
                free.append(int(i))
        assert free and free == list(range(free[0], free[-1]+1)), (p['name'], 'invalid port gap', audit)
        bounds = [float(lines[axis][free[0]]), float(lines[axis][free[-1]+1])]
        if start[dim] > stop[dim]:
            bounds.reverse()
        start[dim], stop[dim] = bounds
        pad = next(q for q in d['pads'] if q['ref'] == p['ref'] and q['pin'] == p['pin'])
        reference = any(Polygon(q['outer'], q['holes']).buffer(1e-8).covers(Point(original_start[:2]))
                        for q in d['copper'][p['reference_layer']])
        own_pad = any(Polygon(q['outer'], q['holes']).buffer(1e-8).covers(Point(original_stop[:2]))
                      for q in pad['polygons'][p['signal_layer']])
        assert reference and own_pad, (p['name'], 'snapped port endpoint misses own copper')
        excite = int(p['number'] == args.drive)
        ports.append(fdtd.AddLumpedPort(p['number'], 50, start, stop, axis, excite=excite, priority=40))
        pm.append(p | {'start': start, 'stop': stop, 'original_start': original_start,
                       'original_stop': original_stop, 'excite': excite, 'edge_audit': audit})
    assert not csx.Update()
    via_audit = []
    for v in d['vias']:
        dx = float(np.min(abs(lines['x']-v['xy'][0])))
        dy = float(np.min(abs(lines['y']-v['xy'][1])))
        radius = v['drill']/2+.025
        assert np.hypot(dx, dy) < radius*.95, ('Unsampled plated barrel', v)
        via_audit.append({'net': v['net'], 'distance_mm': float(np.hypot(dx, dy)), 'radius_mm': radius})
    meta = {'args': vars(args), 'pcb_sha256': d['pcb_sha256'],
            'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'grid': {k: len(v) for k, v in lines.items()},
            'cells': int(np.prod([len(v)-1 for v in lines.values()])),
            'min_spacing_mm': {k: float(np.min(np.diff(v))) for k, v in lines.items()},
            'ports': pm, 'via_audit': via_audit,
            'model': 'CAD copper and pad polygons, all plated barrels and GND planes; no external connector bodies or balun inside EM domain.',
            'dielectric': 'CAD nominal Dk, lossless; no soldermask',
            'copper': args.metal, 'boundary': 'MUR, 10 mm air margin',
            'new_rf_measurements_used': False}
    (out/'model.json').write_text(json.dumps(meta, indent=2)+'\n')
    np.savez(out/'grid.npz', **lines)
    csx.Write2XML(str(out/'geometry.xml'))
    fdtd.Write2XML(str(out/'solver.xml'))
    print('SETUP', json.dumps({k: meta[k] for k in ['grid', 'cells', 'min_spacing_mm', 'copper']}), flush=True)
    if args.setup_only:
        return
    began = time.perf_counter()
    fdtd.Run(str(out), cleanup=False, numThreads=args.threads, verbose=1, dump_statistics=True)
    meta['wall_seconds'] = time.perf_counter()-began
    freq = np.linspace(1e6, 200e6, 1601)
    arrays = {'frequency_hz': freq}
    for p in ports:
        p.CalcPort(str(out), freq, ref_impedance=50)
        key = str(p.number)
        for name in ['uf_inc', 'uf_ref', 'uf_tot', 'if_tot', 'u_time', 'i_time', 'ut_tot', 'it_tot']:
            if hasattr(p, name):
                arrays[name+'_'+key] = getattr(p, name)
    np.savez(out/'results.npz', **arrays)
    (out/'model.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('DONE', json.dumps({'drive': args.drive, 'wall_seconds': meta['wall_seconds'], 'output': str(out)}), flush=True)


if __name__ == '__main__':
    main()
