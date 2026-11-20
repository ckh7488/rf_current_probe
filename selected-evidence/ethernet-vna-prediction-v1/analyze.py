"""Recover S=B/A, connect the forward model, and export premeasurement traces."""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
from datetime import datetime, timezone, timedelta
import numpy as np
import skrf as rf
from network import assembled, self_checks

HERE = Path(__file__).resolve().parent


def matrix_from_waves(a, b):
    # A has incident port as row and independent excitation as column.
    return np.linalg.solve(a.transpose(0, 2, 1), b.transpose(0, 2, 1)).transpose(0, 2, 1)


def wave_matrices(folders, cutoff_ns=None):
    frequency = np.linspace(1e6, 200e6, 1601)
    a = np.empty((len(frequency), 24, 24), complex)
    b = np.empty_like(a)
    signatures = []
    for column, folder in enumerate(folders):
        meta = json.loads((folder/'model.json').read_text())
        assert meta['args']['drive'] == column+1
        signatures.append((meta['input_sha256'], meta['args']['step'], meta['args']['metal'],
                           hashlib.sha256((folder/'grid.npz').read_bytes()).hexdigest()))
        with np.load(folder/'results.npz') as data:
            np.testing.assert_allclose(data['frequency_hz'], frequency)
            if cutoff_ns is None:
                a[:,:,column]=np.stack([data['uf_inc_'+str(i)] for i in range(1,25)],axis=1)
                b[:,:,column]=np.stack([data['uf_ref_'+str(i)] for i in range(1,25)],axis=1)
            else:
                spectra=[]
                for kind in ['u','i']:
                    t=data[kind+'_time_1'];keep=t<=cutoff_ns*1e-9
                    for row in range(2,25):np.testing.assert_array_equal(data[kind+'_time_'+str(row)],t)
                    values=np.stack([data[kind+'t_tot_'+str(i)] for i in range(1,25)],axis=1)
                    dt=float(np.mean(np.diff(t)))
                    spectra.append(2*dt*np.exp(-2j*np.pi*frequency[:,None]*t[keep]) @ values[keep])
                voltage,current=spectra
                a[:,:,column],b[:,:,column]=(voltage+50*current)/2,(voltage-50*current)/2
    assert len(set(signatures)) == 1, 'Mixing extraction geometry or mesh revisions is not allowed'
    assert np.isfinite(a).all() and np.isfinite(b).all()
    return frequency, matrix_from_waves(a, b), a


def observables(networks):
    return {'open_b_s11': networks['open'][:, 1, 1],
            'open_d_to_c_s21': networks['open'][:, 2, 3],
            'matched_a_s11': networks['match'][:, 0, 0],
            'loopback_d_to_c_s21': networks['loopback'][:, 2, 3]}


def csv_traces(path, frequency, curves):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['frequency_hz']+[key+'_'+part for key in curves for part in ['real', 'imag', 'db', 'phase_deg']])
        for i, f in enumerate(frequency):
            values = [float(f)]
            for curve in curves.values():
                v = curve[i]
                values.extend([float(v.real), float(v.imag), float(20*np.log10(max(abs(v), 1e-30))), float(np.angle(v, deg=True))])
            writer.writerow(values)


def self_check_matrix():
    rng = np.random.default_rng(42)
    s = (rng.normal(size=(3, 24, 24))+1j*rng.normal(size=(3, 24, 24)))*.01
    a = np.eye(24)[None, :, :]+(rng.normal(size=s.shape)+1j*rng.normal(size=s.shape))*.02
    np.testing.assert_allclose(matrix_from_waves(a, s @ a), s, atol=1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prefix', default='nominal-v1-p')
    ap.add_argument('--output', default='prediction-v1')
    ap.add_argument('--self-check-only', action='store_true')
    ap.add_argument('--input-freeze')
    args = ap.parse_args()
    self_checks()
    self_check_matrix()
    if args.self_check_only:
        print('Incident-wave matrix recovery: passed')
        return
    out = HERE/args.output
    if out.exists():
        raise SystemExit('Choose a fresh output folder; previous predictions are preserved.')
    folders = [HERE/'runs'/f'{args.prefix}{i:02d}' for i in range(1, 25)]
    classifications={json.loads((p/'model.json').read_text()).get('classification','SIMULATED') for p in folders}
    assert len(classifications)==1,'Do not mix synthetic checks with simulated outputs'
    classification=classifications.pop()
    frequency, pcb, incident = wave_matrices(folders)
    parameters = json.loads((HERE/'electrical-assumptions.json').read_text())
    out.mkdir()
    np.savez(out/'pcb-network.npz', frequency_hz=frequency, s=pcb)
    networks = {mode: assembled(pcb, frequency, mode, parameters) for mode in ['open', 'match', 'loopback']}
    curves = observables(networks)
    csv_traces(out/'predicted-observables.csv', frequency, curves)
    for mode, s in networks.items():
        network = rf.Network(frequency=rf.Frequency.from_f(frequency, unit='Hz'), s=s, z0=50)
        network.comments = classification+' forward model. SMA ports A/J2 B/J3 C/J4 D/J5. See electrical-assumptions.json.'
        network.write_touchstone(str(out/f'{mode}-sma'))
    diagonal=np.diagonal(incident,axis1=1,axis2=2)
    normalized_incident=incident/diagonal[:,None,:]
    checks = {'max_incident_matrix_condition': float(np.linalg.cond(normalized_incident).max()),
              'max_unscaled_incident_matrix_condition':float(np.linalg.cond(incident).max()),
              'pcb_max_singular_value': float(np.linalg.svd(pcb, compute_uv=False).max()),
              'pcb_max_reciprocity_error_linear': float(abs(pcb-pcb.transpose(0, 2, 1)).max()),
              'time_windows': {}}
    numerical_floor={key:np.zeros(len(frequency)) for key in curves}
    for cutoff in [3, 4]:
        _, truncated, _ = wave_matrices(folders, cutoff)
        shorter = observables({mode: assembled(truncated, frequency, mode, parameters) for mode in networks})
        checks['time_windows'][str(cutoff)+'ns'] = {
            key: {'max_complex_difference': float(abs(curves[key]-shorter[key]).max()),
                  'difference_at_100mhz_db': float(20*np.log10(max(abs(np.interp(100e6, frequency, curves[key]-shorter[key])), 1e-30)))}
            for key in curves}
        for key in curves:
            numerical_floor[key]=np.maximum(numerical_floor[key],abs(curves[key]-shorter[key]))
    variations=[('rj_contact_low',['rj45','jack_contact_path_mm'],10.0),
                ('rj_contact_high',['rj45','jack_contact_path_mm'],30.0),
                ('plug_path_low',['plug','internal_path_mm'],32.0),
                ('plug_path_high',['plug','internal_path_mm'],48.0),
                ('plug_velocity_low',['plug','internal_velocity_factor'],.55),
                ('plug_velocity_high',['plug','internal_velocity_factor'],.80),
                ('load_inductance_low',['plug','matched_pair','series_inductance_nh'],4.0),
                ('load_inductance_high',['plug','matched_pair','series_inductance_nh'],20.0),
                ('load_capacitance_low',['plug','matched_pair','parallel_capacitance_pf'],0.0),
                ('load_capacitance_high',['plug','matched_pair','parallel_capacitance_pf'],.40),
                ('loop_inductance_low',['plug','loopback','series_inductance_per_join_nh'],1.0),
                ('loop_inductance_high',['plug','loopback','series_inductance_per_join_nh'],6.0)]
    sensitivity={key:[value] for key,value in curves.items()}
    for name,path,value in variations:
        variant=copy.deepcopy(parameters);target=variant
        for part in path[:-1]:target=target[part]
        target[path[-1]]=value
        changed=observables({mode:assembled(pcb,frequency,mode,variant) for mode in networks})
        csv_traces(out/(name+'.csv'),frequency,changed)
        for key in curves:sensitivity[key].append(changed[key])
    with (out/'sensitivity-and-numerical-floor.csv').open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['frequency_hz']+[key+'_'+part for key in curves for part in ['oat_min_db','oat_max_db','time_window_difference_db']])
        bounds={key:20*np.log10(np.maximum(abs(np.stack(values)),1e-30)) for key,values in sensitivity.items()}
        for i,f in enumerate(frequency):
            row=[float(f)]
            for key in curves:
                row.extend([float(bounds[key][:,i].min()),float(bounds[key][:,i].max()),
                            float(20*np.log10(max(numerical_floor[key][i],1e-30)))])
            writer.writerow(row)
    samples = {}
    for mhz in [1, 10, 50, 100, 150, 200]:
        samples[str(mhz)] = {}
        for key, values in curves.items():
            value = np.interp(mhz*1e6, frequency, values)
            samples[str(mhz)][key] = {'db': float(20*np.log10(max(abs(value), 1e-30))), 'phase_deg': float(np.angle(value, deg=True))}
    report = {'classification': classification, 'new_rf_measurements_used': False,
              'prediction_status': 'NUMERICAL_REVIEW_REQUIRED', 'samples_mhz': samples,
              'checks': checks, 'parameters_sha256': hashlib.sha256((HERE/'electrical-assumptions.json').read_bytes()).hexdigest(),
              'run_folders': [str(p.relative_to(HERE)) for p in folders],
              'sensitivity':'Twelve one-at-a-time input variations plus nominal; not statistical confidence bounds',
              'numerical_floor':'Complex change between full record and 3 ns / 4 ns truncations, not a measurement noise floor'}
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    receipt={'classification':classification+'_OUTPUT_RECEIPT','new_rf_measurements_used':False,
             'created_at_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),
             'input_manifest_sha256':hashlib.sha256((HERE/args.input_freeze/'manifest.json').read_bytes()).hexdigest() if args.input_freeze else None,
             'files':[{'file':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                      for p in sorted(out.iterdir()) if p.is_file()],
             'raw_results':[{'folder':str(p.relative_to(HERE)),'results_sha256':hashlib.sha256((p/'results.npz').read_bytes()).hexdigest(),
                             'model_sha256':hashlib.sha256((p/'model.json').read_bytes()).hexdigest()}
                            for p in folders]}
    (out/'output-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (out/'SHA256.txt').write_text(hashlib.sha256((out/'output-receipt.json').read_bytes()).hexdigest()+'  output-receipt.json\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
